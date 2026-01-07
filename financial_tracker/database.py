""" 
Database layer for persisting transactions, portfolio snapshots, and budgets using SQLite.
"""
import sqlite3
from pathlib import Path
from typing import List, Dict, Optional, Tuple
from datetime import datetime, date
from contextlib import contextmanager
import pandas as pd
from pydantic import ValidationError
from .migrations import migrate
from .logging_config import get_logger
from .validation import validate_transaction, validate_budget, validate_portfolio_snapshot

logger = get_logger(__name__)

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


def _ensure_database_exists():
    """Ensure database and schema exist, then apply migrations."""
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    logger.info(f"Initializing database at {DB_PATH}")
    with _get_connection() as conn:
        _init_schema(conn)
    
    # Apply any pending migrations
    try:
        applied = migrate()
        if applied:
            for version, description in applied:
                logger.info(f"Applied migration {version}: {description}")
    except Exception as e:
        logger.error(f"Migration failed: {e}")
        raise


def _init_schema(conn: sqlite3.Connection):
    """Initialize database schema if tables don't exist."""
    cursor = conn.cursor()
    
    # Transactions table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS transactions (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL,
            description TEXT NOT NULL,
            amount REAL NOT NULL,
            type TEXT NOT NULL,
            balance REAL,
            category TEXT,
            merchant TEXT,
            source_file TEXT,
            imported_at TEXT NOT NULL,
            UNIQUE(date, description, amount)
        )
    """)
    
    # Portfolio snapshots table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS portfolio_snapshots (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            date TEXT NOT NULL UNIQUE,
            cash_balance REAL NOT NULL,
            portfolio_value REAL NOT NULL,
            net_worth REAL NOT NULL
        )
    """)
    
    # Budgets table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS budgets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            category TEXT NOT NULL UNIQUE,
            monthly_limit REAL NOT NULL
        )
    """)
    
    # Financial Goals table
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS goals (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            target_amount REAL NOT NULL,
            current_amount REAL NOT NULL DEFAULT 0,
            target_date TEXT,
            icon TEXT,
            is_completed INTEGER DEFAULT 0
        )
    """)

    # Assets table (Portfolio)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS assets (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL,
            type TEXT NOT NULL,
            quantity REAL NOT NULL DEFAULT 1.0,
            value REAL NOT NULL,
            last_updated TEXT
        )
    """)
    
    conn.commit()

# ... existing code ...

def get_goals() -> List[Dict]:
    """Retrieve all financial goals."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, target_amount, current_amount, target_date, icon, is_completed FROM goals ORDER BY target_date")
        
        goals = []
        for row in cursor.fetchall():
            goals.append({
                "id": row[0],
                "name": row[1],
                "target_amount": row[2],
                "current_amount": row[3],
                "target_date": row[4],
                "icon": row[5] or "PiggyBank",
                "is_completed": bool(row[6])
            })
        return goals

def add_goal(name: str, target_amount: float, target_date: str = None, icon: str = None) -> int:
    """Add a new financial goal."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO goals (name, target_amount, current_amount, target_date, icon)
            VALUES (?, ?, 0, ?, ?)
        """, (name, target_amount, target_date, icon))
        conn.commit()
        return cursor.lastrowid

def update_goal_progress(goal_id: int, amount: float) -> None:
    """Update the current amount of a goal (add to it)."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("""
            UPDATE goals 
            SET current_amount = current_amount + ?,
                is_completed = CASE WHEN (current_amount + ?) >= target_amount THEN 1 ELSE 0 END
            WHERE id = ?
        """, (amount, amount, goal_id))
        conn.commit()

def delete_goal(goal_id: int) -> None:
    """Delete a goal."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM goals WHERE id = ?", (goal_id,))
        conn.commit()

# --- Asset / Portfolio Functions ---

def get_assets() -> List[Dict]:
    """Retrieve all assets."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT id, name, type, quantity, value, last_updated FROM assets ORDER BY value DESC")
        rows = cursor.fetchall()
        return [
            {"id": r[0], "name": r[1], "type": r[2], "quantity": r[3], "value": r[4], "last_updated": r[5]} 
            for r in rows
        ]

def add_asset(name: str, type: str, value: float, quantity: float = 1.0) -> int:
    """Add a new asset manually."""
    with _get_connection() as conn:
        today = date.today().isoformat()
        cursor = conn.cursor()
        cursor.execute("""
            INSERT INTO assets (name, type, quantity, value, last_updated)
            VALUES (?, ?, ?, ?, ?)
        """, (name, type, quantity, value, today))
        conn.commit()
        return cursor.lastrowid

def delete_asset(asset_id: int) -> None:
    """Delete an asset."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        cursor.execute("DELETE FROM assets WHERE id = ?", (asset_id,))
        conn.commit()
