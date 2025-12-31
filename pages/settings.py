"""
Settings and Backup page - System configuration and data management.
"""
import streamlit as st
from datetime import datetime

from financial_tracker.backup import (
    create_backup,
    list_backups,
    restore_backup,
    delete_backup,
    BACKUP_DIR
)
from financial_tracker.config import get_config


def render_settings() -> None:
    """Render the settings and backup page."""
    st.title("⚙️ Settings & Backup")
    
    tab1, tab2 = st.tabs(["🔧 Settings", "💾 Backup & Restore"])
    
    with tab1:
        _render_settings()
    
    with tab2:
        _render_backup()


def _render_settings() -> None:
    """Render application settings."""
    st.subheader("Application Settings")
    
    config = get_config()
    
    st.write("**Display Settings**")
    col1, col2 = st.columns(2)
    
    with col1:
        rows_per_page = st.number_input(
            "Rows per page",
            min_value=10,
            max_value=200,
            value=config.get("rows_per_page", 25),
            step=10,
            help="Number of transactions to display per page"
        )
    
    with col2:
        chart_height = st.number_input(
            "Chart height (pixels)",
            min_value=200,
            max_value=800,
            value=config.get("chart_height", 400),
            step=50
        )
    
    st.write("**Categorization Settings**")
    
    use_embeddings = st.checkbox(
        "Enable embeddings-based categorization",
        value=config.get("use_embeddings", True),
        help="Use AI embeddings for smarter categorization (requires sentence-transformers)"
    )
    
    similarity_threshold = st.slider(
        "Similarity threshold",
        min_value=0.5,
        max_value=0.95,
        value=config.get("similarity_threshold", 0.75),
        step=0.05,
        help="Minimum similarity score for embeddings matching"
    )
    
    st.write("**Data Import Settings**")
    
    auto_categorize = st.checkbox(
        "Auto-categorize on import",
        value=config.get("auto_categorize", True),
        help="Automatically categorize transactions during import"
    )
    
    detect_duplicates = st.checkbox(
        "Detect duplicate transactions",
        value=config.get("detect_duplicates", True),
        help="Skip duplicate transactions during import"
    )
    
    if st.button("💾 Save Settings", type="primary"):
        st.info("ℹ️ Settings are read-only. Edit config.yaml directly to change settings.")


def _render_backup() -> None:
    """Render backup and restore interface."""
    st.subheader("Backup Management")
    
    # Create backup section
    st.write("**Create New Backup**")
    col1, col2, col3 = st.columns(3)
    
    with col1:
        include_db = st.checkbox("Include Database", value=True)
    
    with col2:
        include_config = st.checkbox("Include Config", value=True)
    
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
