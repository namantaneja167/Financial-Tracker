import json
import os
from pathlib import Path
from typing import Any, Dict, List


_BASE_DIR = Path(__file__).parent.parent / "data"


def _ensure_data_dir() -> None:
    """Create data/ folder if it doesn't exist."""
    _BASE_DIR.mkdir(parents=True, exist_ok=True)


def load_keyword_rules() -> List[Dict[str, Any]]:
    """Load keyword→category rules from data/keyword_rules.json."""
    _ensure_data_dir()
    rules_file = _BASE_DIR / "keyword_rules.json"
    if not rules_file.exists():
        return []
    try:
        with open(rules_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return []


def save_keyword_rules(rules: List[Dict[str, Any]]) -> None:
    """Save keyword→category rules to data/keyword_rules.json."""
    _ensure_data_dir()
    rules_file = _BASE_DIR / "keyword_rules.json"
    with open(rules_file, "w", encoding="utf-8") as f:
        json.dump(rules, f, indent=2, ensure_ascii=False)


def load_category_overrides() -> Dict[str, str]:
    """Load per-description category overrides from data/category_overrides.json."""
    _ensure_data_dir()
    overrides_file = _BASE_DIR / "category_overrides.json"
    if not overrides_file.exists():
        return {}
    try:
        with open(overrides_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return {}


def save_category_overrides(overrides: Dict[str, str]) -> None:
    """Save per-description category overrides to data/category_overrides.json."""
    _ensure_data_dir()
    overrides_file = _BASE_DIR / "category_overrides.json"
    with open(overrides_file, "w", encoding="utf-8") as f:
        json.dump(overrides, f, indent=2, ensure_ascii=False)
