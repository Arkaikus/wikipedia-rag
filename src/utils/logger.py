"""
Logging configuration for the RAG Wikipedia Chatbot.

Provides structured logging with both file and console output.
"""

import logging
import sys
from pathlib import Path
from typing import Optional

from rich.console import Console
from rich.logging import RichHandler

# Global logger instances
_loggers: dict[str, logging.Logger] = {}


def setup_logger(
    name: str,
    level: str = "INFO",
    log_file: Optional[str] = None,
    use_rich: bool = True,
) -> logging.Logger:
    """
    Set up a logger with console and optional file output.

    Args:
        name: Logger name (typically __name__)
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        log_file: Optional path to log file
        use_rich: Whether to use rich console output

    Returns:
        Configured logger instance
    """
    # Return existing logger if already configured
    if name in _loggers:
        return _loggers[name]

    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Prevent duplicate handlers
    if logger.handlers:
        return logger

    # Create formatters
    file_formatter = logging.Formatter(
        fmt="%(asctime)s | %(name)s | %(levelname)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
    )

    # Console handler with Rich
    if use_rich:
        console_handler = RichHandler(
            rich_tracebacks=True,
            markup=True,
            show_time=False,
            show_path=False,
        )
        console_handler.setLevel(logging.INFO)
    else:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setLevel(logging.INFO)
        console_handler.setFormatter(file_formatter)

    logger.addHandler(console_handler)

    # File handler (if specified)
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file, encoding="utf-8")
        file_handler.setLevel(logging.DEBUG)
        file_handler.setFormatter(file_formatter)
        logger.addHandler(file_handler)

    _loggers[name] = logger
    return logger


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance, creating it if necessary.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    if name in _loggers:
        return _loggers[name]

    # Import here to avoid circular dependency
    from src.utils.config import get_settings

    settings = get_settings()
    return setup_logger(
        name=name,
        level=settings.log_level,
        log_file=settings.log_file,
        use_rich=True,
    )


# Convenience functions for quick logging
def log_info(message: str, logger_name: str = "rag_chatbot") -> None:
    """Log an info message."""
    logger = get_logger(logger_name)
    logger.info(message)


def log_error(message: str, logger_name: str = "rag_chatbot", exc_info: bool = False) -> None:
    """Log an error message."""
    logger = get_logger(logger_name)
    logger.error(message, exc_info=exc_info)


def log_warning(message: str, logger_name: str = "rag_chatbot") -> None:
    """Log a warning message."""
    logger = get_logger(logger_name)
    logger.warning(message)


def log_debug(message: str, logger_name: str = "rag_chatbot") -> None:
    """Log a debug message."""
    logger = get_logger(logger_name)
    logger.debug(message)
