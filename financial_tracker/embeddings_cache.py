"""
Embeddings caching system for sentence-transformers to avoid recomputing.

This module provides persistent caching of merchant and category embeddings
to significantly improve performance of similarity-based categorization.
"""

import pickle
import hashlib
from pathlib import Path
from typing import Dict, List, Optional
import numpy as np

CACHE_DIR = Path(__file__).parent.parent / "data" / "embeddings_cache"
CACHE_DIR.mkdir(parents=True, exist_ok=True)

CATEGORY_EMBEDDINGS_FILE = CACHE_DIR / "category_embeddings.pkl"
MERCHANT_EMBEDDINGS_FILE = CACHE_DIR / "merchant_embeddings.pkl"


class EmbeddingsCache:
    """Cache for sentence-transformer embeddings with disk persistence."""
    
    def __init__(self, cache_file: Path):
        """
        Initialize cache with a specific file.
        
        Args:
            cache_file: Path to the pickle cache file
        """
        self.cache_file = cache_file
        self.cache: Dict[str, np.ndarray] = {}
        self._load()
    
    def _load(self):
        """Load cache from disk if it exists."""
        if self.cache_file.exists():
            try:
                with open(self.cache_file, 'rb') as f:
                    self.cache = pickle.load(f)
            except (pickle.PickleError, EOFError, ValueError):
                # Corrupted cache, start fresh
                self.cache = {}
    
    def _save(self):
        """Save cache to disk."""
        try:
            with open(self.cache_file, 'wb') as f:
                pickle.dump(self.cache, f, protocol=pickle.HIGHEST_PROTOCOL)
        except (pickle.PickleError, IOError) as e:
            # Failed to save cache, continue without persistence
            pass
    
    def _hash_key(self, text: str) -> str:
        """Create a stable hash key for text."""
        return hashlib.md5(text.lower().encode('utf-8')).hexdigest()
    
    def get(self, text: str) -> Optional[np.ndarray]:
        """
        Get cached embedding for text.
        
        Args:
            text: The text to look up
            
        Returns:
            Cached embedding array or None if not found
        """
        key = self._hash_key(text)
        return self.cache.get(key)
    
    def set(self, text: str, embedding: np.ndarray):
        """
        Store embedding in cache.
        
        Args:
            text: The text being embedded
            embedding: The embedding array
        """
        key = self._hash_key(text)
        self.cache[key] = embedding
    
    def get_batch(self, texts: List[str]) -> Dict[str, Optional[np.ndarray]]:
        """
        Get cached embeddings for multiple texts.
        
        Args:
            texts: List of texts to look up
            
        Returns:
            Dict mapping text to embedding (or None if not cached)
        """
        return {text: self.get(text) for text in texts}
    
    def set_batch(self, texts: List[str], embeddings: List[np.ndarray]):
        """
        Store multiple embeddings in cache.
        
        Args:
            texts: List of texts being embedded
            embeddings: List of corresponding embedding arrays
        """
        for text, embedding in zip(texts, embeddings):
            self.set(text, embedding)
        self._save()
    
    def clear(self):
        """Clear all cached embeddings."""
        self.cache = {}
        if self.cache_file.exists():
            self.cache_file.unlink()
    
    def size(self) -> int:
        """Get number of cached embeddings."""
        return len(self.cache)


# Global cache instances
_category_cache: Optional[EmbeddingsCache] = None
_merchant_cache: Optional[EmbeddingsCache] = None


def get_category_cache() -> EmbeddingsCache:
    """Get the global category embeddings cache."""
    global _category_cache
    if _category_cache is None:
        _category_cache = EmbeddingsCache(CATEGORY_EMBEDDINGS_FILE)
    return _category_cache


def get_merchant_cache() -> EmbeddingsCache:
    """Get the global merchant embeddings cache."""
    global _merchant_cache
    if _merchant_cache is None:
        _merchant_cache = EmbeddingsCache(MERCHANT_EMBEDDINGS_FILE)
    return _merchant_cache


def compute_embeddings_with_cache(model, texts: List[str], cache: EmbeddingsCache) -> np.ndarray:
    """
    Compute embeddings using cache when possible.
    
    Args:
        model: SentenceTransformer model
        texts: List of texts to embed
        cache: Cache instance to use
        
    Returns:
        Array of embeddings (one per text)
    """
    if not texts:
        return np.array([])
    
    # Check cache for each text
    cached_results = cache.get_batch(texts)
    uncached_texts = [text for text, emb in cached_results.items() if emb is None]
    
    # Compute embeddings for uncached texts
    if uncached_texts:
        new_embeddings = model.encode(uncached_texts, convert_to_numpy=True)
        cache.set_batch(uncached_texts, new_embeddings)
    
    # Build result array in original order
    embeddings = []
    for text in texts:
        if cached_results[text] is not None:
            embeddings.append(cached_results[text])
        else:
            # Just computed, get from cache
            embeddings.append(cache.get(text))
    
    return np.array(embeddings)
