"""Lookup table implementation for preservation calculations.

This module provides the core lookup table functionality used to calculate
preservation indices based on temperature and relative humidity values.


Classes:
    LookupTable: A class representing a lookup table for preservation
        environment calculations.

Functions:
    pi: Calculates the preservation index (PI) value.
    emc: Calculates the equilibrium moisture content (EMC) value.
    mold: Calculates the mold risk factor value.
"""

from .types import (
    HumidityError,
    IndexRangeError,
    MoistureContent,
    MoldRisk,
    PreservationError,
    PreservationIndex,
    RelativeHumidity,
    Temperature,
    TemperatureError,
)
from .utils.logging import setup_logging

try:
    from .tables import emc_table, mold_table, pi_table
except ImportError:
    ...


from .util_functions import validate_rh, validate_temp

# Initialize module logger
logger = setup_logging(__name__)


def pi(t: Temperature, rh: RelativeHumidity) -> PreservationIndex:
    """Calculate Preservation Index (PI) value.

    PI represents the overall rate of chemical decay in organic materials based on a
    constant T and RH. A higher number indicates a slower the rate of chemical decay.

    Args:
        t: Temperature in Celsius
        rh: Relative Humidity percentage

    Returns:
        PI value [years].
        Use rate_natural_aging() to convert PI to Environmental Rating.
    """
    validate_rh(rh)
    validate_temp(t)
    try:
        pi: int = pi_table[t, rh]
    except TemperatureError as e:
        logger.error(f"Temperature out of bounds: {e}")
        raise TemperatureError("Temperature out of bounds {e}") from e
    except HumidityError as e:
        logger.error(f"RH out of bounds: {e}")
        raise HumidityError("RH out of bounds") from e
    except Exception as e:
        logger.error(f"Unexpected error calculating PI: {e}")
        raise PreservationError("Unexpected error calculating PI") from e
    return pi


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
    validate_temp(t)
    try:
        mold: int = mold_table[t, rh]
    except IndexRangeError:
        return 0.0
    except Exception as e:
        logger.error(f"Unexpected error calculating mold risk: {e}")
        raise PreservationError("Unexpected error calculating mold risk") from e
    return mold


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
    validate_temp(t)
    try:
        emc: float = emc_table[t, rh]
    except TemperatureError as e:
        logger.error(f"Temperature out of bounds: {e}")
        raise TemperatureError("Temperature out of bounds {e}") from e
    except HumidityError as e:
        logger.error(f"RH out of bounds: {e}")
        raise HumidityError("RH out of bounds {e}") from e
    except Exception as e:
        logger.error(f"Unexpected error calculating EMC: {e}")
        raise PreservationError("Unexpected error calculating EMC") from e
    return emc
