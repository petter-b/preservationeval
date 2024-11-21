"""Constants used in preservation environment calculations.

Constants:
    DP_JS_URL: The URL of the Dew Point Calculator JavaScript file.
    TEMP_MIN: The minimum temperature in Celsius (absolute zero).
    TEMP_MAX: The maximum temperature in Celsius (water boiling point).
    RH_MIN: The minimum relative humidity (0%).
    RH_MAX: The maximum relative humidity (100%).
"""

from typing import Final

DP_JS_URL: Final[str] = "http://www.dpcalc.org/dp.js"

# Validation ranges
TEMP_MIN: Final[float] = -273.15  # Absolute zero in Celsius
TEMP_MAX: Final[float] = 100.0  # Water boiling point
RH_MIN: Final[float] = 0.0
RH_MAX: Final[float] = 100.0

# Table dimensions
PI_TABLE_SHAPE: Final[tuple[int, int]] = (89, 90)
MOLD_TABLE_SHAPE: Final[tuple[int, int]] = (44, 36)
EMC_TABLE_SHAPE: Final[tuple[int, int]] = (86, 101)
