# tests/conftest.py
from pathlib import Path

import pytest


@pytest.fixture
def validation():
    """Provide configured ValidationTest instance."""
    from .validate_core import ValidationTest

    return ValidationTest(force_update=False)


@pytest.fixture
def test_data_dir():
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def test_data_dir() -> Path:
    """Return path to test data directory."""
    return Path(__file__).parent / "data"


@pytest.fixture
def preservation_tester():
    """Return PreservationTester instance configured for testing."""
    from .validate_core import PreservationTester

    return PreservationTester(use_local=True)
