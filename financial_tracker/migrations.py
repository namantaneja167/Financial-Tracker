"""
Schema migration system for the financial tracker database.

This module provides a robust migration framework to manage database schema changes
over time with proper versioning, rollback support, and migration tracking.
"""

import sqlite3
from pathlib import Path
from typing import List, Tuple, Callable
from contextlib import contextmanager

DB_PATH = Path(__file__).parent.parent / "data" / "financial_tracker.db"


@contextmanager
def _get_connection():
    """Context manager for database connections with proper cleanup."""
    conn = sqlite3.connect(DB_PATH)
    try:
        yield conn
    except Exception:
        conn.rollback()
        raise
    finally:
        conn.close()


class Migration:
    """Represents a single database migration."""
    
    def __init__(self, version: int, description: str, up: Callable, down: Callable = None):
        """
        Initialize a migration.
        
        Args:
            version: Migration version number (must be unique and sequential)
            description: Human-readable description of the migration
            up: Function to apply the migration (takes cursor as parameter)
            down: Optional function to rollback the migration (takes cursor as parameter)
        """
        self.version = version
        self.description = description
        self.up = up
        self.down = down


def _create_schema_version_table(cursor: sqlite3.Cursor):
    """Create the schema_version table if it doesn't exist."""
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS schema_version (
            version INTEGER PRIMARY KEY,
            description TEXT NOT NULL,
            applied_at TEXT NOT NULL DEFAULT CURRENT_TIMESTAMP
        )
    """)


def get_current_version() -> int:
    """Get the current database schema version."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        _create_schema_version_table(cursor)
        
        cursor.execute("SELECT MAX(version) FROM schema_version")
        result = cursor.fetchone()[0]
        
        return result if result is not None else 0


def _migration_1_add_merchant_column(cursor: sqlite3.Cursor):
    """Migration 1: Add merchant column to transactions table."""
    cursor.execute("""
        SELECT COUNT(*) FROM pragma_table_info('transactions')
        WHERE name = 'merchant'
    """)
    
    if cursor.fetchone()[0] == 0:
        cursor.execute("ALTER TABLE transactions ADD COLUMN merchant TEXT")


def _migration_2_add_indexes(cursor: sqlite3.Cursor):
    """Migration 2: Add performance indexes to transactions table."""
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date ON transactions(date)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_category ON transactions(category)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_type ON transactions(type)")
    cursor.execute("CREATE INDEX IF NOT EXISTS idx_transactions_date_category ON transactions(date, category)")


# Define all migrations in order
MIGRATIONS: List[Migration] = [
    Migration(
        version=1,
        description="Add merchant column to transactions table",
        up=_migration_1_add_merchant_column
    ),
    Migration(
        version=2,
        description="Add performance indexes to transactions table",
        up=_migration_2_add_indexes
    ),
]


def migrate(target_version: int = None) -> List[Tuple[int, str]]:
    """
    Apply all pending migrations up to target_version.
    
    Args:
        target_version: The version to migrate to (None = latest)
        
    Returns:
        List of (version, description) tuples for applied migrations
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        _create_schema_version_table(cursor)
        
        current_version = get_current_version()
        target = target_version if target_version is not None else max([m.version for m in MIGRATIONS], default=0)
        
        applied = []
        
        for migration in MIGRATIONS:
            if migration.version <= current_version:
                continue  # Already applied
            
            if migration.version > target:
                break  # Don't go beyond target
            
            try:
                # Apply the migration
                migration.up(cursor)
                
                # Record it in schema_version
                cursor.execute("""
                    INSERT INTO schema_version (version, description)
                    VALUES (?, ?)
                """, (migration.version, migration.description))
                
                conn.commit()
                applied.append((migration.version, migration.description))
                
            except Exception as e:
                conn.rollback()
                raise Exception(f"Migration {migration.version} failed: {e}") from e
        
        return applied


def rollback(target_version: int) -> List[Tuple[int, str]]:
    """
    Rollback migrations to a specific version.
    
    Args:
        target_version: The version to rollback to
        
    Returns:
        List of (version, description) tuples for rolled back migrations
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        _create_schema_version_table(cursor)
        
        current_version = get_current_version()
        
        if target_version >= current_version:
            return []  # Nothing to rollback
        
        rolled_back = []
        
        # Find migrations to rollback (in reverse order)
        for migration in reversed(MIGRATIONS):
            if migration.version <= target_version or migration.version > current_version:
                continue
            
            if migration.down is None:
                raise Exception(f"Migration {migration.version} does not support rollback")
            
            try:
                # Rollback the migration
                migration.down(cursor)
                
                # Remove it from schema_version
                cursor.execute("""
                    DELETE FROM schema_version
                    WHERE version = ?
                """, (migration.version,))
                
                conn.commit()
                rolled_back.append((migration.version, migration.description))
                
            except Exception as e:
                conn.rollback()
                raise Exception(f"Rollback of migration {migration.version} failed: {e}") from e
        
        return rolled_back


def get_migration_status() -> List[Tuple[int, str, bool]]:
    """
    Get the status of all migrations.
    
    Returns:
        List of (version, description, applied) tuples
    """
    current_version = get_current_version()
    
    status = []
    for migration in MIGRATIONS:
        applied = migration.version <= current_version
        status.append((migration.version, migration.description, applied))
    
    return status
