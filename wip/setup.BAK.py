"""Setup script for preservationeval package."""

import logging

from setuptools import setup
from setuptools.command.develop import develop
from setuptools.command.install import install

logger = logging.getLogger(__name__)


def generate_tables() -> None:
    """Generate lookup tables during package installation."""
    try:
        from preservationeval.install import install_tables

        install_tables()
        logger.info("Successfully generated lookup tables")
    except ImportError as e:
        logger.error("Could not import install_tables: %s", e)
        raise
    except Exception as e:
        logger.error("Failed to generate tables: %s", e)
        raise


class PostDevelopCommand(develop):
    """Post-installation for development mode."""

    def run(self) -> None:
        """Run development installation and generate tables."""
        develop.run(self)  # First run normal development installation
        self.execute(generate_tables, [], msg="Generating lookup tables")


class PostInstallCommand(install):
    """Post-installation for installation mode."""

    def run(self) -> None:
        """Run installation and generate tables."""
        install.run(self)  # First run normal installation
        self.execute(generate_tables, [], msg="Generating lookup tables")


setup(
    cmdclass={
        "develop": PostDevelopCommand,
        "install": PostInstallCommand,
    },
)
