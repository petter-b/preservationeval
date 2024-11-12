import sys

from setuptools import setup
from setuptools.command.build_py import build_py

from preservationeval.logging import setup_logging

# Setup logging
logger = setup_logging(__name__)


def check_build_depenmdencies():
    """
    Verify that build dependencies are available.

    """
    missing = []
    try:
        import numpy
    except ImportError:
        missing.append("numpy")
    try:
        import requests
    except ImportError:
        missing.append("requests")

    if missing:
        msg = "Missing build dependencies: " + ", ".join(missing)
        logger.error(msg)
        logger.error("Install with: pip install %s", " ".join(missing))
        sys.exit(1)


class BuildPyCommand(build_py):
    """Custom build command to generate tables."""

    def run(self):
        # Generate tables before building
        from generate_tables import generate_tables_module

        generate_tables_module()
        build_py.run(self)


# setup.py - Handles installation
class BuildPyCommand(build_py):
    """Generate tables during installation"""
    def run(self):
        self.generate_tables_module()
        build_py.run(self)

# core.py - Robust table handling
try:
    from .tables_data import PI_DATA, EMC_DATA  # Generated
except ImportError:
    from .const import PITABLE, EMCTABLE  # Fallback

# validate_core.py - Testing framework
class PreservationTester:
    """Handles validation against JavaScript"""
    def run_validation(self):
        # Check dp.js updates
        # Run comparisons
        # Save test data

setup(
    # ... your other setup parameters ...
    cmdclass={
        "build_py": BuildPyCommand,
    },
)
