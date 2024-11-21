"""Structured logger implementation and setup functions.

Provides the actual logger implementation and setup functionality, using
the configuration classes defined in config.py.
"""

import json
import logging
import sys
from typing import Any

from .config import Environment, LogConfig, get_default_config


class StructuredLogger(logging.Logger):
    """Logger that supports structured logging."""

    def _log_structured(
        self,
        level: int,
        msg: str,
        extra: dict[str, Any] | None = None,
        **kwargs: Any,
    ) -> None:
        """Log a message with structured data."""
        if extra is None:
            extra = {}

        # Create structured log entry
        log_entry = {"message": msg, "data": extra, **kwargs}

        # Convert to JSON string
        structured_msg = json.dumps(log_entry)
        super().log(level, structured_msg)


def setup_logging(
    name: str | None = None,
    config: LogConfig | None = None,
    env: str | Environment | None = None,
) -> logging.Logger:
    """Configure and return a logger with given configuration.

    Args:
        name: Logger name. If None, returns the root logger
        config: Logging configuration. If None, uses env-specific default
        env: Environment to use for default config. Can be string or Environment enum

    Returns:
        Configured logger instance

    Raises:
        ValueError: If env is not a valid environment name

    Example:
        >>> logger = setup_logging("myapp", env="development")
        >>> logger = setup_logging("myapp", env=Environment.default())
    """
    if env is None:
        env = Environment.default()
    elif isinstance(env, str):
        # Convert string to enum if needed
        env = Environment.from_string(env)
    # Ensure we have a valid LogConfig
    local_config: LogConfig  # Declare type explicitly
    if config is None:
        try:
            local_config = get_default_config(env)
        except ValueError:
            local_config = get_default_config(Environment.default())
    else:
        local_config = config

    # Register StructuredLogger
    logging.setLoggerClass(StructuredLogger)

    # Get or create logger
    logger = logging.getLogger(name or "root")

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt=local_config.format, datefmt=local_config.date_format
    )

    # Add console handler if enabled
    if local_config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(local_config.level.to_level())
        logger.addHandler(console_handler)

    # Add file handler if enabled
    if local_config.file_output:
        log_file = local_config.get_log_file_path()
        if log_file is not None:
            log_file.parent.mkdir(parents=True, exist_ok=True)
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            file_handler.setLevel(local_config.level.to_level())
            logger.addHandler(file_handler)

    # Configure logger
    logger.setLevel(local_config.level.to_level())
    logger.propagate = local_config.propagate

    # Configure warning capture
    if local_config.capture_warnings:
        logging.captureWarnings(True)

    return logger
