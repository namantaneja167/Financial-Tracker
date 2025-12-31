"""
Unit tests for merchant_normalizer.py - Merchant name normalization.
"""
import json
import tempfile
from pathlib import Path
import pytest

from financial_tracker import merchant_normalizer


@pytest.fixture
def temp_mappings_file(monkeypatch, tmp_path):
    """Create a temporary mappings file for testing."""
    mappings_file = tmp_path / "merchant_mappings.json"
    monkeypatch.setattr(merchant_normalizer, "CUSTOM_MAPPINGS_FILE", mappings_file)
    return mappings_file


class TestBuiltInPatterns:
    """Tests for built-in regex pattern matching."""
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("UBER *TRIP ABC123", "Uber"),
        ("UBER *RIDE XYZ", "Uber"),
        ("UBER EATS *ORDER", "Uber Eats"),
        ("UBER EATS 5678", "Uber Eats"),
        ("LYFT *RIDE 456", "Lyft"),
        ("LYFT *TRIP", "Lyft"),
    ])
    def test_rideshare_patterns(self, input_desc, expected, temp_mappings_file):
        """Test rideshare service patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("AMZN MKTP US*AB1234", "Amazon"),
        ("AMAZON.COM*AB5678", "Amazon"),
        ("AMZ*PRIME VIDEO", "Amazon"),
    ])
    def test_amazon_patterns(self, input_desc, expected, temp_mappings_file):
        """Test Amazon patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("DOORDASH*RESTAURANT", "DoorDash"),
        ("GRUBHUB*ORDER123", "Grubhub"),
    ])
    def test_food_delivery_patterns(self, input_desc, expected, temp_mappings_file):
        """Test food delivery service patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("NETFLIX.COM", "Netflix"),
        ("SPOTIFY USA", "Spotify"),
        ("SPOTIFY PREMIUM", "Spotify"),
        ("APPLE.COM/BILL", "Apple"),
    ])
    def test_subscription_patterns(self, input_desc, expected, temp_mappings_file):
        """Test subscription service patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("WHOLEFDS #123", "Whole Foods"),
        ("WM SUPERCENTER #4567", "Walmart"),
        ("TARGET T-1234", "Target"),
        ("TARGET 12345", "Target"),
        ("COSTCO WHSE #0089", "Costco"),
    ])
    def test_retail_patterns(self, input_desc, expected, temp_mappings_file):
        """Test retail store patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("STARBUCKS STORE 12345", "Starbucks"),
        ("DUNKIN #5678", "Dunkin"),
        ("MCDONALDS F12345", "McDonalds"),
    ])
    def test_restaurant_patterns(self, input_desc, expected, temp_mappings_file):
        """Test restaurant patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("CHEVRON 12345", "Chevron"),
        ("SHELL OIL 12345", "Shell"),
    ])
    def test_gas_station_patterns(self, input_desc, expected, temp_mappings_file):
        """Test gas station patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("VANGUARD INVESTMENT", "Vanguard"),
        ("FIDELITY BRK", "Fidelity"),
    ])
    def test_financial_patterns(self, input_desc, expected, temp_mappings_file):
        """Test financial service patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected
    
    @pytest.mark.parametrize("input_desc,expected", [
        ("PAYPAL *MERCHANT", "PayPal"),
        ("SQ *COFFEE SHOP", "Square"),
        ("TST*RESTAURANT", "Toast"),
        ("GOOGLE *SERVICES", "Google"),
    ])
    def test_payment_processor_patterns(self, input_desc, expected, temp_mappings_file):
        """Test payment processor patterns."""
        result = merchant_normalizer.normalize_merchant(input_desc)
        assert result == expected


class TestCustomMappings:
    """Tests for custom merchant mappings."""
    
    def test_load_custom_mappings_empty(self, temp_mappings_file):
        """Test loading mappings when file doesn't exist."""
        result = merchant_normalizer.load_custom_mappings()
        assert result == {}
    
    def test_save_and_load_custom_mappings(self, temp_mappings_file):
        """Test saving and loading custom mappings."""
        mappings = {
            "LOCAL COFFEE": "Local Coffee Shop",
            "MY GROCERY": "My Grocery Store"
        }
        
        merchant_normalizer.save_custom_mappings(mappings)
        loaded = merchant_normalizer.load_custom_mappings()
        
        assert loaded == mappings
    
    def test_custom_mapping_takes_precedence(self, temp_mappings_file):
        """Test that custom mappings take precedence over built-in."""
        # Custom mapping for something that would match a built-in
        mappings = {"AMAZON.COM*SPECIAL": "Amazon Special"}
        merchant_normalizer.save_custom_mappings(mappings)
        
        result = merchant_normalizer.normalize_merchant("AMAZON.COM*SPECIAL")
        assert result == "Amazon Special"
    
    def test_add_custom_mapping(self, temp_mappings_file):
        """Test adding a single custom mapping."""
        merchant_normalizer.add_custom_mapping("TEST STORE", "Test Store Inc")
        
        mappings = merchant_normalizer.load_custom_mappings()
        assert mappings["TEST STORE"] == "Test Store Inc"
    
    def test_remove_custom_mapping(self, temp_mappings_file):
        """Test removing a custom mapping."""
        mappings = {"STORE A": "Store A Inc", "STORE B": "Store B Inc"}
        merchant_normalizer.save_custom_mappings(mappings)
        
        merchant_normalizer.remove_custom_mapping("STORE A")
        
        remaining = merchant_normalizer.load_custom_mappings()
        assert "STORE A" not in remaining
        assert "STORE B" in remaining
    
    def test_remove_nonexistent_mapping(self, temp_mappings_file):
        """Test removing a mapping that doesn't exist."""
        merchant_normalizer.remove_custom_mapping("NONEXISTENT")
        # Should not raise
    
    def test_get_all_custom_mappings(self, temp_mappings_file):
        """Test getting all custom mappings."""
        mappings = {"A": "Alpha", "B": "Beta"}
        merchant_normalizer.save_custom_mappings(mappings)
        
        result = merchant_normalizer.get_all_custom_mappings()
        assert result == mappings
    
    def test_corrupted_mappings_file(self, temp_mappings_file):
        """Test handling of corrupted mappings file."""
        temp_mappings_file.write_text("not valid json {{{")
        
        result = merchant_normalizer.load_custom_mappings()
        assert result == {}


class TestNormalizeMerchant:
    """Tests for normalize_merchant function."""
    
    def test_empty_description(self, temp_mappings_file):
        """Test normalizing empty description."""
        result = merchant_normalizer.normalize_merchant("")
        assert result == ""
    
    def test_none_description(self, temp_mappings_file):
        """Test normalizing None description."""
        result = merchant_normalizer.normalize_merchant(None)
        assert result == ""
    
    def test_cleans_transaction_codes(self, temp_mappings_file):
        """Test that transaction codes are cleaned."""
        result = merchant_normalizer.normalize_merchant("SOME STORE ABC123DEF456")
        # Should clean up trailing alphanumeric codes
        assert "ABC123DEF456" not in result
    
    def test_cleans_store_numbers(self, temp_mappings_file):
        """Test that store numbers are cleaned."""
        result = merchant_normalizer.normalize_merchant("RANDOM SHOP #1234")
        # Should remove store number suffix
        assert "#1234" not in result
    
    def test_title_case_output(self, temp_mappings_file):
        """Test that unmatched merchants get title cased."""
        result = merchant_normalizer.normalize_merchant("some random store")
        assert result == "Some Random Store"
    
    def test_preserves_whitespace_trimming(self, temp_mappings_file):
        """Test that whitespace is trimmed."""
        result = merchant_normalizer.normalize_merchant("  SOME STORE  ")
        assert not result.startswith(" ")
        assert not result.endswith(" ")

