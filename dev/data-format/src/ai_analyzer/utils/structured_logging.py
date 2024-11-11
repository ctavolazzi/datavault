import json
import logging
from pathlib import Path
from datetime import datetime
from typing import Any, Dict

class JSONFormatter(logging.Formatter):
    """Format logs as valid JSON objects"""
    def format(self, record: logging.LogRecord) -> str:
        log_entry = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra"):
            log_entry["extra"] = record.extra

        return json.dumps(log_entry)

def setup_logging(debug: bool = False):
    """Configure logging with JSON and regular formats"""
    # Create log directory
    log_dir = Path.home() / ".datavault" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Clear existing handlers
    root = logging.getLogger()
    root.handlers.clear()

    # Set up JSON file handler
    json_handler = logging.FileHandler(
        log_dir / "datavault.json",
        mode='a',
        encoding='utf-8'
    )
    json_handler.setFormatter(JSONFormatter())

    # Set up regular file handler
    file_handler = logging.FileHandler(
        log_dir / "datavault.log",
        mode='a',
        encoding='utf-8'
    )
    file_handler.setFormatter(
        logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
    )

    # Set up console handler (for immediate feedback)
    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(message)s'))

    # Configure root logger
    root.setLevel(logging.DEBUG if debug else logging.INFO)
    root.addHandler(json_handler)
    root.addHandler(file_handler)
    root.addHandler(console_handler)

    return logging.getLogger('datavault')