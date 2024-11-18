"""Script to generate lookup tables for preservationeval."""

import sys
from pathlib import Path


def main() -> None:
    """Generate all lookup tables."""
    # Add src to path so we can import the package
    src_path = Path(__file__).parent.parent / "src"
    sys.path.insert(0, str(src_path))

    from preservationeval.tools.tables.generate_tables import generate_all_tables

    generate_all_tables()


if __name__ == "__main__":
    main()
