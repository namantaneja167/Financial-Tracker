"""
Merchant Management page - View and edit merchant normalization rules.
"""
import streamlit as st
import pandas as pd

from financial_tracker.merchant_normalizer import get_all_custom_mappings, save_custom_mappings


def render_merchants() -> None:
    """Render the merchant management page."""
    st.title("🏪 Merchant Management")
    st.write("Manage merchant name normalization rules to clean up transaction descriptions.")
    
    # Get current rules
    rules = get_all_custom_mappings()
    
    # Convert to DataFrame for editing
    if rules:
        rules_df = pd.DataFrame([
            {"Pattern": pattern, "Normalized Name": normalized}
            for pattern, normalized in rules.items()
        ])
    else:
        rules_df = pd.DataFrame(columns=["Pattern", "Normalized Name"])
    
    st.subheader("Current Rules")
    st.info(
        "**Pattern**: Text to search for in merchant names (case-insensitive)\n"
        "**Normalized Name**: Clean name to replace it with"
    )
    
    # Editable table
    edited_df = st.data_editor(
        rules_df,
        num_rows="dynamic",
        width='stretch',
        column_config={
            "Pattern": st.column_config.TextColumn(
                "Pattern",
                help="Text pattern to match (e.g., 'amzn', 'walmart')",
                required=True
            ),
            "Normalized Name": st.column_config.TextColumn(
                "Normalized Name",
                help="Clean merchant name (e.g., 'Amazon', 'Walmart')",
                required=True
            )
        }
    )
    
    col1, col2, col3 = st.columns([2, 1, 1])
    
    with col2:
        if st.button("💾 Save Rules", type="primary", width='stretch'):
            # Convert back to dict
            new_rules = {}
            for _, row in edited_df.iterrows():
                if pd.notna(row["Pattern"]) and pd.notna(row["Normalized Name"]):
                    pattern = str(row["Pattern"]).strip()
                    normalized = str(row["Normalized Name"]).strip()
                    if pattern and normalized:
                        new_rules[pattern] = normalized
            
            save_custom_mappings(new_rules)
            st.success(f"✅ Saved {len(new_rules)} merchant rules!")
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset to Defaults", width='stretch'):
            # Reset to default rules
            default_rules = {
                "amazon": "Amazon",
                "amzn": "Amazon",
                "aws": "Amazon Web Services",
                "walmart": "Walmart",
                "target": "Target",
                "costco": "Costco",
                "starbucks": "Starbucks",
                "mcdonald": "McDonald's",
                "whole foods": "Whole Foods",
                "trader joe": "Trader Joe's",
                "netflix": "Netflix",
                "spotify": "Spotify",
                "uber": "Uber",
                "lyft": "Lyft",
                "venmo": "Venmo",
                "paypal": "PayPal"
            }
            save_custom_mappings(default_rules)
            st.success("✅ Reset to default rules!")
            st.rerun()
    
    # Statistics
    st.subheader("📊 Statistics")
    col1, col2 = st.columns(2)
    col1.metric("Total Rules", len(rules))
    col2.metric("Active Normalizations", sum(1 for r in rules.values() if r))
    
    # Example section
    with st.expander("💡 Examples & Tips"):
        st.markdown("""
        ### How Merchant Normalization Works
        
        The system searches for patterns in transaction descriptions and replaces them with normalized names.
        
        **Example Rules:**
        - Pattern: `amazon` → Normalized: `Amazon`  
          Matches: "AMAZON.COM", "Amazon Prime", "amzn mktp"
        
        - Pattern: `starbucks` → Normalized: `Starbucks`  
          Matches: "STARBUCKS #1234", "Starbucks Coffee"
        
        **Tips:**
        - Use lowercase for patterns (matching is case-insensitive)
        - Shorter patterns match more broadly
        - More specific patterns take precedence over general ones
        - Test rules after saving by re-importing transactions
        
        **Common Patterns:**
        - Online retailers: `amzn`, `amazon`, `ebay`
        - Gas stations: `shell`, `chevron`, `exxon`
        - Grocery stores: `safeway`, `kroger`, `publix`
        - Restaurants: `mcdonald`, `chipotle`, `subway`
        """)
    
    # Bulk import/export
    st.subheader("🔄 Bulk Operations")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.write("**Export Rules**")
        if st.button("📥 Export to CSV"):
            if not rules_df.empty:
                csv = rules_df.to_csv(index=False)
                st.download_button(
                    label="Download CSV",
                    data=csv,
                    file_name="merchant_rules.csv",
                    mime="text/csv"
                )
            else:
                st.warning("No rules to export")
    
    with col2:
        st.write("**Import Rules**")
        uploaded_file = st.file_uploader(
            "Upload CSV",
            type=['csv'],
            help="CSV with columns: Pattern, Normalized Name"
        )
        
        if uploaded_file:
            try:
                import_df = pd.read_csv(uploaded_file)
                if "Pattern" in import_df.columns and "Normalized Name" in import_df.columns:
                    imported_rules = {}
                    for _, row in import_df.iterrows():
                        if pd.notna(row["Pattern"]) and pd.notna(row["Normalized Name"]):
                            imported_rules[str(row["Pattern"]).strip()] = str(row["Normalized Name"]).strip()
                    
                    if imported_rules:
                        save_custom_mappings(imported_rules)
                        st.success(f"✅ Imported {len(imported_rules)} rules!")
                        st.rerun()
                else:
                    st.error("CSV must have 'Pattern' and 'Normalized Name' columns")
            except Exception as e:
                st.error(f"Import failed: {str(e)}")
