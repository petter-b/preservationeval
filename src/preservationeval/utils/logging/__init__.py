"""Structured logging facilities for preservationeval.

This package provides a flexible logging system that supports structured logging
with both console and file output. It includes configuration management and
environment-specific defaults.

Key Components:
    LogLevel: Enum for available log levels (DEBUG, INFO, WARNING, ERROR, CRITICAL)
    LogConfig: Configuration class for logger settings
    Environment: Enum for supported environments (development, production, etc.)
    StructuredLogger: Logger supporting structured data output
    setup_logging: Main function to configure and get a logger
    get_default_config: Get environment-specific default configuration

Basic Usage:
    >>> from preservationeval.utils.logging import setup_logging
    >>> logger = setup_logging("myapp")
    >>> logger.info("Processing started", extra={"temp": 20, "rh": 50})

Configuration:
    >>> from preservationeval.utils.logging import LogConfig, LogLevel
    >>> config = LogConfig(
    ...     level=LogLevel.DEBUG,
    ...     console_output=True,
    ...     file_output=True,
    ... )
    >>> logger = setup_logging("myapp", config=config)

Environment-specific Setup:
    >>> from preservationeval.utils.logging import Environment, get_default_config
    >>> config = get_default_config(Environment.PRODUCTION)
    >>> logger = setup_logging("myapp", config=config)

    # Or more directly:
    >>> logger = setup_logging("myapp", env=Environment.PRODUCTION)

Notes:
    - Default environment is development
    - Log files are created in the configured log directory
    - Structured data is JSON-formatted
    - Warning capture is enabled by default
"""

from .config import Environment, LogConfig, LogLevel, get_default_config
from .structured import StructuredLogger, setup_logging

__all__ = [
    "Environment",
    "LogConfig",
    "LogLevel",
    "StructuredLogger",
    "get_default_config",
    "setup_logging",
]
