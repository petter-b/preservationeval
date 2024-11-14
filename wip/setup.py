"""Setup configuration for preservationeval package."""

import sys
from pathlib import Path
from typing import List

from setuptools import find_packages, setup
from setuptools.command.build_py import build_py


def check_build_dependencies() -> None:
    """Verify that build dependencies are available.

    Raises:
        SystemExit: If any required dependencies are missing.
    """
    missing: List[str] = []
    
    required_packages = ["numpy", "requests"]
    for package in required_packages:
        try:
            __import__(package)
        except ImportError:
            missing.append(package)

    if missing:
        msg = "Missing build dependencies: " + ", ".join(missing)
        print(f"ERROR: {msg}", file=sys.stderr)
        print(
            f"Install with: pip install {' '.join(missing)}", 
            file=sys.stderr
        )
        sys.exit(1)


class BuildPyCommand(build_py):
    """Custom build command to generate lookup tables during installation."""

    def run(self) -> None:
        """Execute the build command.
        
        This method:
        1. Checks for required build dependencies
        2. Adds install directory to Python path
        3. Generates the lookup tables
        4. Runs the standard build process
        
        Raises:
            SystemExit: If table generation fails
        """
        check_build_dependencies()
        
        # Add install directory to Python path
        install_dir = Path(__file__).parent / "install"
        sys.path.insert(0, str(install_dir))
        
        # Generate tables before building
        try:
            from generate_tables import generate_all_tables
            generate_all_tables()
        except Exception as e:
            print(f"ERROR: Failed to generate tables: {e}", file=sys.stderr)
            sys.exit(1)
        finally:
            # Remove install directory from path
            sys.path.pop(0)
            
        # Run the standard build
        build_py.run(self)


setup(
    name="preservationeval",
    version="0.1.0",  # Update with your version
    packages=find_packages(where="src"),
    package_dir={"": "src"},
    python_requires=">=3.11",
    install_requires=[
        "numpy",
        "requests",
        # Add other requirements
    ],
    cmdclass={
        "build_py": BuildPyCommand,
    },
    # Add other setup parameters as needed
)
