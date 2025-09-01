import logging
import os
from typing import Optional

_configured = False

def _configure_logging():
    """Configure logging only once"""
    global _configured
    if not _configured:
        logging.basicConfig(
            level=logging.INFO,
            format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            force=True
        )
        _configured = True

class Logger:
    """Lightweight and easy-to-use logger class

    Args:
        name: Name of logger
    
    Returns:
        Logger instance
    
    Examples:
        >>> logger = Logger(__name__)
        >>> logger.info("This is an info message")
    
    """
    
    def __init__(self, name: Optional[str] = None):
        _configure_logging()
        self.name = name or self.__class__.__module__
        self.logger = logging.getLogger(self.name)
    
    def debug(self, message: str, *args, **kwargs):
        """Log debug message"""
        self.logger.debug(message, *args, **kwargs)
    
    def info(self, message: str, *args, **kwargs):
        """Log info message"""
        self.logger.info(message, *args, **kwargs)
    
    def warning(self, message: str, *args, **kwargs):
        """Log warning message"""
        self.logger.warning(message, *args, **kwargs)
    
    def error(self, message: str, *args, **kwargs):
        """Log error message"""
        self.logger.error(message, *args, **kwargs)
    
    def critical(self, message: str, *args, **kwargs):
        """Log critical message"""
        self.logger.critical(message, *args, **kwargs)
    
    def exception(self, message: str, *args, **kwargs):
        """Log exception with traceback"""
        self.logger.exception(message, *args, **kwargs)
    
    def set_level(self, level):
        """Set logger level"""
        self.logger.setLevel(level)

# Utility function to create logger quickly
def get_logger(name: Optional[str] = None) -> Logger:
    """Create logger instance quickly
    
    Args:
        name: Logger name, defaults to calling module name
    
    Returns:
        Logger instance
    """
    if name is None:
        import inspect
        frame = inspect.currentframe().f_back
        name = frame.f_globals.get('__name__', 'unknown')
    return Logger(name)

# Default logger for this module
logger = get_logger(__name__)