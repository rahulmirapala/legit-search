"""Test configuration and fixtures."""
import pytest
from fastapi.testclient import TestClient
from unittest.mock import MagicMock, patch
from app.main import app
from app.config import Settings

@pytest.fixture
def client():
    """Test client for the FastAPI app."""
    return TestClient(app)

@pytest.fixture
def mock_elasticsearch():
    """Mock Elasticsearch client."""
    mock_es = MagicMock()
    mock_es.ping.return_value = True
    mock_es.indices.exists.return_value = True
    return mock_es

@pytest.fixture
def mock_settings():
    """Mock settings for testing."""
    return Settings(
        es_host="http://localhost:9200",
        index_name="test_legal_judgments"
    )

@pytest.fixture
def sample_query():
    """Sample search query."""
    return "fundamental rights"

@pytest.fixture
def sample_hit():
    """Sample Elasticsearch hit."""
    return {
        '_id': 'test-1',
        '_score': 1.5,
        '_source': {
            'case_name': 'Test Case v. State',
            'year': 2020,
            'judgment_date': '2020-01-15',
            'citation_id': 'TEST-123',
            'full_text': 'This is a test judgment about fundamental rights.',
            'court': 'Supreme Court'
        },
        'highlight': {
            'full_text': ['test judgment about <em>fundamental rights</em>']
        }
    }
