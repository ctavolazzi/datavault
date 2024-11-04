from pathlib import Path
import json
import hashlib
from datetime import datetime, timedelta

class AnalysisCache:
    def __init__(self, cache_dir: Path):
        self.cache_dir = cache_dir
        self.cache_dir.mkdir(parents=True, exist_ok=True)

    def get_cached_result(self, file_path: Path, max_age: timedelta = timedelta(days=1)):
        cache_key = self._generate_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        if cache_file.exists():
            with open(cache_file, 'r') as f:
                cached = json.load(f)
                if (datetime.now() - datetime.fromtimestamp(cached['timestamp'])) < max_age:
                    return cached['results']
        return None

    def cache_result(self, file_path: Path, results: dict):
        cache_key = self._generate_cache_key(file_path)
        cache_file = self.cache_dir / f"{cache_key}.json"
        
        with open(cache_file, 'w') as f:
            json.dump({
                'timestamp': datetime.now().timestamp(),
                'results': results
            }, f)

    def _generate_cache_key(self, file_path: Path) -> str:
        content = file_path.read_bytes()
        return hashlib.md5(content).hexdigest() 