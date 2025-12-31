"""
Budgets page - Budget management and tracking.
"""
from datetime import datetime
import pandas as pd
import streamlit as st

from financial_tracker.categorizer import CATEGORIES
from financial_tracker.database import get_budgets, save_budgets, get_monthly_spend_by_category


def render_budgets() -> None:
    """Render the budgets page with budget management and status."""
    st.header("💰 Monthly Budgets")
    st.markdown("Track your spending against budget limits to stay on top of your finances.")
    
    budgets = get_budgets()
    budget_data = budgets if budgets else []
    budget_dict = {b["category"]: b["monthly_limit"] for b in budgets} if budgets else {}
    
    # Show current month budget status FIRST
    st.subheader("📊 This Month's Progress")
    current_year = datetime.now().year
    current_month = datetime.now().month
    
    spend_by_category = get_monthly_spend_by_category(current_year, current_month)
    
    status_data = []
    for category, spent in spend_by_category.items():
        budget = budget_dict.get(category, 0)
        if budget > 0:
            pct = (spent / budget) * 100
            status = "⚠️ Over Budget" if spent > budget else "✅ On Track"
            remaining = max(0, budget - spent)
            status_data.append({
                "Category": category,
                "Spent": spent,
                "Budget": budget,
                "Remaining": remaining,
                "% Used": pct,
                "Status": status
            })
    
    if status_data:
        status_df = pd.DataFrame(status_data)
        st.dataframe(
            status_df.style.format({
                "Spent": "${:,.2f}",
                "Budget": "${:,.2f}",
                "Remaining": "${:,.2f}",
                "% Used": "{:.1f}%"
            }),
            width='stretch'
        )
    else:
        st.info("💡 Set some budgets below to start tracking your spending!")
    
    st.divider()
    
    # Budget editor section
    st.subheader("✏️ Edit Budgets")
    
    # Ensure all categories have a budget entry option
    existing_categories = {b["category"] for b in budget_data}
    for cat in CATEGORIES:
        if cat not in existing_categories and cat != "Income":
            budget_data.append({"category": cat, "monthly_limit": 0.0})
    
    budget_df = pd.DataFrame(budget_data)
    if not budget_df.empty:
        budget_df = budget_df.sort_values("category")
    
    edited_budget_df = st.data_editor(
        budget_df,
        column_config={
            "category": st.column_config.TextColumn("Category", disabled=True),
            "monthly_limit": st.column_config.NumberColumn(
                "Monthly Limit ($)",
                min_value=0.0,
                step=50.0,
                format="%.2f",
                help="Set to 0 to disable budget tracking for this category"
            )
        },
        hide_index=True,
        width='stretch',
    )
    
    if st.button("💾 Save Budgets", type="primary"):
        budgets_to_save = edited_budget_df.to_dict('records')
        # Filter out zero budgets
        budgets_to_save = [b for b in budgets_to_save if b["monthly_limit"] > 0]
        save_budgets(budgets_to_save)
        st.toast("✅ Budgets saved!", icon="✅")
        st.rerun()
