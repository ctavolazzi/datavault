import pytest
import logging
from logging.handlers import RotatingFileHandler
from pathlib import Path
from unittest.mock import patch
from src.ai_analyzer.utils.logger import setup_logging, SingletonLogger

def test_logger_basic():
    """Test basic logger functionality"""
    logger = setup_logging(debug=True)

    # Verify logger configuration
    assert logger.level == logging.DEBUG
    assert len(logger.handlers) == 2  # Should have file and console handlers
    assert not logger.propagate  # Should not propagate to prevent duplicates

    # Verify handlers
    handlers = logger.handlers
    assert any(isinstance(h, RotatingFileHandler) for h in handlers)
    assert any(isinstance(h, logging.StreamHandler) for h in handlers)

def test_logger_singleton():
    """Test that logger maintains singleton pattern"""
    logger1 = setup_logging()
    logger2 = setup_logging()
    assert logger1 is logger2  # Should be the same instance

def test_logger_debug_mode():
    """Test debug mode configuration"""
    # Reset the singleton
    SingletonLogger._instance = None

    # Test debug mode
    debug_logger = setup_logging(debug=True)
    assert debug_logger.level == logging.DEBUG

    # Reset singleton again
    SingletonLogger._instance = None

    # Test normal mode
    normal_logger = setup_logging(debug=False)
    assert normal_logger.level == logging.INFO

def test_logger_output(tmp_path):
    """Test logger output to file"""
    # Reset the singleton
    SingletonLogger._instance = None

    # Create necessary directories
    log_dir = tmp_path / ".datavault" / "logs"
    log_dir.mkdir(parents=True, exist_ok=True)

    # Temporarily redirect log file to test directory
    with patch.object(Path, 'home', return_value=tmp_path):
        # Setup logger with the test directory
        logger = setup_logging()

        # Test logging
        test_message = "Test log message"
        logger.info(test_message)

        # Force flush handlers
        for handler in logger.handlers:
            handler.flush()

        # Verify log file
        log_file = log_dir / "datavault.log"
        assert log_file.exists(), f"Log file not found at {log_file}"

        # Verify content
        content = log_file.read_text()
        assert test_message in content