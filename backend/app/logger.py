"""
Centralized logging configuration for the application.
Uses loguru for consistent, structured logging across all modules.
"""

import sys
from loguru import logger
from typing import Optional, Dict, Any
import os


class AppLogger:
    """Centralized logger configuration for the application."""
    
    _instance: Optional['AppLogger'] = None
    _configured: bool = False
    
    def __new__(cls) -> 'AppLogger':
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
    
    def __init__(self) -> None:
        if not self._configured:
            self._setup_logging()
            self._configured = True
    
    def _setup_logging(self) -> None:
        """Configure loguru with consistent formatting and levels."""
        # Remove default handler
        logger.remove()
        
        # Determine log level from environment
        log_level = os.getenv("LOG_LEVEL", "INFO").upper()
        
        # Console handler with structured formatting
        logger.add(
            sys.stdout,
            level=log_level,
            format="<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
                   "<level>{level: <8}</level> | "
                   "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> | "
                   "<level>{message}</level>",
            colorize=True,
            backtrace=True,
            diagnose=True
        )
        
        # File handler for persistent logs (optional)
        log_file = os.getenv("LOG_FILE")
        if log_file:
            logger.add(
                log_file,
                level=log_level,
                format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} | {message}",
                rotation="10 MB",
                retention="7 days",
                compression="zip"
            )
    
    def get_logger(self, name: Optional[str] = None) -> 'Logger':
        """Get a logger instance for a specific module.
        
        Args:
            name: Optional module name for context
            
        Returns:
            Configured logger instance
        """
        if name:
            return logger.bind(name=name)
        return logger


# Global logger instance
app_logger = AppLogger()


def get_logger(name: Optional[str] = None) -> 'Logger':
    """Get a configured logger instance.
    
    Args:
        name: Optional module name for context
        
    Returns:
        Configured logger instance
    """
    return app_logger.get_logger(name)


def get_module_logger(module_name: str) -> 'Logger':
    """Get a logger for a specific module with proper naming.
    
    Args:
        module_name: Name of the module requesting the logger
        
    Returns:
        Logger instance bound to the module name
    """
    return logger.bind(module=module_name)


# Standardized logging functions
def log_info(message: str, **kwargs: Any) -> None:
    """Log an info message with standardized format.
    
    Args:
        message: Log message
        **kwargs: Additional context data
    """
    logger.info(message, **kwargs)


def log_error(message: str, error: Optional[Exception] = None, **kwargs: Any) -> None:
    """Log an error message with standardized format.
    
    Args:
        message: Log message
        error: Optional exception object
        **kwargs: Additional context data
    """
    if error:
        logger.error(f"{message}: {str(error)}", **kwargs)
    else:
        logger.error(message, **kwargs)


def log_warning(message: str, **kwargs: Any) -> None:
    """Log a warning message with standardized format.
    
    Args:
        message: Log message
        **kwargs: Additional context data
    """
    logger.warning(message, **kwargs)


def log_debug(message: str, **kwargs: Any) -> None:
    """Log a debug message with standardized format.
    
    Args:
        message: Log message
        **kwargs: Additional context data
    """
    logger.debug(message, **kwargs)


def log_success(message: str, **kwargs: Any) -> None:
    """Log a success message with standardized format.
    
    Args:
        message: Log message
        **kwargs: Additional context data
    """
    logger.success(message, **kwargs)
