"""Utility functions for preservation calculations.

This module provides various utility functions for validating and converting
temperature, relative humidity, and dew point values, as well as calculating
derived quantities such as equilibrium moisture content.
"""

from .const import RH_MAX, RH_MIN, TEMP_MAX, TEMP_MIN
from .types import RelativeHumidity, Temperature


def validate_rh(rh: RelativeHumidity) -> None:
    """Validate that relative humidity is a number between RH_MIN [%] and RH_MAX [%].

    Args:
        rh: Relative humidity value

    Raises:
        TypeError: If 'rh' is not a number.
        ValueError: If 'rh' is not within the valid range.
    """
    if not isinstance(rh, (int | float)):
        raise TypeError(f"Relative humidity must be a number, got {type(rh).__name__}")
    if not RH_MIN <= rh <= RH_MAX:
        raise ValueError(
            f"Relative humidity must be between {RH_MIN} [%] and {RH_MAX} [%], "
            f"got {rh} [%]"
        )


def validate_temp(temp: Temperature) -> None:
    """Validate that temperature is a number in degee Celsius.

    Args:
        temp (int / float): Temperature in degee Celsius, >= TEMP_MIN and <= TEMP_MAX.

    Raises:
        TypeError: If 'temp' is not a number.
        ValueError: If 'temp' < TEMP_MIN or 'temp' > TEMP_MAX
    """
    if not isinstance(temp, (int | float)):
        raise TypeError(f"Temperature must be a number, got {type(temp).__name__}")
    if not (TEMP_MIN <= temp <= TEMP_MAX):
        raise ValueError(
            f"Temperature must be between {TEMP_MIN} [C] and {TEMP_MAX} [C], "
            f"got {temp} [C]"
        )


def to_celsius(x: Temperature, scale: str = "f") -> Temperature:
    """Convert temperature from specified scale to Celsius.

    Args:
        x (float / int): Temperature value
        scale (str):    Input scale
                        - 'f' for Fahrenheit
                        - 'c' for Celsius
                        - 'k' for Kelvin)

    Returns:
        Temperature: Converted temperature value

    Raises:
        ValueError: If scale is none of 'f', 'c' or 'k' or if temperature (x) is out of
            valid range
        TypeError: If x is not integer or float
    """
    if not isinstance(x, (int | float)):
        raise TypeError(f"Temperature must be integer or float, got {type(x)}")
    if scale == "f":
        if x < (TEMP_MIN - 32) * 5 / 9:
            raise ValueError("Fahrenheit temperature must be > -459.67, got {x}")
        return float((x - 32) * 5 / 9)
    elif scale == "c":
        if x < TEMP_MIN:
            raise ValueError("Celsius temperature must be > -273.15, got {x}")
        return float(x)
    elif scale == "k":
        if x < 0:
            raise ValueError("Kelvin temperature must be >= 0, got {x}")
        return float(x - 273.15)
    else:
        raise ValueError(f"Unsupported scale '{scale}', must be 'f', 'c' or 'k'")


def temp(rh: RelativeHumidity, td: Temperature) -> Temperature:
    """Calculate temperature given relative humidity and dew point.

    Args:
        rh (float / int): Relative humidity (%)
        td (float / int): Dew point temperature

    Returns:
        float: Calculated temperature
    """
    validate_rh(rh)
    t_a: float = pow(rh / 100, 1 / 8)
    return (td - (112 * t_a) + 112) / ((0.9 * t_a) + 0.1)


def rh(t: Temperature, td: Temperature) -> RelativeHumidity:
    """Calculate relative humidity given temperature and dew point.

    Args:
        t (float / int): Temperature
        td (float / int): Dew point temperature

    Returns:
        RelativeHumidity: Calculated relative humidity (%)
    """
    return 100 * (pow((112 - (0.1 * t) + td) / (112 + (0.9 * t)), 8))


def dp(t: Temperature, rh: RelativeHumidity) -> Temperature:
    """Calculate dew point given temperature and relative humidity.

    Args:
        t (float / int): Temperature
        rh (float / int): Relative humidity (%)

    Returns:
        Temperature: Calculated dew point temperature
    """
    validate_rh(rh)
    t_a: float = pow(rh / 100, 1 / 8)
    return ((112 + (0.9 * t)) * t_a + (0.1 * t)) - 112
