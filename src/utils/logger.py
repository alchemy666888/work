"""Logging configuration"""

import logging
import colorlog
from src.utils.config import config


def setup_logger(name: str) -> logging.Logger:
    """Set up a colored logger"""

    handler = colorlog.StreamHandler()
    handler.setFormatter(
        colorlog.ColoredFormatter(
            "%(log_color)s%(asctime)s [%(levelname)s] %(name)s: %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
            log_colors={
                "DEBUG": "cyan",
                "INFO": "green",
                "WARNING": "yellow",
                "ERROR": "red",
                "CRITICAL": "red,bg_white",
            },
        )
    )

    logger = colorlog.getLogger(name)
    logger.addHandler(handler)
    logger.setLevel(getattr(logging, config.monitoring.log_level))

    return logger
