from __future__ import annotations

from typing import Optional

import pandas as pd


def prep_analytics_frame(df: pd.DataFrame) -> pd.DataFrame:
    """
    Prepare DataFrame for analytics by adding derived columns.
    
    Args:
        df: Raw transaction DataFrame
        
    Returns:
        DataFrame with Month, Expense, Income, and Category columns added
    """
    out = df.copy()
    out["Date"] = pd.to_datetime(out["Date"], errors="coerce")
    out = out.dropna(subset=["Date"]).copy()
    date_series = pd.to_datetime(out["Date"], errors="coerce")
    out["Month"] = date_series.dt.to_period("M").dt.to_timestamp()

    out["Amount"] = pd.to_numeric(out["Amount"], errors="coerce")
    out["Type"] = out["Type"].astype(str).str.title()

    is_debit = out["Type"] == "Debit"
    is_credit = out["Type"] == "Credit"

    amt = out["Amount"].fillna(0.0).astype(float)
    out["Expense"] = 0.0
    out.loc[is_debit, "Expense"] = amt.loc[is_debit].abs()
    out["Income"] = 0.0
    out.loc[is_credit, "Income"] = amt.loc[is_credit].abs()

    if "Category" in out.columns:
        out["Category"] = out["Category"].fillna("Misc")
    else:
        out["Category"] = "Misc"
    return out


def latest_cash_balance(df: pd.DataFrame) -> Optional[float]:
    """
    Extract the most recent cash balance from statement Balance column.
    
    Args:
        df: Transaction DataFrame with Balance column
        
    Returns:
        Most recent balance or None if not available
    """

    if df.empty or "Balance" not in df.columns:
        return None

    balances = df.copy()
    balances["Balance"] = pd.to_numeric(balances["Balance"], errors="coerce")

    if "Date" in balances.columns:
        balances["Date"] = pd.to_datetime(balances["Date"], errors="coerce")
        with_dates = balances.dropna(subset=["Balance", "Date"]).sort_values("Date")
        if not with_dates.empty:
            val = with_dates.iloc[-1]["Balance"]
            return None if pd.isna(val) else float(val)

    no_dates = balances.dropna(subset=["Balance"])
    if not no_dates.empty:
        val = no_dates.iloc[-1]["Balance"]
        return None if pd.isna(val) else float(val)

    return None
