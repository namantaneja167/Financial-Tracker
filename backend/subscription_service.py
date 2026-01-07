
import pandas as pd
from typing import List, Dict, Any
from financial_tracker.database import get_all_transactions
from financial_tracker.logging_config import get_logger

logger = get_logger(__name__)

def detect_subscriptions() -> List[Dict[str, Any]]:
    """
    Analyzes transactions to detect recurring payments likely to be subscriptions.
    Heuristics:
    - Same Merchant
    - Same Amount (or very close)
    - Occurs at least twice
    """
    try:
        df = get_all_transactions()
        if df.empty:
            return []

        # Filter for debits only
        debits = df[df["Type"] == "Debit"].copy()
        
        # Group by Merchant and Amount
        # We assume subscriptions have exact or very similar amounts
        # For simplicity in MVP, we look for exact matches on simple rounded amounts if needed, 
        # but exact match is safest for things like $14.99
        
        # Count occurrences
        recurring = debits.groupby(["Merchant", "Amount"]).size().reset_index(name="Count")
        
        # Filter for at least 2 occurrences
        subscriptions = recurring[recurring["Count"] >= 2].copy()
        
        # Calculate total yearly cost estimate
        subscriptions["MonthlyCost"] = subscriptions["Amount"]
        subscriptions["YearlyCost"] = subscriptions["Amount"] * 12
        
        # Sort by cost
        subscriptions = subscriptions.sort_values("MonthlyCost", ascending=False)
        
        results = []
        for _, row in subscriptions.iterrows():
            # Get latest date for this subscription
            latest = debits[
                (debits["Merchant"] == row["Merchant"]) & 
                (debits["Amount"] == row["Amount"])
            ]["Date"].max()
            
            results.append({
                "merchant": row["Merchant"],
                "amount": float(row["Amount"]),
                "frequency": "Monthly", # Assumed for now
                "yearly_cost": float(row["YearlyCost"]),
                "last_paid": str(latest)
            })
            
        return results

    except Exception as e:
        logger.error(f"Error detecting subscriptions: {e}")
        return []
