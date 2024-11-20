"""Unit tests for preservationeval.utils module.

Functions:
    test_validate_rh: Test the validate_rh function by checking that it does not raise
    an exception for valid relative humidity values.
    test_validate_temp: Test the validate_temp function by checking that it does not
    raise an exception for valid temperature values.

These tests ensure that the utility functions in the preservationeval.utils module are
functioning correctly.
"""

import pytest

from preservationeval.main.const import TEMP_MAX
from preservationeval.main.utils import to_celsius, validate_rh, validate_temp


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

    # Test invalid scale values
    with pytest.raises(ValueError):
        to_celsius(20, "x")  # Should raise a ValueError
