#!/usr/bin/env python3
"""Script to generate preservation lookup tables.

This script can be used to manually regenerate the lookup tables
if needed. During normal installation, the tables are generated
automatically.

Usage:
    python -m scripts.generate_tables
    # or after making executable:
    ./scripts/generate_tables.py
"""

import sys

from preservationeval.install import generate_tables
from preservationeval.utils.logging import Environment, setup_logging

logger = setup_logging(__name__, env=Environment.PRODUCTION)


def main() -> int:
    """Generate preservation lookup tables.

    Returns:
        0 for success, 1 for failure
    """
    try:
        generate_tables()
        return 0
    except Exception as e:
        logger.error(f"Failed to generate tables: {e}")
        return 1


if __name__ == "__main__":
    sys.exit(main())
