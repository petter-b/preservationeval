"""Utility functions for preservation calculations.

This module provides various utility functions for validating and converting
temperature, relative humidity, and dew point values, as well as calculating
derived quantities such as equilibrium moisture content.
"""

import math

from .const import RH_MAX, RH_MIN, TEMP_MAX, TEMP_MIN
from .types import RelativeHumidity, Temperature

# Limits for Magnus formula (see calculate_dew_point)
MAGNUS_MIN_TEMP = -40
MAGNUS_MAX_TEMP = 50
MAGNUS_MIN_RH = 1
MAGNUS_MAX_RH = 100
MAGNUS_ACCURACY = 0.3


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


def calculate_dew_point(
    temp_celsius: Temperature, rel_humidity: RelativeHumidity
) -> Temperature:
    """Calculate dew point given temperature and relative humidity.

    Calculate dew point using August-Roche-Magnus approximation.

    Args:
        temp_celsius (float): Temperature in Celsius.
        rel_humidity (float): Relative humidity (0-100).

    Returns:
        float: Dew point temperature in Celsius, rounded to 1 decimal place.

    Accuracy:
        Maximum error typically less than ±0.3°C within valid ranges.
        Particularly accurate in mid-range temperatures.

    Limitations:
        Valid temperature range: -40°C to +50°C.
        Valid relative humidity range: 1% to 100%.
        Accuracy decreases:
            - At temperatures below -40°C or above 50°C
            - At very low relative humidity (<5%)

    Notes:
        Uses August-Roche-Magnus formula: Td = (b * alpha) / (a - alpha)
        where alpha = (aT / (b + T)) + ln(RH/100)
        with constants a = 17.625, b = 243.04

        This version is recommended by the World Meteorological Organization
        and is considered more accurate than the simple Magnus formula
        for mid-range temperatures.
    """
    if not MAGNUS_MIN_TEMP <= temp_celsius <= MAGNUS_MAX_TEMP:
        raise ValueError(
            f"Temperature must be between {MAGNUS_MIN_TEMP}°C and {MAGNUS_MAX_TEMP}°C"
        )
    if not MAGNUS_MIN_RH <= rel_humidity <= MAGNUS_MAX_RH:
        raise ValueError(
            f"Relative humidity must be between {MAGNUS_MIN_RH}% and {MAGNUS_MAX_RH}%"
        )

    # August-Roche-Magnus formula constants
    a = 17.625
    b = 243.04

    # Convert relative humidity to decimal
    rel_humidity = rel_humidity / 100

    # Calculate alpha using Magnus formula
    alpha = ((a * temp_celsius) / (b + temp_celsius)) + math.log(rel_humidity)

    # Calculate dew point
    dew_point = (b * alpha) / (a - alpha)

    return round(dew_point, 1)
