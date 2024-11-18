"""Setup configuration for preservationeval package."""

import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


def check_build_dependencies() -> None:
    """Verify that build dependencies are available.

    Raises:
        SystemExit: If any required dependencies are missing.
    """
    missing: list[str] = []

    required_packages = ["numpy", "requests"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        msg = "Missing build dependencies: " + ", ".join(missing)
        print(f"ERROR: {msg}", file=sys.stderr)
        print(f"Install with: pip install {' '.join(missing)}", file=sys.stderr)
        sys.exit(1)


class BuildPyCommand(build_py):
    """Custom build command to generate lookup tables during installation."""

    def run(self) -> None:
        """Execute the build command.

        Generates the lookup tables before proceeding with the standard build.
        """
        check_build_dependencies()

        # Add both project root and src to Python path
        project_root = Path(__file__).parent.absolute()
        src_dir = project_root / "src"
        install_dir = project_root / "install"

        sys.path.insert(0, str(src_dir))
        sys.path.insert(0, str(project_root))

        try:
            # Import and run table generation
            from install.generate_tables import generate_all_tables

            generate_all_tables()
        except Exception as e:
            print(f"ERROR: Failed to generate tables: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Clean up path
            sys.path.pop(0)
            sys.path.pop(0)

        # Run the standard build
        build_py.run(self)


setup(
    cmdclass={
        "build_py": BuildPyCommand,
    },
)
