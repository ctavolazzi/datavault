from typing import Optional, Dict, Any, List
from collections import Counter
import logging
from datetime import timedelta
import base64
from io import BytesIO
import hashlib
import aiohttp
import asyncio
from pathlib import Path
import time
import urllib.parse
import json
import gzip
from PIL import Image

from .config import CacheConfig
from .storage import FileSystemStorage
from .exceptions import CacheError
from .cache_manager import CacheManager

logger = logging.getLogger(__name__)

class CacheService:
    """High-level cache service for application use"""

    _instances = {}  # Class-level dictionary to store instances
    _lock = asyncio.Lock()
    _startup_lock = asyncio.Lock()
    _is_initializing = False
    _operation_locks = {}  # Track operations in progress

    @classmethod
    async def get_instance(cls, config: CacheConfig) -> 'CacheService':
        """Get or create a CacheService instance"""
        instance_key = str(config.base_dir)

        async with cls._lock:
            if instance_key in cls._instances:
                logger.debug(f"Reusing existing CacheService instance for {instance_key}")
                return cls._instances[instance_key]

            logger.debug(f"Creating new CacheService instance for {instance_key}")
            instance = cls(config)
            await instance._initialize()
            cls._instances[instance_key] = instance
            return instance

    def __init__(self, config: CacheConfig):
        """Sync initialization"""
        logger.info("🚀 Starting CacheService initialization...")
        self.config = config
        self._initialized = False
        self._shutting_down = False
        self._session = None
        self._initialization_lock = asyncio.Lock()
        self._cache_locks = {}
        self._operation_locks = {}
        self._memory_cache = {}
        self._memory_cache_timestamps = {}  # Track when items were added
        self.concurrent_downloads = 12
        self.memory_cache_size = 100
        self.memory_cache_ttl = 3600  # 1 hour
        self.stats = CacheStats()  # Add statistics tracking

    async def _initialize(self):
        """Async initialization"""
        if self._initialized:
            logger.debug("CacheService already initialized")
            return

        async with self._initialization_lock:
            if self._initialized:
                return

            logger.debug("Starting CacheService initialization")
            self.storage = FileSystemStorage(self.config)
            self.manager = CacheManager(self.config)
            self.stats = Counter()
            self._processing_cache = set()
            self.download_timeout = aiohttp.ClientTimeout(
                total=15,
                connect=5,
                sock_read=10
            )
            self.max_retries = 3
            self.max_image_size = 10 * 1024 * 1024
            self.blocked_domains = set()
            self.concurrent_downloads = 8
            self._initialized = True
            logger.info("CacheService initialization complete")

    @property
    async def session(self):
        """Lazy session initialization with cancellation handling"""
        if self._shutting_down:
            return None

        try:
            async with self._initialization_lock:
                if self._session is None or self._session.closed:
                    self._session = aiohttp.ClientSession(timeout=self.download_timeout)
                return self._session
        except asyncio.CancelledError:
            logger.debug("Session initialization cancelled")
            return None

    async def get_cache_lock(self, url: str) -> asyncio.Lock:
        """Get or create a lock for a specific URL"""
        if url not in self._cache_locks:
            self._cache_locks[url] = asyncio.Lock()
        return self._cache_locks[url]

    async def startup(self):
        """Initialize resources on startup"""
        self.session = aiohttp.ClientSession(timeout=self.download_timeout)

    async def shutdown(self):
        """Cleanup resources on shutdown"""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None

    async def get(self, key: str, cache_type: str = "search") -> Optional[Dict[str, Any]]:
        """Get item with better error handling"""
        try:
            if not self._initialized:
                await self._initialize()

            # Generate cache key hash
            cache_key = hashlib.md5(key.encode()).hexdigest()

            # Try memory cache first
            if cache_key in self._memory_cache:
                logger.info(f"🚀 Memory cache hit for: {key}")
                return self._memory_cache[cache_key]

            # Try file cache
            result = await self.storage.read(cache_key, cache_type)
            if result:
                # Update memory cache
                self._memory_cache[cache_key] = result
                logger.info(f"📦 File cache hit for: {key}")
                return result

            logger.info(f"❌ Cache miss for: {key}")
            return None

        except Exception as e:
            logger.warning(f"Cache read error for {key}: {str(e)}")
            return None

    async def set(self, key: str, data: Dict[str, Any], cache_type: str = "search") -> None:
        """Set item with deduplication"""
        try:
            if not self._initialized:
                await self._initialize()

            # Generate cache key hash
            cache_key = hashlib.md5(key.encode()).hexdigest()

            # Check if already in memory cache
            if cache_key in self._memory_cache:
                return

            # Update both caches
            self._memory_cache[cache_key] = data
            await self.storage.write(cache_key, data, cache_type)
            logger.info(f"💾 Cached data for: {key}")

        except Exception as e:
            logger.error(f"Cache write error for {key}: {str(e)}")

    def _validate_cache_data(self, data: Any, cache_type: str = "search") -> bool:
        """Validate data before caching"""
        # For images, accept strings (base64 data)
        if cache_type == "images":
            return isinstance(data, str)

        # For search results, validate as before
        if not isinstance(data, dict):
            return False

        if cache_type == "search":
            required_fields = ['articles']
            return all(field in data for field in required_fields)

        return True

    def get_stats(self) -> Dict[str, int]:
        """Return current cache statistics"""
        stats = {
            'hits': self.stats['search_hit'] + self.stats['images_hit'],
            'misses': self.stats['search_miss'] + self.stats['images_miss'],
            'errors': self.stats['search_error'] + self.stats['images_error'],
            'writes': self.stats['search_write'] + self.stats['images_write'],
            'by_type': {
                'search': {
                    'hits': self.stats['search_hit'],
                    'misses': self.stats['search_miss'],
                    'errors': self.stats['search_error'],
                    'writes': self.stats['search_write']
                },
                'images': {
                    'hits': self.stats['images_hit'],
                    'misses': self.stats['images_miss'],
                    'errors': self.stats['images_error'],
                    'writes': self.stats['images_write']
                }
            }
        }

        # Add storage stats if available
        storage_stats = self.manager.get_storage_stats()
        if storage_stats:
            stats.update(storage_stats)

        return stats

    def cleanup(self) -> None:
        """Trigger cache cleanup"""
        try:
            self.manager.cleanup(max_age=timedelta(days=self.config.cleanup_days))
            logger.info("Cache cleanup completed successfully")
        except CacheError as e:
            logger.error(f"Cache cleanup failed: {str(e)}")
            raise

    async def cache_image_async(self, image_url: str, silent: bool = False) -> Optional[str]:
        """Cache an image with quick failure for better UX"""
        if self._is_domain_blocked(image_url):
            return image_url

        # Get lock for this specific URL
        lock = await self.get_cache_lock(image_url)
        async with lock:
            # Check if already cached
            cached_data = await self.get(image_url, cache_type="images")
            if cached_data:
                return cached_data

            try:
                # Quick timeout for first attempt
                timeout = aiohttp.ClientTimeout(total=5, connect=2)
                current_session = await self.session

                async with current_session.get(image_url, timeout=timeout) as response:
                    if response.status != 200:
                        return image_url

                    # Quick size check
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_image_size:
                        return image_url

                    image_data = await response.read()
                    if len(image_data) > self.max_image_size:
                        return image_url

                    image_buffer = BytesIO(image_data)
                    image_base64 = base64.b64encode(image_buffer.getvalue()).decode('utf-8')
                    content_type = response.headers.get('content-type', 'image/jpeg')
                    data_uri = f"data:{content_type};base64,{image_base64}"

                    # Cache the result
                    await self.set(image_url, data_uri, cache_type="images")
                    if not silent:
                        logger.info(f"💾 Cached image: {image_url}")
                    return data_uri

            except (asyncio.TimeoutError, Exception):
                return image_url

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL"""
        try:
            return urllib.parse.urlparse(url).netloc.lower()
        except Exception:
            return url

    def _is_domain_blocked(self, url: str) -> bool:
        """Check if domain is blocked"""
        domain = self._get_domain(url)
        return domain in self.blocked_domains

    def _handle_error_response(self, url: str, status: int):
        """Handle error response and block domain if necessary"""
        domain = self._get_domain(url)
        if status in [403, 404, 429]:
            self.blocked_domains.add(domain)
            logger.warning(f"Blocking domain due to {status}: {domain}")

    async def cache_response_async(self, query: str, response: dict):
        """Cache the API response and its images in batches"""
        try:
            # Cache the main response first
            key = hashlib.md5(query.encode()).hexdigest()
            await self.set(key, response)
            logger.info(f"Caching response for: {query}")

            # Process images in larger batches
            if 'articles' in response:
                image_urls = [
                    article['urlToImage']
                    for article in response['articles']
                    if article.get('urlToImage')
                ]

                # Process in larger batches (20 images at a time)
                batch_size = 20
                for i in range(0, len(image_urls), batch_size):
                    batch = image_urls[i:i + batch_size]

                    # Process batch silently (suppress individual logs)
                    results = await asyncio.gather(
                        *[self.cache_image_async(url, silent=True) for url in batch],
                        return_exceptions=True
                    )

                    # Update articles with cached images
                    cached_count = 0
                    for url, result in zip(batch, results):
                        if isinstance(result, str) and result.startswith('data:'):
                            cached_count += 1
                            for article in response['articles']:
                                if article.get('urlToImage') == url:
                                    article['urlToImage'] = result

                    logger.info(f"Cached {cached_count}/{len(batch)} images in batch")

            # Update cached response with all processed images
            await self.set(key, response)
            logger.info(f"Updated cache with all processed images for: {query}")

        except Exception as e:
            logger.error(f"Failed to cache response: {str(e)}")

    async def cleanup(self):
        """Cleanup resources"""
        if self._shutting_down:
            return

        self._shutting_down = True
        logger.info("Starting CacheService cleanup")

        try:
            async with self._initialization_lock:
                if self._session and not self._session.closed:
                    await self._session.close()
                    logger.debug("Closed aiohttp session")
                self._session = None
                self._cache_locks.clear()
                self._operation_locks.clear()

            instance_key = str(self.config.base_dir)
            async with self._lock:
                if instance_key in self._instances:
                    del self._instances[instance_key]
                    logger.debug(f"Removed instance {instance_key}")

        except Exception as e:
            logger.error(f"Error during cleanup: {str(e)}")
        finally:
            self._initialized = False
            logger.info("CacheService cleanup completed")

    def __del__(self):
        """Remove destructor to avoid event loop issues"""
        pass

    async def fetch_image_with_retry(self, url: str, retries: int = 0) -> Optional[bytes]:
        """Fetch image with retry logic"""
        try:
            async with aiohttp.ClientSession(timeout=self.timeout) as session:
                async with session.get(url) as response:
                    if response.status != 200:
                        raise aiohttp.ClientError(f"HTTP {response.status}")

                    # Check content length if available
                    content_length = response.headers.get('content-length')
                    if content_length and int(content_length) > self.max_image_size:
                        logger.warning(f"Image too large ({content_length} bytes): {url}")
                        return None

                    image_data = await response.read()
                    if len(image_data) > self.max_image_size:
                        logger.warning(f"Image too large after download: {url}")
                        return None

                    return image_data

        except asyncio.TimeoutError:
            if retries < self.max_retries:
                logger.warning(f"Timeout fetching image, retry {retries + 1}: {url}")
                await asyncio.sleep(1 * (retries + 1))  # Exponential backoff
                return await self.fetch_image_with_retry(url, retries + 1)
            logger.warning(f"Timeout fetching image after {self.max_retries} retries: {url}")
            return None

        except Exception as e:
            if retries < self.max_retries:
                logger.warning(f"Error fetching image, retry {retries + 1}: {url} - {str(e)}")
                await asyncio.sleep(1 * (retries + 1))
                return await self.fetch_image_with_retry(url, retries + 1)
            logger.warning(f"Failed to fetch image after {self.max_retries} retries: {url} - {str(e)}")
            return None

    async def get_operation_lock(self, operation_key: str) -> asyncio.Lock:
        """Get a lock for a specific operation"""
        if operation_key not in self._operation_locks:
            self._operation_locks[operation_key] = asyncio.Lock()
        return self._operation_locks[operation_key]

    def _manage_memory_cache(self):
        """Clean up memory cache based on size and TTL"""
        current_time = time.time()

        # Remove expired items
        expired_keys = [
            k for k, timestamp in self._memory_cache_timestamps.items()
            if current_time - timestamp > self.memory_cache_ttl
        ]
        for k in expired_keys:
            self._memory_cache.pop(k, None)
            self._memory_cache_timestamps.pop(k, None)

        # If still over size limit, remove oldest items
        while len(self._memory_cache) > self.memory_cache_size:
            oldest_key = min(
                self._memory_cache_timestamps.keys(),
                key=lambda k: self._memory_cache_timestamps[k]
            )
            self._memory_cache.pop(oldest_key, None)
            self._memory_cache_timestamps.pop(oldest_key, None)

    async def get_image_with_placeholder(self, url: str) -> Dict[str, str]:
        """Get both full image and placeholder"""
        try:
            # Check cache first
            cached = await self.get(url, cache_type="images")
            if cached:
                return {
                    "full": cached,
                    "placeholder": cached,
                    "status": "cached"
                }

            # Generate placeholder immediately
            placeholder = await self._generate_placeholder(url)

            # Start full image processing
            full_image = await self.cache_image_async(url, silent=True)

            return {
                "full": full_image if full_image else url,
                "placeholder": placeholder if placeholder else url,
                "status": "generated"
            }
        except Exception as e:
            logger.error(f"Error processing image {url}: {str(e)}")
            return {"full": url, "placeholder": url, "status": "error"}

    async def _generate_placeholder(self, url: str) -> Optional[str]:
        """Generate a low-res placeholder"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(url, timeout=2) as response:
                    if response.status != 200:
                        return None

                    data = await response.read()
                    img = Image.open(BytesIO(data))

                    # Create tiny thumbnail
                    thumb = img.copy()
                    thumb.thumbnail((32, 32))

                    # Convert to low quality JPEG
                    buffer = BytesIO()
                    thumb.save(buffer, format="JPEG", quality=30)

                    # Convert to base64
                    b64_data = base64.b64encode(buffer.getvalue()).decode()
                    return f"data:image/jpeg;base64,{b64_data}"

        except Exception as e:
            logger.debug(f"Failed to generate placeholder for {url}: {str(e)}")
            return None

    async def get_stats(self) -> Dict[str, Any]:
        """Get current cache statistics"""
        stats = self.stats.get_stats()
        stats.update({
            "memory_cache_size": len(self._memory_cache),
            "memory_cache_max": self.memory_cache_size,
            "memory_cache_ttl": self.memory_cache_ttl
        })
        return stats

class DomainBlocker:
    def __init__(self):
        self.blocked = {}  # domain -> (timestamp, failure_count)
        self.threshold = 3
        self.block_duration = 3600  # 1 hour

    def should_block(self, domain: str) -> bool:
        if domain not in self.blocked:
            return False
        timestamp, count = self.blocked[domain]
        if time.time() - timestamp > self.block_duration:
            del self.blocked[domain]
            return False
        return count >= self.threshold

    def record_failure(self, domain: str):
        now = time.time()
        if domain in self.blocked:
            _, count = self.blocked[domain]
            self.blocked[domain] = (now, count + 1)
        else:
            self.blocked[domain] = (now, 1)

class CacheStats:
    """Track cache performance metrics"""

    def __init__(self):
        self.hits = 0
        self.misses = 0
        self.errors = 0
        self.total_response_time = 0
        self.total_requests = 0
        self.start_time = time.time()

    def record_hit(self, response_time: float):
        self.hits += 1
        self._update_timing(response_time)

    def record_miss(self, response_time: float):
        self.misses += 1
        self._update_timing(response_time)

    def record_error(self):
        self.errors += 1

    def _update_timing(self, response_time: float):
        self.total_response_time += response_time
        self.total_requests += 1

    def get_stats(self) -> Dict[str, Any]:
        uptime = time.time() - self.start_time
        avg_response_time = (
            self.total_response_time / self.total_requests
            if self.total_requests > 0 else 0
        )
        hit_ratio = (
            self.hits / (self.hits + self.misses) * 100
            if (self.hits + self.misses) > 0 else 0
        )

        return {
            "uptime_seconds": int(uptime),
            "total_requests": self.total_requests,
            "hits": self.hits,
            "misses": self.misses,
            "errors": self.errors,
            "hit_ratio_percent": round(hit_ratio, 2),
            "avg_response_ms": round(avg_response_time * 1000, 2)
        }

class CacheVersion:
    def __init__(self):
        self.version = 1
        self.migrations = {
            1: self._migrate_v1_to_v2,
            2: self._migrate_v2_to_v3,
        }

    async def migrate_if_needed(self, data: dict) -> dict:
        data_version = data.get('_version', 1)
        while data_version < self.version:
            migrate_func = self.migrations[data_version]
            data = await migrate_func(data)
            data_version += 1
        return data