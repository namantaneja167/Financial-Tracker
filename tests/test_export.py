"""Tests for export module."""
import pytest
import pandas as pd
from datetime import datetime
import io

from financial_tracker.export import (
    export_transactions_to_csv,
    export_transactions_to_excel,
    get_export_filename,
    _filter_transactions,
    _create_summary
)


class TestExportToCSV:
    """Test CSV export functionality."""
    
    def test_export_basic_csv(self):
        """Test basic CSV export."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Description": ["Test 1", "Test 2"],
            "Amount": [100.0, 200.0],
            "Type": ["Debit", "Credit"]
        })
        
        result = export_transactions_to_csv(df)
        
        assert isinstance(result, bytes)
        assert b"Date" in result
        assert b"Test 1" in result
    
    def test_export_empty_csv(self):
        """Test CSV export with empty DataFrame."""
        df = pd.DataFrame()
        
        result = export_transactions_to_csv(df)
        
        assert isinstance(result, bytes)
    
    def test_export_with_date_filter(self):
        """Test CSV export with date filtering."""
        df = pd.DataFrame({
            "Date": pd.to_datetime(["2025-01-15", "2025-02-15", "2025-03-15"]),
            "Description": ["Jan", "Feb", "Mar"],
            "Amount": [100, 200, 300]
        })
        
        result = export_transactions_to_csv(
            df,
            start_date=datetime(2025, 2, 1),
            end_date=datetime(2025, 2, 28)
        )
        
        assert b"Feb" in result
        assert b"Jan" not in result
    
    def test_export_with_category_filter(self):
        """Test CSV export with category filtering."""
        df = pd.DataFrame({
            "Date": ["2025-01-15", "2025-01-16"],
            "Description": ["Test 1", "Test 2"],
            "Amount": [100, 200],
            "Category": ["Groceries", "Transport"]
        })
        
        result = export_transactions_to_csv(df, categories=["Groceries"])
        
        assert b"Test 1" in result
        assert b"Test 2" not in result


class TestExportToExcel:
    """Test Excel export functionality."""
    
    def test_export_basic_excel(self):
        """Test basic Excel export."""
        df = pd.DataFrame({
            "Date": ["2025-01-15"],
            "Description": ["Test"],
            "Amount": [100.0],
            "Category": ["Groceries"]
        })
        
        result = export_transactions_to_excel(df)
        
        assert isinstance(result, bytes)
        assert len(result) > 0
    
    def test_export_empty_excel(self):
        """Test Excel export with empty DataFrame."""
        df = pd.DataFrame()
        
        result = export_transactions_to_excel(df)
        
        assert isinstance(result, bytes)


class TestFilterTransactions:
    """Test transaction filtering."""
    
    def test_filter_by_date_range(self):
        """Test filtering by date range."""
        df = pd.DataFrame({
            "Date": pd.to_datetime(["2025-01-01", "2025-02-01", "2025-03-01"]),
            "Amount": [100, 200, 300]
        })
        
        result = _filter_transactions(
            df,
            start_date=datetime(2025, 2, 1),
            end_date=datetime(2025, 2, 28),
            categories=None
        )
        
        assert len(result) == 1
        assert result.iloc[0]["Amount"] == 200
    
    def test_filter_by_categories(self):
        """Test filtering by categories."""
        df = pd.DataFrame({
            "Date": ["2025-01-01", "2025-01-02", "2025-01-03"],
            "Category": ["Groceries", "Transport", "Utilities"],
            "Amount": [100, 200, 300]
        })
        
        result = _filter_transactions(df, None, None, ["Groceries", "Transport"])
        
        assert len(result) == 2
    
    def test_filter_empty_dataframe(self):
        """Test filtering empty DataFrame."""
        df = pd.DataFrame()
        
        result = _filter_transactions(df, None, None, None)
        
        assert result.empty


class TestCreateSummary:
    """Test summary creation."""
    
    def test_create_basic_summary(self):
        """Test creating summary statistics."""
        df = pd.DataFrame({
            "Date": pd.to_datetime(["2025-01-15", "2025-01-16"]),
            "Amount": [100.0, 200.0],
            "Type": ["Debit", "Credit"],
            "Category": ["Groceries", "Income"]
        })
        
        result = _create_summary(df)
        
        assert not result.empty
        assert "Total Transactions" in result["Metric"].values
        assert len(result) > 0
    
    def test_summary_with_amounts(self):
        """Test summary includes amount statistics."""
        df = pd.DataFrame({
            "Amount": [100, 200, 300],
            "Category": ["A", "B", "C"]
        })
        
        result = _create_summary(df)
        
        metrics = result["Metric"].tolist()
        assert any("Total Amount" in str(m) for m in metrics)
        assert any("Average Amount" in str(m) for m in metrics)


class TestGetExportFilename:
    """Test filename generation."""
    
    def test_csv_filename(self):
        """Test CSV filename generation."""
        filename = get_export_filename('csv')
        
        assert filename.endswith('.csv')
        assert 'transactions_' in filename
    
    def test_excel_filename(self):
        """Test Excel filename generation."""
        filename = get_export_filename('excel')
        
        assert filename.endswith('.xlsx')
        assert 'transactions_' in filename
    
    def test_custom_prefix(self):
        """Test filename with custom prefix."""
        filename = get_export_filename('csv', prefix='budget')
        
        assert 'budget_' in filename
        assert filename.endswith('.csv')
