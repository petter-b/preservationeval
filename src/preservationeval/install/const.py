"""Constants for table installation."""

from typing import Final

# URLs and file info
DP_JS_URL: Final[str] = "http://www.dpcalc.org/dp.js"
NUM_EMC_DECIMALS: Final[int] = 1

# Package configuration
MODULE_NAME: Final[str] = "preservationeval.main"
SOURCE_DIR: Final[str] = "src"
TABLES_MODULE_NAME: Final[str] = "tables"
PACKAGE_ROOT_MARKERS: Final[list[str]] = ["pyproject.toml", "setup.py"]
