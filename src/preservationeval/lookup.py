from enum import Flag, auto
from math import floor
from typing import Callable, Final, Generic, TypeVar, Union, cast

import numpy as np

from .const import EMCTABLE, PITABLE
from .logging import setup_logging
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
from .utils import validate_rh, validate_temp

# Type variable for lookup table values
T = TypeVar("T", int, float)

# Type alias for table coordinates
TableIndex = tuple[Union[int, float], Union[int, float]]  # (temp, rh)


class BoundaryBehavior(Flag):
    """Defines how to handle indices outside array bounds."""

    RAISE = auto()  # Raise exception for out-of-bounds
    CLAMP_X = auto()  # Clamp x values to min/max, raise for y
    CLAMP_Y = auto()  # Clamp y values to min/max, raise for x
    CLAMP = CLAMP_X | CLAMP_Y  # Clamp both x and y values
    LOG = auto()


class LookupTable(Generic[T]):
    """
    Array with shifted index ranges, backed by numpy.array.
    """

    def __init__(
        self,
        data: np.ndarray,
        temp_min: int,
        rh_min: int,
        boundary_behavior: BoundaryBehavior = BoundaryBehavior.RAISE,
        rounding_func: Callable[[float], int] | None = None,
    ) -> None:
        """
        Args:
            data: 2D numpy array
            temp_min: Minimum temperature
            rh_min: Minimum relative humidity
            boundary: How to handle out-of-bounds indices
            rounding_func: Function used to round float indices to integers. Defaults
                to round_half_up to get same behavior as math.round() in JS code.
        """
        self._logger = setup_logging(self.__class__.__name__)

        if not isinstance(data, np.ndarray):
            raise TypeError("Data must be a numpy array")
        if data.ndim != 2:
            raise ValueError(f"Data must be 2D, got {data.ndim}D")

        self.data: Final[np.ndarray] = data
        self.temp_min: Final[int] = temp_min
        self.rh_min: Final[int] = rh_min
        self.boundary_behavior = boundary_behavior
        self.rounding_func = rounding_func or self._round_half_up

    @property
    def temp_max(self) -> int:
        return int(self.temp_min + self.data.shape[0] - 1)

    @property
    def rh_max(self) -> int:
        return int(self.rh_min + self.data.shape[1] - 1)

    def set_rounding_func(self, rounding_func: Callable[[float], int]) -> None:
        self.rounding_func = rounding_func

    def __getitem__(
        self,
        indices: TableIndex,
    ) -> T:
        """
        Get value using original indices.

        Args:
            indices: Tuple of (temp, rh).

        Returns:
            Value at the specified coordinates.

        Raises:
            TypeError: If indices are not integers or floats.
            TemperatureError: If temperature index is out of bounds and cannot be
                clamped.
            HumidityError: If humidity index is out of bounds and cannot be clamped.
        """
        temp, rh = indices

        # Check for integer or float indices
        if type(temp) not in (int, float) or type(rh) not in (int, float):
            raise TypeError(
                f"Input must be integer or float, "
                f"got temp: {type(temp)}, rh: {type(rh)}"
            )

        # Check for out-of-bounds indices
        if temp < self.temp_min:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping temperature from {temp} to minimum {self.temp_min}"
                    )
                temp = max(self.temp_min, temp)
            else:
                raise TemperatureError(
                    f"Temperature {temp} below minimum {self.temp_min}"
                )

        if temp > self.temp_max:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping temperature from {temp} to maximum {self.temp_max}"
                    )
                temp = min(self.temp_max, temp)
            else:
                raise TemperatureError(
                    f"Temperature {temp} above maximum {self.temp_max}"
                )

        if rh < self.rh_min:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping relative humidity from {rh} to minimum {self.rh_min}"
                    )
                rh = max(self.rh_min, rh)
            else:
                raise HumidityError(f"RH {rh} below minimum {self.rh_min}")

        if rh > self.rh_max:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping relative humidity from {rh} to maximum {self.rh_max}"
                    )
                rh = min(self.rh_max, rh)
            else:
                raise HumidityError(f"RH {rh} above maximum {self.rh_max}")

        # Calculate indices
        temp_idx = self.rounding_func(temp) - self.temp_min
        rh_idx = self.rounding_func(rh) - self.rh_min

        return cast(T, self.data[temp_idx, rh_idx])

    def __str__(self) -> str:
        return (
            f"LookupTable {self.data.shape} {self.data.dtype}\n"
            f"  Temp range: {self.temp_min}..{self.temp_max}\n"
            f"  RH range: {self.rh_min}..{self.rh_max}"
        )

    @staticmethod
    def _round_half_up(n: float) -> int:
        """
        Round a number to the nearest integer. Ties are rounded towards positive
        infinity.

        Args:
            n (float): The number to round.

        Returns:
            int: The rounded integer.
        """
        return floor(n + 0.5)


# Create specific table types
PITable = LookupTable[int]  # Returns integer PI values
EMCTable = LookupTable[float]  # Returns float EMC values
MoldTable = LookupTable[int]  # Returns integer mold risk values

# Initialize module logger
logger = setup_logging(__name__)

# Initialize lookup tables
pi_table: Final[PITable] = LookupTable(
    np.array(PITABLE[:8010]).reshape(89, 90), -23, 6, BoundaryBehavior.CLAMP
)
mold_table: Final[MoldTable] = LookupTable(
    np.array(PITABLE[8010:]).reshape(44, 36), 2, 65, BoundaryBehavior.RAISE
)
emc_table: Final[EMCTable] = LookupTable(
    np.array(EMCTABLE).reshape(86, 101), -20, 0, BoundaryBehavior.CLAMP
)


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
    validate_temp(t)
    try:
        pi = pi_table[t, rh]
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
        mold = mold_table[t, rh]
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
        emc = emc_table[t, rh]
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
