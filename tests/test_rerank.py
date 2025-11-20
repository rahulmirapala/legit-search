"""Unit tests for reranking utilities."""
import pytest
from app.rerank import rerank, is_available

@pytest.mark.unit
def test_rerank_empty_list():
    """Test reranking with empty list."""
    result = rerank("test query", [])
    assert result == []

@pytest.mark.unit
def test_rerank_preserves_hits():
    """Test that reranking preserves all hits."""
    hits = [
        {'case_name': 'Case 1', 'highlights': ['text 1']},
        {'case_name': 'Case 2', 'highlights': ['text 2']},
    ]
    
    result = rerank("test", hits)
    assert len(result) == len(hits)

@pytest.mark.unit
def test_is_available():
    """Test availability check."""
    result = is_available()
    assert isinstance(result, bool)
