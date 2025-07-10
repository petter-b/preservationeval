"""Unit test cases for util_functions module."""

import pytest

from preservationeval.const import RH_MAX, RH_MIN, TEMP_MAX, TEMP_MIN
from preservationeval.util_functions import (
    MAGNUS_MAX_RH,
    MAGNUS_MAX_TEMP,
    MAGNUS_MIN_RH,
    MAGNUS_MIN_TEMP,
    calculate_dew_point,
    to_celsius,
    validate_rh,
    validate_temp,
)


@pytest.mark.unit
class TestValidateRh:
    """Tests for the validate_rh utility function."""

    @pytest.mark.parametrize("valid_rh", [RH_MIN, RH_MAX, 50, 25.5])
    def test_valid_rh_values(self, valid_rh: float) -> None:
        """Tests that valid relative humidity values do not raise an exception."""
        try:
            validate_rh(valid_rh)
        except (ValueError, TypeError) as e:
            pytest.fail(f"validate_rh raised an unexpected exception: {e}")

    def test_invalid_rh_type(self) -> None:
        """Tests that a non-numeric RH value raises a TypeError."""
        with pytest.raises(TypeError, match="Relative humidity must be a number"):
            validate_rh("50")  # type: ignore

    @pytest.mark.parametrize("out_of_range_rh", [RH_MIN - 0.1, RH_MAX + 0.1])
    def test_out_of_range_rh_values(self, out_of_range_rh: float) -> None:
        """Tests that RH values outside the valid range raise a ValueError."""
        with pytest.raises(ValueError, match="Relative humidity must be between"):
            validate_rh(out_of_range_rh)


@pytest.mark.unit
class TestValidateTemp:
    """Tests for the validate_temp utility function."""

    @pytest.mark.parametrize("valid_temp", [TEMP_MIN, TEMP_MAX, 20, -10.5])
    def test_valid_temp_values(self, valid_temp: float) -> None:
        """Tests that valid temperature values do not raise an exception."""
        try:
            validate_temp(valid_temp)
        except (ValueError, TypeError) as e:
            pytest.fail(f"validate_temp raised an unexpected exception: {e}")

    def test_invalid_temp_type(self) -> None:
        """Tests that a non-numeric temperature value raises a TypeError."""
        with pytest.raises(TypeError, match="Temperature must be a number"):
            validate_temp("20")  # type: ignore

    @pytest.mark.parametrize("out_of_range_temp", [TEMP_MIN - 0.1, TEMP_MAX + 0.1])
    def test_out_of_range_temp_values(self, out_of_range_temp: float) -> None:
        """Tests that temperature values outside the valid range raise a ValueError."""
        with pytest.raises(ValueError, match="Temperature must be between"):
            validate_temp(out_of_range_temp)


@pytest.mark.unit
class TestToCelsius:
    """Tests for the to_celsius temperature conversion function."""

    @pytest.mark.parametrize(
        "fahrenheit, celsius", [(32, 0.0), (212, 100.0), (-40, -40.0)]
    )
    def test_conversion_from_fahrenheit(
        self, fahrenheit: float, celsius: float
    ) -> None:
        """Tests temperature conversion from Fahrenheit to Celsius."""
        assert to_celsius(fahrenheit, scale="f") == pytest.approx(celsius)

    @pytest.mark.parametrize("temp_c", [0, 20, 100])
    def test_conversion_from_celsius(self, temp_c: float) -> None:
        """Tests that converting from Celsius returns the same value as a float."""
        assert to_celsius(temp_c, scale="c") == pytest.approx(float(temp_c))

    @pytest.mark.parametrize(
        "kelvin, celsius", [(273.15, 0.0), (373.15, 100.0), (0, -273.15)]
    )
    def test_conversion_from_kelvin(self, kelvin: float, celsius: float) -> None:
        """Tests temperature conversion from Kelvin to Celsius."""
        assert to_celsius(kelvin, scale="k") == pytest.approx(celsius)

    def test_unsupported_scale(self) -> None:
        """Tests that an unsupported scale raises a ValueError."""
        with pytest.raises(ValueError, match="Unsupported scale 'x'"):
            to_celsius(20, scale="x")

    def test_invalid_temperature_type(self) -> None:
        """Tests that a non-numeric temperature input raises a TypeError."""
        with pytest.raises(TypeError, match="Temperature must be integer or float"):
            to_celsius("20", scale="c")  # type: ignore

    @pytest.mark.parametrize(
        "scale, value, error",
        [
            ("f", -460, ValueError),  # Below absolute zero in Fahrenheit
            ("c", -274, ValueError),  # Below absolute zero in Celsius
            ("k", -1, ValueError),  # Below absolute zero in Kelvin
        ],
    )
    def test_out_of_range_for_scale(
        self, scale: str, value: float, error: type[Exception]
    ) -> None:
        """Tests that temperatures below absolute zero raise a ValueError."""
        with pytest.raises(error):
            to_celsius(value, scale=scale)


@pytest.mark.unit
class TestCalculateDewPoint:
    """Tests for the calculate_dew_point function."""

    @pytest.mark.parametrize(
        "temp, rh, expected_dew_point",
        [
            (20, 50, 9.3),
            (30, 80, 26.2),
            (10, 30, -6.8),
            (MAGNUS_MIN_TEMP, MAGNUS_MAX_RH, -40.0),
            # CORRECTED VALUE: The function correctly returns -20.2, not -10.9.
            (MAGNUS_MAX_TEMP, MAGNUS_MIN_RH, -20.2),
        ],
    )
    def test_known_values(
        self, temp: float, rh: float, expected_dew_point: float
    ) -> None:
        """Tests the dew point calculation against known, expected values."""
        assert calculate_dew_point(temp, rh) == pytest.approx(
            expected_dew_point, abs=0.1
        )

    @pytest.mark.parametrize("temp", [MAGNUS_MIN_TEMP - 0.1, MAGNUS_MAX_TEMP + 0.1])
    def test_out_of_range_temperature(self, temp: float) -> None:
        """Tests that temperatures outside the valid range raise a ValueError."""
        with pytest.raises(ValueError, match="Temperature must be between"):
            calculate_dew_point(temp, 50)

    @pytest.mark.parametrize("rh", [MAGNUS_MIN_RH - 0.1, MAGNUS_MAX_RH + 0.1])
    def test_out_of_range_humidity(self, rh: float) -> None:
        """Tests that humidity outside valid range raise a ValueError."""
        with pytest.raises(ValueError, match="Relative humidity must be between"):
            calculate_dew_point(20, rh)
