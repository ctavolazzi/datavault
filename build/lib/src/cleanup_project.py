#!/usr/bin/env python3
from pathlib import Path
import shutil
import logging
from typing import Set, Dict, List
import json
from datetime import datetime

class ProjectCleaner:
    """Handles project cleanup and reorganization"""
    
    def __init__(self, root_dir: Path = None):
        self.root = root_dir or Path.cwd()
        self.logger = self._setup_logger()
        
        # Define specific paths that should never be moved
        self.protected_paths = {
            self.root / 'cleanup_project.py',
            self.root / 'generate_filetree.py',
            self.root / 'requirements.txt',
            self.root / 'README.md',
            self.root / 'setup.py',
            self.root / '.gitignore',
            self.root / '.env',
            self.root / 'pyproject.toml',
            self.root / 'setup.cfg'
        }
        
        # Define file mappings based on project structure
        self.file_mappings = {
            'test_*.py': 'tests',
            '*.py': 'src',
            '*.md': 'docs',
            '*.json': 'datasets/raw',
            '*.png': 'output/figures',
            '*.ipynb': 'notebooks',
            '*.yml': 'config',
            '*.yaml': 'config',
            '*.sql': 'sql'
        }
        
        # Define directories that should be ignored
        self.ignore_dirs = {
            '.git', '__pycache__', '.pytest_cache', 
            'venv', 'env', 'backup_', '.idea', 
            '.vscode', 'node_modules'
        }
        
        self.moved_files: Dict[str, List[Path]] = {} 