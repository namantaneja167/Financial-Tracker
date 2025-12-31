"""
Settings and Backup page - System configuration and data management.
"""
import pandas as pd
import streamlit as st
from datetime import datetime

from financial_tracker.backup import (
    create_backup,
    list_backups,
    restore_backup,
    delete_backup,
    BACKUP_DIR
)
from financial_tracker.categorizer import CATEGORIES, get_keyword_rules, save_rules
from financial_tracker.config import get_config
from financial_tracker.merchant_normalizer import get_all_custom_mappings, save_custom_mappings


def render_settings() -> None:
    """Render the settings and backup page."""
    st.header("⚙️ Settings")
    
    tab1, tab2, tab3, tab4 = st.tabs(["🎨 Preferences", "📋 Category Rules", "🏪 Merchants", "💾 Backup"])
    
    with tab1:
        _render_settings()
    
    with tab2:
        _render_rules()
    
    with tab3:
        _render_merchants()
    
    with tab4:
        _render_backup()


def _render_settings() -> None:
    """Render application settings."""
    st.subheader("Application Preferences")
    
    # Theme toggle - this one actually works!
    st.write("**🎨 Appearance**")
    col_theme1, col_theme2 = st.columns([1, 3])
    
    with col_theme1:
        current_theme = st.session_state.get("theme", "light")
        theme_options = ["light", "dark"]
        new_theme = st.selectbox(
            "Theme",
            options=theme_options,
            index=theme_options.index(current_theme),
            help="Switch between light and dark mode"
        )
        if new_theme != current_theme:
            st.session_state.theme = new_theme
            st.rerun()
    
    with col_theme2:
        st.caption("💡 Theme changes take effect immediately")
    
    st.markdown("---")
    
    config = get_config()
    
    # Display settings as clean read-only values
    st.write("**📊 Display Settings**")
    col1, col2 = st.columns(2)
    with col1:
        st.markdown(f"**Rows per page:** `{config.get('rows_per_page', 25)}`")
    with col2:
        st.markdown(f"**Chart height:** `{config.get('chart_height', 400)}px`")
    
    st.write("**🤖 Categorization Settings**")
    use_embeddings = config.get("use_embeddings", True)
    st.markdown(f"**AI categorization:** {'✅ Enabled' if use_embeddings else '❌ Disabled'}")
    st.markdown(f"**Similarity threshold:** `{config.get('similarity_threshold', 0.75):.0%}`")
    
    st.write("**📥 Import Settings**")
    col1, col2 = st.columns(2)
    with col1:
        auto_cat = config.get("auto_categorize", True)
        st.markdown(f"**Auto-categorize:** {'✅ Yes' if auto_cat else '❌ No'}")
    with col2:
        detect_dup = config.get("detect_duplicates", True)
        st.markdown(f"**Detect duplicates:** {'✅ Yes' if detect_dup else '❌ No'}")
    
    st.info("💡 To modify these settings, edit `config.yaml` in the project root and restart the app.")


def _render_rules() -> None:
    """Render keyword rules management."""
    st.subheader("Category Rules")
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
    
    if st.button("💾 Save Rules", type="primary", key="save_rules"):
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


def _render_merchants() -> None:
    """Render merchant normalization rules."""
    st.subheader("Merchant Names")
    st.markdown("Manage merchant name normalization rules to clean up transaction descriptions.")
    
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
    
    st.info(
        "**Pattern**: Text to search for in merchant names (case-insensitive)  \n"
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
        if st.button("💾 Save Merchants", type="primary", width='stretch'):
            # Convert back to dict
            new_rules = {}
            for _, row in edited_df.iterrows():
                if pd.notna(row["Pattern"]) and pd.notna(row["Normalized Name"]):
                    pattern = str(row["Pattern"]).strip()
                    normalized = str(row["Normalized Name"]).strip()
                    if pattern and normalized:
                        new_rules[pattern] = normalized
            
            save_custom_mappings(new_rules)
            st.toast(f"✅ Saved {len(new_rules)} merchant rules!", icon="✅")
            st.rerun()
    
    with col3:
        if st.button("🔄 Reset to Defaults", width='stretch'):
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
            st.toast("✅ Reset to default rules!", icon="🔄")
            st.rerun()
    
    # Statistics
    col1, col2 = st.columns(2)
    col1.metric("Total Rules", len(rules))
    col2.metric("Active Normalizations", sum(1 for r in rules.values() if r))


def _render_backup() -> None:
    """Render backup and restore interface."""
    st.subheader("Backup Management")
    
    # Create backup section
    st.write("**Create New Backup**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_db = st.checkbox("Include Database", value=True, help="Include transactions, budgets, and portfolio history")
    
    with col2:
        include_config = st.checkbox("Include Config", value=True, help="Include custom rules and merchant mappings")
    
    with col3:
        if st.button("📦 Create Backup", type="primary", width='stretch'):
            if not include_db and not include_config:
                st.error("Must select at least one item to backup")
            else:
                try:
                    backup_path = create_backup(include_db, include_config)
                    st.success(f"✅ Backup created: {backup_path.name}")
                    st.rerun()
                except Exception as e:
                    st.error(f"❌ Backup failed: {str(e)}")
    
    st.divider()
    
    # List existing backups
    st.write("**Existing Backups**")
    backups = list_backups()
    
    if not backups:
        st.info("No backups found. Create your first backup above!")
    else:
        st.write(f"Backup location: `{BACKUP_DIR}`")
        
        for backup in backups:
            with st.expander(f"📦 {backup['name']} ({backup['size_mb']:.2f} MB)"):
                col1, col2 = st.columns([2, 1])
                
                with col1:
                    st.write(f"**Created:** {backup['created'].strftime('%Y-%m-%d %H:%M:%S')}")
                    
                    if backup['metadata']:
                        meta = backup['metadata']
                        includes = []
                        if meta.get('includes_database'):
                            includes.append("Database")
                        if meta.get('includes_config'):
                            includes.append("Config")
                        st.write(f"**Contains:** {', '.join(includes)}")
                
                with col2:
                    if st.button("🔄 Restore", key=f"restore_{backup['name']}"):
                        st.session_state[f"confirm_restore_{backup['name']}"] = True
                    
                    if st.button("🗑️ Delete", key=f"delete_{backup['name']}"):
                        if delete_backup(backup['path']):
                            st.success("Backup deleted!")
                            st.rerun()
                        else:
                            st.error("Failed to delete backup")
                
                # Confirmation dialog for restore
                if st.session_state.get(f"confirm_restore_{backup['name']}", False):
                    st.warning("⚠️ **Warning:** Restoring will replace current data!")
                    
                    col_a, col_b, col_c = st.columns(3)
                    
                    restore_db = col_a.checkbox("Restore Database", value=True, key=f"rdb_{backup['name']}")
                    restore_config = col_b.checkbox("Restore Config", value=True, key=f"rcfg_{backup['name']}")
                    
                    col_d, col_e = st.columns(2)
                    
                    if col_d.button("✅ Confirm Restore", key=f"confirm_{backup['name']}"):
                        try:
                            result = restore_backup(backup['path'], restore_db, restore_config)
                            
                            if result['errors']:
                                st.error(f"❌ Restore errors: {', '.join(result['errors'])}")
                            else:
                                success_msg = []
                                if result['database_restored']:
                                    success_msg.append("database")
                                if result['config_restored']:
                                    success_msg.append("config")
                                
                                st.success(f"✅ Successfully restored: {', '.join(success_msg)}")
                                st.info("🔄 Please restart the application to apply changes")
                                
                                # Clear confirmation state
                                del st.session_state[f"confirm_restore_{backup['name']}"]
                        except Exception as e:
                            st.error(f"❌ Restore failed: {str(e)}")
                    
                    if col_e.button("❌ Cancel", key=f"cancel_{backup['name']}"):
                        del st.session_state[f"confirm_restore_{backup['name']}"]
                        st.rerun()
    
    # Storage info
    st.divider()
    st.subheader("💾 Storage Information")
    
    total_size = sum(b['size_mb'] for b in backups)
    col1, col2, col3 = st.columns(3)
    col1.metric("Total Backups", len(backups))
    col2.metric("Total Size", f"{total_size:.2f} MB")
    col3.metric("Backup Directory", BACKUP_DIR.name)
