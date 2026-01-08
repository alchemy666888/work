"""Logging setup using loguru"""

import sys
from loguru import logger

# Remove default handler
logger.remove()


def setup_logger(level: str = "INFO") -> logger:
    """
    Set up and configure the logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Add console handler with custom format
    logger.add(
        sys.stderr,
        format=(
            "<green>{time:YYYY-MM-DD HH:mm:ss}</green> | "
            "<level>{level: <8}</level> | "
            "<cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - "
            "<level>{message}</level>"
        ),
        level=level,
        colorize=True,
    )

    return logger


def get_logger():
    """Get the configured logger instance."""
    return logger


# Export logger for convenience
__all__ = ["logger", "setup_logger", "get_logger"]
