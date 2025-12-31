"""
Recurring transactions page - Detect and track recurring expenses.
"""
import pandas as pd
import streamlit as st

from financial_tracker.recurring import get_upcoming_recurring_expenses


def render_recurring(df: pd.DataFrame) -> None:
    """
    Render the recurring transactions page.
    
    Args:
        df: DataFrame containing all transactions
    """
    st.header("🔄 Recurring Transactions")
    st.markdown("Automatically detected subscriptions, rent, and other recurring expenses based on your transaction history.")
    
    upcoming = get_upcoming_recurring_expenses(df, days_ahead=60)
    
    if upcoming.empty:
        st.info("No recurring transactions detected yet. Import more historical data to detect patterns.")
    else:
        st.subheader("Upcoming Expected Expenses (Next 60 Days)")
        
        # Calculate total upcoming
        total_upcoming = upcoming["Amount"].sum()
        st.metric("Total Expected Spend", f"${total_upcoming:,.2f}")
        
        st.dataframe(
            upcoming.style.format({
                "Amount": "${:,.2f}"
            }),
            width='stretch'
        )
