"""Main installer logic for preservationeval tables."""

from pathlib import Path

from preservationeval.pyutils.logging import Environment, setup_logging

logger = setup_logging(__name__, env=Environment.INSTALL)


def install_tables(package_path: Path | None = None) -> None:
    """Install lookup tables for preservationeval.

    Args:
        package_path: Optional path where tables should be installed.
            If None, path will be automatically determined.

    Raises:
        ConnectionError: If unable to fetch JavaScript source
        ValueError: If table validation fails or path resolution is unsafe
        OSError: If unable to write generated module
        RuntimeError: If table verification fails
    """
    logger.info("Starting table generation...")
    try:
        from .generate_tables import generate_all_tables

        generate_all_tables()
        logger.info("\033[92m" "Tables generated successfully" "\033[0m")
    except Exception:
        logger.error("Failed to install tables: {e}")
        raise
