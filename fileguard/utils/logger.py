"""Logging utility for FileGuard.

Provides simple, clean logging for verbose and diagnostic output without
polluting standard CLI output in default mode.
"""

import sys
from typing import Optional


class Logger:
    """Configurable console logger for CLI verbosity."""

    def __init__(self, verbose: bool = False, stream=None) -> None:
        self.verbose = verbose
        self.stream = stream if stream is not None else sys.stdout

    def info(self, message: str) -> None:
        """Print an informational message if verbose mode is enabled."""
        if self.verbose:
            print(f"[INFO] {message}", file=self.stream)

    def debug(self, message: str) -> None:
        """Print a debug message if verbose mode is enabled."""
        if self.verbose:
            print(f"[DEBUG] {message}", file=self.stream)

    def warning(self, message: str) -> None:
        """Print a warning message."""
        print(f"[WARN] {message}", file=self.stream)

    def error(self, message: str) -> None:
        """Print an error message."""
        print(f"[ERROR] {message}", file=sys.stderr)


# Global default logger instance
_default_logger = Logger()


def get_logger() -> Logger:
    """Return the global logger instance."""
    return _default_logger


def set_verbose(verbose: bool) -> None:
    """Enable or disable verbosity on the global logger."""
    _default_logger.verbose = verbose


def log_info(message: str) -> None:
    """Helper to log an info message using the global logger."""
    _default_logger.info(message)


def log_debug(message: str) -> None:
    """Helper to log a debug message using the global logger."""
    _default_logger.debug(message)
