"""
Unit tests for logging_config.py - Logging setup and configuration.
"""
import logging
import tempfile
from pathlib import Path
import pytest

from financial_tracker import logging_config, config


class TestSetupLogging:
    """Tests for logging setup."""
    
    def test_setup_logging_returns_logger(self, monkeypatch, tmp_path):
        """Test that setup_logging returns a logger."""
        log_file = tmp_path / "test.log"
        monkeypatch.setattr(config, "_config", {
            "logging": {
                "level": "DEBUG",
                "file": str(log_file),
                "max_size_mb": 1,
                "backup_count": 1
            }
        })
        
        logger = logging_config.setup_logging()
        assert isinstance(logger, logging.Logger)
    
    def test_setup_logging_creates_log_directory(self, monkeypatch, tmp_path):
        """Test that setup_logging creates log directory if needed."""
        log_dir = tmp_path / "logs"
        log_file = log_dir / "test.log"
        
        monkeypatch.setattr(config, "_config", {
            "logging": {
                "level": "INFO",
                "file": str(log_file),
                "max_size_mb": 1,
                "backup_count": 1
            }
        })
        
        logging_config.setup_logging()
        assert log_dir.exists()
    
    def test_setup_logging_file_handler_failure(self, monkeypatch, tmp_path):
        """Test that setup_logging handles file handler failure gracefully."""
        # Use an invalid path to force file handler failure
        monkeypatch.setattr(config, "_config", {
            "logging": {
                "level": "INFO",
                "file": "/nonexistent/path/that/should/fail/test.log",
                "max_size_mb": 1,
                "backup_count": 1
            }
        })
        
        # Should not raise an exception
        logger = logging_config.setup_logging()
        assert isinstance(logger, logging.Logger)


class TestGetLogger:
    """Tests for get_logger function."""
    
    def test_get_logger_returns_named_logger(self):
        """Test that get_logger returns a logger with the given name."""
        logger = logging_config.get_logger("test_module")
        assert isinstance(logger, logging.Logger)
        assert logger.name == "test_module"
    
    def test_get_logger_different_names(self):
        """Test that different names return different loggers."""
        logger1 = logging_config.get_logger("module_a")
        logger2 = logging_config.get_logger("module_b")
        assert logger1 is not logger2
        assert logger1.name != logger2.name

