"""Tests for return type correctness of core functions."""

import json

import pytest

from preservationeval import emc, mold, pi


@pytest.mark.unit
class TestReturnTypes:
    """Verify core functions return native Python types, not numpy scalars."""

    def test_pi_returns_python_int(self) -> None:
        """pi() should return a native Python int."""
        result = pi(20.0, 50.0)
        assert type(result) is int, f"Expected int, got {type(result)}"

    def test_emc_returns_python_float(self) -> None:
        """emc() should return a native Python float."""
        result = emc(20.0, 50.0)
        assert type(result) is float, f"Expected float, got {type(result)}"

    def test_mold_in_range_returns_python_int(self) -> None:
        """mold() should return a native Python int when in table range."""
        result = mold(25.0, 80.0)
        assert type(result) is int, f"Expected int, got {type(result)}"

    def test_mold_out_of_range_returns_python_int(self) -> None:
        """mold() should return int 0 when outside table range, not float 0.0."""
        result = mold(-10.0, 30.0)
        assert type(result) is int, f"Expected int, got {type(result)}"
        assert result == 0

    def test_pi_json_serializable(self) -> None:
        """pi() result should be JSON-serializable without custom encoder."""
        result = pi(20.0, 50.0)
        json.dumps({"pi": result})  # Should not raise TypeError

    def test_emc_json_serializable(self) -> None:
        """emc() result should be JSON-serializable without custom encoder."""
        result = emc(20.0, 50.0)
        json.dumps({"emc": result})  # Should not raise TypeError

    def test_mold_json_serializable(self) -> None:
        """mold() result should be JSON-serializable without custom encoder."""
        result = mold(25.0, 80.0)
        json.dumps({"mold": result})  # Should not raise TypeError
