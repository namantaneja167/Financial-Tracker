"""
Dashboard page - Main transaction overview and analytics.
"""
from typing import Optional
from datetime import datetime
import pandas as pd
import plotly.express as px
import streamlit as st

from financial_tracker.analytics import prep_analytics_frame
from financial_tracker.categorizer import CATEGORIES, get_category_overrides, save_overrides
from financial_tracker.config import get_rows_per_page
from financial_tracker.export import (
    export_transactions_to_csv,
    export_transactions_to_excel,
    get_export_filename
)


def render_dashboard(df: pd.DataFrame) -> None:
    """
    Render the main dashboard page with analytics and transaction list.
    
    Args:
        df: DataFrame containing all transactions
    """
    # Export and search controls at top
    _render_export_controls(df)
    
    # Search/filter functionality
    filtered_df = _render_search_filters(df)
    
    analytics_df = prep_analytics_frame(filtered_df)
    total_income = float(analytics_df["Income"].sum()) if not analytics_df.empty else 0.0
    total_spend = float(analytics_df["Expense"].sum()) if not analytics_df.empty else 0.0
    savings_rate = ((total_income - total_spend) / total_income * 100.0) if total_income > 0 else None

    # KPI Metrics
    c1, c2, c3 = st.columns(3)
    c1.metric("Total Income", f"${total_income:,.2f}")
    c2.metric("Total Spend", f"${total_spend:,.2f}")
    c3.metric("Savings Rate", "—" if savings_rate is None else f"{savings_rate:.1f}%")

    if analytics_df.empty:
        st.warning("No valid dates/amounts available for charts yet.")
    else:
        _render_charts(analytics_df)

    st.subheader("All Transactions")
    _render_transaction_table(filtered_df)


def _render_export_controls(df: pd.DataFrame) -> None:
    """Render export buttons."""
    st.header("📊 Dashboard")
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if not df.empty:
            csv_data = export_transactions_to_csv(df)
            filename = get_export_filename('csv')
            st.download_button(
                label="📥 Export CSV",
                data=csv_data,
                file_name=filename,
                mime="text/csv",
                width='stretch'
            )
        else:
            st.button("📥 Export CSV", disabled=True, width='stretch')
    
    with col3:
        if not df.empty:
            try:
                excel_data = export_transactions_to_excel(df)
                filename = get_export_filename('excel')
                st.download_button(
                    label="📥 Export Excel",
                    data=excel_data,
                    file_name=filename,
                    mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                    width='stretch'
                )
            except ImportError:
                st.button("📥 Export Excel", disabled=True, width='stretch',
                         help="Install openpyxl: pip install openpyxl")
        else:
            st.button("📥 Export Excel", disabled=True, width='stretch')


def _render_search_filters(df: pd.DataFrame) -> pd.DataFrame:
    """Render search and filter controls, return filtered DataFrame."""
    if df.empty:
        return df
    
    # Initialize session state for filter persistence
    if "dashboard_search" not in st.session_state:
        st.session_state.dashboard_search = ""
    if "dashboard_category" not in st.session_state:
        st.session_state.dashboard_category = "All"
    
    # Initialize filter variables with None
    start_date = None
    end_date = None
    min_amount = None
    max_amount = None
    
    with st.expander("🔍 Search & Filter", expanded=False):
        col1, col2 = st.columns(2)
        
        with col1:
            search_text = st.text_input(
                "Search Description",
                value=st.session_state.dashboard_search,
                placeholder="Search transactions...",
                help="Search by description text",
                key="filter_search"
            )
            st.session_state.dashboard_search = search_text
        
        with col2:
            # Category filter
            categories = ["All"] + sorted(df["Category"].unique().tolist()) if "Category" in df.columns else ["All"]
            # Ensure saved category is valid
            default_idx = 0
            if st.session_state.dashboard_category in categories:
                default_idx = categories.index(st.session_state.dashboard_category)
            selected_category = st.selectbox(
                "Filter by Category", 
                categories, 
                index=default_idx, 
                key="filter_category",
                help="Show only transactions in this category"
            )
            st.session_state.dashboard_category = selected_category
        
        col3, col4 = st.columns(2)
        
        # Date range filter
        if "Date" in df.columns:
            df['Date'] = pd.to_datetime(df['Date'], errors='coerce')
            valid_dates = df['Date'].dropna()
            
            if not valid_dates.empty:
                with col3:
                    min_date = valid_dates.min().date()
                    start_date = st.date_input("From Date", value=min_date, min_value=min_date, help="Filter transactions from this date")
                
                with col4:
                    max_date = valid_dates.max().date()
                    end_date = st.date_input("To Date", value=max_date, max_value=max_date, help="Filter transactions until this date")
        
        # Amount range filter
        if "Amount" in df.columns:
            amounts = pd.to_numeric(df["Amount"], errors='coerce').dropna().abs()
            if not amounts.empty:
                col5, col6 = st.columns(2)
                with col5:
                    min_amount = st.number_input("Min Amount", value=0.0, step=10.0, help="Minimum transaction amount (absolute value)")
                with col6:
                    max_amount = st.number_input("Max Amount", value=float(amounts.max()), step=10.0, help="Maximum transaction amount (absolute value)")
    
    # Apply filters
    result = df.copy()
    
    if search_text and "Description" in result.columns:
        result = result[result["Description"].str.contains(search_text, case=False, na=False)]
    
    if selected_category != "All" and "Category" in result.columns:
        result = result[result["Category"] == selected_category]
    
    if "Date" in result.columns and start_date is not None and end_date is not None:
        result = result[
            (result["Date"].dt.date >= start_date) &
            (result["Date"].dt.date <= end_date)
        ]
    
    if "Amount" in result.columns and min_amount is not None and max_amount is not None:
        amounts_abs = pd.to_numeric(result["Amount"], errors='coerce').abs()
        result = result[(amounts_abs >= min_amount) & (amounts_abs <= max_amount)]
    
    if len(result) < len(df):
        st.info(f"Showing {len(result)} of {len(df)} transactions")
    
    return result


def _render_charts(analytics_df: pd.DataFrame) -> None:
    """Render analytics charts."""
    monthly = (
        analytics_df.groupby("Month", as_index=False)
        .agg(Spend=("Expense", "sum"), Income=("Income", "sum"))
        .sort_values("Month")
    )

    st.subheader("Monthly Spend Trend")
    fig_spend = px.line(monthly, x="Month", y="Spend", markers=True)
    st.plotly_chart(fig_spend, width='stretch')

    st.subheader("Category Breakdown")
    by_cat = (
        analytics_df[analytics_df["Expense"] > 0]
        .groupby("Category", as_index=False)
        .agg(Spend=("Expense", "sum"))
        .sort_values("Spend", ascending=False)
    )
    fig_cat = px.pie(by_cat, names="Category", values="Spend", hole=0.45)
    st.plotly_chart(fig_cat, width='stretch')

    st.subheader("Income vs. Expense")
    monthly_long = monthly.melt(
        id_vars=["Month"],
        value_vars=["Income", "Spend"],
        var_name="Type",
        value_name="Total",
    )
    fig_ie = px.bar(monthly_long, x="Month", y="Total", color="Type", barmode="group")
    st.plotly_chart(fig_ie, width='stretch')


def _render_transaction_table(df: pd.DataFrame) -> None:
    """Render paginated transaction table with category editing and bulk actions."""
    # Pagination controls
    rows_per_page = get_rows_per_page()
    total_rows = len(df)
    total_pages = max(1, (total_rows + rows_per_page - 1) // rows_per_page)
    
    if "current_page" not in st.session_state:
        st.session_state.current_page = 1
    
    # Page controls
    col1, col2, col3, col4, col5 = st.columns([2, 1, 2, 1, 2])
    
    with col1:
        if st.button("⬅️ Previous", disabled=(st.session_state.current_page == 1)):
            st.session_state.current_page -= 1
            st.rerun()
    
    with col3:
        st.write(f"Page {st.session_state.current_page} of {total_pages} ({total_rows} total transactions)")
    
    with col5:
        if st.button("Next ➡️", disabled=(st.session_state.current_page >= total_pages)):
            st.session_state.current_page += 1
            st.rerun()
    
    # Calculate slice for current page
    start_idx = (st.session_state.current_page - 1) * rows_per_page
    end_idx = min(start_idx + rows_per_page, total_rows)
    page_df = df.iloc[start_idx:end_idx].copy()
    
    # Add selection column for bulk operations
    page_df.insert(0, "Select", False)
    
    edited_df = st.data_editor(
        page_df,
        column_config={
            "Select": st.column_config.CheckboxColumn(
                "✓",
                help="Select transactions for bulk actions",
                default=False,
            ),
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORIES,
                required=True,
            )
        },
        disabled=["Date", "Description", "Amount", "Type", "Balance"],
        hide_index=True,
        width='stretch',
    )
    
    # Count selected rows
    selected_count = edited_df["Select"].sum() if "Select" in edited_df.columns else 0
    
    # Streamlined action bar
    st.markdown("---")
    
    # Check for any individual category edits
    orig_page_df = df.iloc[start_idx:end_idx]
    individual_changes = 0
    for i, (idx, row) in enumerate(edited_df.iterrows()):
        if "Category" in orig_page_df.columns and i < len(orig_page_df):
            if row["Category"] != orig_page_df.iloc[i]["Category"]:
                individual_changes += 1
    
    action_col1, action_col2, action_col3 = st.columns([1, 2, 1])
    
    with action_col1:
        if selected_count > 0:
            st.caption(f"**{selected_count}** selected")
        elif individual_changes > 0:
            st.caption(f"**{individual_changes}** edited")
        else:
            st.caption("Select rows or edit categories")
    
    with action_col2:
        bulk_category = st.selectbox(
            "Bulk assign category",
            options=[""] + CATEGORIES,
            help="Select a category to apply to all selected transactions",
            label_visibility="collapsed",
            placeholder="Assign category to selected..."
        )
    
    with action_col3:
        # Single unified save button
        has_changes = selected_count > 0 and bulk_category or individual_changes > 0
        button_label = "💾 Save All Changes" if individual_changes > 0 else "🏷️ Apply & Save"
        
        if st.button(button_label, type="primary", disabled=not has_changes, use_container_width=True):
            overrides = get_category_overrides()
            changes = 0
            
            # Apply bulk category to selected rows
            if selected_count > 0 and bulk_category:
                for idx, row in edited_df.iterrows():
                    if row.get("Select", False):
                        overrides[row["Description"]] = bulk_category
                        changes += 1
            
            # Save individual category edits
            for i, (idx, row) in enumerate(edited_df.iterrows()):
                if "Category" in orig_page_df.columns and i < len(orig_page_df):
                    orig_category = orig_page_df.iloc[i]["Category"]
                    if row["Category"] != orig_category and not row.get("Select", False):
                        overrides[row["Description"]] = row["Category"]
                        changes += 1
            
            save_overrides(overrides)
            if changes > 0:
                st.toast(f"✅ Saved {changes} category change(s)!", icon="✅")
                st.rerun()
            else:
                st.toast("No changes to save", icon="ℹ️")
