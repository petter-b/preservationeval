"""Validation framework for comparing JavaScript and Python implementations.

This module provides tools to validate the Python implementation against
the original JavaScript code from dpcalc.org. It handles:
- Downloading and versioning of the JavaScript source
- Generating and running test cases
- Comparing results between implementations
- Managing test data for offline validation
"""

# pylint: disable=missing-docstring
import hashlib
import json
import logging
import shutil
import subprocess
import sys
import tempfile
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import numpy as np
import requests

from preservationeval import emc, mold, pi
from preservationeval.const import DP_JS_URL
from preservationeval.logging import setup_logging
from tests.config import JS_CONFIG, ComparisonConfig, TestConfig
from tests.safepath import create_safe_path
from tests.templates import HTML_TEMPLATE, NODE_SCRIPT_TEMPLATE

# Setup logging
logger = setup_logging(__name__)

# Type aliases
Number = int | float
TestCase = list[float]  # [temperature, relative_humidity]
JSResult = dict[str, Number]  # {'pi': int, 'emc': float, 'mold': int}

# Constants
TEST_DATA_DIR = create_safe_path(
    Path(__file__).parent, "data"
)  # Go up one level to tests/data
DP_JS_PATH = create_safe_path(TEST_DATA_DIR, "dp.js")
TEST_DATA_PATH = create_safe_path(TEST_DATA_DIR, "test_data.json")


@dataclass
class DPJSInfo:
    """Information about dp.js file including content and version hash.

    Attributes:
        content: The JavaScript source code
        hash: SHA-256 hash of the content
        url: Source URL of the JavaScript
    """

    content: str
    hash: str
    url: str

    @classmethod
    def from_file(cls, path: Path) -> "DPJSInfo":
        """Create DPJSInfo from local file."""
        if not path.exists():
            raise FileNotFoundError(f"File not found: {path}")
        content = path.read_text()
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return cls(content=content, hash=hash_value, url=DP_JS_URL)  # Use the constant

    @classmethod
    def from_url(cls, url: str) -> "DPJSInfo":
        """Download and create DPJSInfo from URL.

        Args:
            url: URL to download dp.js from

        Returns:
            DPJSInfo instance with downloaded content

        Raises:
            requests.RequestException: If download fails
        """
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        content = response.text
        hash_value = hashlib.sha256(content.encode()).hexdigest()
        return cls(content=content, hash=hash_value, url=url)

    def save(self, path: Path) -> None:
        """Save dp.js content and hash information.

        Args:
            path: Path to save dp.js file

        The hash information is saved as a JSON file with the same name
        but with .hash extension, containing:
        - hash: SHA-256 hash of the content
        - url: Source URL
        - date: ISO format timestamp of when the file was saved
        """
        path.write_text(self.content)
        hash_info = {
            "hash": self.hash,
            "url": self.url,
            "date": datetime.now().isoformat(),
        }
        path.with_suffix(".hash").write_text(json.dumps(hash_info, indent=2))

    @staticmethod
    def load_hash(path: Path) -> str | None:
        """Load stored hash for a dp.js file.

        Args:
            path: Path to dp.js file (hash file should be alongside)

        Returns:
            Hash string if found, None otherwise
        """
        hash_path = path.with_suffix(".hash")
        if hash_path.exists():
            hash_info = json.loads(hash_path.read_text())
            return str(hash_info["hash"])
        else:
            return None


@dataclass
class ValidationDifference:
    """Represents a difference between JavaScript and Python implementations.

    Attributes:
        temp: Temperature value where difference occurred
        rh: Relative humidity value where difference occurred
        js_value: Value from JavaScript implementation
        py_value: Value from Python implementation
    """

    temp: float
    rh: float
    js_value: Number
    py_value: Number


@dataclass
class ValidationTest:
    """Handles validation of JavaScript vs Python implementation.

    This class manages the complete validation process including:
    - Setting up test environment
    - Maintaining dp.js and test data
    - Generating and running test cases
    - Comparing implementation results
    """

    def __init__(
        self,
        force_update: bool = False,
        temp_range: tuple[float, float, float] = (-30, 70, 0.5),
        rh_range: tuple[float, float, float] = (0, 100, 0.5),
    ):
        """Initialize validation test environment.

        Args:
            force_update: If True, force download of new dp.js
            temp_range: Tuple of (min, max, step) for temperature values
            rh_range: Tuple of (min, max, step) for relative humidity values
        """
        self.force_update = force_update
        self.temp_range = temp_range
        self.rh_range = rh_range
        self.temp_dir: Path | None = None

    def setup(self) -> None:
        """Set up test environment.

        Creates necessary directories and ensures dp.js is available.

        Raises:
            RuntimeError: If environment setup fails
        """
        TEST_DATA_DIR.mkdir(exist_ok=True)
        self._ensure_dpjs()
        self.temp_dir = Path(tempfile.mkdtemp())

    def cleanup(self) -> None:
        """Clean up temporary test environment."""
        if self.temp_dir and self.temp_dir.exists():
            shutil.rmtree(self.temp_dir)
            self.temp_dir = None

    def _ensure_dpjs(self) -> None:
        """Ensure dp.js is available and up to date.

        Downloads new version if:
        - force_update is True
        - File doesn't exist
        - Online version has changed (different hash)

        Raises:
            RuntimeError: If dp.js cannot be obtained
        """
        update_needed = self.force_update or not DP_JS_PATH.exists()

        if update_needed:
            try:
                logger.info("Downloading dp.js...")
                dpjs = DPJSInfo.from_url(DP_JS_URL)
                dpjs.save(DP_JS_PATH)
                logger.info("Downloaded and saved dp.js")
            except requests.RequestException as e:
                logger.error("Failed to download dp.js: %s", e)
                if not DP_JS_PATH.exists():
                    raise RuntimeError("No dp.js available") from e

    def _generate_test_cases(self, num_cases: int) -> list[TestCase]:
        """Generate random test cases within configured ranges.

        Args:
            num_cases: Number of test cases to generate

        Returns:
            List of [temperature, relative_humidity] pairs
        """
        rng = np.random.default_rng()

        # Generate temperature values
        t_min, t_max, t_step = self.temp_range
        t_steps = int((t_max - t_min) / t_step)
        t_indices = rng.integers(0, t_steps + 1, size=num_cases)
        temps = t_min + (t_indices * t_step)

        # Generate RH values
        rh_min, rh_max, rh_step = self.rh_range
        rh_steps = int((rh_max - rh_min) / rh_step)
        rh_indices = rng.integers(0, rh_steps + 1, size=num_cases)
        rhs = rh_min + (rh_indices * rh_step)

        return [[float(t), float(rh)] for t, rh in zip(temps, rhs, strict=False)]

    def _save_test_data(self, cases: list[list[float]], results: list[dict]) -> None:
        """Save test data for future use."""
        data = {
            "generated": datetime.now().isoformat(),
            "dpjs_hash": DPJSInfo.load_hash(DP_JS_PATH),
            "cases": cases,
            "results": results,
        }
        path = create_safe_path(TEST_DATA_DIR, "test_data.json")
        path.write_text(json.dumps(data, indent=2))

    def load_test_data(self) -> tuple[list[list[float]], list[dict]]:
        """Load saved test cases and verify dp.js hash."""
        test_data_path = create_safe_path(TEST_DATA_DIR, "test_data.json")
        if not test_data_path.exists():
            raise FileNotFoundError("Test data file not found")

        with open(test_data_path) as f:
            test_data = json.load(f)

        # Verify dp.js hash matches
        current_hash = DPJSInfo.load_hash(DP_JS_PATH)
        if current_hash != test_data["dpjs_hash"]:
            logger.warning("Test data was generated with different dp.js version")
            if not self.force_update:
                logger.warning("Use force_update=True to regenerate test data")

        return test_data["cases"], test_data["results"]

    def run_tests(
        self, num_cases: int = TestConfig.num_tests, use_cached: bool = True
    ) -> dict[str, list[ValidationDifference]]:
        """Run complete validation test suite.

        Args:
            num_cases: Number of random test cases to generate
            use_cached: Whether to try using cached test data

        Returns:
            Dictionary with keys 'pi', 'emc', 'mold' containing lists of
            differences found between implementations

        Raises:
            RuntimeError: If validation process fails
        """
        try:
            # Check Node.js installation
            self._check_node_installation()

            # Set up test environment
            self.setup()

            # Try to use cached data
            if use_cached and not self.force_update:
                try:
                    test_cases, js_results = self.load_test_data()
                    logger.info("Using cached test data")
                except (FileNotFoundError, json.JSONDecodeError) as e:
                    logger.warning("Could not use cached data: %s", e)
                    logger.info("Generating new test cases")
                    test_cases = self._generate_test_cases(num_cases)
                    logger.info("Running JavaScript tests...")
                    js_results = self._run_javascript_tests(test_cases)
                    # Save new test data
                    self._save_test_data(test_cases, js_results)
            else:
                logger.info("Generating new test cases")
                test_cases = self._generate_test_cases(num_cases)
                logger.info("Running JavaScript tests...")
                js_results = self._run_javascript_tests(test_cases)
                # Save test data
                self._save_test_data(test_cases, js_results)

            logger.info("Running Python tests...")
            py_results = self._run_python_tests(test_cases)

            # Compare results
            differences = self._compare_results(js_results, py_results)

            # Log summary
            total_diffs = sum(len(diffs) for diffs in differences.values())
            if total_diffs == 0:
                logger.info("All tests passed!")
            else:
                logger.warning("Found %d differences:", total_diffs)
                for func, diffs in differences.items():
                    if diffs:
                        logger.warning("%s: %d differences", func.upper(), len(diffs))

            return differences

        except Exception as e:
            logger.error("Validation failed: %s", str(e), exc_info=True)
            raise
        finally:
            self.cleanup()

    def _run_javascript_tests(self, test_cases: list[TestCase]) -> list[JSResult]:
        """Run test cases through JavaScript implementation.

        Args:
            test_cases: List of [temperature, relative_humidity] pairs

        Returns:
            List of results from JavaScript implementation

        Raises:
            RuntimeError: If JavaScript execution fails
        """
        if self.temp_dir is None:
            raise RuntimeError("Test environment not set up")

        # Create package.json
        package_json_path = create_safe_path(self.temp_dir, "package.json")
        with package_json_path.open("w") as f:
            json.dump(JS_CONFIG["package_json"], f, indent=2)

        # Create test files
        test_html_path = create_safe_path(self.temp_dir, "test.html")
        test_html_path.write_text(HTML_TEMPLATE)

        test_js_path = create_safe_path(self.temp_dir, "run_tests.js")
        test_js_path.write_text(NODE_SCRIPT_TEMPLATE)

        # Copy dp.js to temp directory
        dp_js_dest = create_safe_path(self.temp_dir, "dp.js")
        shutil.copy(DP_JS_PATH, dp_js_dest)

        npm_path = shutil.which("npm")
        if npm_path is None:
            raise RuntimeError("npm executable not found")

        node_path = shutil.which("node")
        if node_path is None:
            raise RuntimeError("node executable not found")

        # Run npm install
        try:
            # Install dependencies
            subprocess.run(  # noqa: S603
                [npm_path, "install"],
                cwd=self.temp_dir,
                check=True,
                capture_output=True,
                text=True,
            )

            # Run tests
            process = subprocess.Popen(  # noqa: S603
                [node_path, str(test_js_path), str(test_html_path)],
                cwd=self.temp_dir,
                stdin=subprocess.PIPE,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
            )

            # Send test cases to Node.js process
            stdout, stderr = process.communicate(input=json.dumps(test_cases))

            if process.returncode != 0:
                raise RuntimeError(f"JavaScript execution failed: {stderr}")

            try:
                return json.loads(stdout)  # type: ignore
            except json.JSONDecodeError as e:
                logger.error("Failed to parse JavaScript output: %s", stdout)
                raise RuntimeError("Invalid JSON output from JavaScript") from e

        except subprocess.CalledProcessError as e:
            raise RuntimeError(f"Failed to run JavaScript tests: {e}") from e

    def _run_python_tests(self, test_cases: list[TestCase]) -> list[JSResult]:
        """Run test cases through Python implementation.

        Args:
            test_cases: List of [temperature, relative_humidity] pairs

        Returns:
            List of results from Python implementation
        """
        return [
            {
                "temp": t,
                "rh": rh,
                "pi": pi(t, rh),
                "emc": emc(t, rh),
                "mold": mold(t, rh),
            }
            for t, rh in test_cases
        ]

    def _compare_results(
        self, js_results: list[JSResult], py_results: list[JSResult]
    ) -> dict[str, list[ValidationDifference]]:
        """Compare JavaScript and Python results.

        Args:
            js_results: Results from JavaScript implementation
            py_results: Results from Python implementation

        Returns:
            Dictionary with function names as keys and lists of differences
        """
        differences: dict[str, list[ValidationDifference]] = {
            "pi": [],
            "emc": [],
            "mold": [],
        }

        for js, py in zip(js_results, py_results, strict=False):
            t, rh = js["temp"], js["rh"]

            # Compare PI values
            if js["pi"] != py["pi"]:
                differences["pi"].append(
                    ValidationDifference(t, rh, js["pi"], py["pi"])
                )

            # Compare EMC values (with tolerance)
            if abs(js["emc"] - py["emc"]) > ComparisonConfig.emc_tolerance:
                differences["emc"].append(
                    ValidationDifference(t, rh, js["emc"], py["emc"])
                )

            # Compare Mold values
            if js["mold"] != py["mold"]:
                differences["mold"].append(
                    ValidationDifference(t, rh, js["mold"], py["mold"])
                )

        return differences

    @staticmethod
    def _check_node_installation() -> None:
        """Check if Node.js and npm are available.

        Raises:
            RuntimeError: If Node.js or npm is not installed
        """
        npm_path = shutil.which("npm")
        if npm_path is None:
            raise RuntimeError("npm executable not found")

        node_path = shutil.which("node")
        if node_path is None:
            raise RuntimeError("node executable not found")
        try:
            # Check Node.js
            node_version = subprocess.run(  # noqa: S603
                [node_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug("Found Node.js: %s", node_version.stdout.strip())

            # Check npm
            npm_version = subprocess.run(  # noqa: S603
                [npm_path, "--version"],
                capture_output=True,
                text=True,
                check=True,
            )
            logger.debug("Found npm: %s", npm_version.stdout.strip())

        except (subprocess.CalledProcessError, FileNotFoundError) as e:
            raise RuntimeError(
                "Node.js and npm are required but not found. "
                "Please install them from https://nodejs.org/"
            ) from e


def main() -> None:
    """Run validation as a standalone script."""
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    )

    try:
        validator = ValidationTest(force_update=False)
        differences = validator.run_tests(
            num_cases=TestConfig.num_tests,
            use_cached=True,
        )

        # Report results
        total_diffs = sum(len(diffs) for diffs in differences.values())
        if total_diffs == 0:
            logger.info("All tests passed!")
        else:
            logger.warning("Found %d differences:", total_diffs)
            for func, diffs in differences.items():
                if diffs:
                    logger.warning(
                        "%s: %d differences (showing first %d)",
                        func.upper(),
                        len(diffs),
                        ComparisonConfig.max_differences,
                    )
                    for diff in diffs[: COMPARISON_CONFIG["max_differences_shown"]]:  # type: ignore # noqa E501
                        logger.warning(
                            "  T=%.1f, RH=%.1f: JS=%.6f, PY=%.6f",
                            diff.temp,
                            diff.rh,
                            diff.js_value,
                            diff.py_value,
                        )

        sys.exit(1 if total_diffs > 0 else 0)

    except Exception as e:
        logger.error("Validation failed: %s", e)
        sys.exit(1)


if __name__ == "__main__":
    main()
