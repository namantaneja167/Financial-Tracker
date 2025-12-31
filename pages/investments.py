"""
Investments page - Investment contributions and portfolio tracking.
"""
import pandas as pd
import streamlit as st

from financial_tracker.analytics import latest_cash_balance
from financial_tracker.database import save_portfolio_snapshot


def render_investments(df: pd.DataFrame, portfolio_value: float) -> None:
    """
    Render the investments page with contributions and net worth.
    
    Args:
        df: DataFrame containing all transactions
        portfolio_value: Current portfolio value entered by user
    """
    investments = df[df["Category"] == "Investments"].copy() if "Category" in df.columns else df.iloc[0:0].copy()

    contributions = investments.copy()
    if "Type" in contributions.columns:
        contributions["Type"] = contributions["Type"].astype(str).str.title()
        contributions = contributions[contributions["Type"] == "Debit"]

    st.subheader("Investment Contributions")
    display_cols = [c for c in ["Date", "Description", "Amount", "Type", "Balance", "Category"] if c in contributions.columns]
    st.dataframe(contributions[display_cols], width='stretch')

    cash_balance = latest_cash_balance(df)
    if cash_balance is None:
        cash_balance = 0.0
        st.info("Cash Balance not found in statement; using $0.00 for Net Worth.")

    net_worth = float(cash_balance) + float(portfolio_value)
    n1, n2 = st.columns(2)
    n1.metric("Cash Balance", f"${cash_balance:,.2f}")
    n2.metric("Net Worth", f"${net_worth:,.2f}")
    
    if st.button("Save Portfolio Snapshot"):
        save_portfolio_snapshot(cash_balance, portfolio_value)
        st.success("Portfolio snapshot saved!")
