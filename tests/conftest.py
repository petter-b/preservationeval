from pathlib import Path
from typing import Any, Generator, Union

import pytest
from _pytest.config import Config, Notset
from _pytest.config.argparsing import Parser

from tests.validate_core import ValidationTest


def pytest_addoption(parser: Parser) -> None:
    """Add custom command line options to pytest.

    Args:
        parser: pytest command line parser
    """
    parser.addoption(
        "--force-update",
        action="store_true",
        default=False,
        help="Force update of validation test data",
    )


@pytest.fixture
def validation(request: pytest.FixtureRequest) -> ValidationTest:
    """Provide configured ValidationTest instance.

    Args:
        request: pytest request object containing command line options

    Returns:
        ValidationTest: Configured instance for JavaScript validation
    """
    option: Union[bool, Any, Notset] = request.config.getoption("--force-update")
    force_update: bool = bool(option) if option is not Notset else False
    return ValidationTest(force_update=force_update)


@pytest.fixture
def test_data_dir() -> Path:
    """Provide path to test data directory.

    Returns:
        Path: Directory containing test data
    """
    return Path(__file__).parent / "data"


def pytest_configure(config: Config) -> None:
    """Configure pytest with custom markers.

    Args:
        config: pytest configuration object
    """
    # Register custom markers to prevent pytest warnings
    config.addinivalue_line(
        "markers",
        "unit: marks unit tests that test individual components in isolation",
    )
    config.addinivalue_line(
        "markers",
        "integration: marks integration tests that test component interactions",
    )
    config.addinivalue_line(
        "markers",
        "validation: marks tests that validate against JavaScript reference implementation",  # noqa: E501
    )
    config.addinivalue_line(
        "markers",
        "slow: marks tests that take longer to execute",
    )


@pytest.fixture(autouse=True)
def _verify_test_data_dir(test_data_dir: Path) -> Generator[None, None, None]:
    """Ensure test data directory exists.

    Args:
        test_data_dir: Path to test data directory

    Yields:
        None
    """
    test_data_dir.mkdir(exist_ok=True)
    yield
    # Cleanup could go here if needed
