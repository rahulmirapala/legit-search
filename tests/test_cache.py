"""Unit tests for cache functionality."""
import pytest
import time
from app.cache import TTLCache, make_cache_key

@pytest.mark.unit
def test_cache_set_get():
    """Test basic cache set and get."""
    cache = TTLCache(ttl_seconds=60)
    cache.set("key1", "value1")
    
    assert cache.get("key1") == "value1"

@pytest.mark.unit
def test_cache_expiration():
    """Test cache TTL expiration."""
    cache = TTLCache(ttl_seconds=1)
    cache.set("key1", "value1")
    
    # Should exist immediately
    assert cache.get("key1") == "value1"
    
    # Wait for expiration
    time.sleep(1.1)
    assert cache.get("key1") is None

@pytest.mark.unit
def test_cache_max_size():
    """Test cache eviction when max size reached."""
    cache = TTLCache(ttl_seconds=60, max_size=3)
    
    cache.set("key1", "value1")
    cache.set("key2", "value2")
    cache.set("key3", "value3")
    
    # All should exist
    assert cache.get("key1") is not None
    assert cache.get("key2") is not None
    assert cache.get("key3") is not None
    
    # Add one more - should evict oldest
    cache.set("key4", "value4")
    assert cache.get("key4") is not None
    # One of the older ones should be evicted
    assert len(cache.store) == 3

@pytest.mark.unit
def test_make_cache_key():
    """Test cache key generation."""
    key1 = make_cache_key("query", 3.0, 1, 10, True, False, True, "bm25", 0.3, False)
    key2 = make_cache_key("query", 3.0, 1, 10, True, False, True, "bm25", 0.3, False)
    key3 = make_cache_key("query", 3.0, 2, 10, True, False, True, "bm25", 0.3, False)
    
    # Same parameters should give same key
    assert key1 == key2
    
    # Different parameters should give different key
    assert key1 != key3
