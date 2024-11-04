from pathlib import Path
import json
import hashlib
from typing import Set, Dict, List
from datetime import datetime
from ..core import get_logger

logger = get_logger(__name__)

def get_content_hash(data: Dict) -> str:
    """Generate a hash of the article content"""
    # Only hash the actual article content, not metadata
    content = json.dumps([
        {k: v for k, v in article.items() if k != 'collected_at'}
        for article in data['articles']
    ], sort_keys=True)
    return hashlib.md5(content.encode()).hexdigest()

def cleanup_collections(data_dir: Path = None) -> None:
    """Remove duplicate collections, keeping the newest of each"""
    if data_dir is None:
        data_dir = Path("datasets/news/raw")
    
    # Map content hashes to files
    hash_map: Dict[str, List[Path]] = {}
    
    # Process all JSON files
    for file_path in data_dir.glob("*.json"):
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
            content_hash = get_content_hash(data)
            
            if content_hash not in hash_map:
                hash_map[content_hash] = []
            hash_map[content_hash].append(file_path)
            
        except Exception as e:
            logger.error(f"Error processing {file_path}: {e}")
    
    # Remove duplicates
    for content_hash, files in hash_map.items():
        if len(files) > 1:
            # Sort by filename (which includes timestamp)
            files.sort()
            # Keep the newest file
            for file_path in files[:-1]:
                logger.info(f"Removing duplicate: {file_path}")
                file_path.unlink()

def main():
    """Run cleanup utility"""
    logger.info("Starting collection cleanup...")
    cleanup_collections()
    logger.info("Cleanup complete!")

if __name__ == "__main__":
    main() 