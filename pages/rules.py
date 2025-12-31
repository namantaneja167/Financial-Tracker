"""
Rules page - Manage categorization keyword rules.
"""
import pandas as pd
import streamlit as st

from financial_tracker.categorizer import CATEGORIES, get_keyword_rules, save_rules


def render_rules() -> None:
    """Render the keyword rules management page."""
    st.header("📋 Keyword Rules")
    st.markdown("Define keyword patterns to automatically categorize transactions. Matching is case-insensitive.")
    
    rules = get_keyword_rules()
    
    rules_data = []
    for rule in rules:
        rules_data.append({
            "Category": rule["category"],
            "Keywords": ", ".join(rule["keywords"])
        })
    
    rules_df = pd.DataFrame(rules_data) if rules_data else pd.DataFrame(columns=["Category", "Keywords"])
    
    st.info("💡 **Tip**: Enter keywords separated by commas. Example: `netflix, hulu, disney+` for Subscriptions.")
    
    edited_rules_df = st.data_editor(
        rules_df,
        column_config={
            "Category": st.column_config.SelectboxColumn(
                "Category",
                options=CATEGORIES,
                required=True,
                help="Select the category for matching transactions"
            ),
            "Keywords": st.column_config.TextColumn(
                "Keywords (comma-separated)",
                help="Enter keywords separated by commas. Any transaction containing these words will be assigned to this category.",
                required=True,
                width="large"
            )
        },
        num_rows="dynamic",
        hide_index=True,
        width='stretch',
    )
    
    if st.button("💾 Save Rules", type="primary"):
        new_rules = []
        for _, row in edited_rules_df.iterrows():
            keywords = [kw.strip() for kw in row["Keywords"].split(",") if kw.strip()]
            if keywords:
                new_rules.append({
                    "category": row["Category"],
                    "keywords": keywords
                })
        save_rules(new_rules)
        st.toast("✅ Rules saved successfully!", icon="✅")
