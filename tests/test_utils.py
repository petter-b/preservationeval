"""Unit tests for preservationeval.util_functions module.

Functions:
    test_validate_rh: Test the validate_rh function by checking that it does not raise
    an exception for valid relative humidity values.
    test_validate_temp: Test the validate_temp function by checking that it does not
    raise an exception for valid temperature values.

These tests ensure that the utility functions in the preservationeval.utils module are
functioning correctly.
"""

import pytest

from preservationeval.const import TEMP_MAX
from preservationeval.util_functions import (
    MAGNUS_ACCURACY,
    calculate_dew_point,
    to_celsius,
    validate_rh,
    validate_temp,
)


@pytest.mark.unit
def test_validate_rh() -> None:
    # Test valid relative humidity values
    validate_rh(50)  # Should not raise an exception
    validate_rh(50.0)  # Should not raise an exception

    # Test invalid relative humidity values
    with pytest.raises(TypeError):
        validate_rh("50")  # type: ignore # Should raise a TypeError
    with pytest.raises(ValueError):
        validate_rh(-1)  # Should raise a ValueError
    with pytest.raises(ValueError):
        validate_rh(101)  # Should raise a ValueError


@pytest.mark.unit
def test_validate_temp() -> None:
    # Test valid temperature values
    validate_temp(20)  # Should not raise an exception
    validate_temp(20.0)  # Should not raise an exception

    # Test invalid temperature values
    with pytest.raises(TypeError):
        validate_temp("20")  # type: ignore # Should raise a TypeError
    with pytest.raises(ValueError):
        validate_temp(-1000)  # Should raise a ValueError
    with pytest.raises(ValueError):
        validate_temp(1000)  # Should raise a ValueError


@pytest.mark.unit
def test_to_celsius() -> None:
    # Test conversion from Fahrenheit to Celsius
    assert to_celsius(32, "f") == 0  # Should return 0
    assert to_celsius(212, "f") == TEMP_MAX  # Should return 100

    # Test conversion from Celsius to Celsius
    assert to_celsius(0, "c") == 0  # Should return 0
    assert to_celsius(100, "c") == TEMP_MAX  # Should return 100

    # Test conversion from Kelvin to Celsius
    assert to_celsius(273.15, "k") == 0  # Should return 0
    assert to_celsius(373.15, "k") == TEMP_MAX  # Should return 100

    # Test invalid temperature values
    with pytest.raises(TypeError):
        to_celsius("20", "f")  # type: ignore # Should raise a TypeError
    with pytest.raises(ValueError):
        to_celsius(-500, "f")  # Should raise a ValueError
    with pytest.raises(ValueError):
        to_celsius(-500, "k")  # Should raise a ValueError
    with pytest.raises(ValueError):
        to_celsius(-274, "c")  # Should raise a ValueError

    # Test invalid scale values
    with pytest.raises(ValueError):
        to_celsius(20, "x")  # Should raise a ValueError


@pytest.mark.parametrize(
    "temp,humidity,expected",
    [
        # Common cases
        (20.0, 50.0, 9.28),  # Room temperature, moderate humidity
        (25.0, 80.0, 21.31),  # Warm and humid
        (0.0, 70.0, -4.81),  # Freezing temperature
        # Edge cases
        (-40.0, 100.0, -40.0),  # Lower temperature limit
        (50.0, 100.0, 50.0),  # Upper temperature limit
        (20.0, 1.0, -38.0),  # Minimum humidity
        (20.0, 100.0, 20.0),  # Maximum humidity
        # Common meteorological conditions
        (15.0, 40.0, 1.51),  # Cool, dry day
        (30.0, 60.0, 21.44),  # Hot, moderately humid day
        (5.0, 90.0, 3.75),  # Cold, humid morning
    ],
)
def test_dew_point_calculation(temp: float, humidity: float, expected: float) -> None:
    """Test dew point calculations against known values.

    The expected values were calculated using the August-Roche-Magnus formula
    with constants a = 17.625 and b = 243.04.
    """
    assert abs(calculate_dew_point(temp, humidity) - expected) < MAGNUS_ACCURACY


@pytest.mark.parametrize(
    "temp,humidity",
    [
        (-41.0, 50.0),  # Too cold
        (51.0, 50.0),  # Too hot
        (20.0, 0.0),  # Humidity too low
        (20.0, 101.0),  # Humidity too high
        (float("nan"), 50.0),  # Invalid temperature
        (20.0, float("nan")),  # Invalid humidity
    ],
)
def test_invalid_inputs(temp: float, humidity: float) -> None:
    """Test that invalid inputs raise appropriate exceptions."""
    with pytest.raises(ValueError):
        calculate_dew_point(temp, humidity)
