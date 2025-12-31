"""
Unit tests for config.py - Configuration management.
"""
import pytest
from pathlib import Path
import tempfile
import yaml

from financial_tracker import config


@pytest.fixture(autouse=True)
def reset_config():
    """Reset config between tests."""
    config._config = None
    yield
    config._config = None


class TestConfigLoading:
    """Tests for configuration loading."""
    
    def test_get_config_returns_dict(self):
        """Test that get_config returns a dictionary."""
        result = config.get_config()
        assert isinstance(result, dict)
    
    def test_get_config_has_default_sections(self):
        """Test that default config has expected sections."""
        result = config.get_config()
        assert "ollama" in result
        assert "categories" in result
        assert "ui" in result
        assert "database" in result
    
    def test_get_config_caches_result(self):
        """Test that config is cached after first call."""
        result1 = config.get_config()
        result2 = config.get_config()
        assert result1 is result2


class TestConfigGet:
    """Tests for the get() function."""
    
    def test_get_existing_path(self):
        """Test getting an existing config path."""
        result = config.get("ollama.base_url")
        assert result == "http://localhost:11434"
    
    def test_get_nested_path(self):
        """Test getting deeply nested config value."""
        result = config.get("ollama.model")
        assert result is not None
    
    def test_get_nonexistent_path_returns_default(self):
        """Test that nonexistent path returns default."""
        result = config.get("nonexistent.path", "default_value")
        assert result == "default_value"
    
    def test_get_partial_path_returns_default(self):
        """Test that partial path returns default."""
        result = config.get("ollama.nonexistent", "default")
        assert result == "default"


class TestConvenienceAccessors:
    """Tests for convenience accessor functions."""
    
    def test_get_ollama_url(self):
        """Test get_ollama_url returns URL."""
        result = config.get_ollama_url()
        assert "http" in result
    
    def test_get_ollama_model(self):
        """Test get_ollama_model returns model name."""
        result = config.get_ollama_model()
        assert isinstance(result, str)
        assert len(result) > 0
    
    def test_get_ollama_timeout(self):
        """Test get_ollama_timeout returns int."""
        result = config.get_ollama_timeout()
        assert isinstance(result, int)
        assert result > 0
    
    def test_get_similarity_threshold(self):
        """Test get_similarity_threshold returns float."""
        result = config.get_similarity_threshold()
        assert isinstance(result, float)
        assert 0 <= result <= 1
    
    def test_get_categories(self):
        """Test get_categories returns list."""
        result = config.get_categories()
        assert isinstance(result, list)
        assert len(result) > 0
        assert "Groceries" in result
    
    def test_get_rows_per_page(self):
        """Test get_rows_per_page returns int."""
        result = config.get_rows_per_page()
        assert isinstance(result, int)
        assert result > 0
    
    def test_get_max_file_size_mb(self):
        """Test get_max_file_size_mb returns int."""
        result = config.get_max_file_size_mb()
        assert isinstance(result, int)
        assert result > 0
    
    def test_get_log_level(self):
        """Test get_log_level returns valid level."""
        result = config.get_log_level()
        assert result in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]
    
    def test_get_log_file(self):
        """Test get_log_file returns path string."""
        result = config.get_log_file()
        assert isinstance(result, str)


class TestReloadConfig:
    """Tests for reload_config function."""
    
    def test_reload_config_clears_cache(self):
        """Test that reload_config clears the cached config."""
        config1 = config.get_config()
        config.reload_config()
        # After reload, _config should be repopulated
        assert config._config is not None


class TestMergeConfigs:
    """Tests for _merge_configs function."""
    
    def test_merge_simple_values(self):
        """Test merging simple values."""
        default = {"a": 1, "b": 2}
        user = {"a": 10}
        result = config._merge_configs(default, user)
        assert result == {"a": 10, "b": 2}
    
    def test_merge_nested_dicts(self):
        """Test merging nested dictionaries."""
        default = {"outer": {"a": 1, "b": 2}}
        user = {"outer": {"a": 10}}
        result = config._merge_configs(default, user)
        assert result == {"outer": {"a": 10, "b": 2}}
    
    def test_merge_add_new_keys(self):
        """Test that new keys are added."""
        default = {"a": 1}
        user = {"b": 2}
        result = config._merge_configs(default, user)
        assert result == {"a": 1, "b": 2}

