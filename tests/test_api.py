"""Integration tests for API endpoints."""
import pytest
from unittest.mock import patch, MagicMock

@pytest.mark.integration
def test_health_endpoint(client):
    """Test health check endpoint."""
    with patch('app.main.get_es_client') as mock_es:
        mock_client = MagicMock()
        mock_client.indices.exists.return_value = True
        mock_es.return_value = mock_client
        
        response = client.get("/health")
        assert response.status_code == 200
        data = response.json()
        assert "elasticsearch" in data
        assert "index_exists" in data

@pytest.mark.integration
def test_root_endpoint(client):
    """Test root endpoint."""
    response = client.get("/")
    assert response.status_code == 200
    data = response.json()
    assert "message" in data

@pytest.mark.integration
def test_search_missing_query(client):
    """Test search endpoint with missing query parameter."""
    response = client.get("/search")
    assert response.status_code == 422  # Validation error

@pytest.mark.integration
def test_search_invalid_page(client):
    """Test search endpoint with invalid page parameter."""
    response = client.get("/search?q=test&page=0")
    assert response.status_code == 422

@pytest.mark.integration
def test_aggregations_endpoint(client):
    """Test aggregations endpoint."""
    with patch('app.main.get_es_client') as mock_es:
        mock_client = MagicMock()
        mock_client.search.return_value = {
            'hits': {'total': {'value': 100}},
            'aggregations': {
                'years': {'buckets': [{'key': 2020, 'doc_count': 10}]},
                'courts': {'buckets': []},
                'year_stats': {'min': 2000, 'max': 2020}
            }
        }
        mock_es.return_value = mock_client
        
        response = client.get("/aggregations")
        assert response.status_code == 200
        data = response.json()
        assert "years" in data
        assert "courts" in data
        assert "year_range" in data
