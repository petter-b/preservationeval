"""Path management for downloaded and cached files.

This module handles path management for downloaded files and test data,
providing different behavior for development and production installations.
"""

import os
import sys
from pathlib import Path
from typing import Final

# Check if we're in development mode (pip install -e .)
IS_DEV_INSTALL: Final = os.environ.get("PRESERVATIONEVAL_DEV") == "1" or any(
    arg in sys.argv for arg in ["-e", "--editable"]
)


def get_cache_dir() -> Path:
    """Get the appropriate cache directory based on installation type.

    Returns:
        Path to cache directory:
        - In dev: project_root/tools/cache/
        - In prod: temporary directory that will be cleaned up
    """
    if IS_DEV_INSTALL:
        # Use persistent cache in development
        cache_dir = Path(__file__).parent.parent / "cache"
        cache_dir.mkdir(exist_ok=True)
        return cache_dir
    else:
        # Use temporary directory in production
        import tempfile

        return Path(tempfile.mkdtemp(prefix="preservationeval-"))


def get_dp_js_path() -> Path:
    """Get path for cached dew.js file."""
    return get_cache_dir() / "dew.js"


def get_validation_data_path() -> Path:
    """Get path for validation test data."""
    return get_cache_dir() / "validation_data.json"
