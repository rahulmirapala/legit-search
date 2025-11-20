"""Unit tests for semantic embedding utilities."""
import pytest
from app.semantic import embed_texts, embed_query, is_available

@pytest.mark.unit
def test_embed_texts_returns_list():
    """Test that embed_texts returns a list."""
    result = embed_texts(["test text"])
    assert isinstance(result, list)

@pytest.mark.unit
def test_embed_query_returns_list_or_none():
    """Test that embed_query returns list or None."""
    result = embed_query("test query")
    assert result is None or isinstance(result, list)

@pytest.mark.unit
def test_is_available():
    """Test availability check."""
    result = is_available()
    assert isinstance(result, bool)
