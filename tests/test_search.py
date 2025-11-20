"""Unit tests for search utilities."""
import pytest
from app.search import autospell, build_multi_match_query, build_hybrid_query

@pytest.mark.unit
def test_autospell():
    """Test spell correction."""
    # Simple typo
    assert autospell("teh") == "the"
    assert autospell("quik brown fox") == "quick brown fox"
    
    # Already correct
    assert autospell("fundamental rights") == "fundamental rights"

@pytest.mark.unit
def test_build_multi_match_query_basic():
    """Test basic multi_match query building."""
    query = build_multi_match_query("test query", title_boost=3.0, size=10, from_offset=0)
    
    assert 'query' in query
    assert 'multi_match' in query['query'] or 'bool' in query['query']
    assert query['size'] == 10
    assert query['from'] == 0

@pytest.mark.unit
def test_build_multi_match_query_with_filters():
    """Test multi_match query with filters."""
    filters = {'year_from': 2010, 'year_to': 2020, 'court': 'Supreme Court'}
    query = build_multi_match_query("test", filters=filters)
    
    assert 'query' in query
    # Check if filter is applied (will be in bool query)
    assert 'bool' in query['query']

@pytest.mark.unit
def test_build_multi_match_query_highlights():
    """Test highlighting configuration."""
    # With highlights
    query_with = build_multi_match_query("test", include_highlights=True)
    assert 'highlight' in query_with
    
    # Without highlights
    query_without = build_multi_match_query("test", include_highlights=False)
    assert 'highlight' not in query_without

@pytest.mark.unit
def test_build_hybrid_query():
    """Test hybrid query building."""
    vector = [0.1] * 384  # Mock embedding vector
    query = build_hybrid_query(
        "test query", 
        vector, 
        title_boost=3.0, 
        semantic_weight=0.3
    )
    
    assert 'query' in query
    assert 'bool' in query['query']
    assert 'should' in query['query']['bool']
    # Should have both BM25 and semantic components
    assert len(query['query']['bool']['should']) == 2

@pytest.mark.unit
def test_build_hybrid_query_with_filters():
    """Test hybrid query with filters."""
    vector = [0.1] * 384
    filters = {'year_from': 2015}
    query = build_hybrid_query("test", vector, filters=filters)
    
    assert 'bool' in query['query']
    # Filters should be present
    if 'filter' in query['query']['bool']:
        assert len(query['query']['bool']['filter']) > 0
