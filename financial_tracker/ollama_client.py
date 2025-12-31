import json
import os
import re
from typing import Any, Dict, List, Optional
import time

import requests
from financial_tracker.config import get_ollama_url, get_ollama_model, get_ollama_timeout, get
from financial_tracker.logging_config import get_logger

logger = get_logger(__name__)


def _extract_json_block(text: str) -> Any:
    """Pull the first JSON object/array out of a model response."""
    text = text.strip()

    array_match = re.search(r"\[(?:.|\n|\r)*\]", text)
    if array_match:
        return json.loads(array_match.group(0))

    obj_match = re.search(r"\{(?:.|\n|\r)*\}", text)
    if obj_match:
        return json.loads(obj_match.group(0))

    return json.loads(text)


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


def ollama_extract_transactions(raw_text: str) -> List[Dict[str, Any]]:
    """Call local Ollama and ask it to output structured transaction JSON."""

    prompt = (
        "You are a precise data extraction engine.\n"
        "Extract bank statement transactions from the RAW TEXT below.\n\n"
        "Return ONLY valid JSON (no markdown, no commentary).\n"
        "Output format must be a JSON array of objects.\n"
        "Each object MUST have these keys exactly: Date, Description, Amount, Type, Balance\n"
        "- Date: keep the statement date string as written (e.g., 2025-12-01 or 12/01/2025).\n"
        "- Description: merchant/payee + memo text.\n"
        "- Amount: a number (negative for debits is allowed, but not required if Type is set).\n"
        "- Type: must be either 'Debit' or 'Credit'.\n"
        "- Balance: number if present on the statement line, otherwise null.\n"
        "If you are unsure about a field, use null (except Description which can be empty string).\n\n"
        "RAW TEXT:\n"
        + raw_text
    )

    url = f"{get_ollama_url()}/api/generate"
    resp = requests.post(
        url,
        json={
            "model": get_ollama_model(),
            "prompt": prompt,
            "stream": False,
            "options": {"temperature": 0},
        },
        timeout=get_ollama_timeout(),
    )
    resp.raise_for_status()
    data = resp.json()
    content = (data.get("response") or "").strip()

    parsed = _extract_json_block(content)
    if isinstance(parsed, dict):
        parsed = parsed.get("transactions")

    if not isinstance(parsed, list):
        raise ValueError("Model did not return a JSON array of transactions")

    normalized: List[Dict[str, Any]] = []
    for item in parsed:
        if isinstance(item, dict):
            normalized.append(_normalize_record(item))

    return normalized
