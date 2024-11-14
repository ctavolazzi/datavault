from typing import Dict, Any, Optional
from datetime import datetime, timedelta
from pathlib import Path
import hashlib
from .storage import StorageBackend

class CacheManager:
    """Handles low-level cache operations and maintenance"""
    def __init__(self, storage: StorageBackend):
        self.storage = storage

    def get_cache_entry(self, key: str, cache_type: str = "search") -> Optional[Dict[str, Any]]:
        """Get entry from cache"""
        key_hash = hashlib.md5(key.encode()).hexdigest()

        # Check today's cache first, then previous days
        today = datetime.now()
        for days_ago in range(7):  # Check up to week-old caches
            date = today - timedelta(days=days_ago)
            cache_path = (
                Path("cache") / str(date.year) / str(date.month) /
                str(date.day) / cache_type / f"{key_hash}.json"
            )

            try:
                data = self.storage.read(key, cache_path)
                if data:
                    return data['response']
            except CacheError:
                continue

        return None

    def store_cache_entry(self, key: str, data: Dict[str, Any], cache_type: str = "search") -> None:
        """Store entry in cache"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        today = datetime.now()

        cache_path = (
            Path("cache") / str(today.year) / str(today.month) /
            str(today.day) / cache_type / f"{key_hash}.json"
        )

        cache_data = {
            "query": key,
            "timestamp": datetime.now().isoformat(),
            "response": data
        }

        self.storage.write(key, cache_data, cache_path)

    def cleanup(self, max_age: timedelta) -> None:
        """Clean up expired cache entries"""
        cutoff_date = datetime.now() - max_age
        base_path = Path("cache")

        if not base_path.exists():
            return

        for year_dir in base_path.iterdir():
            if not year_dir.is_dir():
                continue

            for month_dir in year_dir.iterdir():
                if not month_dir.is_dir():
                    continue

                for day_dir in month_dir.iterdir():
                    if not day_dir.is_dir():
                        continue

                    try:
                        dir_date = datetime(
                            int(year_dir.name),
                            int(month_dir.name),
                            int(day_dir.name)
                        )

                        if dir_date < cutoff_date:
                            for cache_file in day_dir.rglob("*.json"):
                                cache_file.unlink()
                            day_dir.rmdir()
                    except (ValueError, OSError) as e:
                        logger.error(f"Cleanup error for {day_dir}: {e}")

    def get_storage_stats(self) -> Dict[str, Any]:
        """Get storage statistics"""
        stats = {
            'total_size': 0,
            'file_count': 0,
            'cache_types': {}
        }

        base_path = Path("cache")
        if not base_path.exists():
            return stats

        for cache_file in base_path.rglob("*.json"):
            stats['file_count'] += 1
            stats['total_size'] += cache_file.stat().st_size

            # Track stats by cache type
            cache_type = cache_file.parent.name
            if cache_type not in stats['cache_types']:
                stats['cache_types'][cache_type] = {
                    'file_count': 0,
                    'size': 0
                }
            stats['cache_types'][cache_type]['file_count'] += 1
            stats['cache_types'][cache_type]['size'] += cache_file.stat().st_size

        return stats