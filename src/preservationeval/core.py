"""
Alternate implementation of PI, MRF, and EMC calculation using numpy 2D arrays.

This module provides functions to calculate Preservation Index (PI),
Mold Risk Factor (MRF),and Equilibrium Moisture Content (EMC) using numpy 2D
arrays for efficient computation.

Functions:
    round_half_up(n: float) -> int:
        Round a number to the nearest integer. Ties are rounded away from zero.

    to_celsius(x: float, scale: str = 'f') -> float:
        Convert temperature to Celsius.

    pi(t: Temperature, rh: RelativeHumidity) -> PreservationIndex:
        Calculate Preservation Index (PI) value.

    mold(t: Temperature, rh: RelativeHumidity) -> MoldRisk:
        Calculate Mold Risk Factor.

    emc(t: Temperature, rh: RelativeHumidity) -> MoistureContent:
        Calculate Equilibrium Moisture Content (EMC).

Classes:
    BoundaryBehavior(Enum):
        Enum for boundary behavior options.

    ShiftedArray:
        Class for handling shifted arrays with boundary behavior.
"""

# Standard library imports
from typing import Final

# Third-party imports
import numpy as np

from .const import EMCTABLE, PITABLE

# Local imports
from .logging import setup_logging
from .types import (
    BoundaryBehavior,
    EnvironmentalRating,
    HumidityError,
    IndexRangeError,
    MoistureContent,
    MoldRisk,
    PreservationError,
    PreservationIndex,
    RelativeHumidity,
    ShiftedArray,
    Temperature,
    TemperatureError,
    XAboveMaxError,
    XBelowMinError,
    YAboveMaxError,
    YBelowMinError,
)

# from .tables import fetch_and_validate_tables

# Initialize module logger
logger = setup_logging(__name__)


# Initialize ShiftedArrays
pi_table: Final[ShiftedArray] = ShiftedArray(
    np.array(PITABLE[:8010]).reshape(89, 90), -23, 6, BoundaryBehavior.CLAMP
)
mold_table: Final[ShiftedArray] = ShiftedArray(
    np.array(PITABLE[8010:]).reshape(44, 36), 2, 65, BoundaryBehavior.RAISE
)
emc_table: Final[ShiftedArray] = ShiftedArray(
    np.array(EMCTABLE).reshape(86, 101), -20, 0, BoundaryBehavior.CLAMP
)


def round_half_up(n: float) -> int:
    """
    Round a number to the nearest integer. Ties are rounded away from zero.

    Args:
        n (float): The number to round.

    Returns:
        int: The rounded integer.
    """
    if n >= 0:
        return int(n + 0.5)
    else:
        return int(n - 0.5)


# To get exact same behavior as in the original JS code we use round_half_up()
# when converting float to int, could be changed to round() if you dont care
# about that
to_int = round_half_up


def to_celsius(x: Temperature, scale: str = "f") -> Temperature:
    """Convert temperature to specified scale.

    Args:
        x (float / int): Temperature value
        scale (str):    Target scale
                        - 'f' for Fahrenheit
                        - 'c' for Celsius
                        - 'k' for Kelvin)

    Returns:
        Temperature: Converted temperature value

    Raises:
        ValueError: If scale is none of 'f', 'c' or 'k'
    """
    if scale == "f":
        return float((x * 1.8) + 32.0)
    elif scale == "c":
        return float(x)
    elif scale == "k":
        return float(x + 273.15)
    else:
        raise ValueError(f"Unsupported scale '{scale}'")


def validate_rh(rh: RelativeHumidity) -> None:
    """
    Validate relative humidity is between 0 [%] and 100 [%] incluive

    Args:
        rh (int / float)

    Raises:
        HumidityError: If 'rh' is < 0 or 'rh' > 100.
    """
    if not (0 <= rh <= 100):
        raise HumidityError(
            f"Relative humidity must be between 0 [%] and 100 [%], got {rh} [%]"  # noqa E501
        )


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


def pi(t: Temperature, rh: RelativeHumidity) -> PreservationIndex:
    """
    Calculate Preservation Index (PI) value. PI represents the overall rate of
    chemical decay in organic materials based on a constant T and RH. A higher
    number indicates a slower the rate of chemical decay.

    Args:
        t: Temperature in Celsius
        rh: Relative Humidity percentage

    Returns:
        PI value [years].
        Use rate_natural_aging() to convert PI to Environmental Rating.
    """
    validate_rh(rh)
    try:
        pi = pi_table[to_int(t), to_int(rh)]
    except (XBelowMinError, XAboveMaxError) as e:
        logger.error(f"Temperature out of bounds: {e}")
        raise TemperatureError("Temperature out of bounds") from e
    except (YBelowMinError, YAboveMaxError) as e:
        logger.error(f"RH out of bounds: {e}")
        raise HumidityError("RH out of bounds") from e
    except Exception as e:
        logger.error(f"Error calculating PI: {e}")
        raise PreservationError("Error calculating PI") from e
    return int(pi)


def mold(t: Temperature, rh: RelativeHumidity) -> MoldRisk:
    """Calculate Mold Risk Factor.

    Args:
        t: Temperature in Celsius (2 to 45°C for risk calculation)
        rh: Relative Humidity percentage (≥65% for risk calculation)

    Returns:
        0 if no risk (t < 2°C or t > 45°C or rh < 65%),
        otherwise returns risk value from lookup table where
        higher values indicate greater mold risk
    """
    validate_rh(rh)
    try:
        mold = mold_table[to_int(t), to_int(rh)]
    except IndexRangeError:
        return 0.0
    except Exception as e:
        logger.error(f"Error calculating mold risk: {e}")
        raise PreservationError("Error calculating mold risk") from e
    return float(mold)


def emc(t: Temperature, rh: RelativeHumidity) -> MoistureContent:
    """Calculate Equilibrium Moisture Content (EMC).

    Args:
        t: Temperature in Celsius (-20 to 65°C)
        rh: Relative Humidity percentage (0 to 100%)

    Returns:
        EMC value from lookup table as percentage, where:
        - 5% ≤ EMC ≤ 12.5%: OK for mechanical damage
        - EMC < 7.0%: Good for metal corrosion
        - 7.0% ≤ EMC < 10.5%: OK for metal corrosion
        - EMC ≥ 10.5%: Risk for metal corrosion
    """
    validate_rh(rh)
    try:
        emc = emc_table[to_int(t), to_int(rh)]
    except (XBelowMinError, XAboveMaxError) as e:
        logger.error(f"Temperature out of bounds: {e}")
        raise TemperatureError("Temperature out of bounds") from e
    except (YBelowMinError, YAboveMaxError) as e:
        logger.error(f"RH out of bounds: {e}")
        raise HumidityError("RH out of bounds") from e
    except Exception as e:
        logger.error(f"Error calculating EMC: {e}")
        raise PreservationError("Error calculating EMC") from e
    return float(emc)


def rate_natural_aging(pi: PreservationIndex) -> EnvironmentalRating:
    """
    Evaluate Natural Aging risk as a function of Preservation Index (PI).

    Args:
        pi (PreservationIndex): The Preservation Index value.

    Returns:
        EnvironmentalRating: The environmental rating based on PI.
            - GOOD: If PI is ≥75
            - OK: If PI is between 45 and 75
            - RISK: If PI is <45
    """
    if pi >= 75:
        return EnvironmentalRating.GOOD
    elif pi < 45:
        return EnvironmentalRating.RISK
    else:
        return EnvironmentalRating.OK


def rate_mechanical_damage(emc: MoistureContent) -> EnvironmentalRating:
    """
    Evaluate the risk of Mechanical Damage as a function of Equilibrium
    Moisture Content (EMC).

    Args:
        emc (MoistureContent): The Equilibrium Moisture Content value.

    Returns:
        EnvironmentalRating: The environmental rating based on EMC.
            - OK: If EMC is between 5 and 12.5
            - RISK: If EMC is outside the range 5-12.5
    """
    if 5 <= emc <= 12.5:
        return EnvironmentalRating.OK
    else:
        return EnvironmentalRating.RISK


def rate_mold_growth(mrf: MoldRisk) -> EnvironmentalRating:
    """
    Evaluate the risk of Mold Growth as a function of Mold Risk Factor (MRF).

    Args:
        mrf (MoldRisk): The Mold Risk Factor value.

    Returns:
        EnvironmentalRating: The environmental rating based on MRF.
            - GOOD: If MRF is 0 (No Risk)
            - RISK: If MRF is >0 (Risk, value represents days to mold)
    """
    if mrf == 0:
        return EnvironmentalRating.GOOD
    else:
        return EnvironmentalRating.RISK


def rate_metal_corrosion(emc: MoistureContent) -> EnvironmentalRating:
    """
    Evaluate the risk of Metal Corrosion as a function of Equilibrium Moisture
    Content (EMC).

    Args:
        emc (MoistureContent): The Equilibrium Moisture Content value.

    Returns:
        EnvironmentalRating: The environmental rating based on EMC.
            - GOOD: If EMC is <7.0
            - OK: If EMC is between 7.1 and 10.5
            - RISK: If EMC is ≥10.5
    """
    if emc < 7.0:
        return EnvironmentalRating.GOOD
    elif emc < 10.5:
        return EnvironmentalRating.OK
    else:
        return EnvironmentalRating.RISK
