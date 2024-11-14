from dataclasses import dataclass
from pathlib import Path
from typing import Optional

@dataclass
class CacheConfig:
    """Configuration for cache service"""
    base_dir: Path
    max_age_hours: int = 24
    cleanup_days: int = 7
    enable_compression: bool = False
    compression_level: int = 6

    @classmethod
    def from_dict(cls, config: dict) -> 'CacheConfig':
        """Create config from dictionary"""
        base_dir = Path(config.get('base_dir', 'cache'))
        return cls(
            base_dir=base_dir,
            max_age_hours=config.get('max_age_hours', 24),
            cleanup_days=config.get('cleanup_days', 7),
            enable_compression=config.get('enable_compression', False),
            compression_level=config.get('compression_level', 6)
        )

    def get_cache_path(self, cache_type: str = "search") -> Path:
        """Get the path for a specific cache type"""
        cache_path = self.base_dir / cache_type
        cache_path.mkdir(parents=True, exist_ok=True)
        return cache_path