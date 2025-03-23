"""
Centralized logging module for ModelForge.
Provides a simple, consistent logging interface for all modules.
"""

import logging
import sys
import os
from typing import Optional, Literal

# Define log levels
LogLevel = Literal["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]

# Default log format
DEFAULT_FORMAT = "%(asctime)s - %(name)s - %(levelname)s - %(message)s"

# Create logs directory if it doesn't exist
os.makedirs("logs", exist_ok=True)

def get_logger(name: str, 
               level: LogLevel = "DEBUG", 
               log_file: Optional[str] = "logs/modelforge.log",
               format_str: str = DEFAULT_FORMAT) -> logging.Logger:
    """
    Get a configured logger instance.
    
    Args:
        name: Logger name (typically __name__ from the calling module)
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Path to log file, or None to disable file logging
        format_str: Log message format string
    
    Returns:
        Configured logger instance
    """
    # Get level from environment variable if set
    env_level = os.environ.get("MODELFORGE_LOG_LEVEL")
    if env_level and env_level.upper() in ["DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"]:
        level = env_level.upper()  # type: ignore
    
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level))
    
    # Remove existing handlers to avoid duplicates
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)
    
    # Disable propagation to prevent duplicate logs
    logger.propagate = False
    
    # Create formatter
    formatter = logging.Formatter(format_str)
    
    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # Add file handler if log_file is specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    return logger

# Default application logger
app_logger = get_logger("modelforge") 