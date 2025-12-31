"""Tests for CSV importer module."""
import pytest
import io

from financial_tracker.csv_importer import parse_csv_to_transactions


class TestParseCSVToTransactions:
    """Test CSV parsing functionality."""
    
    def test_parse_standard_csv(self):
        """Test parsing standard CSV format."""
        csv_content = b"""Date,Description,Amount,Type,Balance
2025-01-15,Grocery Store,-50.25,Debit,1000.00
2025-01-16,Salary,2000.00,Credit,3000.00"""
        
        result = parse_csv_to_transactions(csv_content)
        
        assert len(result) == 2
        assert result[0]["Description"] == "Grocery Store"
        assert float(result[0]["Amount"]) == -50.25
        assert result[1]["Description"] == "Salary"
        assert float(result[1]["Amount"]) == 2000.00
    
    def test_parse_empty_csv(self):
        """Test parsing empty CSV."""
        csv_content = b"""Date,Description,Amount,Type,Balance"""
        
        result = parse_csv_to_transactions(csv_content)
        
        assert len(result) == 0
    
    def test_parse_csv_with_missing_columns(self):
        """Test CSV with only essential columns."""
        csv_content = b"""Date,Description,Amount
2025-01-15,Test Transaction,100.00"""
        
        result = parse_csv_to_transactions(csv_content)
        
        assert len(result) == 1
        assert result[0]["Date"] == "2025-01-15"
