from __future__ import annotations

from typing import Any, Dict, List, Optional
import os
from pathlib import Path

import pandas as pd
import numpy as np

from financial_tracker.storage import (
    load_category_overrides,
    load_keyword_rules,
    save_category_overrides,
    save_keyword_rules,
)
from financial_tracker.embeddings_cache import (
    get_category_cache,
    get_merchant_cache,
    compute_embeddings_with_cache,
)
from financial_tracker.config import get_similarity_threshold, get_categories

# Lazy-load embeddings model to avoid startup delay
_EMBEDDINGS_MODEL = None


def _get_embeddings_model():
    """Lazy-load sentence-transformers model."""
    global _EMBEDDINGS_MODEL
    if _EMBEDDINGS_MODEL is None:
        try:
            from sentence_transformers import SentenceTransformer
            # Use a lightweight model for local inference
            _EMBEDDINGS_MODEL = SentenceTransformer('all-MiniLM-L6-v2')
        except ImportError:
            _EMBEDDINGS_MODEL = None
    return _EMBEDDINGS_MODEL


# Get categories from config (single source of truth)
CATEGORIES: List[str] = get_categories()


_DEFAULT_KEYWORD_RULES: List[Dict[str, Any]] = [
    {"category": "Rent", "keywords": ["rent", "landlord", "property management", "lease"]},
    {
        "category": "Groceries",
        "keywords": [
            "grocery",
            "supermarket",
            "whole foods",
            "trader joe",
            "aldi",
            "lidl",
            "kroger",
            "safeway",
            "publix",
            "walmart grocery",
            "costco",
            "sprouts",
            "farmers market",
        ],
    },
    {
        "category": "Dining",
        "keywords": [
            "starbucks",
            "coffee",
            "cafe",
            "restaurant",
            "diner",
            "bar",
            "grill",
            "pizza",
            "doordash",
            "uber eats",
            "grubhub",
            "chipotle",
            "panera",
            "subway",
            "mcdonald",
            "burger",
            "taco",
            "shake shack",
        ],
    },
    {
        "category": "Transport",
        "keywords": [
            "uber",
            "lyft",
            "taxi",
            "transit",
            "metro",
            "train",
            "bus",
            "parking",
            "toll",
            "gas",
            "fuel",
            "exxon",
            "shell",
            "chevron",
        ],
    },
    {
        "category": "Utilities",
        "keywords": [
            "electric",
            "power",
            "water",
            "sewer",
            "gas utility",
            "internet",
            "wifi",
            "verizon",
            "at&t",
            "t-mobile",
            "comcast",
            "xfinity",
            "spectrum",
            "utility",
        ],
    },
    {
        "category": "Investments",
        "keywords": [
            "brokerage",
            "robinhood",
            "vanguard",
            "fidelity",
            "schwab",
            "etrade",
            "td ameritrade",
            "investment",
        ],
    },
    {
        "category": "Income",
        "keywords": [
            "payroll",
            "salary",
            "paycheck",
            "direct deposit",
            "deposit",
            "bonus",
            "interest",
            "refund",
        ],
    },
    {
        "category": "Shopping",
        "keywords": [
            "amazon",
            "target",
            "best buy",
            "walmart",
            "etsy",
            "shop",
            "store",
            "purchase",
            "order",
        ],
    },
]


def get_keyword_rules() -> List[Dict[str, Any]]:
    """Load keyword rules from storage; fall back to defaults if empty."""
    saved = load_keyword_rules()
    return saved if saved else _DEFAULT_KEYWORD_RULES


def save_rules(rules: List[Dict[str, Any]]) -> None:
    """Persist keyword rules to storage."""
    save_keyword_rules(rules)


def get_category_overrides() -> Dict[str, str]:
    """Load per-description category overrides from storage."""
    return load_category_overrides()


def save_overrides(overrides: Dict[str, str]) -> None:
    """Persist category overrides to storage."""
    save_category_overrides(overrides)


def _keyword_category(description: str, rules: List[Dict[str, Any]]) -> Optional[str]:
    desc = (description or "").lower()
    if not desc.strip():
        return None

    for rule in rules:
        for kw in rule.get("keywords", []):
            if kw in desc:
                return str(rule["category"])
    return None


def _simulate_llm_category(description: str) -> str:
    """Deterministic, local 'LLM-like' classifier fallback."""

    desc = (description or "").lower().strip()
    if not desc:
        return "Misc"

    scores: Dict[str, int] = {c: 0 for c in CATEGORIES}

    evidence: Dict[str, List[str]] = {
        "Rent": ["apartment", "housing", "unit", "lease"],
        "Groceries": ["market", "foods", "produce", "butcher", "bakery"],
        "Dining": ["cuisine", "takeout", "lunch", "dinner", "breakfast"],
        "Transport": ["ride", "trip", "station", "fare", "vehicle"],
        "Utilities": ["bill", "statement", "autopay", "monthly", "service"],
        "Investments": ["broker", "securities", "shares", "fund", "ira", "401k"],
        "Income": ["pay", "employer", "wages", "payout", "income"],
        "Shopping": ["online", "retail", "cart", "shipping", "merch"],
    }

    for category, words in evidence.items():
        for w in words:
            if w in desc:
                scores[category] += 2

    if any(w in desc for w in ["payroll", "salary", "wages", "direct deposit"]):
        scores["Income"] += 3
    if any(w in desc for w in ["dividend", "contribution", "brokerage", "vanguard", "fidelity"]):
        scores["Investments"] += 3

    best = max(scores.items(), key=lambda kv: kv[1])
    if best[1] <= 0:
        return "Misc"
    return best[0]


def _embeddings_category(description: str, known_merchants: List[Dict[str, str]], threshold: float = None) -> Optional[str]:
    """
    Use embeddings similarity to find category from known merchants.
    
    Args:
        description: Transaction description to categorize
        known_merchants: List of dicts with 'description' and 'category' keys
        threshold: Minimum cosine similarity to consider a match (0-1), uses config if None
        
    Returns:
        Category string if similar merchant found, None otherwise
    """
    if threshold is None:
        threshold = get_similarity_threshold()
    
    model = _get_embeddings_model()
    if model is None or not known_merchants:
        return None
    
    try:
        # Get caches
        merchant_cache = get_merchant_cache()
        
        # Encode the new description with caching
        desc_embedding = compute_embeddings_with_cache(model, [description], merchant_cache)[0]
        
        # Encode all known merchants with caching
        known_descriptions = [m['description'] for m in known_merchants]
        known_embeddings = compute_embeddings_with_cache(model, known_descriptions, merchant_cache)
        
        # Calculate cosine similarity
        from sklearn.metrics.pairwise import cosine_similarity
        similarities = cosine_similarity([desc_embedding], known_embeddings)[0]
        
        # Find best match above threshold
        best_idx = np.argmax(similarities)
        best_score = similarities[best_idx]
        
        if best_score >= threshold:
            return known_merchants[best_idx]['category']
        
        return None
    except Exception:
        return None


def categorize_transactions(df: pd.DataFrame, use_embeddings: bool = True) -> pd.DataFrame:
    """Add/overwrite a `Category` column based on Description.
    
    Categorization priority:
    1. Per-description overrides (exact match)
    2. Keyword rules (substring match)
    3. Embeddings similarity (if use_embeddings=True and model available)
    4. Simulated LLM fallback
    
    Args:
        df: DataFrame with Description column
        use_embeddings: Whether to use embeddings-based categorization
    """

    rules = get_keyword_rules()
    overrides = get_category_overrides()
    
    # Build known merchants from database for embeddings
    known_merchants = []
    if use_embeddings:
        try:
            from financial_tracker.database import get_all_transactions
            all_txns = get_all_transactions()
            if not all_txns.empty and 'Category' in all_txns.columns:
                # Get unique merchant-category pairs (exclude Misc and empty categories)
                valid_txns = all_txns[
                    (all_txns['Category'].notna()) & 
                    (all_txns['Category'] != '') & 
                    (all_txns['Category'] != 'Misc')
                ]
                
                for desc, cat in zip(valid_txns['Description'], valid_txns['Category']):
                    if desc and cat and cat in CATEGORIES:
                        known_merchants.append({'description': str(desc), 'category': str(cat)})
        except Exception:
            pass

    categories: List[str] = []

    for _, row in df.iterrows():
        description = row.get("Description", "")
        description_str = "" if description is None else str(description)

        # 1. Check override first (exact match)
        if description_str in overrides:
            category = overrides[description_str]
        else:
            # 2. Try keyword rules
            category = _keyword_category(description_str, rules)
            
            # 3. Try embeddings similarity
            if category is None and use_embeddings and known_merchants:
                category = _embeddings_category(description_str, known_merchants)
            
            # 4. Fall back to simulated LLM
            if category is None:
                category = _simulate_llm_category(description_str)

        if category not in CATEGORIES:
            category = "Misc"
        categories.append(category)

    df["Category"] = categories
    return df
