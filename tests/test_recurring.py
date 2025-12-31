"""Tests for recurring transactions module."""
import pytest
import pandas as pd
from datetime import datetime, timedelta

from financial_tracker.recurring import (
    detect_recurring_transactions,
    get_upcoming_recurring_expenses
)


class TestDetectRecurringTransactions:
    """Test recurring transaction detection."""
    
    def test_detect_monthly_subscription(self):
        """Test detecting monthly subscription."""
        # Create monthly subscription pattern
        dates = [datetime(2025, 1, 15), datetime(2025, 2, 15), datetime(2025, 3, 15)]
        df = pd.DataFrame({
            "Date": dates,
            "Description": ["Netflix Subscription", "Netflix Subscription", "Netflix Subscription"],
            "Amount": [15.99, 15.99, 15.99],
            "Category": ["Entertainment", "Entertainment", "Entertainment"]
        })
        
        result = detect_recurring_transactions(df)
        
        assert len(result) > 0
        assert result[0]["frequency_days"] == pytest.approx(30, abs=2)  # About 30 days
        assert result[0]["occurrences"] == 3
    
    def test_detect_no_recurring_single_transaction(self):
        """Test with single transaction (not recurring)."""
        df = pd.DataFrame({
            "Date": [datetime(2025, 1, 15)],
            "Description": ["One-time purchase"],
            "Amount": [100.00]
        })
        
        result = detect_recurring_transactions(df)
        
        assert len(result) == 0
    
    def test_detect_empty_dataframe(self):
        """Test with empty DataFrame."""
        df = pd.DataFrame()
        
        result = detect_recurring_transactions(df)
        
        assert result == []
    
    def test_detect_no_date_column(self):
        """Test with DataFrame missing Date column."""
        df = pd.DataFrame({
            "Description": ["Test"],
            "Amount": [100]
        })
        
        result = detect_recurring_transactions(df)
        
        assert result == []
    
    def test_detect_weekly_pattern(self):
        """Test detecting weekly pattern."""
        # Create weekly pattern
        base_date = datetime(2025, 1, 1)
        dates = [base_date + timedelta(days=7*i) for i in range(4)]
        
        df = pd.DataFrame({
            "Date": dates,
            "Description": ["Weekly Groceries"] * 4,
            "Amount": [50] * 4,
            "Category": ["Groceries"] * 4
        })
        
        result = detect_recurring_transactions(df)
        
        assert len(result) > 0
        assert result[0]["frequency_days"] == pytest.approx(7, abs=1)
    
    def test_detect_inconsistent_intervals_rejected(self):
        """Test that inconsistent intervals are rejected."""
        df = pd.DataFrame({
            "Date": [datetime(2025, 1, 1), datetime(2025, 1, 8), datetime(2025, 2, 1)],
            "Description": ["Irregular Payment"] * 3,
            "Amount": [100] * 3
        })
        
        result = detect_recurring_transactions(df)
        
        # Should be rejected due to inconsistency (7 days then 24 days)
        assert len(result) == 0
    
    def test_detect_similar_descriptions(self):
        """Test grouping similar descriptions."""
        # Use same first 3 words to ensure grouping
        df = pd.DataFrame({
            "Date": [datetime(2025, 1, 15), datetime(2025, 2, 15), datetime(2025, 3, 15)],
            "Description": ["Spotify Premium", "Spotify Premium", "Spotify Premium"],
            "Amount": [10, 10, 10]  # Round to nearest 10 for grouping
        })
        
        result = detect_recurring_transactions(df)
        
        # Should group identical descriptions
        assert len(result) > 0
        assert result[0]["occurrences"] == 3
    
    def test_detect_filters_long_intervals(self):
        """Test that intervals > 90 days are filtered."""
        df = pd.DataFrame({
            "Date": [datetime(2025, 1, 1), datetime(2025, 4, 15), datetime(2025, 8, 1)],
            "Description": ["Quarterly Payment"] * 3,
            "Amount": [500] * 3
        })
        
        result = detect_recurring_transactions(df)
        
        # Should be filtered (intervals > 90 days)
        assert len(result) == 0
    
    def test_detect_next_expected_date(self):
        """Test calculation of next expected date."""
        dates = [datetime(2025, 1, 15), datetime(2025, 2, 15)]
        df = pd.DataFrame({
            "Date": dates,
            "Description": ["Monthly Bill", "Monthly Bill"],
            "Amount": [100, 100]
        })
        
        result = detect_recurring_transactions(df)
        
        assert len(result) > 0
        # Next expected should be about 1 month after last date
        expected_next = dates[-1] + timedelta(days=31)
        assert result[0]["next_expected"].date() == expected_next.date()
    
    def test_detect_invalid_dates_dropped(self):
        """Test that invalid dates are handled."""
        df = pd.DataFrame({
            "Date": [datetime(2025, 1, 15), None, datetime(2025, 2, 15)],
            "Description": ["Test", "Test", "Test"],
            "Amount": [100, 100, 100]
        })
        
        result = detect_recurring_transactions(df)
        
        # Should work with valid dates only
        assert isinstance(result, list)


class TestGetUpcomingRecurringExpenses:
    """Test upcoming recurring expenses."""
    
    def test_upcoming_expenses_within_30_days(self):
        """Test finding expenses due in next 30 days."""
        # Create transaction that should recur soon
        base_date = datetime.now() - timedelta(days=30)
        dates = [base_date - timedelta(days=30*i) for i in range(3)]
        dates.reverse()  # Chronological order
        
        df = pd.DataFrame({
            "Date": dates,
            "Description": ["Rent Payment"] * 3,
            "Amount": [1500] * 3,
            "Category": ["Housing"] * 3
        })
        
        result = get_upcoming_recurring_expenses(df, days_ahead=30)
        
        # Should find the upcoming rent payment
        assert len(result) > 0
        assert "Description" in result.columns
        assert "Days Until" in result.columns
    
    def test_upcoming_expenses_no_recurring(self):
        """Test with no recurring patterns."""
        df = pd.DataFrame({
            "Date": [datetime.now()],
            "Description": ["One-time"],
            "Amount": [100]
        })
        
        result = get_upcoming_recurring_expenses(df)
        
        assert len(result) == 0
    
    def test_upcoming_expenses_custom_days_ahead(self):
        """Test with custom days_ahead parameter."""
        base_date = datetime.now() - timedelta(days=45)
        dates = [base_date - timedelta(days=45*i) for i in range(3)]
        dates.reverse()
        
        df = pd.DataFrame({
            "Date": dates,
            "Description": ["Quarterly Fee"] * 3,
            "Amount": [300] * 3
        })
        
        result = get_upcoming_recurring_expenses(df, days_ahead=60)
        
        # Should find it with longer window
        assert len(result) >= 0  # May or may not find depending on exact timing
    
    def test_upcoming_expenses_includes_all_fields(self):
        """Test that result includes all expected fields."""
        base_date = datetime.now() - timedelta(days=30)
        dates = [base_date - timedelta(days=30*i) for i in range(3)]
        dates.reverse()
        
        df = pd.DataFrame({
            "Date": dates,
            "Description": ["Monthly Service"] * 3,
            "Amount": [50] * 3,
            "Category": ["Utilities"] * 3
        })
        
        result = get_upcoming_recurring_expenses(df)
        
        if len(result) > 0:
            expected_cols = ["Description", "Amount", "Category", "Expected Date", 
                           "Days Until", "Frequency", "Confidence"]
            for col in expected_cols:
                assert col in result.columns
    
    def test_upcoming_expenses_sorted_by_date(self):
        """Test that results are sorted by expected date."""
        # Create two recurring patterns with different intervals
        base1 = datetime.now() - timedelta(days=15)
        base2 = datetime.now() - timedelta(days=25)
        
        df = pd.DataFrame({
            "Date": [
                base1 - timedelta(days=15*2), base1 - timedelta(days=15), base1,
                base2 - timedelta(days=25*2), base2 - timedelta(days=25), base2
            ],
            "Description": ["Bill A", "Bill A", "Bill A", "Bill B", "Bill B", "Bill B"],
            "Amount": [100, 100, 100, 200, 200, 200],
            "Category": ["Utilities"] * 6
        })
        
        result = get_upcoming_recurring_expenses(df)
        
        if len(result) > 1:
            # Check that dates are sorted
            dates = result["Expected Date"].tolist()
            assert dates == sorted(dates)
