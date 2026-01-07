"""
Configuration management for the Financial Tracker application.

Loads settings from config.yaml with fallback to sensible defaults.
"""

import logging
import os
from pathlib import Path
from typing import Any, Dict, List, Optional
import yaml

logger = logging.getLogger(__name__)

# Default configuration
DEFAULT_CONFIG = {
    "ollama": {
        "base_url": "http://localhost:11434",
        "model": "llama3.2:latest",
        "timeout": 500,
        "api_key": None,
        "max_retries": 3,
    },
    "categorization": {
        "similarity_threshold": 0.6,
        "use_embeddings": True,
        "embedding_model": "all-MiniLM-L6-v2",
    },
    "categories": [
        "Rent",
        "Groceries",
        "Dining",
        "Transport",
        "Utilities",
        "Investments",
        "Income",
        "Shopping",
        "Misc",
    ],
    "recurring": {
        "min_occurrences": 3,
        "similarity_threshold": 0.85,
        "interval_tolerance_days": 5,
    },
    "file_upload": {
        "max_size_mb": 10,
        "allowed_pdf_types": ["application/pdf"],
        "allowed_csv_types": ["text/csv", "text/plain"],
    },
    "database": {
        "path": "data/financial_tracker.db",
        "backup_enabled": False,
        "backup_interval_days": 7,
    },
    "ui": {
        "rows_per_page": 100,
        "theme": "light",
        "default_currency": "USD",
    },
    "logging": {
        "level": "INFO",
        "file": "data/app.log",
        "max_size_mb": 10,
        "backup_count": 3,
    },
}

# Global config instance
_config: Optional[Dict[str, Any]] = None


def _load_config_file() -> Dict[str, Any]:
    """Load configuration from config.yaml if it exists."""
    config_path = Path(__file__).parent.parent / "config.yaml"
    
    if not config_path.exists():
        return {}
    
    try:
        with open(config_path, 'r') as f:
            return yaml.safe_load(f) or {}
    except (yaml.YAMLError, IOError) as e:
        logger.warning(f"Failed to load config.yaml: {e}")
        return {}


def _merge_configs(default: Dict[str, Any], user: Dict[str, Any]) -> Dict[str, Any]:
    """Recursively merge user config into default config."""
    result = default.copy()
    
    for key, value in user.items():
        if key in result and isinstance(result[key], dict) and isinstance(value, dict):
            result[key] = _merge_configs(result[key], value)
        else:
            result[key] = value
    
    return result


def get_config() -> Dict[str, Any]:
    """Get the application configuration."""
    global _config
    
    if _config is None:
        user_config = _load_config_file()
        _config = _merge_configs(DEFAULT_CONFIG, user_config)
    
    return _config


def get(path: str, default: Any = None) -> Any:
    """
    Get a configuration value by dot-separated path.
    
    Example:
        get("ollama.base_url") -> "http://localhost:11434"
        get("ui.rows_per_page") -> 100
    
    Args:
        path: Dot-separated path to config value
        default: Default value if path not found
        
    Returns:
        Configuration value or default
    """
    config = get_config()
    parts = path.split(".")
    
    value = config
    for part in parts:
        if isinstance(value, dict) and part in value:
            value = value[part]
        else:
            return default
    
    return value


def reload_config():
    """Reload configuration from disk."""
    global _config
    _config = None
    get_config()


# Convenience accessors for commonly used settings
def get_ollama_url() -> str:
    """Get Ollama API base URL."""
    return get("ollama.base_url", "http://localhost:11434")


def get_ollama_model() -> str:
    """Get Ollama model name."""
    return get("ollama.model", "gemini-3-flash-preview:cloud")


def get_ollama_timeout() -> int:
    """Get Ollama API timeout in seconds."""
    return get("ollama.timeout", 30)


def get_ollama_api_key() -> Optional[str]:
    """Get Ollama API key from env or config."""
    return os.getenv("OLLAMA_API_KEY") or get("ollama.api_key")


def get_ollama_headers() -> Dict[str, str]:
    """Build request headers for Ollama (e.g., Authorization)."""
    headers: Dict[str, str] = {}
    api_key = get_ollama_api_key()
    if api_key:
        headers["Authorization"] = f"Bearer {api_key}"
    return headers


def get_similarity_threshold() -> float:
    """Get embeddings similarity threshold."""
    return get("categorization.similarity_threshold", 0.6)


def get_categories() -> List[str]:
    """Get list of transaction categories."""
    return get("categories", DEFAULT_CONFIG["categories"])


def get_rows_per_page() -> int:
    """Get number of rows per page for pagination."""
    return get("ui.rows_per_page", 100)


def get_max_file_size_mb() -> int:
    """Get maximum file upload size in MB."""
    return get("file_upload.max_size_mb", 10)


def get_log_level() -> str:
    """Get logging level."""
    return get("logging.level", "INFO")


def get_log_file() -> str:
    """Get log file path."""
    return get("logging.file", "data/app.log")


def get_google_api_key() -> Optional[str]:
    """Get Google API Key from env."""
    return os.getenv("GOOGLE_API_KEY")

def get_gemini_model() -> str:
    """Get Gemini model name."""
    return get("gemini.model", "gemini-3-flash-preview")
