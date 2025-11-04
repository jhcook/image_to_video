"""
Logging configuration for video generation library.

Provides structured logging to both console and file with proper formatting.
Logs are written to logs/ directory with rotating file handlers.
"""

import logging
import sys
from pathlib import Path
from logging.handlers import RotatingFileHandler


def setup_logger(
    name: str = "video_gen",
    log_level: str = "INFO",
    log_to_file: bool = True,
    log_dir: str = "logs"
) -> logging.Logger:
    """
    Set up a logger with console and optional file handlers.
    
    Args:
        name: Logger name
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_to_file: Whether to write logs to file
        log_dir: Directory for log files
        
    Returns:
        Configured logger instance
    """
    logger = logging.getLogger(name)
    
    # Don't add handlers if they already exist
    if logger.handlers:
        return logger
    
    # Set log level
    level = getattr(logging, log_level.upper(), logging.INFO)
    logger.setLevel(level)
    
    # Create formatters
    console_formatter = logging.Formatter(
        '%(message)s'  # Simple format for console
    )
    
    file_formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(level)
    console_handler.setFormatter(console_formatter)
    logger.addHandler(console_handler)
    
    # File handler (if enabled)
    if log_to_file:
        # Create logs directory if it doesn't exist
        log_path = Path(log_dir)
        log_path.mkdir(parents=True, exist_ok=True)
        
        # Use fixed log file name
        log_file = log_path / "video_gen.log"
        
        # Rotating file handler (10MB max, keep 5 backups)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)  # Log everything to file
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)
        
        logger.debug(f"Logging to: {log_file}")
    
    return logger


def get_logger(name: str = "video_gen") -> logging.Logger:
    """
    Get an existing logger or create a new one.
    
    Args:
        name: Logger name
        
    Returns:
        Logger instance
    """
    logger = logging.getLogger(name)
    
    # If logger doesn't have handlers, set it up with defaults
    if not logger.handlers:
        return setup_logger(name)
    
    return logger


# Module-level logger for library use
_library_logger = None


def init_library_logger(verbose: bool = False, log_to_file: bool = True) -> logging.Logger:
    """
    Initialize the library-wide logger.
    
    Args:
        verbose: If True, set log level to DEBUG, otherwise INFO
        log_to_file: Whether to write logs to file
        
    Returns:
        Configured logger
    """
    global _library_logger
    
    log_level = "DEBUG" if verbose else "INFO"
    _library_logger = setup_logger(
        name="video_gen",
        log_level=log_level,
        log_to_file=log_to_file
    )
    
    return _library_logger


def get_library_logger() -> logging.Logger:
    """
    Get the library-wide logger, initializing if needed.
    
    Returns:
        Logger instance
    """
    global _library_logger
    
    if _library_logger is None:
        _library_logger = init_library_logger()
    
    return _library_logger
