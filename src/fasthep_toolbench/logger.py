"""Standard logger configurations for the FAST-HEP packages"""

from __future__ import annotations

import sys

import loguru


def logger_with_logfile(logfile: str) -> loguru.Logger:
    """
    Create a logger that writes to both the console and a specified log file.

    Args:
        logfile (str): The path to the log file.

    Returns:
        loguru.Logger: Configured logger instance.
    """
    logger = loguru.logger
    logger.remove()  # Remove default logger
    logger.add(sys.stderr, level="INFO")  # Log to console
    logger.add(
        logfile, level="DEBUG", rotation="10 MB", retention="10 days"
    )  # Log to file
    return logger
