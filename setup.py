"""Setup script for preservationeval."""

import logging
import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py
from setuptools.command.install import install

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomBuildPy(build_py):
    """Custom build command that generates lookup tables during build.

    This command performs the following steps:
    1. Adds src directory to Python path
    2. Generates preservation lookup tables (PI, EMC, Mold)
    3. Removes src from path
    4. Runs standard build process
    """

    def run(self) -> None:
        """Run the build command with table generation.

        Raises:
            ImportError: If required modules cannot be imported
            TableGenerationError: If table generation fails
        """
        # Add src to Python path temporarily
        src_path = Path(__file__).parent / "src"
        sys.path.insert(0, str(src_path))

        try:
            if not self.dry_run:
                from preservationeval.install.generate_tables import generate_tables

                logger.debug(
                    "\033[94m" "Generating preservation lookup tables..." "\033[0m"
                )
                generate_tables()
                logger.debug(
                    "\033[92m" "Table generation completed successfully" "\033[0m"
                )
            build_py.run(self)
        except Exception as e:
            logger.error(f"Error during build: {e}")
            raise  # This will cause the build to fail

        finally:
            # Remove src from path
            sys.path.pop(0)

        # Run standard build
        super().run()


class CustomInstall(install):
    """Custom installation class that checks for dependencies after installation.

    This class extends the standard installation class and adds a dependency check.
    If any critical dependencies are missing, an ImportError is raised.
    """

    def run(self) -> None:
        """Run the installation command with dependency checking.

        This command first runs the standard installation using install.run(self).
        After installation, it checks that all critical dependencies are present.
        If any critical dependencies are missing, an ImportError is raised.
        """
        try:
            super().run()  # type: ignore
            self.check_dependencies()
        except Exception as e:
            logger.error(f"Error during installation: {e}")
            raise

    def check_dependencies(self) -> None:
        """Check that all critical dependencies are present after installation.

        This function checks that all required modules are available after
        installation. If any critical dependencies are missing, an ImportError
        is raised.

        Note: Critical dependencies are modules that are required for the
        package to function correctly. If any of these modules are missing,
        the package cannot be used.

        Raises:
            ImportError: If any critical dependencies are missing
        """
        required_modules = [
            "preservationeval.tables",
        ]
        for module in required_modules:
            try:
                __import__(module)
            except ImportError as e:
                raise ImportError(
                    f"Critical module '{module}' not found. "
                    "Installation may be incomplete."
                ) from e


cmdclass_dict: dict[str, type[build_py | install]] = {
    "build_py": CustomBuildPy,
    "install": CustomInstall,
}

setup(
    cmdclass=cmdclass_dict,
)
