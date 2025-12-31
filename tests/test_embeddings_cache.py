"""Tests for embeddings cache module."""
import pytest
import numpy as np
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
import pickle
import tempfile
import shutil

from financial_tracker.embeddings_cache import (
    EmbeddingsCache,
    get_category_cache,
    get_merchant_cache,
    compute_embeddings_with_cache,
)


class TestEmbeddingsCache:
    """Test embeddings cache functionality."""
    
    @pytest.fixture
    def temp_cache_dir(self):
        """Create temporary cache directory."""
        temp_dir = Path(tempfile.mkdtemp())
        yield temp_dir
        shutil.rmtree(temp_dir)
    
    @pytest.fixture
    def cache(self, temp_cache_dir):
        """Create test cache instance."""
        cache_file = temp_cache_dir / "test_cache.pkl"
        return EmbeddingsCache(cache_file)
    
    def test_cache_initialization(self, temp_cache_dir):
        """Test cache initializes correctly."""
        cache_file = temp_cache_dir / "test_cache.pkl"
        cache = EmbeddingsCache(cache_file)
        assert cache.cache_file == cache_file
        assert isinstance(cache.cache, dict)
        assert len(cache.cache) == 0
    
    def test_set_and_get(self, cache):
        """Test setting and getting embeddings."""
        embedding = np.array([0.1, 0.2, 0.3])
        cache.set("test text", embedding)
        
        result = cache.get("test text")
        assert result is not None
        np.testing.assert_array_equal(result, embedding)
    
    def test_get_nonexistent(self, cache):
        """Test getting non-existent key returns None."""
        result = cache.get("nonexistent")
        assert result is None
    
    def test_hash_key_case_insensitive(self, cache):
        """Test that hash keys are case-insensitive."""
        embedding = np.array([1.0, 2.0])
        cache.set("Test Text", embedding)
        
        result = cache.get("test text")
        assert result is not None
        np.testing.assert_array_equal(result, embedding)
    
    def test_persistence(self, temp_cache_dir):
        """Test cache persists to disk."""
        cache_file = temp_cache_dir / "persist_test.pkl"
        
        # Create cache and add data
        cache1 = EmbeddingsCache(cache_file)
        embedding = np.array([0.5, 0.6])
        cache1.set("persist test", embedding)
        cache1._save()
        
        # Create new cache instance, should load from disk
        cache2 = EmbeddingsCache(cache_file)
        result = cache2.get("persist test")
        assert result is not None
        np.testing.assert_array_equal(result, embedding)
    
    def test_corrupted_cache_file(self, temp_cache_dir):
        """Test handling of corrupted cache file."""
        cache_file = temp_cache_dir / "corrupted.pkl"
        
        # Write corrupted data
        with open(cache_file, 'wb') as f:
            f.write(b"not valid pickle data")
        
        # Should initialize with empty cache
        cache = EmbeddingsCache(cache_file)
        assert len(cache.cache) == 0
    
    def test_get_batch(self, cache):
        """Test batch get operation."""
        emb1 = np.array([1.0, 2.0])
        emb2 = np.array([3.0, 4.0])
        
        cache.set("text1", emb1)
        cache.set("text2", emb2)
        
        results = cache.get_batch(["text1", "text2", "text3"])
        
        assert len(results) == 3
        np.testing.assert_array_equal(results["text1"], emb1)
        np.testing.assert_array_equal(results["text2"], emb2)
        assert results["text3"] is None
    
    def test_set_batch(self, cache):
        """Test batch set operation."""
        texts = ["text1", "text2", "text3"]
        embeddings = [
            np.array([1.0, 2.0]),
            np.array([3.0, 4.0]),
            np.array([5.0, 6.0])
        ]
        
        cache.set_batch(texts, embeddings)
        
        # Verify all were stored
        assert cache.get("text1") is not None
        assert cache.get("text2") is not None
        assert cache.get("text3") is not None
    
    def test_clear(self, cache):
        """Test clearing cache."""
        embedding = np.array([1.0, 2.0])
        cache.set("test", embedding)
        cache._save()
        
        assert cache.size() == 1
        assert cache.cache_file.exists()
        
        cache.clear()
        
        assert cache.size() == 0
        assert not cache.cache_file.exists()
    
    def test_size(self, cache):
        """Test size method."""
        assert cache.size() == 0
        
        cache.set("text1", np.array([1.0]))
        assert cache.size() == 1
        
        cache.set("text2", np.array([2.0]))
        assert cache.size() == 2
    
    def test_save_io_error(self, temp_cache_dir):
        """Test save handles IO errors gracefully."""
        cache_file = temp_cache_dir / "readonly" / "cache.pkl"
        cache = EmbeddingsCache(cache_file)
        
        # Set an embedding
        cache.set("test", np.array([1.0]))
        
        # Try to save (should fail silently due to missing directory)
        cache._save()  # Should not raise exception
        
        # Cache should still work in memory
        assert cache.get("test") is not None


class TestGlobalCaches:
    """Test global cache instances."""
    
    def test_get_category_cache(self):
        """Test getting category cache singleton."""
        cache1 = get_category_cache()
        cache2 = get_category_cache()
        assert cache1 is cache2  # Same instance
        assert isinstance(cache1, EmbeddingsCache)
    
    def test_get_merchant_cache(self):
        """Test getting merchant cache singleton."""
        cache1 = get_merchant_cache()
        cache2 = get_merchant_cache()
        assert cache1 is cache2  # Same instance
        assert isinstance(cache1, EmbeddingsCache)
    
    def test_separate_caches(self):
        """Test category and merchant caches are separate."""
        cat_cache = get_category_cache()
        mer_cache = get_merchant_cache()
        assert cat_cache is not mer_cache


class TestComputeEmbeddingsWithCache:
    """Test compute embeddings with cache."""
    
    @pytest.fixture
    def mock_model(self):
        """Create mock SentenceTransformer model."""
        model = Mock()
        model.encode = Mock(return_value=np.array([
            [1.0, 2.0],
            [3.0, 4.0]
        ]))
        return model
    
    @pytest.fixture
    def temp_cache(self, tmp_path):
        """Create temporary cache."""
        cache_file = tmp_path / "test_cache.pkl"
        return EmbeddingsCache(cache_file)
    
    def test_compute_all_uncached(self, mock_model, temp_cache):
        """Test computing embeddings when none are cached."""
        texts = ["groceries", "transport"]
        
        result = compute_embeddings_with_cache(mock_model, texts, temp_cache)
        
        # Model should be called
        mock_model.encode.assert_called_once()
        assert result.shape == (2, 2)
        
        # Results should be cached
        assert temp_cache.get("groceries") is not None
        assert temp_cache.get("transport") is not None
    
    def test_compute_all_cached(self, mock_model, temp_cache):
        """Test computing embeddings when all are cached."""
        # Pre-populate cache
        temp_cache.set("groceries", np.array([1.0, 2.0]))
        temp_cache.set("transport", np.array([3.0, 4.0]))
        
        texts = ["groceries", "transport"]
        result = compute_embeddings_with_cache(mock_model, texts, temp_cache)
        
        # Model should not be called
        mock_model.encode.assert_not_called()
        assert result.shape == (2, 2)
    
    def test_compute_partial_cached(self, mock_model, temp_cache):
        """Test computing with some cached and some new."""
        # Pre-cache one text
        temp_cache.set("groceries", np.array([1.0, 2.0]))
        
        # Mock model to return embedding for new text
        mock_model.encode.return_value = np.array([[3.0, 4.0]])
        
        texts = ["groceries", "transport"]
        result = compute_embeddings_with_cache(mock_model, texts, temp_cache)
        
        # Model should be called only for uncached text
        mock_model.encode.assert_called_once()
        called_texts = mock_model.encode.call_args[0][0]
        assert "transport" in called_texts
        assert "groceries" not in called_texts
        
        assert result.shape == (2, 2)
    
    def test_compute_empty_list(self, mock_model, temp_cache):
        """Test computing with empty text list."""
        result = compute_embeddings_with_cache(mock_model, [], temp_cache)
        
        assert result.shape == (0,)
        mock_model.encode.assert_not_called()
    
    def test_compute_maintains_order(self, mock_model, temp_cache):
        """Test that result order matches input order."""
        # Pre-cache some texts
        temp_cache.set("B", np.array([2.0, 2.0]))
        temp_cache.set("D", np.array([4.0, 4.0]))
        
        # Mock model for new texts
        mock_model.encode.return_value = np.array([
            [1.0, 1.0],  # A
            [3.0, 3.0]   # C
        ])
        
        texts = ["A", "B", "C", "D"]
        result = compute_embeddings_with_cache(mock_model, texts, temp_cache)
        
        # Check order is preserved
        assert result.shape == (4, 2)
        np.testing.assert_array_equal(result[1], np.array([2.0, 2.0]))  # B
        np.testing.assert_array_equal(result[3], np.array([4.0, 4.0]))  # D
