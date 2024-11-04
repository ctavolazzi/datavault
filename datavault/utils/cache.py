import json
import pickle
from pathlib import Path
from typing import Any, Optional
from datetime import datetime, timedelta
import hashlib

class Cache:
    """Simple caching system for expensive operations"""
    
    def __init__(self, cache_dir: Optional[Path] = None):
        self.cache_dir = cache_dir or Path.home() / '.datavault' / 'cache'
        self.cache_dir.mkdir(parents=True, exist_ok=True)
    
    def get(self, key: str, max_age: Optional[timedelta] = None) -> Optional[Any]:
        """Retrieve item from cache"""
        cache_file = self._get_cache_file(key)
        if not cache_file.exists():
            return None
            
        try:
            with open(cache_file, 'rb') as f:
                data = pickle.load(f)
                
            # Check if cache is expired
            if max_age and (datetime.now() - data['timestamp']) > max_age:
                return None
                
            return data['value']
        except Exception:
            return None
    
    def set(self, key: str, value: Any):
        """Store item in cache"""
        cache_file = self._get_cache_file(key)
        try:
            with open(cache_file, 'wb') as f:
                pickle.dump({
                    'timestamp': datetime.now(),
                    'value': value
                }, f)
        except Exception as e:
            click.echo(f"Warning: Failed to cache value: {e}")
    
    def clear(self, older_than: Optional[timedelta] = None):
        """Clear cached items"""
        for cache_file in self.cache_dir.glob('*'):
            if older_than:
                age = datetime.now() - datetime.fromtimestamp(cache_file.stat().st_mtime)
                if age > older_than:
                    cache_file.unlink()
            else:
                cache_file.unlink()
    
    def _get_cache_file(self, key: str) -> Path:
        """Generate cache file path from key"""
        key_hash = hashlib.md5(key.encode()).hexdigest()
        return self.cache_dir / f"{key_hash}.cache" 