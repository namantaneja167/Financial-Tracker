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


def _normalize_record(record: Dict[str, Any]) -> Dict[str, Any]:
    date_value = record.get("Date") or record.get("date")
    description = record.get("Description") or record.get("description")
    amount = record.get("Amount") or record.get("amount")
    tx_type = record.get("Type") or record.get("type")
    balance = record.get("Balance") or record.get("balance")

    normalized: Dict[str, Any] = {
        "Date": str(date_value).strip() if date_value is not None else None,
        "Description": str(description).strip() if description is not None else "",
        "Amount": _to_number(amount),
        "Type": (str(tx_type).strip().title() if tx_type is not None else None),
        "Balance": _to_number(balance),
    }

    if not normalized["Type"] and normalized["Amount"] is not None:
        normalized["Type"] = "Credit" if normalized["Amount"] >= 0 else "Debit"

    return normalized


def _extract_transaction_list(parsed: Any) -> List[Dict[str, Any]]:
    """Try to pull a list of transactions out of various response shapes."""
    if isinstance(parsed, list):
        return parsed
    if isinstance(parsed, dict):
        # Common keys used by different models
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


def ollama_extract_transactions(raw_text: str) -> List[Dict[str, Any]]:
    """Call local Ollama and ask it to output structured transaction JSON."""
    
    if not raw_text or len(raw_text.strip()) < 50:
        raise ValueError(f"PDF text is too short or empty ({len(raw_text)} chars). Cannot extract transactions.")

    # For very large PDFs, truncate to avoid overwhelming smaller models
    max_chars = 50000
    if len(raw_text) > max_chars:
        logger.warning(f"PDF text is {len(raw_text)} chars, truncating to {max_chars} for model processing")
        raw_text = raw_text[:max_chars] + "\n... [truncated]"

    logger.info(f"Sending {len(raw_text)} characters to Ollama model {get_ollama_model()}")

    prompt = (
        "Extract bank transactions from this statement. Return JSON array format:\n"
        "[{\"Date\": \"YYYY-MM-DD\", \"Description\": \"text\", \"Amount\": 123.45, \"Type\": \"Debit\" or \"Credit\", \"Balance\": 1000.00}]\n\n"
        "Rules:\n"
        "- Return ONLY the JSON array, no other text\n"
        "- Date format: keep as-is from statement\n"
        "- Amount: number only\n"
        "- Type: must be 'Debit' or 'Credit'\n"
        "- Balance: running balance if shown, otherwise null\n\n"
        f"Statement text:\n{raw_text}"
    )

    url = f"{get_ollama_url()}/api/generate"
    try:
        resp = requests.post(
            url,
            json={
                "model": get_ollama_model(),
                "prompt": prompt,
                "stream": False,
                "format": "json",  # force JSON-only response if model supports it
                "options": {
                    "temperature": 0,
                },
            },
            headers=get_ollama_headers(),
            timeout=get_ollama_timeout(),
        )
    except requests.exceptions.ReadTimeout as exc:
        raise RuntimeError(
            f"Ollama timed out after {get_ollama_timeout()}s. The PDF may be too large or the model is slow. "
            "Try a smaller PDF or increase the timeout in config.yaml (ollama.timeout)."
        ) from exc

    if resp.status_code == 401:
        raise RuntimeError(
            "Ollama returned 401 Unauthorized. If your Ollama server requires a token, set OLLAMA_API_KEY=<token> and restart the app."
        )

    resp.raise_for_status()

    try:
        data = resp.json()
    except ValueError as exc:
        raise RuntimeError(f"Ollama response was not JSON: {resp.text[:500]}") from exc

    content = (data.get("response") or "").strip()

    logger.info(f"Ollama returned {len(content)} characters")
    
    if not content:
        raise ValueError("Ollama returned an empty response. The model may not support this PDF format or the text is unreadable.")

    try:
        parsed = _extract_transaction_list(_extract_json_block(content))
    except ValueError as exc:
        snippet = content[:500]
        logger.error(f"Failed to parse Ollama response. First 500 chars: {snippet}")
        raise ValueError(f"Model did not return a JSON array of transactions. Response snippet: {snippet}") from exc

    normalized: List[Dict[str, Any]] = []
    for item in parsed:
        if isinstance(item, dict):
            normalized.append(_normalize_record(item))
    
    logger.info(f"Extracted {len(normalized)} transactions from Ollama response")
    
    if not normalized:
        raise ValueError("Ollama returned JSON but no valid transaction records were found. The model may have misunderstood the statement format.")

    return normalized
