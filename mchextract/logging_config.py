"""Logging configuration module for mch-extract."""

import logging
import sys


class ColoredFormatter(logging.Formatter):
    """Custom formatter that adds colors to log messages based on level."""

    # ANSI color codes
    COLORS = {
        "DEBUG": "\033[36m",  # Cyan
        "INFO": "\033[0m",  # Default (no color)
        "WARNING": "\033[33m",  # Yellow
        "ERROR": "\033[31m",  # Red
        "CRITICAL": "\033[31m",  # Red
        "RESET": "\033[0m",  # Reset to default
    }

    def format(self, record: logging.LogRecord) -> str:
        # Get the color for this log level
        color = self.COLORS.get(record.levelname, self.COLORS["RESET"])
        reset = self.COLORS["RESET"]

        # Format the message
        formatted_message = super().format(record)

        # Apply color only to WARNING and ERROR levels for user-facing messages
        if record.levelname in ["WARNING", "ERROR", "CRITICAL"]:
            return f"{color}{formatted_message}{reset}"

        return formatted_message


def setup_logging(verbose: bool = False) -> None:
    """Set up logging configuration.

    Args:
        verbose: If True, enable debug logging to stderr. If False, only show INFO and above to stdout.
    """
    # Create a logger
    logger = logging.getLogger()
    logger.setLevel(logging.DEBUG if verbose else logging.INFO)

    # Clear any existing handlers
    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    # Create console handler for user-facing messages (INFO and above)
    console_handler = logging.StreamHandler(sys.stderr)
    console_handler.setLevel(logging.INFO)

    # Create colored formatter for user-facing messages
    user_formatter = ColoredFormatter("%(message)s")
    console_handler.setFormatter(user_formatter)

    # Add handler to logger
    logger.addHandler(console_handler)

    # If verbose, set level to DEBUG
    if verbose:
        console_handler.setLevel(logging.DEBUG)
        debug_formatter = ColoredFormatter("[%(levelname)s] %(name)s: %(message)s")
        console_handler.setFormatter(debug_formatter)
