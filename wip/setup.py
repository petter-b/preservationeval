"""Setup script for preservationeval package."""

import importlib.util
import sys
from pathlib import Path


def import_module_from_path(module_path: Path) -> None:
    """Import and execute a Python module from a file path.

    Args:
        module_path: Path to the Python module to import
    """
    spec = importlib.util.spec_from_file_location("tables_gen", module_path)
    if spec is None or spec.loader is None:
        raise ImportError(f"Could not load module from {module_path}")

    module = importlib.util.module_from_spec(spec)
    sys.modules["tables_gen"] = module
    spec.loader.exec_module(module)

    # Call the generation function
    if hasattr(module, "generate_all_tables"):
        module.generate_all_tables()
    else:
        raise AttributeError("Module does not contain generate_all_tables()")


def main() -> None:
    """Generate lookup tables."""
    # Find and execute the table generation module directly
    src_path = Path(__file__).parent / "src" / "preservationeval" / "tools" / "tables"
    generate_module = src_path / "generate_tables.py"

    if not generate_module.exists():
        raise FileNotFoundError(f"Cannot find {generate_module}")

    # Add src directory to path so relative imports work
    sys.path.insert(0, str(src_path.parent.parent.parent))

    import_module_from_path(generate_module)


if __name__ == "__main__":
    main()
