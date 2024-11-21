# src/preservationeval/config.py
"""Configuration facilities for preservationeval package.

Provides default configurations for various package components including
logging, cache directories, and other settings.
"""

from pathlib import Path

from .utils.logging import LogConfig, get_default_config
from .utils.safepath import create_safe_path


def get_preservationeval_log_config(env: str = "development") -> LogConfig:
    """Get preservationeval-specific logging configuration.

    Builds on the generic defaults but adds preservationeval-specific paths
    and settings.
    """
    # Get generic base config
    config = get_default_config(env)

    # Add preservationeval-specific paths
    base_dir = create_safe_path(Path.home(), ".preservationeval", "logs")
    config.log_dir = create_safe_path(base_dir, env)
    config.file_name = f"preservationeval-{env}.log"

    return config


# Could add other configuration functions here
# def get_cache_dir(env: str = "development") -> Path:
#     """Get cache directory for preservationeval."""
#     ...
