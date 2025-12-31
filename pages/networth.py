"""
Net worth page - Track net worth over time.
"""
import pandas as pd
import plotly.express as px
import streamlit as st

from financial_tracker.database import get_portfolio_history


def render_networth() -> None:
    """Render the net worth tracking page."""
    st.header("📈 Net Worth Over Time")
    
    history = get_portfolio_history()
    
    if history.empty:
        st.info("No portfolio snapshots yet. Enter your portfolio value and click 'Save Portfolio Snapshot' in the Investments tab.")
    else:
        fig_networth = px.line(
            history,
            x="Date",
            y="NetWorth",
            markers=True,
            labels={"NetWorth": "Net Worth ($)", "Date": "Date"}
        )
        st.plotly_chart(fig_networth, width='stretch')
        
        # Calculate monthly change
        if len(history) >= 2:
            latest = history.iloc[-1]
            previous = history.iloc[-2]
            change = latest["NetWorth"] - previous["NetWorth"]
            change_pct = (change / previous["NetWorth"]) * 100 if previous["NetWorth"] != 0 else 0
            
            col1, col2, col3 = st.columns(3)
            col1.metric("Current Net Worth", f"${latest['NetWorth']:,.2f}")
            col2.metric("Previous", f"${previous['NetWorth']:,.2f}")
            col3.metric("Change", f"${change:,.2f}", f"{change_pct:+.1f}%")
        
        st.subheader("Historical Data")
        st.dataframe(
            history.style.format({
                "CashBalance": "${:,.2f}",
                "PortfolioValue": "${:,.2f}",
                "NetWorth": "${:,.2f}"
            }),
            width='stretch'
        )
