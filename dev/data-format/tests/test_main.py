import pytest
from pathlib import Path
import json
import logging
from unittest.mock import Mock, patch, ANY
from datetime import datetime
import requests

from main import (
    DataFetcher,
    FetchError,
    RateLimitExceeded,
    ValidationError,
    DataFormat
)

# Configure logging for tests
logging.basicConfig(level=logging.DEBUG)

@pytest.fixture
def test_config(tmp_path):
    """Create a test configuration"""
    config = {
        "version": "1.0",
        "sources": [{
            "id": "test_source",
            "url": "https://api.example.com/data",
            "last_fetched": "2024-03-21T10:00:00Z",
            "fetch_frequency": "daily",
            "data_format": "json",
            "storage_path": str(tmp_path / "data"),
            "headers": {"User-Agent": "TestBot/1.0"},
            "enabled": True,
            "rate_limit": {
                "per_seconds": 60,
                "max_requests": 1
            }
        }]
    }

    config_path = tmp_path / "test_config.json"
    with open(config_path, 'w') as f:
        json.dump(config, f)
    return config_path

@pytest.fixture
def mock_response():
    """Create a mock response object"""
    response = Mock(spec=requests.Response)
    response.status_code = 200
    response.content = b'{"test": "data"}'
    return response

@pytest.fixture
def fetcher(test_config):
    """Create a DataFetcher instance with test config"""
    return DataFetcher(str(test_config))

@pytest.fixture
def mock_time():
    """Mock time.time() to control rate limiting"""
    with patch('time.time') as mock:
        mock.return_value = 0
        yield mock

class TestDataFetcher:
    """Test suite for DataFetcher class"""

    def test_initialization(self, test_config):
        """Test successful initialization"""
        fetcher = DataFetcher(str(test_config))
        assert fetcher.config['version'] == "1.0"
        assert len(fetcher.config['sources']) == 1

    def test_initialization_invalid_config(self, tmp_path):
        """Test initialization with invalid config"""
        invalid_config = tmp_path / "invalid.json"
        invalid_config.write_text("invalid json")

        with pytest.raises(ValueError, match="Invalid JSON in config file"):
            DataFetcher(str(invalid_config))

    @patch('requests.get')
    def test_successful_fetch(self, mock_get, fetcher, mock_response):
        """Test successful data fetch"""
        mock_get.return_value = mock_response

        result = fetcher.fetch_source("test_source")
        assert result is True

        # Verify the request was made with correct parameters
        mock_get.assert_called_once_with(
            "https://api.example.com/data",
            headers={"User-Agent": "TestBot/1.0"},
            timeout=ANY
        )

    @patch('requests.get')
    def test_rate_limit(self, mock_get, fetcher, mock_response):
        """Test rate limiting functionality"""
        mock_get.return_value = mock_response
        source = next(s for s in fetcher.config['sources'])

        # First request should succeed
        assert fetcher.fetch_source("test_source") is True

        # Second request within rate limit window should fail
        with pytest.raises(RateLimitExceeded):
            fetcher.fetch_source("test_source")

    @patch('requests.get')
    def test_invalid_json_response(self, mock_get, fetcher, mock_time):
        """Test handling of invalid JSON response"""
        # Setup mock response
        response = Mock(spec=requests.Response)
        response.status_code = 200
        response.content = b'invalid json'
        response.url = "https://api.example.com/data"
        mock_get.return_value = response

        # Configure source without rate limit
        source = next(s for s in fetcher.config['sources'])
        source['data_format'] = "json"
        source.pop('rate_limit', None)  # Remove rate limit

        # Should return False on validation error
        with pytest.raises(ValidationError):
            fetcher.fetch_source("test_source")

    @patch('requests.get')
    def test_network_error(self, mock_get, fetcher):
        """Test handling of network errors"""
        mock_get.side_effect = requests.exceptions.RequestException("Network error")

        result = fetcher.fetch_source("test_source")
        assert result is False

    @patch('backoff._sync.datetime')
    @patch('datetime.datetime')
    @patch('requests.get')
    def test_last_fetched_update(self, mock_get, mock_datetime, mock_backoff_datetime, fetcher, mock_response):
        """Test that last_fetched is updated after successful fetch"""
        # Create a real datetime for comparison
        fixed_dt = datetime(2024, 3, 21, 10, 0, 0)

        # Create a mock timedelta for backoff
        mock_timedelta = Mock()
        mock_timedelta.total_seconds.return_value = 0

        # Set up datetime mocks
        mock_datetime.now.return_value = fixed_dt
        mock_datetime.utcnow.return_value = fixed_dt
        mock_backoff_datetime.now.return_value = fixed_dt
        mock_backoff_datetime.timedelta = mock_timedelta

        # Mock subtraction operation
        def mock_sub(self, other):
            return mock_timedelta
        mock_backoff_datetime.now.return_value.__sub__ = mock_sub

        # Set up response
        mock_get.return_value = mock_response

        # Remove rate limit from source
        source = next(s for s in fetcher.config['sources'])
        source.pop('rate_limit', None)

        # Perform the fetch
        fetcher.fetch_source("test_source")

        # Verify the timestamp was updated
        assert source['last_fetched'] == fixed_dt.isoformat() + "Z"

    def test_disabled_source(self, fetcher):
        """Test handling of disabled sources"""
        source = next(s for s in fetcher.config['sources'])
        source['enabled'] = False

        result = fetcher.fetch_source("test_source")
        assert result is False

    @patch('requests.get')
    def test_html_validation(self, mock_get, fetcher):
        """Test HTML content validation"""
        response = Mock(spec=requests.Response)
        response.status_code = 200
        response.content = b'<html><body>Valid HTML</body></html>'
        mock_get.return_value = response

        source = next(s for s in fetcher.config['sources'])
        source['data_format'] = DataFormat.HTML

        result = fetcher.fetch_source("test_source")
        assert result is True

    def test_nonexistent_source(self, fetcher):
        """Test fetching nonexistent source"""
        try:
            fetcher.fetch_source("nonexistent")
            pytest.fail("Expected ValueError was not raised")
        except ValueError as e:
            assert "Source nonexistent not found" in str(e)

    @patch('requests.get')
    def test_storage_path_creation(self, mock_get, fetcher, mock_response, tmp_path):
        """Test that storage path is created if it doesn't exist"""
        mock_get.return_value = mock_response

        source = next(s for s in fetcher.config['sources'])
        new_storage_path = tmp_path / "new_storage"
        source['storage_path'] = str(new_storage_path)

        fetcher.fetch_source("test_source")
        assert new_storage_path.exists()

    @patch('requests.get')
    def test_response_save_format(self, mock_get, fetcher, mock_response):
        """Test that responses are saved with correct format"""
        mock_get.return_value = mock_response

        fetcher.fetch_source("test_source")

        storage_path = Path(fetcher.config['sources'][0]['storage_path'])
        saved_files = list(storage_path.glob("*.json"))
        assert len(saved_files) == 1
        assert saved_files[0].suffix == ".json"

    def _configure_source_without_rate_limit(self, fetcher, source_id: str):
        """Helper to remove rate limit from a source"""
        source = next((s for s in fetcher.config['sources'] if s['id'] == source_id), None)
        if source:
            source.pop('rate_limit', None)
        return source
