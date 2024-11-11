import logging
from pathlib import Path
from logging.handlers import RotatingFileHandler

class SingletonLogger:
    """A singleton logger class to ensure only one logger instance exists."""
    _instance = None

    @classmethod
    def get_logger(cls, debug: bool = False) -> logging.Logger:
        """Get or create a logger instance with file and console handlers.

        Args:
            debug (bool): If True, sets logging level to DEBUG; otherwise INFO

        Returns:
            logging.Logger: Configured logger instance
        """
        if cls._instance is None:
            # Create log directory in user's home directory
            log_dir = Path.home() / ".datavault" / "logs"
            log_dir.mkdir(parents=True, exist_ok=True)

            # Configure root logger
            logger = logging.getLogger('datavault')
            logger.setLevel(logging.DEBUG if debug else logging.INFO)

            # Remove any existing handlers to prevent duplication
            if logger.hasHandlers():
                logger.handlers.clear()

            # Create rotating file handler (5MB max size, keep 5 backup files)
            log_file = log_dir / "datavault.log"
            file_handler = RotatingFileHandler(
                log_file,
                maxBytes=5*1024*1024,  # 5 MB
                backupCount=5,
                encoding='utf-8'
            )

            # Configure file handler format (with timestamp and level)
            file_formatter = logging.Formatter(
                '%(asctime)s [%(levelname)8s] %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            file_handler.setFormatter(file_formatter)
            logger.addHandler(file_handler)

            # Create console handler (for immediate feedback)
            console_handler = logging.StreamHandler()
            console_handler.setLevel(logging.DEBUG if debug else logging.INFO)

            # Configure console handler format (simple messages only)
            console_formatter = logging.Formatter('%(message)s')
            console_handler.setFormatter(console_formatter)
            logger.addHandler(console_handler)

            # Prevent propagation to root logger to avoid duplicate logs
            logger.propagate = False

            cls._instance = logger

        return cls._instance

def setup_logging(debug: bool = False) -> logging.Logger:
    """Get or create the singleton logger instance.

    Args:
        debug (bool): If True, enables debug logging

    Returns:
        logging.Logger: Configured logger instance
    """
    return SingletonLogger.get_logger(debug)