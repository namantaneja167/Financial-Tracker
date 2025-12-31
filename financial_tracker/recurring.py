"""
Detect recurring transactions and predict upcoming expenses.
"""
from typing import List, Dict
from datetime import datetime, timedelta
from collections import defaultdict
import pandas as pd


def detect_recurring_transactions(df: pd.DataFrame, similarity_threshold: float = 0.8) -> List[Dict]:
    """
    Detect recurring transactions based on similar description and amount.
    
    Returns list of recurring patterns with:
    - description: representative description
    - amount: typical amount
    - frequency: days between occurrences
    - last_date: most recent occurrence
    - next_expected: predicted next date
    - occurrences: number of times seen
    """
    if df.empty or "Date" not in df.columns:
        return []
    
    # Convert dates if needed
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    df = df.dropna(subset=["Date"]).sort_values("Date")
    
    # Group by similar description and amount
    patterns = defaultdict(list)
    
    for _, row in df.iterrows():
        desc = str(row.get("Description", "")).lower().strip()
        amount = float(row.get("Amount", 0))
        date = row["Date"]
        
        # Create a simplified key (first few words + amount range)
        desc_key = " ".join(desc.split()[:3])  # First 3 words
        amount_key = round(amount / 10) * 10  # Round to nearest 10
        
        key = (desc_key, amount_key)
        patterns[key].append({
            "date": date,
            "description": row.get("Description", ""),
            "amount": amount,
            "category": row.get("Category", "")
        })
    
    # Analyze patterns for recurring behavior
    recurring = []
    
    for key, transactions in patterns.items():
        if len(transactions) < 2:
            continue  # Need at least 2 occurrences
        
        # Sort by date
        transactions = sorted(transactions, key=lambda x: x["date"])
        
        # Calculate intervals between consecutive transactions
        intervals = []
        for i in range(1, len(transactions)):
            days = (transactions[i]["date"] - transactions[i-1]["date"]).days
            intervals.append(days)
        
        if not intervals:
            continue
        
        # Check if intervals are roughly consistent (monthly: ~30 days, weekly: ~7 days)
        avg_interval = sum(intervals) / len(intervals)
        
        # Only consider if interval is between 7 and 90 days (weekly to quarterly)
        if avg_interval < 7 or avg_interval > 90:
            continue
        
        # Check consistency (standard deviation relative to mean)
        if len(intervals) > 1:
            variance = sum((x - avg_interval) ** 2 for x in intervals) / len(intervals)
            std_dev = variance ** 0.5
            consistency = 1 - (std_dev / avg_interval) if avg_interval > 0 else 0
            
            if consistency < 0.7:  # Require 70% consistency
                continue
        
        last_txn = transactions[-1]
        next_expected = last_txn["date"] + timedelta(days=int(avg_interval))
        
        recurring.append({
            "description": last_txn["description"],
            "amount": last_txn["amount"],
            "category": last_txn["category"],
            "frequency_days": int(avg_interval),
            "last_date": last_txn["date"],
            "next_expected": next_expected,
            "occurrences": len(transactions),
            "confidence": min(consistency, 1.0) if len(intervals) > 1 else 0.8
        })
    
    # Sort by next expected date
    recurring = sorted(recurring, key=lambda x: x["next_expected"])
    
    return recurring


def get_upcoming_recurring_expenses(df: pd.DataFrame, days_ahead: int = 30) -> pd.DataFrame:
    """
    Get recurring expenses expected in the next N days.
    """
    recurring = detect_recurring_transactions(df)
    
    if not recurring:
        return pd.DataFrame()
    
    today = datetime.now()
    cutoff = today + timedelta(days=days_ahead)
    
    upcoming = []
    for rec in recurring:
        if rec["next_expected"] <= cutoff:
            days_until = (rec["next_expected"] - today).days
            upcoming.append({
                "Description": rec["description"],
                "Amount": rec["amount"],
                "Category": rec["category"],
                "Expected Date": rec["next_expected"].date(),
                "Days Until": days_until,
                "Frequency": f"Every {rec['frequency_days']} days",
                "Confidence": f"{rec['confidence']*100:.0f}%"
            })
    
    return pd.DataFrame(upcoming)
