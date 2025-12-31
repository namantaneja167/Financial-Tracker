"""
Backup and restore functionality for the financial tracker.

Provides database and configuration backups with timestamped files.
"""

import shutil
import zipfile
from datetime import datetime
from pathlib import Path
from typing import List, Optional
import json


# Define paths
DB_PATH = Path(__file__).parent.parent / "data" / "financial_tracker.db"
CONFIG_PATH = Path(__file__).parent.parent / "config.yaml"
BACKUP_DIR = Path(__file__).parent.parent / "backups"
BACKUP_DIR.mkdir(parents=True, exist_ok=True)


def create_backup(include_db: bool = True, include_config: bool = True) -> Path:
    """
    Create a backup archive containing database and/or config files.
    
    Args:
        include_db: Include database file in backup
        include_config: Include configuration files in backup
        
    Returns:
        Path to created backup file
        
    Raises:
        ValueError: If neither db nor config is included
        FileNotFoundError: If required files don't exist
    """
    if not include_db and not include_config:
        raise ValueError("Must include at least database or config in backup")
    
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    backup_filename = f"financial_tracker_backup_{timestamp}.zip"
    backup_path = BACKUP_DIR / backup_filename
    
    with zipfile.ZipFile(backup_path, 'w', zipfile.ZIP_DEFLATED) as backup_zip:
        # Backup database
        if include_db and DB_PATH.exists():
            backup_zip.write(DB_PATH, arcname=DB_PATH.name)
        elif include_db:
            raise FileNotFoundError(f"Database file not found: {DB_PATH}")
        
        # Backup config
        if include_config and CONFIG_PATH.exists():
            backup_zip.write(CONFIG_PATH, arcname=CONFIG_PATH.name)
        elif include_config:
            # Create minimal config if it doesn't exist
            pass
        
        # Add metadata
        metadata = {
            "backup_date": datetime.now().isoformat(),
            "includes_database": include_db,
            "includes_config": include_config,
            "database_name": DB_PATH.name if include_db else None,
            "config_name": CONFIG_PATH.name if include_config else None
        }
        backup_zip.writestr("backup_metadata.json", json.dumps(metadata, indent=2))
    
    return backup_path


def list_backups() -> List[dict]:
    """
    List all available backups.
    
    Returns:
        List of dicts with backup info (name, path, size, created_date)
    """
    backups = []
    
    for backup_file in BACKUP_DIR.glob("financial_tracker_backup_*.zip"):
        try:
            stat = backup_file.stat()
            created = datetime.fromtimestamp(stat.st_mtime)
            
            # Try to read metadata
            metadata = None
            try:
                with zipfile.ZipFile(backup_file, 'r') as zf:
                    if "backup_metadata.json" in zf.namelist():
                        metadata = json.loads(zf.read("backup_metadata.json"))
            except:
                pass
            
            backups.append({
                "name": backup_file.name,
                "path": backup_file,
                "size_mb": stat.st_size / (1024 * 1024),
                "created": created,
                "metadata": metadata
            })
        except Exception:
            continue
    
    # Sort by creation date, newest first
    backups.sort(key=lambda x: x["created"], reverse=True)
    return backups


def restore_backup(backup_path: Path, restore_db: bool = True, restore_config: bool = True) -> dict:
    """
    Restore from a backup file.
    
    Args:
        backup_path: Path to backup zip file
        restore_db: Restore database file
        restore_config: Restore config file
        
    Returns:
        Dict with restoration status
        
    Raises:
        FileNotFoundError: If backup file doesn't exist
        ValueError: If backup is invalid
    """
    if not backup_path.exists():
        raise FileNotFoundError(f"Backup file not found: {backup_path}")
    
    if not restore_db and not restore_config:
        raise ValueError("Must restore at least database or config")
    
    result = {
        "database_restored": False,
        "config_restored": False,
        "errors": []
    }
    
    try:
        with zipfile.ZipFile(backup_path, 'r') as backup_zip:
            # Read metadata if available
            metadata = None
            if "backup_metadata.json" in backup_zip.namelist():
                metadata = json.loads(backup_zip.read("backup_metadata.json"))
            
            # Restore database
            if restore_db:
                db_name = metadata.get("database_name") if metadata else DB_PATH.name
                if db_name in backup_zip.namelist():
                    # Create backup of current database
                    if DB_PATH.exists():
                        backup_current = DB_PATH.parent / f"{DB_PATH.stem}_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{DB_PATH.suffix}"
                        shutil.copy2(DB_PATH, backup_current)
                    
                    # Extract database
                    backup_zip.extract(db_name, DB_PATH.parent)
                    if db_name != DB_PATH.name:
                        # Rename if necessary
                        extracted = DB_PATH.parent / db_name
                        extracted.rename(DB_PATH)
                    
                    result["database_restored"] = True
                else:
                    result["errors"].append("Database file not found in backup")
            
            # Restore config
            if restore_config:
                config_name = metadata.get("config_name") if metadata else CONFIG_PATH.name
                if config_name in backup_zip.namelist():
                    # Create backup of current config
                    if CONFIG_PATH.exists():
                        backup_current = CONFIG_PATH.parent / f"{CONFIG_PATH.stem}_pre_restore_{datetime.now().strftime('%Y%m%d_%H%M%S')}{CONFIG_PATH.suffix}"
                        shutil.copy2(CONFIG_PATH, backup_current)
                    
                    # Extract config
                    backup_zip.extract(config_name, CONFIG_PATH.parent)
                    if config_name != CONFIG_PATH.name:
                        extracted = CONFIG_PATH.parent / config_name
                        extracted.rename(CONFIG_PATH)
                    
                    result["config_restored"] = True
                else:
                    result["errors"].append("Config file not found in backup")
    
    except Exception as e:
        result["errors"].append(f"Restore failed: {str(e)}")
    
    return result


def delete_backup(backup_path: Path) -> bool:
    """
    Delete a backup file.
    
    Args:
        backup_path: Path to backup file to delete
        
    Returns:
        True if deleted successfully
    """
    try:
        if backup_path.exists():
            backup_path.unlink()
            return True
        return False
    except Exception:
        return False


def get_backup_info(backup_path: Path) -> Optional[dict]:
    """
    Get detailed information about a backup file.
    
    Args:
        backup_path: Path to backup file
        
    Returns:
        Dict with backup details or None if invalid
    """
    if not backup_path.exists():
        return None
    
    try:
        with zipfile.ZipFile(backup_path, 'r') as zf:
            files = zf.namelist()
            
            metadata = None
            if "backup_metadata.json" in files:
                metadata = json.loads(zf.read("backup_metadata.json"))
            
            return {
                "path": backup_path,
                "size_mb": backup_path.stat().st_size / (1024 * 1024),
                "files": files,
                "metadata": metadata
            }
    except Exception:
        return None
