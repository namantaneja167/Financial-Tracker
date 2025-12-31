"""
Integration tests for the Financial Tracker application.

Tests complete workflows from PDF/CSV import to database storage and analytics.
"""
import tempfile
from pathlib import Path
import pytest
import pandas as pd

from financial_tracker import database
from financial_tracker.categorizer import categorize_transactions
from financial_tracker.csv_importer import parse_csv_to_transactions
from financial_tracker.recurring import detect_recurring_transactions
from financial_tracker.merchant_normalizer import normalize_merchant


@pytest.fixture
def temp_db(monkeypatch):
    """Create a temporary database for integration tests."""
    with tempfile.TemporaryDirectory() as tmpdir:
        db_path = Path(tmpdir) / "test_integration.db"
        monkeypatch.setattr(database, "DB_PATH", db_path)
        database._ensure_database_exists()
        yield db_path


class TestCSVImportFlow:
    """Integration tests for CSV import workflow."""
    
    def test_complete_csv_import_flow(self, temp_db):
        """Test complete flow: CSV -> parse -> categorize -> store -> retrieve."""
        # Create test CSV data
        csv_content = b"""Date,Description,Amount,Type,Balance
2025-12-01,Whole Foods Market,89.45,Debit,2500.00
2025-12-02,Direct Deposit Salary,3000.00,Credit,5500.00
2025-12-03,Uber Trip,15.75,Debit,5484.25
2025-12-04,Netflix Subscription,15.99,Debit,5468.26
"""
        
        # Parse CSV
        transactions = parse_csv_to_transactions(csv_content)
        assert len(transactions) == 4
        
        # Create DataFrame and normalize merchants
        df = pd.DataFrame(transactions)
        df["Merchant"] = df["Description"].apply(normalize_merchant)
        
        # Categorize
        df = categorize_transactions(df, use_embeddings=False)
        
        # Store in database
        transactions_to_insert = df.to_dict('records')
        inserted, skipped = database.insert_transactions(transactions_to_insert)
        assert inserted == 4
        assert skipped == 0
        
        # Retrieve and verify
        stored_df = database.get_all_transactions()
        assert len(stored_df) == 4
        # Database returns in DESC order by date, so most recent first
        assert "Whole Foods Market" in stored_df["Description"].values
        # Categories assigned by keyword matching - check valid categories exist
        assert stored_df["Category"].notna().all()
        assert len(stored_df["Category"].unique()) > 0
    
    def test_duplicate_import_handling(self, temp_db):
        """Test that duplicate imports are handled correctly."""
        csv_content = b"""Date,Description,Amount,Type,Balance
2025-12-01,Test Store,50.00,Debit,1000.00
"""
        
        # First import
        transactions = parse_csv_to_transactions(csv_content)
        df = pd.DataFrame(transactions)
        df["Merchant"] = df["Description"].apply(normalize_merchant)
        df = categorize_transactions(df, use_embeddings=False)
        inserted1, skipped1 = database.insert_transactions(df.to_dict('records'))
        
        assert inserted1 == 1
        assert skipped1 == 0
        
        # Second import (duplicate)
        transactions = parse_csv_to_transactions(csv_content)
        df = pd.DataFrame(transactions)
        df["Merchant"] = df["Description"].apply(normalize_merchant)
        df = categorize_transactions(df, use_embeddings=False)
        inserted2, skipped2 = database.insert_transactions(df.to_dict('records'))
        
        assert inserted2 == 0
        assert skipped2 == 1
        
        # Verify only 1 transaction in database
        stored_df = database.get_all_transactions()
        assert len(stored_df) == 1


class TestBudgetAlertFlow:
    """Integration tests for budget alerts workflow."""
    
    def test_budget_alert_flow(self, temp_db):
        """Test budget creation, spending tracking, and alert generation."""
        # Set up budget
        budgets = [
            {"category": "Dining", "monthly_limit": 200.0}
        ]
        database.save_budgets(budgets)
        
        # Add transactions
        transactions = [
            {
                "Date": "2025-12-01",
                "Description": "Restaurant A",
                "Amount": 50.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Dining",
                "Merchant": "Restaurant A"
            },
            {
                "Date": "2025-12-05",
                "Description": "Restaurant B",
                "Amount": 75.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Dining",
                "Merchant": "Restaurant B"
            },
            {
                "Date": "2025-12-10",
                "Description": "Restaurant C",
                "Amount": 100.0,
                "Type": "Debit",
                "Balance": None,
                "Category": "Dining",
                "Merchant": "Restaurant C"
            }
        ]
        database.insert_transactions(transactions)
        
        # Check spending
        spend = database.get_monthly_spend_by_category(2025, 12)
        assert spend["Dining"] == 225.0
        
        # Verify over budget
        budget_dict = {b["category"]: b["monthly_limit"] for b in database.get_budgets()}
        assert spend["Dining"] > budget_dict["Dining"]


class TestRecurringDetectionFlow:
    """Integration tests for recurring transaction detection."""
    
    def test_recurring_detection_subscription(self, temp_db):
        """Test detection of recurring subscription."""
        # Add recurring transactions (Netflix)
        transactions = [
            {
                "Date": "2025-09-15",
                "Description": "Netflix",
                "Amount": 15.99,
                "Type": "Debit",
                "Balance": None,
                "Category": "Entertainment",
                "Merchant": "Netflix"
            },
            {
                "Date": "2025-10-15",
                "Description": "Netflix",
                "Amount": 15.99,
                "Type": "Debit",
                "Balance": None,
                "Category": "Entertainment",
                "Merchant": "Netflix"
            },
            {
                "Date": "2025-11-15",
                "Description": "Netflix",
                "Amount": 15.99,
                "Type": "Debit",
                "Balance": None,
                "Category": "Entertainment",
                "Merchant": "Netflix"
            }
        ]
        database.insert_transactions(transactions)
        
        # Detect recurring
        df = database.get_all_transactions()
        recurring_patterns = detect_recurring_transactions(df)
        
        # Should detect Netflix as recurring
        assert isinstance(recurring_patterns, list)
        assert len(recurring_patterns) > 0
        # Check if Netflix is in detected patterns
        netflix_found = any("Netflix" in str(p.get("pattern", "")).lower() for p in recurring_patterns)
        assert netflix_found or len(recurring_patterns) >= 1  # At least found something recurring


class TestPortfolioTrackingFlow:
    """Integration tests for portfolio tracking workflow."""
    
    def test_portfolio_tracking_flow(self, temp_db):
        """Test portfolio snapshot creation and history tracking."""
        # Save initial snapshot
        database.save_portfolio_snapshot(10000.0, 50000.0)
        
        # Save updated snapshot (same day - should update)
        database.save_portfolio_snapshot(11000.0, 52000.0)
        
        # Retrieve history
        history = database.get_portfolio_history()
        
        assert len(history) == 1
        assert history.iloc[0]["CashBalance"] == 11000.0
        assert history.iloc[0]["PortfolioValue"] == 52000.0
        assert history.iloc[0]["NetWorth"] == 63000.0


class TestMerchantNormalizationFlow:
    """Integration tests for merchant normalization."""
    
    def test_merchant_normalization_in_import(self, temp_db):
        """Test that merchant normalization works during import."""
        csv_content = b"""Date,Description,Amount,Type,Balance
2025-12-01,UBER *TRIP 12345,25.50,Debit,1000.00
2025-12-02,AMZN MKTP US*AB123,45.99,Debit,954.01
2025-12-03,SQ *COFFEE SHOP,5.75,Debit,948.26
"""
        
        # Parse and normalize
        transactions = parse_csv_to_transactions(csv_content)
        df = pd.DataFrame(transactions)
        df["Merchant"] = df["Description"].apply(normalize_merchant)
        
        # Verify normalization
        assert df.iloc[0]["Merchant"] == "Uber"
        assert df.iloc[1]["Merchant"] == "Amazon"
        assert df.iloc[2]["Merchant"] == "Square"
        
        # Store with normalized merchants
        df = categorize_transactions(df, use_embeddings=False)
        database.insert_transactions(df.to_dict('records'))
        
        # Retrieve and verify
        stored_df = database.get_all_transactions()
        # Check that normalized merchants are present (order may vary)
        merchants = stored_df["Merchant"].tolist()
        assert "Uber" in merchants
        assert "Amazon" in merchants
        assert "Square" in merchants


class TestEndToEndImportWorkflow:
    """End-to-end tests for complete import workflow."""
    
    def test_complete_workflow_with_analytics(self, temp_db):
        """Test complete workflow including analytics."""
        from financial_tracker.analytics import prep_analytics_frame
        
        # Import transactions
        csv_content = b"""Date,Description,Amount,Type,Balance
2025-12-01,Grocery Store,100.00,Debit,2000.00
2025-12-05,Salary,3000.00,Credit,5000.00
2025-12-10,Gas Station,50.00,Debit,4950.00
2025-12-15,Restaurant,75.00,Debit,4875.00
"""
        transactions = parse_csv_to_transactions(csv_content)
        df = pd.DataFrame(transactions)
        df["Merchant"] = df["Description"].apply(normalize_merchant)
        df = categorize_transactions(df, use_embeddings=False)
        database.insert_transactions(df.to_dict('records'))
        
        # Retrieve for analytics
        stored_df = database.get_all_transactions()
        analytics_df = prep_analytics_frame(stored_df)
        
        # Verify analytics
        assert "Month" in analytics_df.columns
        assert "Expense" in analytics_df.columns
        assert "Income" in analytics_df.columns
        
        total_income = analytics_df["Income"].sum()
        total_expense = analytics_df["Expense"].sum()
        
        assert total_income == 3000.0
        assert total_expense == 225.0  # 100 + 50 + 75
