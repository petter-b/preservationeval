"""Build script for preservationeval."""

import logging

from setuptools.build_meta import *

logging.basicConfig(level=logging.INFO, format="%(asctime)s - %(name)s: %(message)s")
logger = logging.getLogger(__name__)


def build_wheel(wheel_directory, config_settings=None, metadata_directory=None):  # type: ignore # noqa E501
    try:
        from preservationeval.install.generate_tables import generate_tables

        logger.debug("\033[94m" "Generating preservation lookup tables..." "\033[0m")
        generate_tables()
        logger.debug("\033[92m" "Table generation completed successfully" "\033[0m")

        # Call the original build_wheel function
        return __build_wheel(wheel_directory, config_settings, metadata_directory)
    except Exception as e:
        logger.error(f"Error during build: {e}")
        raise


# Override the build_wheel function
__build_wheel = globals()["build_wheel"]
globals()["build_wheel"] = build_wheel
