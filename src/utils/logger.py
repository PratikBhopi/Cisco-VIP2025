"""
Logging utilities for Network Topology Analyzer.
"""

import logging
import sys
from pathlib import Path
from typing import Optional
from loguru import logger


def setup_logger(verbose: bool = False, log_file: Optional[str] = None) -> logging.Logger:
    """
    Setup logging configuration.
    
    Args:
        verbose: Enable debug level logging
        log_file: Optional log file path
        
    Returns:
        Configured logger instance
    """
    # Remove default loguru handler
    logger.remove()
    
    # Set log level
    level = "DEBUG" if verbose else "INFO"
    
    # Add console handler
    logger.add(
        sys.stderr,
        level=level,
        format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
        colorize=True
    )
    
    # Add file handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        logger.add(
            log_file,
            level=level,
            format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
            rotation="10 MB",
            retention="7 days",
            compression="zip"
        )
    
    return logger