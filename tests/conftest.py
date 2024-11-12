# tests/conftest.py
from pathlib import Path

import pytest

from tests.validate_core import ValidationTest


@pytest.fixture
def validation() -> ValidationTest:
    """Provide configured ValidationTest instance."""
    from .validate_core import ValidationTest

    return ValidationTest(force_update=False)


@pytest.fixture
def test_data_dir() -> Path:
    """Provide path to test data directory."""
    return Path(__file__).parent / "data"
