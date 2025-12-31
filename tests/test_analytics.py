"""Tests for analytics module."""
import pytest
import pandas as pd
import numpy as np
from datetime import datetime

from financial_tracker.analytics import prep_analytics_frame, latest_cash_balance


class TestPrepAnalyticsFrame:
    """Test analytics DataFrame preparation."""
    
    def test_prep_basic_transactions(self):
        """Test basic transaction preparation."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Description": ["Grocery", "Salary"],
            "Amount": [50.25, 2000.00],
            "Type": ["Debit", "Credit"]
        })
        
        result = prep_analytics_frame(df)
        
        assert "Month" in result.columns
        assert "Expense" in result.columns
        assert "Income" in result.columns
        assert "Category" in result.columns
        assert result["Expense"].iloc[0] == 50.25
        assert result["Income"].iloc[1] == 2000.00
    
    def test_prep_adds_month_column(self):
        """Test Month column is derived from Date."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-02-20"],
            "Amount": [100, 200],
            "Type": ["Debit", "Debit"]
        })
        
        result = prep_analytics_frame(df)
        
        assert len(result["Month"].unique()) == 2
        assert pd.Timestamp("2025-01-01") in result["Month"].values
        assert pd.Timestamp("2025-02-01") in result["Month"].values
    
    def test_prep_splits_expense_income(self):
        """Test splitting amounts into Expense and Income."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16", "2025-01-17"],
            "Amount": [100, 200, 50],
            "Type": ["Debit", "Credit", "Debit"]
        })
        
        result = prep_analytics_frame(df)
        
        # Debits become Expenses
        assert result.loc[result["Type"] == "Debit", "Expense"].sum() == 150
        # Credits become Income
        assert result.loc[result["Type"] == "Credit", "Income"].sum() == 200
    
    def test_prep_handles_missing_category(self):
        """Test that missing Category column is added with Misc."""
        df = pd.DataFrame({
            "Date": ["2025-01-15"],
            "Amount": [100],
            "Type": ["Debit"]
        })
        
        result = prep_analytics_frame(df)
        
        assert "Category" in result.columns
        assert result["Category"].iloc[0] == "Misc"
    
    def test_prep_fills_na_categories(self):
        """Test that NA categories are filled with Misc."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Amount": [100, 200],
            "Type": ["Debit", "Credit"],
            "Category": ["Groceries", None]
        })
        
        result = prep_analytics_frame(df)
        
        assert result["Category"].iloc[0] == "Groceries"
        assert result["Category"].iloc[1] == "Misc"
    
    def test_prep_handles_invalid_dates(self):
        """Test that invalid dates are dropped."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "not a date", "2025-01-17"],
            "Amount": [100, 200, 300],
            "Type": ["Debit", "Debit", "Debit"]
        })
        
        result = prep_analytics_frame(df)
        
        # Invalid date row should be dropped
        assert len(result) == 2
    
    def test_prep_handles_invalid_amounts(self):
        """Test that invalid amounts are coerced to NaN and filled."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Amount": [100, "invalid"],
            "Type": ["Debit", "Debit"]
        })
        
        result = prep_analytics_frame(df)
        
        # Invalid amount becomes 0 after fillna
        assert result["Expense"].iloc[1] == 0
    
    def test_prep_normalizes_type_case(self):
        """Test that Type is normalized to title case."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Amount": [100, 200],
            "Type": ["debit", "CREDIT"]
        })
        
        result = prep_analytics_frame(df)
        
        assert result["Type"].iloc[0] == "Debit"
        assert result["Type"].iloc[1] == "Credit"
    
    def test_prep_preserves_original_df(self):
        """Test that original DataFrame is not modified."""
        df = pd.DataFrame({
            "Date": ["2025-01-15"],
            "Amount": [100],
            "Type": ["Debit"]
        })
        
        original_cols = set(df.columns)
        prep_analytics_frame(df)
        
        # Original DataFrame should be unchanged
        assert set(df.columns) == original_cols


class TestLatestCashBalance:
    """Test latest cash balance extraction."""
    
    def test_latest_balance_with_dates(self):
        """Test extracting latest balance when dates are present."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16", "2025-01-17"],
            "Balance": [1000, 950, 1100]
        })
        
        result = latest_cash_balance(df)
        
        assert result == 1100.0
    
    def test_latest_balance_without_dates(self):
        """Test extracting latest balance without Date column."""
        df = pd.DataFrame({
            "Balance": [1000, 950, 1100]
        })
        
        result = latest_cash_balance(df)
        
        # Last balance in DataFrame
        assert result == 1100.0
    
    def test_latest_balance_empty_df(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        
        result = latest_cash_balance(df)
        
        assert result is None
    
    def test_latest_balance_no_balance_column(self):
        """Test with DataFrame missing Balance column."""
        df = pd.DataFrame({
            "Date": ["2025-01-15"],
            "Amount": [100]
        })
        
        result = latest_cash_balance(df)
        
        assert result is None
    
    def test_latest_balance_all_na(self):
        """Test when all Balance values are NA."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Balance": [None, np.nan]
        })
        
        result = latest_cash_balance(df)
        
        assert result is None
    
    def test_latest_balance_invalid_balance_values(self):
        """Test with invalid balance values."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Balance": ["invalid", 1000]
        })
        
        result = latest_cash_balance(df)
        
        # Should return the valid balance
        assert result == 1000.0
    
    def test_latest_balance_sorts_by_date(self):
        """Test that balances are sorted by date before extraction."""
        df = pd.DataFrame({
            "Date": ["2025-01-17", "2025-01-15", "2025-01-16"],
            "Balance": [1100, 1000, 950]
        })
        
        result = latest_cash_balance(df)
        
        # Should return balance from latest date (2025-01-17)
        assert result == 1100.0
    
    def test_latest_balance_with_mixed_na(self):
        """Test with mix of valid and NA balances."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16", "2025-01-17"],
            "Balance": [1000, None, 1100]
        })
        
        result = latest_cash_balance(df)
        
        # Should return latest valid balance
        assert result == 1100.0
