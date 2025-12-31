"""
Unit tests for storage.py - JSON file storage operations.
"""
import json
import pytest
from pathlib import Path
import tempfile

from financial_tracker import storage


@pytest.fixture
def temp_storage_dir(monkeypatch, tmp_path):
    """Set up temporary storage directory."""
    data_dir = tmp_path / "data"
    monkeypatch.setattr(storage, "_BASE_DIR", data_dir)
    return data_dir


class TestKeywordRules:
    """Tests for keyword rules storage."""
    
    def test_load_keyword_rules_empty(self, temp_storage_dir):
        """Test loading rules when file doesn't exist."""
        result = storage.load_keyword_rules()
        assert result == []
    
    def test_save_and_load_keyword_rules(self, temp_storage_dir):
        """Test saving and loading keyword rules."""
        rules = [
            {"category": "Groceries", "keywords": ["grocery", "food"]},
            {"category": "Dining", "keywords": ["restaurant", "cafe"]}
        ]
        
        storage.save_keyword_rules(rules)
        loaded = storage.load_keyword_rules()
        
        assert loaded == rules
    
    def test_load_keyword_rules_corrupted_file(self, temp_storage_dir):
        """Test loading rules from corrupted JSON file."""
        temp_storage_dir.mkdir(parents=True, exist_ok=True)
        rules_file = temp_storage_dir / "keyword_rules.json"
        rules_file.write_text("not valid json {{{")
        
        result = storage.load_keyword_rules()
        assert result == []


class TestCategoryOverrides:
    """Tests for category overrides storage."""
    
    def test_load_category_overrides_empty(self, temp_storage_dir):
        """Test loading overrides when file doesn't exist."""
        result = storage.load_category_overrides()
        assert result == {}
    
    def test_save_and_load_category_overrides(self, temp_storage_dir):
        """Test saving and loading category overrides."""
        overrides = {
            "AMAZON PURCHASE": "Shopping",
            "RENT PAYMENT": "Rent"
        }
        
        storage.save_category_overrides(overrides)
        loaded = storage.load_category_overrides()
        
        assert loaded == overrides
    
    def test_load_category_overrides_corrupted_file(self, temp_storage_dir):
        """Test loading overrides from corrupted JSON file."""
        temp_storage_dir.mkdir(parents=True, exist_ok=True)
        overrides_file = temp_storage_dir / "category_overrides.json"
        overrides_file.write_text("invalid json!")
        
        result = storage.load_category_overrides()
        assert result == {}


class TestEnsureDataDir:
    """Tests for _ensure_data_dir function."""
    
    def test_ensure_data_dir_creates_directory(self, temp_storage_dir):
        """Test that _ensure_data_dir creates the directory."""
        assert not temp_storage_dir.exists()
        storage._ensure_data_dir()
        assert temp_storage_dir.exists()
    
    def test_ensure_data_dir_idempotent(self, temp_storage_dir):
        """Test that _ensure_data_dir can be called multiple times."""
        storage._ensure_data_dir()
        storage._ensure_data_dir()
        assert temp_storage_dir.exists()

