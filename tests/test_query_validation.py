"""Tests for query validation module."""
import pytest
from app.query_validation import clean_query, LEGAL_STOPWORDS


class TestCleanQuery:
    """Test query cleaning and validation."""
    
    def test_empty_query(self):
        """Test that empty queries are rejected."""
        cleaned, is_valid, error = clean_query("")
        assert not is_valid
        assert error == 'Query cannot be empty'
        assert cleaned == ''
    
    def test_whitespace_only_query(self):
        """Test that whitespace-only queries are rejected."""
        cleaned, is_valid, error = clean_query("   ")
        assert not is_valid
        assert error == 'Query cannot be empty'
    
    def test_single_character_query(self):
        """Test that single character queries are rejected."""
        cleaned, is_valid, error = clean_query("a")
        assert not is_valid
        assert "too short" in error.lower() or "single character" in error.lower()
    
    def test_query_too_short(self):
        """Test minimum query length validation."""
        cleaned, is_valid, error = clean_query("x")
        assert not is_valid
        assert "Single character" in error or "too short" in error.lower()
    
    def test_stopwords_only_query(self):
        """Test that queries with only stopwords are rejected."""
        # Query with only common stopwords
        cleaned, is_valid, error = clean_query("the and or")
        assert not is_valid
        assert "more specific" in error.lower()
    
    def test_valid_simple_query(self):
        """Test a valid simple query."""
        cleaned, is_valid, error = clean_query("contract")
        assert is_valid
        assert error is None
        assert cleaned == "contract"
    
    def test_valid_multi_word_query(self):
        """Test a valid multi-word query."""
        cleaned, is_valid, error = clean_query("breach of contract")
        assert is_valid
        assert error is None
        assert cleaned == "breach of contract"
    
    def test_valid_case_name_query(self):
        """Test a valid case name query."""
        cleaned, is_valid, error = clean_query("Kesavananda Bharati v State of Kerala")
        assert is_valid
        assert error is None
        assert cleaned == "Kesavananda Bharati v State of Kerala"
    
    def test_excessive_whitespace_cleaned(self):
        """Test that excessive whitespace is normalized."""
        cleaned, is_valid, error = clean_query("contract    law   dispute")
        assert is_valid
        assert error is None
        assert cleaned == "contract law dispute"
        assert "    " not in cleaned
    
    def test_leading_trailing_whitespace_removed(self):
        """Test that leading/trailing whitespace is removed."""
        cleaned, is_valid, error = clean_query("  contract law  ")
        assert is_valid
        assert error is None
        assert cleaned == "contract law"
    
    def test_mixed_stopwords_and_meaningful_words(self):
        """Test query with mix of stopwords and meaningful words."""
        cleaned, is_valid, error = clean_query("the quick brown fox")
        assert is_valid
        assert error is None
        # Should be valid because it has meaningful words like "quick", "brown", "fox"
    
    def test_legal_citation_query(self):
        """Test a legal citation query."""
        cleaned, is_valid, error = clean_query("AIR 1973 SC 1461")
        assert is_valid
        assert error is None
    
    def test_numeric_query(self):
        """Test queries with numbers."""
        cleaned, is_valid, error = clean_query("2024")
        assert is_valid
        assert error is None
    
    def test_special_characters_preserved(self):
        """Test that special characters are preserved."""
        cleaned, is_valid, error = clean_query("Section 377 IPC")
        assert is_valid
        assert error is None
        assert "377" in cleaned
    
    def test_case_insensitive_stopword_check(self):
        """Test that stopword checking is case-insensitive."""
        # "THE AND OR" in uppercase should still be rejected
        cleaned, is_valid, error = clean_query("THE AND OR")
        assert not is_valid
        assert "more specific" in error.lower()
    
    def test_two_character_meaningful_word(self):
        """Test that 2-character meaningful words are acceptable."""
        # "AI" is a meaningful term even if short
        cleaned, is_valid, error = clean_query("AI law")
        assert is_valid
        assert error is None


class TestStopwordsList:
    """Test the stopwords list."""
    
    def test_common_legal_stopwords_present(self):
        """Test that common legal stopwords are in the list."""
        assert 'the' in LEGAL_STOPWORDS
        assert 'and' in LEGAL_STOPWORDS
        assert 'or' in LEGAL_STOPWORDS
        assert 'shall' in LEGAL_STOPWORDS
        assert 'said' in LEGAL_STOPWORDS
    
    def test_stopwords_lowercase(self):
        """Test that all stopwords are lowercase."""
        for word in LEGAL_STOPWORDS:
            assert word.islower(), f"Stopword '{word}' is not lowercase"


@pytest.mark.integration
def test_search_with_invalid_queries(client):
    """Test that the search endpoint rejects invalid queries."""
    # Empty query
    response = client.get("/search?q=")
    assert response.status_code == 400
    assert "empty" in response.json()["message"].lower()
    
    # Single character query
    response = client.get("/search?q=a")
    assert response.status_code == 400
    assert "single character" in response.json()["message"].lower()
    
    # Stopwords only query
    response = client.get("/search?q=the+and+or")
    assert response.status_code == 400
    assert "specific" in response.json()["message"].lower()


@pytest.mark.integration  
def test_search_with_valid_query(client, mock_elasticsearch):
    """Test that the search endpoint accepts valid queries."""
    # Mock Elasticsearch response
    mock_elasticsearch.search.return_value = {
        'hits': {
            'total': {'value': 1},
            'hits': [{
                '_id': '1',
                '_score': 1.0,
                '_source': {
                    'case_name': 'Test Case',
                    'year': 2020,
                    'full_text': 'Test content'
                }
            }]
        }
    }
    
    response = client.get("/search?q=contract+law")
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
    assert data["original_query"] == "contract law"
