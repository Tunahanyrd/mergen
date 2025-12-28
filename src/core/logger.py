"""
Centralized logging system for Mergen.

Provides structured logging with:
- Multiple log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
- File rotation (10MB per file, 5 backups)
- Console and file output
- Configurable verbosity
"""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from pathlib import Path


class MergenLogger:
    """Singleton logger for Mergen application."""
    
    _instance = None
    _loggers = {}
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialized = False
        return cls._instance
    
    def __init__(self):
        if self._initialized:
            return
        
        self._initialized = True
        self.log_dir = Path.home() / ".config" / "mergen" / "logs"
        self.log_dir.mkdir(parents=True, exist_ok=True)
        
        # Default log file
        self.log_file = self.log_dir / "mergen.log"
        
        # Check verbose mode
        self.verbose = os.environ.get("MERGEN_VERBOSE") == "1"
        
    def get_logger(self, name: str) -> logging.Logger:
        """
        Get or create logger for module.
        
        Args:
            name: Logger name (usually __name__)
            
        Returns:
            Configured logger instance
        """
        if name in self._loggers:
            return self._loggers[name]
        
        logger = logging.getLogger(name)
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        # Prevent duplicate handlers
        if logger.handlers:
            return logger
        
        # File handler with rotation
        file_handler = RotatingFileHandler(
            self.log_file,
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=5,
            encoding='utf-8'
        )
        file_handler.setLevel(logging.DEBUG)
        
        # Console handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.DEBUG if self.verbose else logging.WARNING)
        
        # Formatters
        detailed_formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
        
        simple_formatter = logging.Formatter(
            '%(levelname)s: %(message)s'
        )
        
        file_handler.setFormatter(detailed_formatter)
        console_handler.setFormatter(simple_formatter if not self.verbose else detailed_formatter)
        
        logger.addHandler(file_handler)
        logger.addHandler(console_handler)
        
        self._loggers[name] = logger
        return logger


# Global instance
_logger_instance = MergenLogger()


def get_logger(name: str = __name__) -> logging.Logger:
    """
    Get logger for module.
    
    Usage:
        from src.core.logger import get_logger
        logger = get_logger(__name__)
        logger.info("Message")
    
    Args:
        name: Module name (use __name__)
        
    Returns:
        Logger instance
    """
    return _logger_instance.get_logger(name)


# Convenience function for compatibility
def setup_logging(verbose: bool = False):
    """
    Setup global logging configuration.
    
    Args:
        verbose: Enable verbose (DEBUG) logging
    """
    if verbose:
        os.environ["MERGEN_VERBOSE"] = "1"
        
        # Update existing loggers
        for logger in _logger_instance._loggers.values():
            logger.setLevel(logging.DEBUG)
            for handler in logger.handlers:
                if isinstance(handler, logging.StreamHandler):
                    handler.setLevel(logging.DEBUG)
