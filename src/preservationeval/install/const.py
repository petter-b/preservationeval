"""Configuration used for table installation and generation.

This module defines all constant values used during the table generation process,
including URLs, file paths, and configuration parameters.

Note:
    All constants are marked Final to prevent modification during runtime.
"""

from typing import Final

# Source data configuration
DP_JS_URL: Final[str] = "http://www.dpcalc.org/dp.js"
NUM_EMC_DECIMALS: Final[int] = 1  # Number of decimal places for EMC values (0.0-30.0)

# Package structure configuration
MODULE_NAME: Final[str] = "preservationeval"  # Target module for tables
SOURCE_DIR: Final[str] = "src"  # Source directory relative to package root
TABLES_MODULE_NAME: Final[str] = "tables"  # Generated module name

# Package root detection
PACKAGE_ROOT_MARKERS: Final[tuple[str, ...]] = (
    "pyproject.toml",
    "setup.py",
)  # Files that indicate package root
