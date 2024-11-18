"""Setup script for preservationeval."""

import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


class CustomBuildPy(build_py):
    """Custom build command that generates tables during build."""

    def run(self) -> None:
        """Run the build command with table generation."""
        # Add src to Python path temporarily
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

        from preservationeval.install.installer import install_tables
        from preservationeval.pyutils.logging import setup_logging

        logger = setup_logging(__name__)

        logger.info("\033[94m" "Installing tables..." "\033[0m")

        install_tables()

        # Remove src from path
        sys.path.pop(0)

        # Then do the regular build
        super().run()


setup(
    cmdclass={
        "build_py": CustomBuildPy,
    },
)
