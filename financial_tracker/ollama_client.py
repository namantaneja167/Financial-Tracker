import json
import os
import re
from typing import Any, Dict, List, Optional
import time

import requests
from financial_tracker.config import (
    get_ollama_url,
    get_ollama_model,
    get_ollama_timeout,
    get_ollama_headers,
)
from financial_tracker.logging_config import get_logger

logger = get_logger(__name__)


def _extract_json_block(text: str) -> Any:
    """Pull the first JSON object/array out of a model response with clearer errors."""
    text = (text or "").strip()
    if not text:
        raise ValueError("Empty response from Ollama model")

    try:
        array_match = re.search(r"\[(?:.|\n|\r)*\]", text)
        if array_match:
            return json.loads(array_match.group(0))

        obj_match = re.search(r"\{(?:.|\n|\r)*\}", text)
        if obj_match:
            return json.loads(obj_match.group(0))

        return json.loads(text)
    except json.JSONDecodeError as exc:
        snippet = text[:500]
        raise ValueError(f"Model response was not valid JSON (first 500 chars): {snippet}") from exc


def _to_number(value: Any) -> Optional[float]:
    if value is None:
        return None
    if isinstance(value, (int, float)):
        return float(value)
    s = str(value).strip()
    if not s:
        return None
    s = s.replace(",", "")
    s = re.sub(r"[^0-9.\-]", "", s)
    if not s or s in {"-", "."}:
        return None
    try:
        return float(s)
    except ValueError:
        return None


def _is_metadata_or_summary_row(record: Dict[str, Any]) -> bool:
    """Detect if a record is metadata/summary rather than actual transaction."""
    # Check for suspicious field values that indicate metadata
    description = str(record.get("Description") or record.get("description") or "").lower()
    amount = record.get("Amount") or record.get("amount")
    
    # Skip rows with empty descriptions
    if not description or len(description.strip()) == 0:
        logger.debug(f"Skipping row with empty description")
        return True
    
    # Skip rows that look like headers or metadata keywords
    metadata_keywords = {"opening balance", "closing balance", "total", "statement", "date range", 
                         "account number", "account holder", "balance as on", "page", "continued",
                         "beginning balance", "ending balance", "summary", "account summary"}
    if any(keyword in description for keyword in metadata_keywords):
        logger.debug(f"Skipping metadata row: {description[:50]}")
        return True
    
    # Skip rows with suspiciously round or large amounts (likely totals)
    if isinstance(amount, (int, float)) and amount is not None:
        # Amounts >= 1,000,000 are likely summaries or invalid
        if amount >= 1000000:
            logger.debug(f"Skipping row with excessive amount: {amount}")
            return True
        
        # Amounts ending in .00 could be totals/summaries (heuristic)
        if amount > 10000 and amount == int(amount):
            # Check if description has "total" variants
            if any(t in description for t in ["total", "sum", "batch"]):
                logger.debug(f"Skipping likely summary row: {description} ({amount})")
                return True
    
    return False


def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    date_value = record.get("Date") or record.get("date") or record.get("transactionDate") or record.get("transactiondate") or record.get("Value Date") or record.get("value_date")
    description = record.get("Description") or record.get("description") or record.get("remarks") or record.get("Remarks") or record.get("Transaction Remarks") or record.get("remark")
    amount = record.get("Amount") or record.get("amount") or record.get("amountPaid") or record.get("amountpaid") or record.get("Withdrawal Amount") or record.get("withdrawal_amount") or record.get("Deposit Amount") or record.get("deposit_amount")
    tx_type = record.get("Type") or record.get("type")
    balance = record.get("Balance") or record.get("balance") or record.get("Balance(INR)") or record.get("balance_amount")

    # Normalize Type field: check for Debit/Credit keywords or Withdrawal/Deposit
    def normalize_type(type_str: Any, amount_val: Any) -> str:
        """Infer Debit/Credit from type string or amount sign."""
        if type_str:
            type_lower = str(type_str).lower().strip()

            # Check for explicit Debit/Credit keywords
            if "debit" in type_lower or "withdrawal" in type_lower:
                return "Debit"
            elif "credit" in type_lower or "deposit" in type_lower:
                return "Credit"

            # If type_str contains slashes or looks like a description, it's probably malformed
            # Default to Debit for malformed types (don't infer from amount)
            if "/" in type_str or len(type_str) > 50:
                logger.warning(f"Type field looks malformed: '{type_str}', defaulting to Debit")
                return "Debit"
            
            # Last resort: accept if it's already Debit/Credit (case-insensitive)
            if type_lower in ["debit", "credit"]:
                return type_lower.capitalize()
            
            # Unknown type format, infer from amount
            logger.warning(f"Unknown transaction type: '{type_str}', inferring from amount")

        # If no type or type was unparseable, infer from amount
        amount_num = _to_number(amount_val)
        if amount_num is not None and amount_num > 0:
            return "Credit"
        elif amount_num is not None and amount_num < 0:
            return "Debit"
        
        # Last resort: default to Debit
        return "Debit"

    normalized_type = normalize_type(tx_type, amount)
    
    normalized: Dict[str, Any] = {
        "Date": str(date_value).strip() if date_value is not None else None,
        "Description": str(description).strip() if description is not None else "",
        "Amount": _to_number(amount),
        "Type": normalized_type,
        "Balance": _to_number(balance),
    }

    return normalized


def _extract_transaction_list(parsed: Any) -> List[Dict[str, Any]]:
    """Try to pull a list of transactions out of various response shapes."""
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        # If it looks like a single transaction record, wrap it in a list
        # Check for transaction-like keys (date, amount, description, etc.)
        tx_keys = {"date", "amount", "type", "description", "balance", "transactionid", "transactionid"}
        if any(key.lower() in parsed for key in tx_keys):
            logger.warning("Single transaction object detected, wrapping in list")
            return [parsed]
        
        # Common keys used by different models for transaction arrays
        for key in ("transactions", "data", "items", "records", "result"):
            val = parsed.get(key)
            if isinstance(val, list):
                return val
        # If dict values contain a list (possibly nested), return the first list found
        stack = list(parsed.values())
        while stack:
            v = stack.pop(0)
            if isinstance(v, list):
                return v
            if isinstance(v, dict):
                stack.extend(v.values())
    raise ValueError("Model did not return a JSON array of transactions")


def _clean_pdf_text(raw_text: str) -> str:
    """Clean and normalize PDF-extracted text for better model processing."""
    # Remove common HTML/XML artifacts
    text = raw_text
    
    # Remove HTML/XML tags
    import re
    text = re.sub(r'<[^>]+>', '', text)  # Remove HTML tags
    text = re.sub(r'\{["\']?row["\']?:\s*\d+[^}]*\}', '', text)  # Remove row metadata objects
    
    # Clean up excess whitespace while preserving line structure
    lines = []
    for line in text.split('\n'):
        # Strip leading/trailing whitespace but preserve internal structure
        line = line.strip()
        if line:  # Only keep non-empty lines
            lines.append(line)
    
    text = '\n'.join(lines)
    return text



def _extract_chunk(chunk_text: str, chunk_num: int, total_chunks: int) -> List[Dict[str, Any]]:
    import google.generativeai as genai
    from financial_tracker.config import get_google_api_key, get_gemini_model, get_ollama_model

    api_key = get_google_api_key()
    if not api_key:
         raise RuntimeError("GOOGLE_API_KEY not found. Please check .env file.")

    genai.configure(api_key=api_key)
    # Use "gemini-2.0-flash-exp" or "gemini-1.5-flash" if available for speed, otherwise config default
    model_name = get_gemini_model() 
    model = genai.GenerativeModel(model_name)

    logger.info(f"Processing chunk {chunk_num}/{total_chunks}: {len(chunk_text)} characters using {model_name}")
    
    chunk_note = f" (chunk {chunk_num} of {total_chunks})" if total_chunks > 1 else ""

    prompt = (
        "You are a bank statement parser. Extract transaction data from the text below.\n\n"
        "CRITICAL: Your response MUST be ONLY a JSON array. Do NOT include any explanation or text.\n\n"
        "TASK: Convert EACH INDIVIDUAL TRANSACTION ROW into JSON format\n"
        "OUTPUT FORMAT: Return ONLY a JSON array like this (no other text):\n"
        "[{\"Date\": \"15-01-2024\", \"Description\": \"purchase description\", \"Amount\": 1000.00, \"Type\": \"Debit\", \"Balance\": 50000.00}]\n\n"
        "CRITICAL RULES:\n"
        "- ONLY output the JSON array, absolutely nothing else\n"
        "- NO explanations, NO comments, NO markdown, ONLY JSON\n"
        "- Start your response with [ and end with ]\n"
        "- Extract EVERY transaction row (skip header rows and summary rows)\n"
        f"- This is part of a larger statement{chunk_note}, extract all transactions you see\n"
        "- Do NOT include closing balance, opening balance, or total rows\n"
        "- Do NOT include balance summary rows\n"
        "- Amount: numeric value only, MUST be less than 1,000,000\n"
        "- Do NOT extract rows with suspiciously large round numbers (like 1000000, 999999, etc)\n"
        "- Date format: DD-MM-YYYY or DD.MM.YYYY as shown\n"
        "- Description: extract the transaction remarks/description text (MUST be non-empty, no blanks)\n"
        "- Amount: the numeric value from either Withdrawal or Deposit column\n"
        "- Type: 'Debit' for withdrawals, 'Credit' for deposits\n"
        "- Balance: the closing balance after transaction\n\n"
        "DO NOT EXTRACT:\n"
        "- Row numbers or column headers\n"
        "- HTML/XML tags (row, colspan, data, etc)\n"
        "- Summary rows containing words: 'Total', 'Opening Balance', 'Closing Balance', 'Statement', 'Summary'\n"
        "- Rows with empty descriptions\n"
        "- Rows with amounts >= 1,000,000\n\n"
        "REMEMBER: Output ONLY the JSON array. Start with [ and end with ]. No other text.\n\n"
        "TEXT TO PARSE:\n"
        f"{chunk_text}"
    )

    try:
        response = model.generate_content(prompt, generation_config={"response_mime_type": "application/json"})
        content = response.text
    except Exception as e:
        raise RuntimeError(f"Gemini API Error: {e}")

    logger.info(f"Gemini returned {len(content)} characters")
    
    if not content:
        raise ValueError("Gemini returned an empty response. The model may not support this PDF format or the text is unreadable.")

    try:
        parsed = _extract_transaction_list(_extract_json_block(content))
    except ValueError as exc:
        snippet = content[:500]
        logger.error(f"Failed to parse Gemini response. First 500 chars: {snippet}")
        raise ValueError(f"Model did not return a JSON array of transactions. Response snippet: {snippet}") from exc

    normalized: List[Dict[str, Any]] = []
    for item in parsed:
        if isinstance(item, dict):
            # Filter out metadata/summary rows
            if _is_metadata_or_summary_row(item):
                logger.info(f"FILTERED OUT: {item}")
                continue
            
            normalized.append(_normalize_record(item))
    
    logger.info(f"Extracted {len(normalized)} valid transactions from chunk (filtered {len(parsed) - len(normalized)} metadata/invalid rows)")
    
    return normalized


def ollama_extract_transactions(raw_text: str) -> List[Dict[str, Any]]:
    """Call Google Gemini and ask it to output structured transaction JSON.
    
    For large PDFs, processes in chunks to stay within model context limits.
    """
    
    if not raw_text or len(raw_text.strip()) < 3:
        raise ValueError(f"PDF text is too short or empty ({len(raw_text)} chars). Cannot extract transactions.")

    # Clean the extracted text first
    raw_text = _clean_pdf_text(raw_text)
    
    # For large PDFs, split into chunks
    # Gemini 1.5 Pro/Flash has HUGE context (1M+ tokens), so simple chunking is less critical, 
    # but we keep it for safety and cost control if using Pro.
    original_len = len(raw_text)
    chunk_size = 30000 
    overlap = 500 
    
    if original_len <= chunk_size:
        # Small enough to process in one go
        logger.info(f"Sending {original_len} characters to Gemini")
        return _extract_chunk(raw_text, 1, 1)
    
    # Split into chunks
    chunks = []
    pos = 0
    while pos < original_len:
        # Find end of chunk at line boundary
        end_pos = min(pos + chunk_size, original_len)
        if end_pos < original_len:
            # Try to find a line break near the end
            newline_pos = raw_text.rfind('\n', end_pos - 200, end_pos)
            if newline_pos > pos:
                end_pos = newline_pos
        
        chunk = raw_text[pos:end_pos]
        chunks.append(chunk)
        pos = end_pos - overlap  # Overlap to avoid cutting transactions
    
    logger.info(f"PDF text is {original_len} chars, splitting into {len(chunks)} chunks for processing")
    
    # Process each chunk
    all_transactions = []
    seen_transactions = set()  # To deduplicate overlapping transactions
    
    for i, chunk in enumerate(chunks, 1):
        try:
            chunk_transactions = _extract_chunk(chunk, i, len(chunks))
            
            # Deduplicate based on (Date, Description, Amount)
            for tx in chunk_transactions:
                tx_key = (
                    str(tx.get("Date", "")).strip(),
                    str(tx.get("Description", "")).strip()[:50],  # First 50 chars
                    float(tx.get("Amount", 0))
                )
                if tx_key not in seen_transactions:
                    seen_transactions.add(tx_key)
                    all_transactions.append(tx)
                else:
                    logger.debug(f"Skipping duplicate transaction: {tx_key}")
        
        except Exception as e:
            logger.error(f"Error processing chunk {i}/{len(chunks)}: {e}")
            # Continue with other chunks even if one fails
            continue
    
    logger.info(f"Extracted {len(all_transactions)} total unique transactions from {len(chunks)} chunks")
    
    if not all_transactions:
        logger.warning("Gemini returned no valid transaction records across all chunks. The statement may be empty or the format may not have been recognized.")
    
    return all_transactions

