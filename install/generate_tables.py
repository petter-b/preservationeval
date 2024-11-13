"""Generate lookup tables for preservationeval during installation."""

# TODO: Inlcude DP_JS_HASH in the genrted module
# TODO: Validate the generated tables and include _VALIDATED in the generated module

import sys
from pathlib import Path

from preservationeval.const import DP_JS_URL

from .export import generate_tables_module
from .parse import fetch_and_validate_tables


def generate_all_tables() -> None:
    """Generate all lookup tables and save them as a Python module."""
    try:
        # 1. Fetch and validate tables
        pi_table, emc_table, mold_table = fetch_and_validate_tables(DP_JS_URL)

        # 2. Determine output path
        src_path = Path(__file__).parent.parent / "src" / "preservationeval"

        # 3. Generate the module
        generate_tables_module(
            pi_table=pi_table,
            emc_table=emc_table,
            mold_table=mold_table,
            module_name="tables",
            output_path=src_path,
        )
        print("Successfully generated lookup tables")

    except Exception as e:
        print(f"Error generating tables: {e}", file=sys.stderr)
        raise


if __name__ == "__main__":
    generate_all_tables()
