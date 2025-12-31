"""
Unit tests for categorizer.py - Transaction categorization logic.
"""
import pytest
import pandas as pd
from unittest.mock import Mock, patch, MagicMock

from financial_tracker.categorizer import (
    categorize_transactions,
    _keyword_category,
    _simulate_llm_category,
    _embeddings_category,
    get_keyword_rules,
    save_rules,
    CATEGORIES,
)


class TestKeywordCategorization:
    """Tests for keyword-based categorization."""
    
    def test_keyword_category_match(self):
        """Test that keyword matching works."""
        rules = [
            {"category": "Groceries", "keywords": ["whole foods", "safeway", "grocery"]},
            {"category": "Dining", "keywords": ["restaurant", "cafe", "pizza"]}
        ]
        
        assert _keyword_category("WHOLE FOODS MARKET", rules) == "Groceries"
        assert _keyword_category("Pizza Hut", rules) == "Dining"
        assert _keyword_category("unknown store", rules) is None
    
    def test_keyword_category_case_insensitive(self):
        """Test that keyword matching is case-insensitive."""
        rules = [{"category": "Transport", "keywords": ["uber", "lyft"]}]
        
        assert _keyword_category("UBER *TRIP", rules) == "Transport"
        assert _keyword_category("uber trip", rules) == "Transport"
        assert _keyword_category("Uber Trip", rules) == "Transport"
    
    def test_keyword_category_empty_description(self):
        """Test handling of empty description."""
        rules = [{"category": "Groceries", "keywords": ["grocery"]}]
        assert _keyword_category("", rules) is None
        assert _keyword_category(None, rules) is None


class TestLLMFallback:
    """Tests for simulated LLM categorization fallback."""
    
    def test_simulate_llm_category_rent(self):
        """Test LLM fallback for rent-related transactions."""
        result = _simulate_llm_category("APARTMENT LEASE PAYMENT")
        assert result == "Rent"
    
    def test_simulate_llm_category_groceries(self):
        """Test LLM fallback for grocery-related transactions."""
        result = _simulate_llm_category("FARMERS MARKET")
        assert result == "Groceries"
    
    def test_simulate_llm_category_income(self):
        """Test LLM fallback for income transactions."""
        result = _simulate_llm_category("PAYROLL DIRECT DEPOSIT")
        assert result == "Income"
    
    def test_simulate_llm_category_unknown(self):
        """Test LLM fallback returns Misc for unknown."""
        result = _simulate_llm_category("COMPLETELY UNKNOWN MERCHANT")
        # Result should be one of the valid categories
        assert result in CATEGORIES
    
    def test_simulate_llm_category_empty(self):
        """Test LLM fallback with empty description."""
        result = _simulate_llm_category("")
        assert result == "Misc"


class TestEmbeddingsCategorization:
    """Tests for embeddings-based categorization."""
    
    @patch('financial_tracker.categorizer._get_embeddings_model')
    @patch('financial_tracker.categorizer.compute_embeddings_with_cache')
    def test_embeddings_category_match(self, mock_compute, mock_get_model):
        """Test embeddings categorization with high similarity."""
        # Mock model
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        
        # Mock embeddings
        import numpy as np
        mock_compute.side_effect = [
            np.array([[1.0, 0.0, 0.0]]),  # Description embedding
            np.array([[0.95, 0.1, 0.0]])  # Known merchant embedding (high similarity)
        ]
        
        known_merchants = [
            {"description": "Whole Foods", "category": "Groceries"}
        ]
        
        result = _embeddings_category("Whole Foods Market", known_merchants, threshold=0.6)
        assert result == "Groceries"
    
    @patch('financial_tracker.categorizer._get_embeddings_model')
    def test_embeddings_category_no_model(self, mock_get_model):
        """Test embeddings categorization when model unavailable."""
        mock_get_model.return_value = None
        
        known_merchants = [{"description": "Test", "category": "Shopping"}]
        result = _embeddings_category("Test Store", known_merchants)
        assert result is None
    
    @patch('financial_tracker.categorizer._get_embeddings_model')
    @patch('financial_tracker.categorizer.compute_embeddings_with_cache')
    def test_embeddings_category_below_threshold(self, mock_compute, mock_get_model):
        """Test embeddings categorization with low similarity."""
        mock_model = Mock()
        mock_get_model.return_value = mock_model
        
        import numpy as np
        mock_compute.side_effect = [
            np.array([[1.0, 0.0, 0.0]]),  # Description embedding
            np.array([[0.0, 1.0, 0.0]])   # Known merchant embedding (low similarity)
        ]
        
        known_merchants = [
            {"description": "Completely Different Store", "category": "Shopping"}
        ]
        
        result = _embeddings_category("My Store", known_merchants, threshold=0.6)
        assert result is None


class TestCategorizeTransactions:
    """Tests for full transaction categorization pipeline."""
    
    def test_categorize_empty_dataframe(self):
        """Test categorizing empty DataFrame."""
        df = pd.DataFrame(columns=["Description"])
        result = categorize_transactions(df, use_embeddings=False)
        assert "Category" in result.columns
        assert len(result) == 0
    
    @patch('financial_tracker.categorizer.get_keyword_rules')
    @patch('financial_tracker.categorizer.get_category_overrides')
    def test_categorize_with_overrides(self, mock_overrides, mock_rules):
        """Test that category overrides take precedence."""
        mock_rules.return_value = []
        mock_overrides.return_value = {"STORE A": "Shopping"}
        
        df = pd.DataFrame({
            "Description": ["STORE A", "STORE B"]
        })
        
        result = categorize_transactions(df, use_embeddings=False)
        assert result.loc[0, "Category"] == "Shopping"
        assert result.loc[1, "Category"] in CATEGORIES  # Fallback
    
    @patch('financial_tracker.categorizer.get_keyword_rules')
    @patch('financial_tracker.categorizer.get_category_overrides')
    def test_categorize_with_keywords(self, mock_overrides, mock_rules):
        """Test categorization with keyword rules."""
        mock_overrides.return_value = {}
        mock_rules.return_value = [
            {"category": "Groceries", "keywords": ["whole foods", "grocery"]}
        ]
        
        df = pd.DataFrame({
            "Description": ["WHOLE FOODS MARKET", "RANDOM STORE"]
        })
        
        result = categorize_transactions(df, use_embeddings=False)
        assert result.loc[0, "Category"] == "Groceries"
        assert result.loc[1, "Category"] in CATEGORIES
    
    @patch('financial_tracker.categorizer.get_keyword_rules')
    @patch('financial_tracker.categorizer.get_category_overrides')
    @patch('financial_tracker.categorizer._get_embeddings_model')
    def test_categorize_with_embeddings_disabled(self, mock_model, mock_overrides, mock_rules):
        """Test that embeddings can be disabled."""
        mock_overrides.return_value = {}
        mock_rules.return_value = []
        
        df = pd.DataFrame({
            "Description": ["TEST STORE"]
        })
        
        result = categorize_transactions(df, use_embeddings=False)
        assert "Category" in result.columns
        # Model should not be called
        mock_model.assert_not_called()


class TestRuleManagement:
    """Tests for keyword rule management."""
    
    @patch('financial_tracker.categorizer.load_keyword_rules')
    def test_get_keyword_rules(self, mock_load):
        """Test loading keyword rules."""
        mock_load.return_value = [
            {"category": "Groceries", "keywords": ["grocery"]}
        ]
        
        rules = get_keyword_rules()
        assert len(rules) == 1
        assert rules[0]["category"] == "Groceries"
    
    @patch('financial_tracker.categorizer.load_keyword_rules')
    def test_get_keyword_rules_defaults(self, mock_load):
        """Test that defaults are returned when no saved rules."""
        mock_load.return_value = []
        
        rules = get_keyword_rules()
        assert len(rules) > 0  # Should return defaults
    
    @patch('financial_tracker.categorizer.save_keyword_rules')
    def test_save_rules(self, mock_save):
        """Test saving keyword rules."""
        rules = [{"category": "Shopping", "keywords": ["amazon", "target"]}]
        save_rules(rules)
        mock_save.assert_called_once_with(rules)
