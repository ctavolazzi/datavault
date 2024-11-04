from pathlib import Path
from typing import Dict, Any
import magic
import hashlib
from PIL import Image
import zipfile
from datetime import datetime

class FileAnalyzer:
    def __init__(self, encoding: str = 'utf-8'):
        self.encoding = encoding

    def analyze(self, path: Path, calculate_hash: bool = False) -> Dict[str, Any]:
        """Main analysis method"""
        info = self._get_basic_info(path)
        
        if calculate_hash:
            info['hash'] = self._calculate_hash(path)
        
        mime_type = info['mime_type']
        if mime_type.startswith('text'):
            self._analyze_text(path, info)
        elif mime_type.startswith('image'):
            self._analyze_image(path, info)
        elif mime_type == 'application/zip':
            self._analyze_zip(path, info)
            
        return info

    def _get_basic_info(self, path: Path) -> Dict[str, Any]:
        """Get basic file information"""
        stats = path.stat()
        return {
            'size': stats.st_size,
            'created': datetime.fromtimestamp(stats.st_ctime),
            'modified': datetime.fromtimestamp(stats.st_mtime),
            'mime_type': magic.from_file(str(path), mime=True),
            'type': magic.from_file(str(path)),
            'extension': path.suffix
        }

    # ... other analysis methods ... 