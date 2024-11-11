import logging
import sys
from pathlib import Path
from datetime import datetime

def setup_logger(name: str = "datavault", level: str = "INFO"):
    """Configure logging for the application"""
    # Create logs directory if it doesn't exist
    log_dir = Path.home() / ".datavault" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Create log filename with timestamp
    log_file = log_dir / f"datavault_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Create handlers
    console_handler = logging.StreamHandler(sys.stderr)
    file_handler = logging.FileHandler(log_file)

    # Create formatters
    console_format = logging.Formatter('%(levelname)s: %(message)s')
    file_format = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

    # Set formatters
    console_handler.setFormatter(console_format)
    file_handler.setFormatter(file_format)

    # Add handlers
    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger