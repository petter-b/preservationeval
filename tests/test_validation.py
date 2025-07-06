"""Validation tests comparing Python implementation against JavaScript reference.

This module provides two types of validation tests:
1. test_against_javascript: Runs random test cases through both implementations
2. test_specific_cases: Tests specific cases from saved test data

To run these tests:
    pytest test_validation.py               # Run all validation tests
    pytest test_validation.py -v            # Run with verbose output
    pytest test_validation.py -k javascript # Run only JavaScript comparison
    pytest test_validation.py -k specific   # Run only specific cases

Requirements:
    - Node.js and npm must be installed
    - Test data directory must exist with:
        - dp.js: JavaScript reference implementation
        - test_data.json: Saved test cases and results
"""

import json
from pathlib import Path
from typing import Any

from preservationeval import emc, mold, pi
from tests.config import ComparisonConfig
from tests.validate_core import ValidationTest


def test_against_javascript(validation: ValidationTest) -> None:
    """Test Python implementation against JavaScript.

    Args:
        validation: ValidationTest fixture providing configured test instance
    """
    differences = validation.run_tests()

    assert not differences["pi"], f"PI calculations differ: {differences['pi']}"
    assert not differences["emc"], f"EMC calculations differ: {differences['emc']}"
    assert not differences["mold"], f"Mold calculations differ: {differences['mold']}"


def test_specific_cases(test_data_dir: Path) -> None:
    """Test specific known cases.

    Args:
        test_data_dir: Path fixture providing test data directory
    """
    test_data_path = test_data_dir / "test_data.json"
    assert test_data_path.exists(), f"Test data file not found at {test_data_path}"

    with Path.open(test_data_path) as f:
        data: dict[str, Any] = json.load(f)

    cases: list[list[float]] = data["cases"]
    results: list[dict[str, float]] = data["results"]

    for case, expected in zip(cases, results, strict=False):
        t, rh = case
        assert pi(t, rh) == expected["pi"], f"PI mismatch at T={t}, RH={rh}"
        assert abs(emc(t, rh) - expected["emc"]) < ComparisonConfig.emc_tolerance, (
            f"EMC mismatch at T={t}, RH={rh}"
        )
        assert mold(t, rh) == expected["mold"], f"Mold mismatch at T={t}, RH={rh}"
