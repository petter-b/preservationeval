"""Generate lookup tables for preservationeval during installation."""

import sys
from importlib import import_module, reload
from pathlib import Path

from preservationeval.types import EMCTable, MoldTable, PITable
from preservationeval.utils.logging import Environment, setup_logging
from preservationeval.utils.safepath import create_safe_path

from .const import (
    DP_JS_URL,
    MODULE_NAME,
    PACKAGE_ROOT_MARKERS,
    SOURCE_DIR,
    TABLES_MODULE_NAME,
)
from .export import generate_tables_module
from .parse import fetch_and_validate_tables

logger = setup_logging(__name__, env=Environment.INSTALL)


def find_package_root() -> Path:
    """Find the root directory of the package.

    Returns:
        Path to the package root directory.

    Raises:
        OSError: If package root cannot be found.
        ValueError: If path resolution is unsafe.
    """
    current = Path(__file__).resolve()
    for parent in [current, *current.parents]:
        if any((parent / marker).exists() for marker in PACKAGE_ROOT_MARKERS):
            return parent
    raise OSError("Cannot find package root directory")


def get_module_path(root_path: Path) -> Path:
    """Get the path where the module should be generated.

    Args:
        root_path: Package root directory

    Returns:
        Path where module should be generated

    Raises:
        OSError: If module path cannot be determined
        ValueError: If path resolution is unsafe
    """
    try:
        module_path = create_safe_path(
            root_path, SOURCE_DIR, MODULE_NAME.replace(".", "/")
        )
        if not module_path.exists():
            raise OSError(f"Module path not found: {module_path}")
        return module_path
    except ValueError:
        logger.error("Unsafe path resolution attempted")
        raise


def verify_tables() -> bool:
    """Verify that tables were generated and initialized correctly.

    Returns:
        True if tables are initialized correctly.

    Raises:
        RuntimeError: If tables are not initialized correctly.
    """
    try:
        # Import or reload the tables module
        module_path = f"{MODULE_NAME}.{TABLES_MODULE_NAME}"
        try:
            tables_module = import_module(module_path)
            tables_module = reload(tables_module)
        except ImportError as e:
            raise RuntimeError(f"Failed to import {module_path}") from e

        if not getattr(tables_module, "_INITIALIZED", False):
            raise RuntimeError("Tables generated but not initialized")

        logger.info(f"Verified import of {module_path}.")

        return True

    except Exception as e:
        logger.error("Table verification failed: %s", e)
        raise


def generate_tables() -> tuple[PITable, EMCTable, MoldTable]:
    """Generate lookup tables from IPI JavaScript source.

    Returns:
        Tuple of (PITable, EMCTable, MoldTable)

    Raises:
        ConnectionError: If unable to fetch JavaScript source
        ValueError: If table validation fails
    """
    logger.info(f"Fetching and validating tables from {DP_JS_URL}")
    return fetch_and_validate_tables(DP_JS_URL)


def generate_all_tables() -> None:
    """Generate all lookup tables and save them as a Python module.

    Raises:
        ConnectionError: If unable to fetch JavaScript source
        ValueError: If table validation fails or path resolution is unsafe
        OSError: If unable to write generated module
        RuntimeError: If table verification fails
    """
    try:
        # 1. Generate tables
        pi_table, emc_table, mold_table = generate_tables()

        # 2. Find output path
        root_path = find_package_root()
        output_path = get_module_path(root_path)

        # 3. Generate the module
        generate_tables_module(
            pi_table=pi_table,
            emc_table=emc_table,
            mold_table=mold_table,
            module_name=TABLES_MODULE_NAME,
            output_path=output_path,
        )

        # 4. Verify generated tables
        verify_tables()

    except Exception as e:
        logger.error("Failed to generate tables: %s", e)
        print(f"Error generating tables: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    generate_all_tables()
