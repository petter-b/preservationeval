"""Logging configuration for preservationeval package."""

import json
import logging
import sys
from dataclasses import dataclass
from enum import Enum
from pathlib import Path
from typing import Any, Dict, Optional


class LogLevel(str, Enum):
    """Logging levels with string representations."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def to_level(self) -> int:
        """Convert to logging level."""
        return int(getattr(logging, self.value))


@dataclass
class LogConfig:
    """Logging configuration settings."""
    # General settings
    level: LogLevel = LogLevel.DEBUG
    format: str = (
        # "%(asctime)s - %(levelname)s - %(name)s - %(message)s"
        "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s"
    )
    date_format: str = "%Y-%m-%d %H:%M:%S"

    # Output settings
    console_output: bool = True
    file_output: bool = False
    log_dir: Optional[Path] = None
    file_name: str = "preservationeval.log"

    # Behavior settings
    propagate: bool = False
    capture_warnings: bool = True

    def get_log_file_path(self) -> Optional[Path]:
        """Get the full path for the log file if file output is enabled."""
        if not self.file_output or not self.log_dir:
            return None
        return self.log_dir / self.file_name


class StructuredLogger(logging.Logger):
    """Logger that supports structured logging."""

    def _log_structured(
        self,
        level: int,
        msg: str,
        extra: Optional[Dict[str, Any]] = None,
        **kwargs: Any
    ) -> None:
        """Log a message with structured data."""
        if extra is None:
            extra = {}

        # Create structured log entry
        log_entry = {
            "message": msg,
            "data": extra,
            **kwargs
        }

        # Convert to JSON string
        structured_msg = json.dumps(log_entry)
        super().log(level, structured_msg)


def setup_logging(
    name: Optional[str] = None,
    config: Optional[LogConfig] = None,
    env: str = "development"
) -> logging.Logger:
    """Configure and return a logger with given configuration.

    Args:
        name: Logger name. If None, returns the root logger
        config: Logging configuration. If None, uses default config
        env: Environment ("development" or "production")

    Returns:
        Configured logger instance

    Example:
        >>> logger = setup_logging("preservationeval.tables")
        >>> logger.debug("Processing table data")
    """
    # Use default config if none provided
    if config is None:
        config = LogConfig()

    # Register StructuredLogger
    logging.setLoggerClass(StructuredLogger)

    # Get or create logger
    logger = logging.getLogger(name or "root")

    # Clear existing handlers
    logger.handlers.clear()

    # Create formatter
    formatter = logging.Formatter(
        fmt=config.format,
        datefmt=config.date_format
    )

    # Add console handler if enabled
    if config.console_output:
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        console_handler.setLevel(config.level.to_level())
        logger.addHandler(console_handler)

    # Add file handler if enabled
    if config.file_output and (log_file := config.get_log_file_path()):
        # Create log directory if it doesn't exist
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setFormatter(formatter)
        file_handler.setLevel(config.level.to_level())
        logger.addHandler(file_handler)

    # Configure logger
    logger.setLevel(config.level.to_level())
    logger.propagate = config.propagate

    # Configure warning capture
    if config.capture_warnings:
        logging.captureWarnings(True)

    return logger


def get_default_config(env: str = "development") -> LogConfig:
    """Get default logging configuration for the given environment."""
    if env == "development":
        return LogConfig(
            level=LogLevel.DEBUG,
            console_output=True,
            file_output=True,
            log_dir=Path("logs"),
            file_name="preservationeval-dev.log"
        )
    elif env == "production":
        return LogConfig(
            level=LogLevel.INFO,
            console_output=False,
            file_output=True,
            log_dir=Path("/var/log/preservationeval"),
            file_name="preservationeval.log"
        )
    else:
        raise ValueError(f"Unknown environment: {env}")