import requests
import json
import time
from datetime import datetime
from pathlib import Path
from typing import Dict, Any, Optional
import logging
from bs4 import BeautifulSoup
import backoff  # Add to requirements.txt
from pydantic import BaseModel, HttpUrl  # Add to requirements.txt
from enum import Enum

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('datavault.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)

class DataFormat(str, Enum):
    """Supported data formats"""
    JSON = "json"
    HTML = "html"
    XML = "xml"

class RateLimit(BaseModel):
    """Rate limit configuration"""
    per_seconds: int
    max_requests: Optional[int] = None

class Source(BaseModel):
    """Data source configuration"""
    id: str
    url: HttpUrl
    last_fetched: Optional[str]
    fetch_frequency: str
    data_format: DataFormat
    storage_path: str
    headers: Dict[str, str] = {}
    enabled: bool = True
    rate_limit: Optional[RateLimit] = None

class FetchError(Exception):
    """Base exception for fetch operations"""
    pass

class RateLimitExceeded(FetchError):
    """Raised when rate limit is exceeded"""
    pass

class ValidationError(FetchError):
    """Raised when content validation fails"""
    pass

class DataFetcher:
    def __init__(self, config_path: str):
        """Initialize the DataFetcher with a config file path"""
        self.config_path = Path(config_path)
        self.logger = logging.getLogger(f"{__name__}.DataFetcher")
        self._last_request_time: Dict[str, float] = {}

        try:
            self.config = self._load_config()
            self.logger.info(f"Loaded configuration from {config_path}")
        except Exception as e:
            self.logger.error(f"Failed to load configuration: {str(e)}")
            raise

    @backoff.on_exception(
        backoff.expo,
        (requests.exceptions.RequestException, FetchError),
        max_tries=3
    )
    def fetch_source(self, source_id: str) -> bool:
        """Fetch data for a specific source ID with exponential backoff retry"""
        try:
            source = next((s for s in self.config['sources'] if s['id'] == source_id), None)
            if not source:
                self.logger.error(f"Source {source_id} not found")
                raise ValueError(f"Source {source_id} not found")

            if not source.get('enabled', True):
                self.logger.info(f"Source {source_id} is disabled, skipping")
                return False

            if not self._check_rate_limit(source):
                raise RateLimitExceeded(f"Rate limit exceeded for source {source_id}")

            response = self._make_request(source)

            if not self._validate_response(response.content, source['data_format']):
                raise ValidationError(f"Invalid {source['data_format']} response from {source['url']}")

            self._save_response(response, source)
            self._update_last_fetched(source)

            return True

        except ValueError as e:
            raise  # Re-raise ValueError for nonexistent sources
        except FetchError as e:
            self.logger.error(f"Fetch error for {source_id}: {str(e)}")
            raise
        except Exception as e:
            self.logger.error(f"Unexpected error fetching {source_id}: {str(e)}")
            return False

    def _make_request(self, source: Dict[str, Any]) -> requests.Response:
        """Make HTTP request with appropriate method and parameters"""
        method = source.get('method', 'GET').upper()
        request_kwargs = {
            'headers': source.get('headers', {}),
            'timeout': 30
        }

        if method == 'POST' and 'payload' in source:
            request_kwargs['json'] = source['payload']
            response = requests.post(source['url'], **request_kwargs)
        else:
            response = requests.get(source['url'], **request_kwargs)

        response.raise_for_status()
        return response

    def _check_rate_limit(self, source: Dict[str, Any]) -> bool:
        """Check if we're within rate limits"""
        if 'rate_limit' not in source:
            return True

        rate_limit = source['rate_limit']
        source_id = source['id']
        current_time = time.time()

        if source_id not in self._last_request_time:
            self._last_request_time[source_id] = 0

        time_diff = current_time - self._last_request_time[source_id]

        if time_diff < rate_limit.get('per_seconds', 0):
            self.logger.warning(
                f"Rate limit hit for {source_id}. "
                f"Need to wait {rate_limit['per_seconds'] - time_diff:.2f} seconds"
            )
            return False

        self._last_request_time[source_id] = current_time
        return True

    def _validate_response(self, content: bytes, format: str) -> bool:
        """Validate response content based on format"""
        try:
            if format == DataFormat.JSON:
                return self._validate_json_response(content)
            elif format == DataFormat.HTML:
                return self._validate_html_response(content)
            return True
        except Exception as e:
            self.logger.error(f"Validation error for {format}: {str(e)}")
            return False

    def _validate_json_response(self, content: bytes) -> bool:
        """Validate that response content is valid JSON"""
        try:
            json.loads(content)
            return True
        except json.JSONDecodeError as e:
            self.logger.error(f"Invalid JSON: {str(e)}")
            return False

    def _validate_html_response(self, content: bytes) -> bool:
        """Validate that response content is valid HTML"""
        try:
            BeautifulSoup(content, 'html.parser')
            return True
        except Exception as e:
            self.logger.error(f"Invalid HTML: {str(e)}")
            return False

    def _save_response(self, response: requests.Response, source: Dict[str, Any]):
        """Save the response content to storage"""
        try:
            storage_path = Path(source['storage_path'])
            storage_path.mkdir(parents=True, exist_ok=True)

            timestamp = datetime.utcnow().strftime('%Y%m%d_%H%M%S')
            output_path = storage_path / f"{timestamp}.{source['data_format']}"

            with open(output_path, 'wb') as f:
                f.write(response.content)

            self.logger.info(f"Saved response to {output_path}")
        except Exception as e:
            self.logger.error(f"Failed to save response: {str(e)}")
            raise

    def _update_last_fetched(self, source: Dict[str, Any]):
        """Update the last_fetched timestamp for a source"""
        try:
            source['last_fetched'] = datetime.utcnow().isoformat() + 'Z'
            self._save_config()
        except Exception as e:
            self.logger.error(f"Failed to update last_fetched: {str(e)}")
            raise

    def _load_config(self) -> Dict[str, Any]:
        """Load and validate configuration file"""
        try:
            with open(self.config_path, 'r') as f:
                config = json.load(f)

            # Basic validation of required fields
            if 'version' not in config:
                raise ValueError("Config missing 'version' field")
            if 'sources' not in config:
                raise ValueError("Config missing 'sources' field")

            return config
        except json.JSONDecodeError as e:
            raise ValueError(f"Invalid JSON in config file: {str(e)}")
        except Exception as e:
            raise ValueError(f"Failed to load config: {str(e)}")

    def _save_config(self):
        """Save the updated config back to file"""
        try:
            with open(self.config_path, 'w') as f:
                json.dump(self.config, f, indent=2)
            self.logger.debug("Configuration saved successfully")
        except Exception as e:
            self.logger.error(f"Failed to save configuration: {str(e)}")
            raise
