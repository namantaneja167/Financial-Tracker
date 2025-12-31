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
    
    conn.commit()


def insert_transactions(transactions: List[Dict], source_file: str = "manual") -> Tuple[int, int]:
    """
    Insert transactions into database with deduplication and validation.
    
    Args:
        transactions: List of transaction dictionaries
        source_file: Source file name for tracking
        
    Returns:
        (inserted_count, skipped_count)
        
    Raises:
        ValidationError: If transaction data is invalid
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        inserted = 0
        skipped = 0
        imported_at = datetime.now().isoformat()
        
        for txn in transactions:
            try:
                # Validate transaction data
                validated = validate_transaction(txn)
                
                cursor.execute("""
                    INSERT INTO transactions (date, description, amount, type, balance, category, merchant, source_file, imported_at)
                    VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
                """, (
                    str(validated.Date),
                    validated.Description,
                    validated.Amount,
                    validated.Type,
                    validated.Balance,
                    validated.Category,
                    validated.Merchant,
                    source_file,
                    imported_at
                ))
                inserted += 1
            except sqlite3.IntegrityError:
                # Duplicate transaction (same date, description, amount)
                skipped += 1
            except ValidationError as e:
                logger.warning(f"Skipping invalid transaction: {e}")
                skipped += 1
        
        conn.commit()
        
        return inserted, skipped


def get_all_transactions() -> pd.DataFrame:
    """Retrieve all transactions as a DataFrame."""
    with _get_connection() as conn:
        df = pd.read_sql_query("""
            SELECT date, description, amount, type, balance, category, merchant, source_file, imported_at
            FROM transactions
            ORDER BY date DESC
        """, conn)
    
    # Normalize column names to match app expectations
    df.columns = ["Date", "Description", "Amount", "Type", "Balance", "Category", "Merchant", "SourceFile", "ImportedAt"]
    
    if not df.empty and "Date" in df.columns:
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce").dt.date
    
    return df


def update_transaction_category(date: str, description: str, amount: float, new_category: str) -> None:
    """
    Update category for a specific transaction.
    
    Args:
        date: Transaction date
        description: Transaction description
        amount: Transaction amount
        new_category: New category to assign
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("""
            UPDATE transactions
            SET category = ?
            WHERE date = ? AND description = ? AND amount = ?
        """, (new_category, date, description, amount))
        
        conn.commit()


def save_portfolio_snapshot(cash_balance: float, portfolio_value: float) -> None:
    """
    Save or update portfolio snapshot for today.
    
    Args:
        cash_balance: Current cash balance
        portfolio_value: Current portfolio value
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        today = date.today().isoformat()
        net_worth = cash_balance + portfolio_value
        
        cursor.execute("""
            INSERT OR REPLACE INTO portfolio_snapshots (date, cash_balance, portfolio_value, net_worth)
            VALUES (?, ?, ?, ?)
        """, (today, cash_balance, portfolio_value, net_worth))
        
        conn.commit()


def get_portfolio_history() -> pd.DataFrame:
    """Retrieve portfolio snapshot history as DataFrame."""
    with _get_connection() as conn:
        df = pd.read_sql_query("""
            SELECT date, cash_balance, portfolio_value, net_worth
            FROM portfolio_snapshots
            ORDER BY date ASC
        """, conn)
    
    if not df.empty:
        df.columns = ["Date", "CashBalance", "PortfolioValue", "NetWorth"]
        df["Date"] = pd.to_datetime(df["Date"], errors="coerce")
    
    return df


def get_budgets() -> List[Dict]:
    """Retrieve all budgets."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("SELECT category, monthly_limit FROM budgets ORDER BY category")
        budgets = [{"category": row[0], "monthly_limit": row[1]} for row in cursor.fetchall()]
        
        return budgets


def save_budgets(budgets: List[Dict]) -> None:
    """
    Replace all budgets with new list.
    
    Args:
        budgets: List of budget dictionaries with category and monthly_limit
    """
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        cursor.execute("DELETE FROM budgets")
        
        for budget in budgets:
            cursor.execute("""
                INSERT INTO budgets (category, monthly_limit)
                VALUES (?, ?)
            """, (budget["category"], budget["monthly_limit"]))
        
        conn.commit()


def get_monthly_spend_by_category(year: int, month: int) -> Dict[str, float]:
    """Get total spend by category for a specific month."""
    with _get_connection() as conn:
        cursor = conn.cursor()
        
        # Calculate month boundaries: first day of month to first day of next month
        start_date = f"{year:04d}-{month:02d}-01"
        if month == 12:
            end_date = f"{year + 1:04d}-01-01"
        else:
            end_date = f"{year:04d}-{month + 1:02d}-01"
        
        cursor.execute("""
            SELECT category, SUM(amount) as total
            FROM transactions
            WHERE date >= ? AND date < ? AND type = 'Debit' AND category != ''
            GROUP BY category
        """, (start_date, end_date))
        
        spend_by_category = {row[0]: row[1] for row in cursor.fetchall()}
        
        return spend_by_category
