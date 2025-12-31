import io
from typing import Any, Dict, List

import pandas as pd


def parse_csv_to_transactions(csv_bytes: bytes) -> List[Dict[str, Any]]:
    """Parse a bank CSV export into standard transaction format.

    Returns a list of dicts with keys: Date, Description, Amount, Type, Balance.
    """

    try:
        df = pd.read_csv(io.BytesIO(csv_bytes))
    except Exception:
        return []

    # Common column name mappings (case-insensitive)
    col_map = {
        "date": ["date", "transaction date", "posting date", "trans date"],
        "description": ["description", "memo", "payee", "merchant", "details"],
        "amount": ["amount", "transaction amount", "debit/credit", "value"],
        "type": ["type", "transaction type", "debit/credit"],
        "balance": ["balance", "running balance", "account balance"],
    }

    df.columns = [str(c).strip().lower() for c in df.columns]

    def find_col(aliases: List[str]) -> str:
        for alias in aliases:
            if alias in df.columns:
                return alias
        return ""

    date_col = find_col(col_map["date"])
    desc_col = find_col(col_map["description"])
    amt_col = find_col(col_map["amount"])
    type_col = find_col(col_map["type"])
    balance_col = find_col(col_map["balance"])

    if not date_col or not desc_col or not amt_col:
        return []

    transactions: List[Dict[str, Any]] = []

    for _, row in df.iterrows():
        date_val = str(row[date_col]) if date_col and pd.notna(row[date_col]) else None
        desc_val = str(row[desc_col]).strip() if desc_col and pd.notna(row[desc_col]) else ""
        
        amt_raw = row[amt_col] if amt_col and pd.notna(row[amt_col]) else 0.0
        try:
            amt_val = float(str(amt_raw).replace(",", "").replace("$", "").strip())
        except ValueError:
            amt_val = 0.0

        type_val = None
        if type_col and pd.notna(row[type_col]):
            t = str(row[type_col]).strip().lower()
            if "debit" in t or "withdrawal" in t:
                type_val = "Debit"
            elif "credit" in t or "deposit" in t:
                type_val = "Credit"

        if type_val is None:
            type_val = "Debit" if amt_val < 0 else "Credit"

        balance_val = None
        if balance_col and pd.notna(row[balance_col]):
            try:
                balance_val = float(str(row[balance_col]).replace(",", "").replace("$", "").strip())
            except ValueError:
                pass

        transactions.append({
            "Date": date_val,
            "Description": desc_val,
            "Amount": amt_val,
            "Type": type_val,
            "Balance": balance_val,
        })

    return transactions
