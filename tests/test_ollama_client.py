"""Tests for Ollama client module."""
import json
import pytest
from unittest.mock import Mock, patch
import requests

from financial_tracker.ollama_client import (
    ollama_extract_transactions,
    _extract_json_block,
    _to_number,
    _normalize_record,
)


class TestExtractJsonBlock:
    """Test JSON extraction from model responses."""
    
    def test_extract_json_array(self):
        """Test extracting JSON array from text."""
        text = 'Here is the data: [{"name": "test"}, {"name": "test2"}]'
        result = _extract_json_block(text)
        assert isinstance(result, list)
        assert len(result) == 2
        assert result[0]["name"] == "test"
    
    def test_extract_json_object(self):
        """Test extracting JSON object from text."""
        text = 'Some text {"key": "value", "count": 42} more text'
        result = _extract_json_block(text)
        assert isinstance(result, dict)
        assert result["key"] == "value"
        assert result["count"] == 42
    
    def test_extract_pure_json(self):
        """Test extracting pure JSON without surrounding text."""
        # Note: _extract_json_block prioritizes arrays over objects
        # So a plain array will be extracted as an array
        text = '[{"amount": 100}]'
        result = _extract_json_block(text)
        assert isinstance(result, list)
        assert len(result) == 1
        
        # Object without array is extracted as object
        text2 = '{"status": "success"}'
        result2 = _extract_json_block(text2)
        assert isinstance(result2, dict)
        assert result2["status"] == "success"
    
    def test_extract_multiline_json(self):
        """Test extracting JSON with newlines."""
        text = """Here is the result:
        [
            {"date": "2025-01-01"},
            {"date": "2025-01-02"}
        ]
        """
        result = _extract_json_block(text)
        assert isinstance(result, list)
        assert len(result) == 2


class TestToNumber:
    """Test number conversion utility."""
    
    def test_convert_integer(self):
        """Test converting integer to float."""
        assert _to_number(42) == 42.0
    
    def test_convert_float(self):
        """Test converting float."""
        assert _to_number(42.5) == 42.5
    
    def test_convert_string_number(self):
        """Test converting string number."""
        assert _to_number("123.45") == 123.45
    
    def test_convert_with_comma(self):
        """Test converting number with comma separator."""
        assert _to_number("1,234.56") == 1234.56
    
    def test_convert_with_currency_symbol(self):
        """Test removing currency symbols."""
        assert _to_number("$100.00") == 100.0
    
    def test_convert_negative(self):
        """Test converting negative number."""
        assert _to_number("-50.25") == -50.25
    
    def test_convert_none(self):
        """Test converting None."""
        assert _to_number(None) is None
    
    def test_convert_empty_string(self):
        """Test converting empty string."""
        assert _to_number("") is None
    
    def test_convert_whitespace(self):
        """Test converting whitespace."""
        assert _to_number("   ") is None
    
    def test_convert_invalid_string(self):
        """Test converting invalid string."""
        assert _to_number("not a number") is None
    
    def test_convert_dash_only(self):
        """Test converting dash only."""
        assert _to_number("-") is None
    
    def test_convert_dot_only(self):
        """Test converting dot only."""
        assert _to_number(".") is None


class TestNormalizeRecord:
    """Test record normalization."""
    
    def test_normalize_complete_record(self):
        """Test normalizing complete transaction record."""
        record = {
            "Date": "2025-01-15",
            "Description": "Whole Foods",
            "Amount": 50.25,
            "Type": "Debit",
            "Balance": 1000.00
        }
        result = _normalize_record(record)
        assert result["Date"] == "2025-01-15"
        assert result["Description"] == "Whole Foods"
        assert result["Amount"] == 50.25
        assert result["Type"] == "Debit"
        assert result["Balance"] == 1000.00
    
    def test_normalize_lowercase_keys(self):
        """Test normalizing record with lowercase keys."""
        record = {
            "date": "2025-01-15",
            "description": "Amazon",
            "amount": "100.00",
            "type": "credit",
            "balance": "2000.00"
        }
        result = _normalize_record(record)
        assert result["Date"] == "2025-01-15"
        assert result["Description"] == "Amazon"
        assert result["Amount"] == 100.0
        assert result["Type"] == "Credit"
        assert result["Balance"] == 2000.0
    
    def test_normalize_missing_type_positive_amount(self):
        """Test type inference for positive amount."""
        record = {
            "Date": "2025-01-15",
            "Description": "Salary",
            "Amount": 5000.0
        }
        result = _normalize_record(record)
        assert result["Type"] == "Credit"
    
    def test_normalize_missing_type_negative_amount(self):
        """Test type inference for negative amount."""
        record = {
            "Date": "2025-01-15",
            "Description": "Rent",
            "Amount": -1500.0
        }
        result = _normalize_record(record)
        assert result["Type"] == "Debit"
    
    def test_normalize_missing_balance(self):
        """Test normalizing record without balance."""
        record = {
            "Date": "2025-01-15",
            "Description": "Coffee",
            "Amount": 5.0,
            "Type": "Debit"
        }
        result = _normalize_record(record)
        assert result["Balance"] is None
    
    def test_normalize_empty_description(self):
        """Test normalizing record with missing description."""
        record = {
            "Date": "2025-01-15",
            "Amount": 10.0,
            "Type": "Debit"
        }
        result = _normalize_record(record)
        assert result["Description"] == ""
    
    def test_normalize_string_amount(self):
        """Test normalizing record with string amount."""
        record = {
            "Date": "2025-01-15",
            "Description": "Store",
            "Amount": "$123.45",
            "Type": "Debit"
        }
        result = _normalize_record(record)
        assert result["Amount"] == 123.45


class TestOllamaExtractTransactions:
    """Test Ollama transaction extraction."""
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_success(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test successful transaction extraction."""
        # Mock configuration
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        # Mock response
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps([
                {
                    "Date": "2025-01-15",
                    "Description": "Whole Foods Market",
                    "Amount": -50.25,
                    "Type": "Debit",
                    "Balance": 1000.00
                },
                {
                    "Date": "2025-01-16",
                    "Description": "Paycheck Deposit",
                    "Amount": 2000.00,
                    "Type": "Credit",
                    "Balance": 3000.00
                }
            ])
        }
        mock_post.return_value = mock_response
        
        # Call function
        raw_text = "Bank statement text here..."
        result = ollama_extract_transactions(raw_text)
        
        # Verify results
        assert len(result) == 2
        assert result[0]["Description"] == "Whole Foods Market"
        assert result[0]["Amount"] == -50.25
        assert result[1]["Description"] == "Paycheck Deposit"
        assert result[1]["Amount"] == 2000.0
        
        # Verify API call
        mock_post.assert_called_once()
        call_args = mock_post.call_args
        assert "http://localhost:11434/api/generate" in call_args[0]
        assert call_args[1]["json"]["model"] == "llama2"
        assert call_args[1]["json"]["stream"] is False
        assert call_args[1]["timeout"] == 30
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_wrapped_in_dict(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test extraction when response is wrapped in transactions key."""
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps({
                "transactions": [
                    {
                        "Date": "2025-01-15",
                        "Description": "Coffee",
                        "Amount": 5.0,
                        "Type": "Debit",
                        "Balance": None
                    }
                ]
            })
        }
        mock_post.return_value = mock_response
        
        result = ollama_extract_transactions("text")
        assert len(result) == 1
        assert result[0]["Description"] == "Coffee"
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_http_error(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test handling of HTTP errors."""
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        mock_response = Mock()
        mock_response.raise_for_status.side_effect = requests.HTTPError("500 Server Error")
        mock_post.return_value = mock_response
        
        with pytest.raises(requests.HTTPError):
            ollama_extract_transactions("text")
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_invalid_json(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test handling of invalid JSON response."""
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": "not valid json at all"
        }
        mock_post.return_value = mock_response
        
        with pytest.raises((json.JSONDecodeError, ValueError)):
            ollama_extract_transactions("text")
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_not_array(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test handling when response is not an array."""
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps({"not": "an array"})
        }
        mock_post.return_value = mock_response
        
        with pytest.raises(ValueError, match="did not return a JSON array"):
            ollama_extract_transactions("text")
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_empty_array(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test extraction with empty transaction array."""
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps([])
        }
        mock_post.return_value = mock_response
        
        result = ollama_extract_transactions("text")
        assert result == []
    
    @patch('financial_tracker.ollama_client.requests.post')
    @patch('financial_tracker.ollama_client.get_ollama_url')
    @patch('financial_tracker.ollama_client.get_ollama_model')
    @patch('financial_tracker.ollama_client.get_ollama_timeout')
    def test_extract_transactions_mixed_valid_invalid(self, mock_timeout, mock_model, mock_url, mock_post):
        """Test extraction with mix of valid dict and invalid items."""
        mock_url.return_value = "http://localhost:11434"
        mock_model.return_value = "llama2"
        mock_timeout.return_value = 30
        
        mock_response = Mock()
        mock_response.json.return_value = {
            "response": json.dumps([
                {
                    "Date": "2025-01-15",
                    "Description": "Valid Transaction",
                    "Amount": 50.0,
                    "Type": "Debit"
                },
                "invalid item",
                None,
                {
                    "Date": "2025-01-16",
                    "Description": "Another Valid",
                    "Amount": 100.0,
                    "Type": "Credit"
                }
            ])
        }
        mock_post.return_value = mock_response
        
        result = ollama_extract_transactions("text")
        # Only dict items are normalized
        assert len(result) == 2
        assert result[0]["Description"] == "Valid Transaction"
        assert result[1]["Description"] == "Another Valid"
