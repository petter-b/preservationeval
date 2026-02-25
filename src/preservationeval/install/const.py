"""Configuration used for table installation and generation.

This module defines all constant values used during the table generation process,
including URLs, file paths, and configuration parameters.

Note:
    All constants are marked Final to prevent modification during runtime.
"""

from typing import Final

# Source data configuration
# Note: URL and decimals were previously configurable via [tool.preservationeval]
# in pyproject.toml. Now hardcoded here as the single source of truth.
DP_JS_URL: Final[str] = "http://www.dpcalc.org/dp.js"
DP_JS_SHA256: Final[str] = (
    "e47db658c389b1eb3e1b93f9cb94aad47c255b30a837b034068ea724a8eda79b"
)
NUM_EMC_DECIMALS: Final[int] = 1  # Number of decimal places for EMC values (0.0-30.0)

# Package structure configuration
MODULE_NAME: Final[str] = "preservationeval"  # Target module for tables
SOURCE_DIR: Final[str] = "src"  # Source directory relative to package root
TABLES_MODULE_NAME: Final[str] = "tables"  # Generated module name

# Package root detection
PACKAGE_ROOT_MARKERS: Final[tuple[str, ...]] = (
    "pyproject.toml",
)  # Files that indicate package root

# Network retry configuration
MAX_DOWNLOAD_RETRIES: Final[int] = 3
RETRY_BACKOFF_BASE: Final[float] = 1.0  # seconds; doubles each retry
DOWNLOAD_TIMEOUT: Final[int] = 30  # seconds

# JavaScript execution timeout
JS_EXECUTION_TIMEOUT_SEC: Final[float] = 30.0  # seconds per eval call
