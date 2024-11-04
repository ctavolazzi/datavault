from pathlib import Path
from datetime import datetime
from collections import defaultdict
from typing import Dict, List, Tuple

class ProjectAnalyzer:
    def __init__(self, project_dir: Path):
        self.project_dir = project_dir
        self.files = list(project_dir.rglob("*"))
    
    def get_basic_stats(self) -> Dict[str, int]:
        """Get basic project statistics"""
        return {
            'total_files': len([f for f in self.files if f.is_file()]),
            'total_dirs': len([f for f in self.files if f.is_dir()]),
            'python_files': len([f for f in self.files if f.is_file() and f.suffix == '.py']),
            'total_size_mb': sum(f.stat().st_size for f in self.files if f.is_file()) / (1024 * 1024)
        }
    
    def get_file_types(self, top_n: int = 5) -> List[Tuple[str, int]]:
        """Get file type distribution"""
        extensions = defaultdict(int)
        for f in self.files:
            if f.is_file():
                ext = f.suffix.lower() or 'no extension'
                extensions[ext] += 1
        
        return sorted(extensions.items(), key=lambda x: x[1], reverse=True)[:top_n]
    
    def get_recent_activity(self, limit: int = 5) -> List[Tuple[datetime, Path]]:
        """Get recently modified files"""
        recent_files = sorted(
            [f for f in self.files if f.is_file()],
            key=lambda x: x.stat().st_mtime,
            reverse=True
        )[:limit]
        
        return [(datetime.fromtimestamp(f.stat().st_mtime), f) for f in recent_files]
    
    def get_concerns(self, size_threshold_mb: int = 1) -> Dict[str, List[Path]]:
        """Identify potential concerns"""
        return {
            'large_files': [
                f for f in self.files 
                if f.is_file() and f.stat().st_size > size_threshold_mb * 1024 * 1024
            ],
            'empty_dirs': [
                d for d in self.files 
                if d.is_dir() and not any(d.iterdir())
            ]
        } 