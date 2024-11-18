"""Setup script for preservationeval table installation."""

import sys
from pathlib import Path
from typing import ClassVar

from setuptools import Command, setup


class GenerateTables(Command):
    """Custom command to generate tables."""

    description = "generate preservationeval lookup tables"
    user_options: ClassVar[list] = []

    def initialize_options(self) -> None:
        """Set default values for options."""
        pass

    def finalize_options(self) -> None:
        """Set final values for options."""
        pass

    def run(self) -> None:
        """Run command."""
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

        try:
            from preservationeval.install.installer import install_tables
            from preservationeval.pyutils.logging import setup_logging

            logger = setup_logging(__name__)

            logger.info("\033[94m" "Installing tables..." "\033[0m")

            install_tables()

        finally:
            sys.path.pop(0)


setup(
    cmdclass={
        "generate_tables": GenerateTables,
    },
)
