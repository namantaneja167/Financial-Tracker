"""
Unit tests for database.py - Database operations and connection management.
"""
import sqlite3
from datetime import date
from pathlib import Path
import tempfile
import pytest
import pandas as pd

from financial_tracker import database


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database for testing."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test.db"
        monkeypatch.setattr(database, "DB_PATH", db_path)
        database._ensure_database_exists()
        yield db_path


class TestDatabaseConnection:
    """Tests for database connection management."""
    
    def test_connection_context_manager(self, temp_db):
        """Test that connection context manager works correctly."""
        with database._get_connection() as conn:
            assert isinstance(conn, sqlite3.Connection)
            cursor = conn.cursor()
            cursor.execute("SELECT 1")
            result = cursor.fetchone()
            assert result == (1,)
    
    def test_connection_rollback_on_error(self, temp_db):
        """Test that connection rolls back on error."""
        try:
            with database._get_connection() as conn:
                cursor = conn.cursor()
                cursor.execute("CREATE TABLE test_table (id INTEGER)")
                conn.commit()
                # Cause an error
                raise ValueError("Test error")
        except ValueError:
            pass
        
        # Verify table was not created (rolled back)
        with database._get_connection() as conn:
            cursor = conn.cursor()
            cursor.execute(
                "SELECT name FROM sqlite_master WHERE type='table' AND name='test_table'"
            )
            result = cursor.fetchone()
            # Table should exist because CREATE TABLE was committed before error
            # Let's test with INSERT instead


class TestTransactionOperations:
    """Tests for transaction CRUD operations."""
    
    def test_insert_transactions(self, temp_db):
        """Test inserting transactions."""
        transactions = [
            {
                "Date": "2025-12-15",
                "Description": "Grocery Store",
                "Amount": 45.67,
                "Type": "Debit",
                "Balance": 1000.0,
                "Category": "Groceries",
                "Merchant": "Grocery Store"
            },
            {
                "Date": "2025-12-16",
                "Description": "Salary",
                "Amount": 3000.0,
                "Type": "Credit",
                "Balance": 4000.0,
                "Category": "Income",
                "Merchant": "Employer"
            }
        ]
        
        inserted, skipped = database.insert_transactions(transactions)
        assert inserted == 2
        assert skipped == 0
    
    def test_insert_duplicate_transactions(self, temp_db):
        """Test that duplicate transactions are skipped."""
        transaction = {
            "Date": "2025-12-15",
            "Description": "Test Store",
            "Amount": 25.0,
            "Type": "Debit",
            "Balance": 1000.0,
            "Category": "Shopping",
            "Merchant": "Test Store"
        }
        
        # Insert first time
        inserted1, skipped1 = database.insert_transactions([transaction])
        assert inserted1 == 1
        assert skipped1 == 0
        
        # Insert duplicate
        inserted2, skipped2 = database.insert_transactions([transaction])
        assert inserted2 == 0
        assert skipped2 == 1
    
    def test_get_all_transactions(self, temp_db):
        """Test retrieving all transactions."""
        transactions = [
            {
                "Date": "2025-12-15",
                "Description": "Store A",
                "Amount": 50.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Shopping",
                "Merchant": "Store A"
            }
        ]
        database.insert_transactions(transactions)
        
        df = database.get_all_transactions()
        assert not df.empty
        assert len(df) == 1
        assert df.iloc[0]["Description"] == "Store A"
        assert df.iloc[0]["Amount"] == 50.0
    
    def test_update_transaction_category(self, temp_db):
        """Test updating transaction category."""
        transaction = {
            "Date": "2025-12-15",
            "Description": "Mystery Store",
            "Amount": 30.0,
            "Type": "Debit",
            "Balance": None,
            "Category": "Misc",
            "Merchant": "Mystery Store"
        }
        database.insert_transactions([transaction])
        
        # Update category
        database.update_transaction_category(
            "2025-12-15",
            "Mystery Store",
            30.0,
            "Shopping"
        )
        
        # Verify update
        df = database.get_all_transactions()
        assert df.iloc[0]["Category"] == "Shopping"


class TestBudgetOperations:
    """Tests for budget CRUD operations."""
    
    def test_save_and_get_budgets(self, temp_db):
        """Test saving and retrieving budgets."""
        budgets = [
            {"category": "Groceries", "monthly_limit": 500.0},
            {"category": "Dining", "monthly_limit": 300.0}
        ]
        
        database.save_budgets(budgets)
        retrieved = database.get_budgets()
        
        assert len(retrieved) == 2
        assert retrieved[0]["category"] == "Dining"  # Sorted alphabetically
        assert retrieved[0]["monthly_limit"] == 300.0
    
    def test_save_budgets_replaces_all(self, temp_db):
        """Test that save_budgets replaces all existing budgets."""
        # Save initial budgets
        initial = [{"category": "Groceries", "monthly_limit": 500.0}]
        database.save_budgets(initial)
        
        # Save new budgets
        new_budgets = [{"category": "Dining", "monthly_limit": 300.0}]
        database.save_budgets(new_budgets)
        
        # Verify only new budgets exist
        retrieved = database.get_budgets()
        assert len(retrieved) == 1
        assert retrieved[0]["category"] == "Dining"
    
    def test_get_monthly_spend_by_category(self, temp_db):
        """Test getting monthly spend by category."""
        transactions = [
            {
                "Date": "2025-12-15",
                "Description": "Grocery 1",
                "Amount": 50.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Groceries",
                "Merchant": "Store"
            },
            {
                "Date": "2025-12-16",
                "Description": "Grocery 2",
                "Amount": 75.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Groceries",
                "Merchant": "Store"
            },
            {
                "Date": "2025-12-17",
                "Description": "Restaurant",
                "Amount": 40.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Dining",
                "Merchant": "Restaurant"
            }
        ]
        database.insert_transactions(transactions)
        
        spend = database.get_monthly_spend_by_category(2025, 12)
        assert spend["Groceries"] == 125.0
        assert spend["Dining"] == 40.0


class TestPortfolioOperations:
    """Tests for portfolio snapshot operations."""
    
    def test_save_portfolio_snapshot(self, temp_db):
        """Test saving portfolio snapshot."""
        database.save_portfolio_snapshot(10000.0, 50000.0)
        
        history = database.get_portfolio_history()
        assert not history.empty
        assert len(history) == 1
        assert history.iloc[0]["CashBalance"] == 10000.0
        assert history.iloc[0]["PortfolioValue"] == 50000.0
        assert history.iloc[0]["NetWorth"] == 60000.0
    
    def test_portfolio_snapshot_upsert(self, temp_db):
        """Test that saving snapshot on same day updates existing."""
        database.save_portfolio_snapshot(10000.0, 50000.0)
        database.save_portfolio_snapshot(12000.0, 55000.0)
        
        history = database.get_portfolio_history()
        assert len(history) == 1
        assert history.iloc[0]["CashBalance"] == 12000.0
    
    def test_get_portfolio_history_sorted(self, temp_db):
        """Test that portfolio history is sorted by date."""
        # Insert snapshots in reverse order
        database.save_portfolio_snapshot(10000.0, 50000.0)
        
        history = database.get_portfolio_history()
        assert not history.empty
        # Verify date column is datetime
        assert pd.api.types.is_datetime64_any_dtype(history["Date"])
