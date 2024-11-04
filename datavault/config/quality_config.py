from pathlib import Path
import yaml

class QualityConfig:
    DEFAULT_CONFIG = {
        'thresholds': {
            'complexity': 10,
            'duplication_length': 50,
            'max_line_length': 100
        },
        'ignore_patterns': [
            '*/tests/*',
            '*/migrations/*',
            '*/.venv/*'
        ],
        'lint_rules': {
            'enable': ['C', 'W', 'E', 'F'],
            'disable': ['C0111', 'C0103']  # Specific rules to ignore
        }
    }

    def __init__(self, config_path: Path = None):
        self.config = self.DEFAULT_CONFIG.copy()
        if config_path and config_path.exists():
            self._load_config(config_path)

    def _load_config(self, path: Path):
        with open(path, 'r') as f:
            user_config = yaml.safe_load(f)
            self.config.update(user_config) 