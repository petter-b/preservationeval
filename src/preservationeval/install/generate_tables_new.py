"""Generate lookup tables for preservationeval.

This module handles the complete table generation and installation process:
1. Downloads source data from IPI's Dew Point Calculator
2. Parses JavaScript code to extract table data
3. Generates and validates lookup tables
4. Installs tables as a Python module
"""

from importlib import import_module, reload
from pathlib import Path

from preservationeval.pyutils.logging import setup_logging
from preservationeval.pyutils.paths import PathError, find_package_root, get_module_path
from preservationeval.table_types import EMCTable, MoldTable, PITable

from .const import (
    DP_JS_URL,
    MODULE_NAME,
    PACKAGE_ROOT_MARKERS,
    SOURCE_DIR,
    TABLES_MODULE_NAME,
)
from .export import generate_tables_module
from .parse import fetch_and_validate_tables

logger = setup_logging(__name__)


class TableGenerationError(Exception):
    """Base exception for table generation errors."""
    
    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        super().__init__(message)
        self.original_error = original_error


def verify_tables(module_path: str) -> bool:
    """Verify that tables were generated and initialized correctly."""
    try:
        tables_module = import_module(module_path)
        tables_module = reload(tables_module)
        
        if not getattr(tables_module, "_INITIALIZED", False):
            raise TableGenerationError("Tables generated but not initialized")
        
        logger.info(f"Verified import of {module_path}")
        return True
        
    except ImportError as e:
        raise TableGenerationError(f"Failed to import {module_path}", e)
    except Exception as e:
        raise TableGenerationError("Table verification failed", e)


def generate_tables(package_path: Path | None = None) -> None:
    """Generate and install lookup tables for preservationeval."""
    try:
        # Get installation path
        if package_path is None:
            root_path = find_package_root(Path(__file__), PACKAGE_ROOT_MARKERS)
            package_path = get_module_path(root_path, SOURCE_DIR, MODULE_NAME)
            
        logger.info("Fetching and validating tables...")
        pi_table, emc_table, mold_table = fetch_and_validate_tables(DP_JS_URL)
        
        logger.info("Generating tables module...")
        generate_tables_module(
            pi_table=pi_table,
            emc_table=emc_table,
            mold_table=mold_table,
            module_name=TABLES_MODULE_NAME,
            output_path=package_path,
        )
        
        # Verify installation
        module_path = f"{MODULE_NAME}.{TABLES_MODULE_NAME}"
        verify_tables(module_path)
        
        logger.info("\033[92mTables generated successfully\033[0m")
        
    except (PathError, Exception) as e:
        error_msg = f"Table generation failed: {e}"
        logger.error(error_msg)
        raise TableGenerationError(error_msg, e)


if __name__ == "__main__":
    generate_tables()
