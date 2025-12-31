"""
Merchant name normalization to clean up transaction descriptions.
Maps variations like "UBER *TRIP ABC123" → "Uber" for better grouping.
"""
import re
import json
from pathlib import Path
from typing import Dict, Optional


# Built-in normalization patterns (regex → normalized name)
BUILT_IN_PATTERNS = [
    (re.compile(r'UBER\s*\*.*', re.IGNORECASE), 'Uber'),
    (re.compile(r'UBER\s+EATS.*', re.IGNORECASE), 'Uber Eats'),
    (re.compile(r'LYFT\s*\*.*', re.IGNORECASE), 'Lyft'),
    (re.compile(r'AMZN\s+MKTP.*', re.IGNORECASE), 'Amazon'),
    (re.compile(r'AMAZON\.COM.*', re.IGNORECASE), 'Amazon'),
    (re.compile(r'AMZ\s*\*.*', re.IGNORECASE), 'Amazon'),
    (re.compile(r'DOORDASH\s*\*.*', re.IGNORECASE), 'DoorDash'),
    (re.compile(r'GRUBHUB\s*\*.*', re.IGNORECASE), 'Grubhub'),
    (re.compile(r'NETFLIX\.COM', re.IGNORECASE), 'Netflix'),
    (re.compile(r'SPOTIFY\s+USA', re.IGNORECASE), 'Spotify'),
    (re.compile(r'SPOTIFY.*', re.IGNORECASE), 'Spotify'),
    (re.compile(r'APPLE\.COM/BILL', re.IGNORECASE), 'Apple'),
    (re.compile(r'PAYPAL\s*\*.*', re.IGNORECASE), 'PayPal'),
    (re.compile(r'SQ\s*\*.*', re.IGNORECASE), 'Square'),
    (re.compile(r'TST\s*\*.*', re.IGNORECASE), 'Toast'),
    (re.compile(r'GOOGLE\s*\*.*', re.IGNORECASE), 'Google'),
    (re.compile(r'WHOLEFDS.*', re.IGNORECASE), 'Whole Foods'),
    (re.compile(r'WM\s+SUPERCENTER.*', re.IGNORECASE), 'Walmart'),
    (re.compile(r'TARGET\s+T?-?\d+.*', re.IGNORECASE), 'Target'),
    (re.compile(r'TARGET\s+\d+.*', re.IGNORECASE), 'Target'),
    (re.compile(r'COSTCO\s+WHSE.*', re.IGNORECASE), 'Costco'),
    (re.compile(r'STARBUCKS.*', re.IGNORECASE), 'Starbucks'),
    (re.compile(r'DUNKIN\s*#\d+.*', re.IGNORECASE), 'Dunkin'),
    (re.compile(r'MCDONALDS.*', re.IGNORECASE), 'McDonalds'),
    (re.compile(r'CHEVRON\s+\d+.*', re.IGNORECASE), 'Chevron'),
    (re.compile(r'SHELL\s+OIL.*', re.IGNORECASE), 'Shell'),
    (re.compile(r'VANGUARD.*', re.IGNORECASE), 'Vanguard'),
    (re.compile(r'FIDELITY.*', re.IGNORECASE), 'Fidelity'),
]

CUSTOM_MAPPINGS_FILE = Path(__file__).parent.parent / "data" / "merchant_mappings.json"


def load_custom_mappings() -> Dict[str, str]:
    """Load custom merchant mappings from JSON."""
    if not CUSTOM_MAPPINGS_FILE.exists():
        return {}
    
    try:
        with open(CUSTOM_MAPPINGS_FILE, 'r') as f:
            return json.load(f)
    except (json.JSONDecodeError, IOError, OSError):
        return {}


def save_custom_mappings(mappings: Dict[str, str]) -> None:
    """Save custom merchant mappings to JSON."""
    CUSTOM_MAPPINGS_FILE.parent.mkdir(parents=True, exist_ok=True)
    with open(CUSTOM_MAPPINGS_FILE, 'w') as f:
        json.dump(mappings, f, indent=2)


def normalize_merchant(description: Optional[str]) -> str:
    """
    Normalize merchant name from transaction description.
    
    Priority:
    1. Custom mappings (exact match)
    2. Built-in regex patterns
    3. Return cleaned original
    
    Args:
        description: Raw transaction description (can be None)
        
    Returns:
        Normalized merchant name
    """
    if not description:
        return ""
    
    # Check custom mappings first (exact match on original)
    custom_mappings = load_custom_mappings()
    if description in custom_mappings:
        return custom_mappings[description]
    
    # Check built-in patterns
    for pattern, normalized_name in BUILT_IN_PATTERNS:
        if pattern.match(description):
            return normalized_name
    
    # Return cleaned version: remove common suffixes and extra whitespace
    cleaned = description.strip()
    
    # Remove common transaction codes at end
    cleaned = re.sub(r'\s+[A-Z0-9]{6,}$', '', cleaned)  # Remove long alphanumeric codes
    cleaned = re.sub(r'\s+#\d+$', '', cleaned)  # Remove store numbers like #1234
    cleaned = re.sub(r'\s+\d{10,}$', '', cleaned)  # Remove long numeric codes
    
    # Title case for better readability
    cleaned = cleaned.title()
    
    return cleaned


def add_custom_mapping(original: str, normalized: str) -> None:
    """Add a custom merchant mapping."""
    mappings = load_custom_mappings()
    mappings[original] = normalized
    save_custom_mappings(mappings)


def get_all_custom_mappings() -> Dict[str, str]:
    """Get all custom merchant mappings."""
    return load_custom_mappings()


def remove_custom_mapping(original: str) -> None:
    """Remove a custom merchant mapping."""
    mappings = load_custom_mappings()
    if original in mappings:
        del mappings[original]
        save_custom_mappings(mappings)
