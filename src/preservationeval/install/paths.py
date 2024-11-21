"""Path utilities for package installation and configuration.

This module provides utilities for safely handling paths during package
installation and configuration, including finding package roots and
creating safe paths within the package structure.
"""

from collections.abc import Sequence
from pathlib import Path

from preservationeval.utils.logging import Environment, setup_logging

logger = setup_logging(__name__, env=Environment.INSTALL)


class PathError(Exception):
    """Base exception for path-related errors."""

    def __init__(self, message: str, path: Path | None = None) -> None:
        """Initialize with error message and optional path.

        Args:
            message: Error description
            path: Path that caused the error
        """
        super().__init__(message)
        self.path = path


def find_package_root(
    start_path: Path,
    markers: Sequence[str],
) -> Path:
    """Find the root directory of a package.

    Args:
        start_path: Path to start searching from
        markers: Files/directories that indicate package root

    Returns:
        Path to the package root directory

    Raises:
        PathError: If package root cannot be found
    """
    current = start_path.resolve()
    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in markers):
            logger.debug(f"Found package root at: {parent}")
            return parent
    raise PathError("Cannot find package root directory", current)


def get_module_path(
    root_path: Path,
    source_dir: str,
    module_path: str,
) -> Path:
    """Get the path where a module should be located.

    Args:
        root_path: Package root directory
        source_dir: Source directory name (e.g., 'src')
        module_path: Dotted module path (e.g., 'package.submodule')

    Returns:
        Path where module should be located

    Raises:
        PathError: If module path cannot be determined or is unsafe
    """
    try:
        module_parts = module_path.split(".")
        full_path = root_path / source_dir / Path(*module_parts)
        resolved_path = full_path.resolve()

        # Safety check - make sure we didn't escape root
        if not str(resolved_path).startswith(str(root_path.resolve())):
            raise PathError(
                "Module path escapes package root",
                resolved_path,
            )

        if not resolved_path.exists():
            raise PathError(
                f"Module path does not exist: {resolved_path}",
                resolved_path,
            )

        return resolved_path

    except Exception as e:
        if isinstance(e, PathError):
            raise
        raise PathError(f"Error resolving module path: {e}", full_path) from e
