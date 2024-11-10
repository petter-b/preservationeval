# Standard library imports
from enum import Enum, Flag, auto
from typing import Callable, Tuple, TypeAlias, Union

# Third-party imports
import numpy as np

# Local imports
from preservationeval.logging import setup_logging

# Types aliases
Number: TypeAlias = Union[int, float]
Temperature: TypeAlias = Number
RelativeHumidity: TypeAlias = Number
PreservationIndex: TypeAlias = float
MoldRisk: TypeAlias = float
MoistureContent: TypeAlias = float


# Custom Exceptions
class PreservationError(Exception):
    """Base exception for preservation calculation errors."""

    ...


class TemperatureError(PreservationError):
    """Exception for temperature range violations."""

    ...


class HumidityError(PreservationError):
    """Exception for humidity range violations."""

    ...


class IndexRangeError(PreservationError):
    """Exception for index range violations."""

    ...


class XBelowMinError(IndexRangeError):
    """X index below minimum value."""

    ...


class XAboveMaxError(IndexRangeError):
    """X index above maximum value."""

    ...


class YBelowMinError(IndexRangeError):
    """Y index below minimum value."""

    ...


class YAboveMaxError(IndexRangeError):
    """Y index above maximum value."""

    ...


class EnvironmentalRating(Enum):
    GOOD = "GOOD"
    OK = "OK"
    RISK = "RISK"


class BoundaryBehavior(Flag):
    """Defines how to handle indices outside array bounds."""

    RAISE = auto()  # Raise exception for out-of-bounds
    CLAMP_X = auto()  # Clamp x values to min/max, raise for y
    CLAMP_Y = auto()  # Clamp y values to min/max, raise for x
    CLAMP = CLAMP_X | CLAMP_Y  # Clamp both x and y values
    LOG = auto()


class LookupTable:
    """
    Array with shifted index ranges, backed by numpy.array.
    """

    def __init__(
        self,
        data: np.ndarray,
        temp_min: int,
        rh_min: int,
        boundary_behavior: BoundaryBehavior = BoundaryBehavior.RAISE,
        rounding_func: Callable[[float], int] | None = None,  # type: ignore
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

        if not isinstance(data, np.ndarray) or data.ndim != 2:
            raise TypeError("Data must be a 2D numpy array")

        self.data = data
        self.temp_min = temp_min
        self.rh_min = rh_min
        self.boundary_behavior = boundary_behavior
        if rounding_func is None:
            self.rounding_func = LookupTable._round_half_up
        else:
            self.rounding_func = rounding_func

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
        indices: Tuple[Number, Number],
    ) -> Number:
        """
        Get value using original indices.

        Args:
            indices: Tuple of (temp, rh).
            boundary_behavior: How to handle out-of-bounds indices

        Returns:
            Value at the specified coordinates

        Raises:
            TypeError: If indices are not integers
            XBelowMinError: If x index is below min and boundary_behavior is RAISE or CLAMP_Y  # noqa E501
            XAboveMaxError: If x index is above max and boundary_behavior is RAISE or CLAMP_Y  # noqa E501
            YBelowMinError: If y index is below min and boundary_behavior is RAISE or CLAMP_X  # noqa E501
            YAboveMaxError: If y index is above max and boundary_behavior is RAISE or CLAMP_X  # noqa E501
        """
        temp, rh = indices

        temp = int(self._round_half_up(temp))
        rh = int(self._round_half_up(rh))

        # Check for integer indices
        if not isinstance(temp, Number) or not isinstance(rh, Number):
            raise TypeError(
                f"Input must be integer or float, got x: {type(temp)}, y: {type(rh)}"
            )

        # Check for out-of-bounds indices
        if temp < self.temp_min:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping x index from {temp} to minimum {self.temp_min}"
                )
                temp = max(self.temp_min, temp)
            else:
                raise XBelowMinError(f"X index {temp} below minimum {self.temp_min}")

        if temp > self.temp_max:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping x index from {temp} to maximum {self.temp_max}"
                )
                temp = min(self.temp_max, temp)
            else:
                raise XAboveMaxError(f"X index {temp} above maximum {self.temp_max}")

        if rh < self.rh_min:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping y index from {rh} to minimum {self.rh_min}"
                )
                rh = max(self.rh_min, rh)
            else:
                raise YBelowMinError(f"Y index {rh} below minimum {self.rh_min}")

        if rh > self.rh_max:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping y index from {rh} to maximum {self.rh_max}"
                )
                rh = min(self.rh_max, rh)
            else:
                raise YAboveMaxError(f"Y index {rh} above maximum {self.rh_max}")

        x_idx = int(temp - self.temp_min)
        y_idx = int(rh - self.rh_min)
        return self.data[x_idx, y_idx]  # type: ignore

    def __str__(self) -> str:
        return (
            f"ShiftedArray {self.data.shape} {self.data.dtype}\n"
            f"  X range: {self.temp_min}..{self.temp_max}\n"
            f"  Y range: {self.rh_min}..{self.rh_max}"
        )

    @staticmethod
    def _round_half_up(n: float) -> int:
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
