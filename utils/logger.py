"""Logging setup using loguru"""

import sys
from pathlib import Path
from loguru import logger

# Remove default handler
logger.remove()

# Log file path
LOG_DIR = Path("data/logs")
LOG_FILE = LOG_DIR / "monitor.log"


def setup_logger(level: str = "INFO") -> logger:
    """
    Set up and configure the logger.

    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    # Ensure log directory exists
    LOG_DIR.mkdir(parents=True, exist_ok=True)

    # Add file handler for all logs (errors, warnings, alerts)
    logger.add(
        LOG_FILE,
        format="{time:YYYY-MM-DD HH:mm:ss} | {level: <8} | {name}:{function}:{line} - {message}",
        level="DEBUG",
        rotation="10 MB",
        retention="7 days",
        encoding="utf-8",
    )

    # Add console handler - only show INFO and above, minimal format
    # Using filter to suppress during Rich live display
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
        filter=lambda record: record["level"].name not in ("DEBUG",),
    )

    return logger


def log_alert(severity: str, message: str, **extra):
    """
    Log an alert to file without interrupting console.

    Args:
        severity: Alert severity (info, warning, critical)
        message: Alert message
        **extra: Additional data to log
    """
    log_msg = f"ALERT: {message}"
    if extra:
        log_msg += f" | data={extra}"

    if severity == "critical":
        logger.opt(depth=1).error(log_msg)
    elif severity == "warning":
        logger.opt(depth=1).warning(log_msg)
    else:
        logger.opt(depth=1).info(log_msg)


def get_logger():
    """Get the configured logger instance."""
    return logger


def get_log_file_path() -> Path:
    """Get the path to the log file."""
    return LOG_FILE


# Export logger for convenience
__all__ = ["logger", "setup_logger", "get_logger", "log_alert", "get_log_file_path"]
