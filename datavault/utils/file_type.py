import magic
import mimetypes
from pathlib import Path
from typing import Dict, Optional

class FileTypeDetector:
    """Detect and analyze file types"""
    
    def __init__(self):
        self.magic = magic.Magic(mime=True)
        self.file_categories = {
            'text': ['.txt', '.md', '.rst', '.log'],
            'code': ['.py', '.js', '.java', '.cpp', '.h', '.css', '.html'],
            'data': ['.json', '.yaml', '.xml', '.csv', '.sql'],
            'image': ['.jpg', '.jpeg', '.png', '.gif', '.bmp', '.svg'],
            'document': ['.pdf', '.doc', '.docx', '.odt', '.rtf'],
            'archive': ['.zip', '.tar', '.gz', '.rar', '.7z'],
            'binary': ['.exe', '.dll', '.so', '.dylib']
        }
    
    def analyze(self, file_path: Path) -> Dict[str, str]:
        """Analyze a file and return its type information"""
        try:
            mime_type = self.magic.from_file(str(file_path))
            category = self._get_category(file_path)
            
            return {
                'mime_type': mime_type,
                'category': category,
                'extension': file_path.suffix.lower(),
                'encoding': self._detect_encoding(file_path)
            }
        except Exception as e:
            return {
                'mime_type': 'unknown',
                'category': 'unknown',
                'extension': file_path.suffix.lower(),
                'error': str(e)
            }
    
    def _get_category(self, file_path: Path) -> str:
        """Determine the category of a file"""
        ext = file_path.suffix.lower()
        for category, extensions in self.file_categories.items():
            if ext in extensions:
                return category
        return 'other'
    
    def _detect_encoding(self, file_path: Path) -> Optional[str]:
        """Attempt to detect file encoding"""
        try:
            import chardet
            with open(file_path, 'rb') as f:
                raw = f.read(1024)
                result = chardet.detect(raw)
                return result['encoding']
        except ImportError:
            return None 