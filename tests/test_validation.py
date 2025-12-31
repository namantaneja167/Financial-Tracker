"""
Unit tests for validation.py - Pydantic models and validators.
"""
from datetime import date
import pytest
from pydantic import ValidationError

from financial_tracker.validation import (
    Transaction,
    Budget,
    PortfolioSnapshot,
    validate_transaction,
    validate_budget,
    validate_portfolio_snapshot,
)


class TestTransactionModel:
    """Tests for Transaction Pydantic model."""
    
    def test_valid_transaction(self):
        """Test creating a valid transaction."""
        txn = Transaction(
            Date="2025-12-15",
            Description="Whole Foods Market",
            Amount=45.67,
            Type="Debit",
            Balance=1234.56,
            Category="Groceries",
            Merchant="Whole Foods"
        )
        assert txn.Date == date(2025, 12, 15)
        assert txn.Amount == 45.67
        assert txn.Type == "Debit"
    
    def test_date_parsing_formats(self):
        """Test various date formats are parsed correctly."""
        formats = [
            ("2025-12-15", date(2025, 12, 15)),
            ("12/15/2025", date(2025, 12, 15)),
            ("15/12/2025", date(2025, 12, 15)),
        ]
        for date_str, expected in formats:
            txn = Transaction(
                Date=date_str,
                Description="Test",
                Amount=10.0,
                Type="Debit"
            )
            assert txn.Date == expected
    
    def test_amount_cleaning(self):
        """Test amount parsing with currency symbols."""
        txn = Transaction(
            Date="2025-12-15",
            Description="Test",
            Amount="$1,234.56",
            Type="Credit"
        )
        assert txn.Amount == 1234.56
    
    def test_type_normalization(self):
        """Test transaction type normalization."""
        types = [
            ("debit", "Debit"),
            ("DEBIT", "Debit"),
            ("withdrawal", "Debit"),
            ("credit", "Credit"),
            ("CREDIT", "Credit"),
            ("deposit", "Credit"),
        ]
        for input_type, expected in types:
            txn = Transaction(
                Date="2025-12-15",
                Description="Test",
                Amount=10.0,
                Type=input_type
            )
            assert txn.Type == expected
    
    def test_invalid_type(self):
        """Test that invalid transaction types raise error."""
        with pytest.raises(ValidationError) as exc_info:
            Transaction(
                Date="2025-12-15",
                Description="Test",
                Amount=10.0,
                Type="invalid"
            )
        assert "Invalid transaction type" in str(exc_info.value)
    
    def test_invalid_date(self):
        """Test that invalid dates raise error."""
        with pytest.raises(ValidationError):
            Transaction(
                Date="not-a-date",
                Description="Test",
                Amount=10.0,
                Type="Debit"
            )
    
    def test_empty_description(self):
        """Test that empty description raises error."""
        with pytest.raises(ValidationError):
            Transaction(
                Date="2025-12-15",
                Description="",
                Amount=10.0,
                Type="Debit"
            )
    
    def test_amount_range_validation(self):
        """Test amount must be within reasonable range."""
        with pytest.raises(ValidationError):
            Transaction(
                Date="2025-12-15",
                Description="Test",
                Amount=10_000_000,  # Too large
                Type="Debit"
            )
    
    def test_optional_balance(self):
        """Test that Balance is optional."""
        txn = Transaction(
            Date="2025-12-15",
            Description="Test",
            Amount=10.0,
            Type="Debit"
        )
        assert txn.Balance is None


class TestBudgetModel:
    """Tests for Budget Pydantic model."""
    
    def test_valid_budget(self):
        """Test creating a valid budget."""
        budget = Budget(category="Groceries", monthly_limit=500.0)
        assert budget.category == "Groceries"
        assert budget.monthly_limit == 500.0
    
    def test_budget_limit_parsing(self):
        """Test budget limit parsing with currency symbols."""
        budget = Budget(category="Dining", monthly_limit="$1,200.50")
        assert budget.monthly_limit == 1200.50
    
    def test_negative_budget_limit(self):
        """Test that negative budget limits raise error."""
        with pytest.raises(ValidationError) as exc_info:
            Budget(category="Test", monthly_limit=-100)
        assert "Budget limit must be positive" in str(exc_info.value)
    
    def test_zero_budget_limit(self):
        """Test that zero budget limit raises error."""
        with pytest.raises(ValidationError):
            Budget(category="Test", monthly_limit=0)
    
    def test_empty_category(self):
        """Test that empty category raises error."""
        with pytest.raises(ValidationError):
            Budget(category="", monthly_limit=100)


class TestPortfolioSnapshotModel:
    """Tests for PortfolioSnapshot Pydantic model."""
    
    def test_valid_snapshot(self):
        """Test creating a valid portfolio snapshot."""
        snapshot = PortfolioSnapshot(
            date="2025-12-15",
            cash_balance=10000.0,
            portfolio_value=50000.0,
            net_worth=60000.0
        )
        assert snapshot.date == date(2025, 12, 15)
        assert snapshot.net_worth == 60000.0
    
    def test_net_worth_validation(self):
        """Test that net worth must match cash + portfolio."""
        with pytest.raises(ValidationError) as exc_info:
            PortfolioSnapshot(
                date="2025-12-15",
                cash_balance=10000.0,
                portfolio_value=50000.0,
                net_worth=70000.0  # Wrong!
            )
        assert "doesn't match cash + portfolio" in str(exc_info.value)
    
    def test_negative_cash_balance(self):
        """Test that negative cash balance raises error."""
        with pytest.raises(ValidationError):
            PortfolioSnapshot(
                date="2025-12-15",
                cash_balance=-1000.0,
                portfolio_value=50000.0,
                net_worth=49000.0
            )
    
    def test_date_parsing(self):
        """Test date parsing for portfolio snapshot."""
        snapshot = PortfolioSnapshot(
            date="2025-12-15",
            cash_balance=1000.0,
            portfolio_value=5000.0,
            net_worth=6000.0
        )
        assert snapshot.date == date(2025, 12, 15)


class TestValidationFunctions:
    """Tests for validation helper functions."""
    
    def test_validate_transaction(self):
        """Test validate_transaction function."""
        data = {
            "Date": "2025-12-15",
            "Description": "Test Store",
            "Amount": 25.50,
            "Type": "Debit",
            "Category": "Shopping"
        }
        txn = validate_transaction(data)
        assert isinstance(txn, Transaction)
        assert txn.Amount == 25.50
    
    def test_validate_budget(self):
        """Test validate_budget function."""
        data = {"category": "Groceries", "monthly_limit": 600}
        budget = validate_budget(data)
        assert isinstance(budget, Budget)
        assert budget.monthly_limit == 600.0
    
    def test_validate_portfolio_snapshot(self):
        """Test validate_portfolio_snapshot function."""
        data = {
            "date": "2025-12-15",
            "cash_balance": 2000.0,
            "portfolio_value": 8000.0,
            "net_worth": 10000.0
        }
        snapshot = validate_portfolio_snapshot(data)
        assert isinstance(snapshot, PortfolioSnapshot)
        assert snapshot.net_worth == 10000.0
    
    def test_validate_transaction_invalid_data(self):
        """Test validation function with invalid data."""
        data = {
            "Date": "invalid",
            "Description": "Test",
            "Amount": "not-a-number",
            "Type": "Debit"
        }
        with pytest.raises(ValidationError):
            validate_transaction(data)
