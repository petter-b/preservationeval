"""Test module for preservationeval.core_functions."""

from typing import Any

import pytest

from preservationeval.core_functions import emc, mold, pi
from preservationeval.types import (
    HumidityError,
    IndexRangeError,
    PreservationError,
    TemperatureError,
)

from .config import ComparisonConfig

# Test data from validated cases
#
# Each tuple in the list represents a validated case with the following structure:
#   (temp, rh, expected_pi, expected_emc, expected_mold)  # noqa: ERA001
#
VALIDATED_CASES = [
    (23.0, 2.5, 102, 0.8, 0),  # Low RH case
    (27.5, 74.0, 9, 13.8, 46),  # High mold risk case
    (32.5, 80.0, 5, 15.4, 13),  # Moderate risk case
    (-13.0, 33.0, 7840, 6.6, 0),  # Cold temperature case
    (20.0, 70.0, 26, 13.1, 165),  # High mold risk case
    (23.5, 52.5, 25, 9.6, 0),  # Moderate case
    (14.0, 30.5, 161, 6.4, 0),  # Low risk case
]


@pytest.mark.validation
class TestValidatedCases:
    """Test against known validated cases."""

    @pytest.mark.parametrize(
        "temp,rh,expected_pi,expected_emc,expected_mold", VALIDATED_CASES
    )
    def test_validated_cases(
        self,
        temp: float,
        rh: float,
        expected_pi: int,
        expected_emc: float,
        expected_mold: int,
    ) -> None:
        """Test all functions against validated cases."""
        # Test PI calculation
        assert pi(temp, rh) == expected_pi, f"PI mismatch at T={temp}, RH={rh}"

        # Test EMC calculation (with small tolerance for floating point)
        calculated_emc = emc(temp, rh)
        assert abs(calculated_emc - expected_emc) < ComparisonConfig.emc_tolerance, (
            f"EMC mismatch at T={temp}, RH={rh}"
        )

        # Test mold calculation
        assert mold(temp, rh) == expected_mold, (
            f"Mold risk mismatch at T={temp}, RH={rh}"
        )


@pytest.mark.unit
class TestInputValidation:
    """Test input validation for all functions."""

    @pytest.mark.parametrize(
        "temp,rh,expected_error",
        [
            ("20", 50, TypeError),  # Invalid temperature type
            (20, "50", TypeError),  # Invalid RH type
            (None, 50, TypeError),  # None temperature
            (20, None, TypeError),  # None RH
        ],
    )
    def test_type_validation(
        self, temp: Any, rh: Any, expected_error: type[Exception]
    ) -> None:
        """Test type validation for all functions."""
        with pytest.raises(expected_error):
            pi(temp, rh)
        with pytest.raises(expected_error):
            emc(temp, rh)
        with pytest.raises(expected_error):
            mold(temp, rh)

    def test_value_validation(self) -> None:
        """Test value range validation."""
        # Test with values from the validation set that we know should work
        valid_temp, valid_rh = VALIDATED_CASES[0][:2]
        assert pi(valid_temp, valid_rh) > 0
        assert emc(valid_temp, valid_rh) >= 0
        assert mold(valid_temp, valid_rh) >= 0


@pytest.mark.integration
class TestErrorHandling:
    """Test error handling and logging."""

    def test_error_handling_invalid_rh(self) -> None:
        """Test handling of invalid RH values."""
        with pytest.raises(ValueError) as exc_info:
            pi(20.0, -1.0)
        assert "Relative humidity must be between" in str(exc_info.value)

    def test_error_handling_invalid_temp(self) -> None:
        """Test handling of invalid temperature values."""
        with pytest.raises(ValueError) as exc_info:
            pi(-273.16, 50.0)  # Below absolute zero
        assert "Temperature must be between" in str(exc_info.value)

    def test_internal_error_handling(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test handling of internal lookup errors."""

        # Create a mock LookupTable that raises an error
        class MockLookupTable:
            def __getitem__(self, key: Any) -> Any:
                raise RuntimeError("Mock table error")

        # Replace the real table with our mock
        mock_table = MockLookupTable()
        monkeypatch.setattr("preservationeval.core_functions.pi_table", mock_table)

        # This should now trigger our mock error and be wrapped
        with pytest.raises(PreservationError) as exc_info:
            pi(20.0, 50.0)
        assert "Unexpected error" in str(exc_info.value)


@pytest.mark.validation
class TestBoundaryConditions:
    """Test behavior at boundary conditions."""

    @pytest.mark.parametrize(
        "temp,rh,expected_pi,expected_emc,expected_mold",
        [
            # From your test_data.json, cases near boundaries:
            (-18.0, 43.5, 9999, 8.1, 0),  # Near min temp
            (61.5, 3.5, 1, 0.7, 0),  # Near max temp
            (28.5, 0.0, 48, 0.0, 0),  # Min RH
            (44.0, 97.0, 1, 24.1, 5),  # Near max RH
        ],
    )
    def test_boundary_values(
        self,
        temp: float,
        rh: float,
        expected_pi: int,
        expected_emc: float,
        expected_mold: int,
    ) -> None:
        """Test calculations near boundary values match reference data."""
        assert pi(temp, rh) == expected_pi
        assert abs(emc(temp, rh) - expected_emc) < ComparisonConfig.emc_tolerance
        assert mold(temp, rh) == expected_mold


@pytest.mark.unit
class TestSpecificErrorPaths:
    """Test specific error paths in core functions."""

    def test_emc_temperature_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test EMC handling of TemperatureError."""

        class MockTable:
            def __getitem__(self, key: Any) -> Any:
                raise TemperatureError("Mock temperature error")

        monkeypatch.setattr("preservationeval.core_functions.emc_table", MockTable())

        with pytest.raises(TemperatureError) as exc_info:
            emc(20.0, 50.0)
        assert "Temperature out of bounds" in str(exc_info.value)

    def test_emc_humidity_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test EMC handling of HumidityError."""

        class MockTable:
            def __getitem__(self, key: Any) -> Any:
                raise HumidityError("Mock humidity error")

        monkeypatch.setattr("preservationeval.core_functions.emc_table", MockTable())

        with pytest.raises(HumidityError) as exc_info:
            emc(20.0, 50.0)
        assert "RH out of bounds" in str(exc_info.value)

    def test_mold_index_range_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test mold handling of IndexRangeError."""

        class MockTable:
            def __getitem__(self, key: Any) -> Any:
                raise IndexRangeError("Mock index range error")

        monkeypatch.setattr("preservationeval.core_functions.mold_table", MockTable())

        # Should return 0 instead of raising error
        assert mold(20.0, 50.0) == 0.0

    def test_mold_unexpected_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test mold handling of unexpected errors."""

        class MockTable:
            def __getitem__(self, key: Any) -> Any:
                raise RuntimeError("Mock unexpected error")

        monkeypatch.setattr("preservationeval.core_functions.mold_table", MockTable())

        with pytest.raises(PreservationError) as exc_info:
            mold(20.0, 50.0)
        assert "Unexpected error calculating mold risk" in str(exc_info.value)

    def test_pi_temperature_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test PI handling of TemperatureError."""

        class MockTable:
            def __getitem__(self, key: Any) -> Any:
                raise TemperatureError("Mock temperature error")

        monkeypatch.setattr("preservationeval.core_functions.pi_table", MockTable())

        with pytest.raises(TemperatureError) as exc_info:
            pi(20.0, 50.0)
        assert "Temperature out of bounds" in str(exc_info.value)

    def test_pi_humidity_error(self, monkeypatch: pytest.MonkeyPatch) -> None:
        """Test PI handling of HumidityError."""

        class MockTable:
            def __getitem__(self, key: Any) -> Any:
                raise HumidityError("Mock humidity error")

        monkeypatch.setattr("preservationeval.core_functions.pi_table", MockTable())

        with pytest.raises(HumidityError) as exc_info:
            pi(20.0, 50.0)
        assert "RH out of bounds" in str(exc_info.value)
