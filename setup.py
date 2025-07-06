"""Setup script for preservationeval."""

import logging
import subprocess
import sys
from pathlib import Path

from setuptools import Distribution, setup
from setuptools.command.build_py import build_py
from setuptools.command.install import install

logging.basicConfig(
    level=logging.INFO, format="%(asctime)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)


class CustomDistribution(Distribution):
    """Custom distribution for preservationeval.

    This distribution class is used to set the package version from Git tags.
    """

    def __init__(self, attrs: dict[str, str] | None = None) -> None:
        """Initialize the distribution with version information."""
        attrs = attrs or {}
        logger.debug("Initializing distribution")
        logger.debug(f"version: {attrs.get('version', '')!s}")
        self._write_version_file()
        if attrs.get("version", "unknown") == "unknown":
            attrs["version"] = self._get_version()
        logger.debug(f"version: {attrs['version']!s}")
        super().__init__(attrs)

    def _get_git_version(self) -> str | None:
        """Get the current version of the package from Git tags."""
        curr_path = Path(__file__).resolve().parent
        git_base = curr_path / ".git"
        if not git_base.is_dir():
            return None

        try:
            output = (
                subprocess.check_output(
                    ["git", "describe", "--tags", "--long"],  # noqa: S607
                    cwd=curr_path,
                )
                .decode("utf-8")
                .split("-")
            )
            return output[0] if int(output[1]) == 0 else f"{output[0]}-{output[1]}"
        except subprocess.CalledProcessError:
            logger.warning("Failed to get version from Git tags")
            return None

    def _write_version_file(self) -> None:
        """Write version string to src/preservationeval/_version.py."""
        src_path = Path(__file__).resolve().parent / "src"
        sys.path.insert(0, str(src_path))

        try:
            from preservationeval._version import (  # noqa: PLC0415
                version as file_version,
            )
        except ImportError:
            file_version = "unknown"

        git_version = self._get_git_version()

        if git_version is not None and git_version != file_version:
            version_file = src_path / "preservationeval" / "_version.py"
            try:
                with version_file.open("w") as f:
                    f.write(f'version = "{git_version}"\n')
            except OSError:
                logger.error(f"Failed to write version file: {version_file}")

    def _get_version(self) -> str:
        """Read the version from the generated _version.py file."""
        src_path = Path(__file__).resolve().parent / "src"
        sys.path.insert(0, str(src_path))

        try:
            from preservationeval._version import version  # noqa: PLC0415

            return str(version)
        except ImportError:
            logger.warning("Failed to import version from _version.py")
            return "0.0.0"  # fallback version
        finally:
            sys.path.pop(0)  # Remove the temporarily added path


class CustomBuildPy(build_py):
    """Custom build command that generates lookup tables during build."""

    def _generate_tables(self) -> None:
        """Generate lookup tables for preservationeval."""
        # Add src to Python path temporarily
        src_path = Path(__file__).resolve().parent / "src"
        sys.path.insert(0, str(src_path))

        try:
            if not self.dry_run:
                from preservationeval.install.generate_tables import (  # noqa: PLC0415
                    generate_tables,
                )

                generate_tables()
        except Exception as e:
            logger.error(f"Error generating preservationeval.tables: {e}")
            raise  # This will cause the build to fail

        finally:
            # Remove src from path
            sys.path.pop(0)

    def run(self) -> None:
        """Run the build command with table generation.

        This command performs the following steps:
        1. Generates preservation lookup tables (PI, EMC, Mold)
        2. Runs standard build process
        """
        self.execute(
            self._generate_tables,
            (),
            msg="Generating preservationeval.tables module...",
        )
        build_py.run(self)


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
            super().run()
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
    distclass=CustomDistribution,
    cmdclass=cmdclass_dict,
)
