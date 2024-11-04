from pathlib import Path
import yaml
from typing import Dict, Any

class Config:
    """Handle application configuration"""
    
    DEFAULT_CONFIG = {
        'theme': 'light',
        'preview_lines': 5,
        'max_file_size': 100_000_000,  # 100MB
        'ignore_patterns': [
            '*/.git/*',
            '*/__pycache__/*',
            '*/venv/*',
            '*.pyc'
        ]
    }
    
    def __init__(self, config_path: Path = None):
        self.config = self.DEFAULT_CONFIG.copy()
        self.config_path = config_path or Path.home() / '.datavault' / 'config.yml'
        self._load_config()
    
    def _load_config(self):
        """Load configuration from file"""
        if self.config_path.exists():
            try:
                with open(self.config_path, 'r') as f:
                    user_config = yaml.safe_load(f)
                    if user_config:
                        self.config.update(user_config)
            except Exception as e:
                print(f"Error loading config: {e}")
    
    def save_config(self):
        """Save current configuration to file"""
        self.config_path.parent.mkdir(parents=True, exist_ok=True)
        with open(self.config_path, 'w') as f:
            yaml.dump(self.config, f)
    
    def get(self, key: str, default: Any = None) -> Any:
        """Get configuration value"""
        return self.config.get(key, default)
    
    def set(self, key: str, value: Any):
        """Set configuration value"""
        self.config[key] = value
        self.save_config() 