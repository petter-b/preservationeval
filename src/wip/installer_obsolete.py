"""Main installer logic for preservationeval tables.

This module manages the table generation and installation process by:
1. Determining the correct installation path
2. Triggering table generation from JavaScript source
3. Installing generated tables into the package

The installer can be run during package installation or manually if
tables need to be regenerated.
"""

from pathlib import Path
from typing import NoReturn

from preservationeval.utils.logging import setup_logging

logger = setup_logging(__name__)


class InstallError(Exception):
    """Base exception for installation errors."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize with message and optional original error."""
        super().__init__(message)
        self.original_error = original_error


def _handle_install_error(e: Exception) -> NoReturn:
    """Handle installation errors with proper logging and re-raising.

    Args:
        e: The caught exception

    Raises:
        InstallError: Wrapped installation error
    """
    error_msg = f"Table installation failed: {e}"
    logger.error(error_msg)
    raise InstallError(error_msg, e)


def install_tables(package_path: Path | None = None) -> None:
    """Install lookup tables for preservationeval.

    This function manages the complete table installation process:
    1. Validates and resolves installation path
    2. Triggers table generation from source
    3. Installs generated tables into the package

    Args:
        package_path: Optional path where tables should be installed.
            If None, path will be automatically determined.

    Raises:
        InstallError: If installation fails for any reason, wrapping the original error:
            - ConnectionError: If unable to fetch JavaScript source
            - ValueError: If table validation fails or path resolution is unsafe
            - OSError: If unable to write generated module
            - RuntimeError: If table verification fails
    """
    logger.info("Starting table generation...")
    try:
        from .generate_tables_old import generate_all_tables

        generate_all_tables()
        logger.info("\033[92mTables generated successfully\033[0m")
    except Exception as e:
        _handle_install_error(e)
