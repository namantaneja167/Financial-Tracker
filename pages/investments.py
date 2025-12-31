"""
Investments page - Investment contributions and portfolio tracking.
"""
import pandas as pd
import streamlit as st

from financial_tracker.analytics import latest_cash_balance
from financial_tracker.database import save_portfolio_snapshot


def render_investments(df: pd.DataFrame) -> None:
    """
    Render the investments page with contributions and net worth.
    
    Args:
        df: DataFrame containing all transactions
    """
    st.header("💼 Investments")
    
    # Portfolio value input - persisted in session state
    if "portfolio_value" not in st.session_state:
        st.session_state.portfolio_value = 0.0
    
    investments = df[df["Category"] == "Investments"].copy() if "Category" in df.columns else df.iloc[0:0].copy()

    contributions = investments.copy()
    if "Type" in contributions.columns:
        contributions["Type"] = contributions["Type"].astype(str).str.title()
        contributions = contributions[contributions["Type"] == "Debit"]

    st.subheader("Investment Contributions")
    display_cols = [c for c in ["Date", "Description", "Amount", "Type", "Balance", "Category"] if c in contributions.columns]
    if contributions.empty:
        st.info("No investment contributions found. Transactions categorized as 'Investments' will appear here.")
    else:
        st.dataframe(contributions[display_cols], width='stretch')

    st.subheader("Portfolio Snapshot")
    
    col1, col2 = st.columns(2)
    with col1:
        portfolio_value = st.number_input(
            "Current Portfolio Value ($)",
            min_value=0.0,
            value=st.session_state.portfolio_value,
            step=1000.0,
            format="%.2f",
            help="Enter your total investment portfolio value (401k, IRA, brokerage, etc.)"
        )
        st.session_state.portfolio_value = portfolio_value

    cash_balance = latest_cash_balance(df)
    if cash_balance is None:
        cash_balance = 0.0
        st.caption("💡 Cash balance not found in statement; using $0.00")

    net_worth = float(cash_balance) + float(portfolio_value)
    
    st.subheader("Summary")
    c1, c2, c3 = st.columns(3)
    c1.metric("Cash Balance", f"${cash_balance:,.2f}")
    c2.metric("Portfolio Value", f"${portfolio_value:,.2f}")
    c3.metric("Net Worth", f"${net_worth:,.2f}")
    
    if st.button("💾 Save Portfolio Snapshot", type="primary", help="Save current values to track net worth over time"):
        save_portfolio_snapshot(cash_balance, portfolio_value)
        st.toast("✅ Portfolio snapshot saved!", icon="✅")
