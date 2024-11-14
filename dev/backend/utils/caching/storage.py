from typing import Optional, Dict, Any, Protocol
import json
import aiofiles
import logging
from pathlib import Path

logger = logging.getLogger(__name__)

class StorageBackend(Protocol):
    """Protocol for cache storage backends"""

    async def read(self, key: str, cache_type: str = "search") -> Optional[Dict[str, Any]]: ...
    async def write(self, key: str, data: Any, cache_type: str = "search") -> None: ...
    async def delete(self, key: str, cache_type: str = "search") -> bool: ...
    def get_all_files(self, cache_type: str = "search") -> list[Path]: ...

class FileSystemStorage:
    """File system based storage implementation"""

    def __init__(self, config):
        self.config = config

    async def read(self, key: str, cache_type: str = "search") -> Optional[Dict[str, Any]]:
        """Read data from cache file"""
        try:
            cache_path = self.config.get_cache_path(cache_type) / f"{key}.json"
            if cache_path.exists():
                async with aiofiles.open(cache_path, 'r') as f:
                    data = await f.read()
                    return json.loads(data)
            return None
        except Exception as e:
            logger.warning(f"Cache read error: {str(e)}")
            return None

    async def write(self, key: str, data: Any, cache_type: str = "search") -> None:
        """Write data to cache file"""
        try:
            cache_path = self.config.get_cache_path(cache_type) / f"{key}.json"
            cache_path.parent.mkdir(parents=True, exist_ok=True)

            async with aiofiles.open(cache_path, 'w') as f:
                await f.write(json.dumps(data))
        except Exception as e:
            logger.error(f"Cache write error: {str(e)}")
            raise

    async def delete(self, key: str, cache_type: str = "search") -> bool:
        """Delete a cached item"""
        try:
            cache_path = self.config.get_cache_path(cache_type) / f"{key}.json"
            if cache_path.exists():
                cache_path.unlink()
                return True
            return False
        except Exception as e:
            logger.error(f"Cache delete error: {str(e)}")
            return False

    def get_all_files(self, cache_type: str = "search") -> list[Path]:
        """Get all cache files of a specific type"""
        try:
            cache_path = self.config.get_cache_path(cache_type)
            return list(cache_path.glob("*.json"))
        except Exception as e:
            logger.error(f"Error listing cache files: {str(e)}")
            return []