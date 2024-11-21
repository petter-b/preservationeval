"""Configuration classes for structured logging.

Provides configuration classes and enums that define how logging should be
set up, separate from the actual logger implementation.
"""

import logging
from dataclasses import dataclass
from enum import Enum
from pathlib import Path

from preservationeval.utils.safepath import create_safe_path


class LogLevel(str, Enum):
    """Logging levels with string representations."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"

    def to_level(self) -> int:
        """Convert the LogLevel instance to a numeric logging level.

        Returns:
            int: The numeric logging level corresponding to this LogLevel.
        """
        # Use getattr to retrieve the numerical value associated with
        # the log level name stored in self.value
        return int(getattr(logging, self.value))


class Environment(str, Enum):
    """Valid logging environments."""

    DEVELOPMENT = "development"
    PRODUCTION = "production"
    TEST = "test"
    INSTALL = "install"

    @classmethod
    def default(cls) -> "Environment":
        """Get the default environment."""
        return cls.DEVELOPMENT

    @classmethod
    def from_string(cls, env: str) -> "Environment":
        """Create Environment from string, with helpful error message.

        Args:
            env: String representation of environment

        Returns:
            Corresponding Environment enum value

        Raises:
            ValueError: If env is not a valid environment name
        """
        try:
            return cls(env.lower())
        except ValueError:
            valid = ", ".join(e.value for e in cls)
            raise ValueError(
                f"Invalid environment '{env}'. Must be one of: {valid}"
            ) from None


@dataclass
class LogConfig:
    """Logging configuration settings."""

    # General settings
    level: LogLevel = LogLevel.DEBUG
    format: str = "%(asctime)s - %(levelname)s - %(name)s - %(funcName)s - %(message)s"
    date_format: str = "%Y-%m-%d %H:%M:%S"

    # Output settings
    console_output: bool = True
    file_output: bool = False
    log_dir: Path | None = None
    file_name: str = "preservationeval.log"

    # Behavior settings
    propagate: bool = False
    capture_warnings: bool = True

    def get_log_file_path(self) -> Path | None:
        """Get the full path for the log file if file output is enabled."""
        if not self.file_output or not self.log_dir:
            return None
        return create_safe_path(self.log_dir, self.file_name)


def get_default_config(env: str | Environment | None = None) -> LogConfig:
    """Get generic default logging configuration.

    Args:
        env: Environment name or Environment enum value

    Returns:
        Generic LogConfig with sensible defaults for the environment

    Raises:
        ValueError: If env is not a valid environment name
    """
    if env is None:
        env = Environment.default()
    elif isinstance(env, str):
        # Convert string to enum if needed
        env = Environment.from_string(env)

    base_configs = {
        Environment.DEVELOPMENT: LogConfig(
            level=LogLevel.DEBUG,
            console_output=True,
            file_output=True,
        ),
        Environment.PRODUCTION: LogConfig(
            level=LogLevel.INFO,
            console_output=False,
            file_output=True,
        ),
        Environment.TEST: LogConfig(
            level=LogLevel.DEBUG,
            console_output=True,
            file_output=True,
        ),
        Environment.INSTALL: LogConfig(
            level=LogLevel.INFO,
            console_output=True,
            file_output=True,
            format="%(asctime)s - %(name)s: %(message)s",
        ),
    }

    return base_configs[env]
