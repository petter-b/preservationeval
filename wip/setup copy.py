"""Setup script for preservationeval."""

import sys
from pathlib import Path

from setuptools import setup
from setuptools.command.build_py import build_py


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
            from preservationeval.install.generate_tables import generate_tables
            from preservationeval.pyutils.logging import Environment, setup_logging

            logger = setup_logging(__name__, env=Environment.INSTALL)

            logger.debug("\033[94mGenerating preservation lookup tables...\033[0m")
            generate_tables()
            logger.debug("\033[92mTable generation completed successfully\033[0m")

        except Exception as e:
            logger.error(f"Failed to generate tables: {e}")
            raise

        finally:
            # Remove src from path
            sys.path.pop(0)

        # Run standard build
        super().run()


cmdclass_dict: dict[str, type[build_py]] = {
    "build_py": CustomBuildPy,
}

setup(
    cmdclass=cmdclass_dict,
    # Other setup parameters should be moved to pyproject.toml
)
