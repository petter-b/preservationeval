"""Script to install lookup tables during installation.

This script generates and installs the lookup tables required by preservationeval.
It is intended to be run during the installation process, but can also be run manually
to regenerate the tables if needed.

Usage:
    python -m install
"""

import sys
from pathlib import Path

from setuptools.command.build_py import build_py


class CustomBuildPy(build_py):
    """Custom build command that generates tables during build."""

    def run(self) -> None:
        """Run the build command with table generation."""
        # Add src to Python path temporarily
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

        print("Installing tables...")
        # Import and run the installer
        from preservationeval.install.installer import install_tables

        install_tables()

        # Remove src from path
        sys.path.pop(0)
