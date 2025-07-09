"""Core lookup table implementation for preservation calculations.

This module provides the fundamental LookupTable class used for efficient
lookup of preservation-related values based on temperature and humidity.
"""

from collections.abc import Callable
from enum import Flag, auto
from math import floor
from typing import Any, Final, Generic, TypeVar, cast

import numpy as np
import numpy.typing as npt

from preservationeval.utils.logging import setup_logging

from .exceptions import HumidityError, TemperatureError

# Type variable for lookup table values
T = TypeVar("T", int, float)

# Type alias for table coordinates
TableIndex = tuple[int | float, int | float]  # (temp, rh)


class BoundaryBehavior(Flag):
    """Defines how to handle indices outside array bounds."""

    RAISE = auto()  # Raise exception for out-of-bounds
    CLAMP_X = auto()  # Clamp x values to min/max, raise for y
    CLAMP_Y = auto()  # Clamp y values to min/max, raise for x
    CLAMP = CLAMP_X | CLAMP_Y  # Clamp both x and y values
    LOG = auto()


class LookupTable(Generic[T]):  # noqa: UP046
    """Array with shifted index ranges, backed by numpy.array.

    rray
    dat : 2D         temp_min: Minimum temperature
        rh_min: Minimum relative humidity
        boundary: How to handle out-of-bounds indices
        rounding_func: Function used to round float indices to integers. Defaults
            to round_half_up to get same behavior as math.round() in JS code.

    Attributes:
        data: 2D numpy array
        temp_min: Minimum temperature
        rh_min: Minimum relative humidity
        boundary_behavior: How to handle out-of-bounds indices
        rounding_func: Function used to round float indices to integers
    """

    NDIMS_EXPECTED: Final[int] = 2

    def __init__(
        self,
        data: npt.NDArray[np.floating[Any] | np.integer[Any]],
        temp_min: int,
        rh_min: int,
        boundary_behavior: BoundaryBehavior = BoundaryBehavior.RAISE,
        rounding_func: Callable[[float], int] | None = None,
    ) -> None:
        """Initialize LookupTable with 2D numpy array and shifted index ranges."""
        self._logger = setup_logging(self.__class__.__name__)

        if not isinstance(data, np.ndarray):
            raise TypeError("Data must be a numpy array")
        if data.ndim != self.NDIMS_EXPECTED:
            raise ValueError(f"Data must be 2D, got {data.ndim}D")

        self.data: Final[npt.NDArray[np.floating[Any] | np.integer[Any]]] = data
        self.temp_min: Final[int] = temp_min
        self.rh_min: Final[int] = rh_min
        self.boundary_behavior = boundary_behavior
        self.rounding_func = rounding_func or self._round_half_up

    @property
    def temp_max(self) -> int:
        """Maximum temperature value for the table, based on the data shape."""
        return int(self.temp_min + self.data.shape[0] - 1)

    @property
    def rh_max(self) -> int:
        """Maximum relative humidity value for the table, based on the data shape."""
        return int(self.rh_min + self.data.shape[1] - 1)

    def set_rounding_func(self, rounding_func: Callable[[float], int] | None) -> None:
        """Set rounding function for float indices.

        Args:
            rounding_func: Function used to round float indices to integers.
                If None, defaults to round_half_up to get same behavior as
                math.round() in JS code.
        """
        if rounding_func is None:
            self.rounding_func = self._round_half_up
        else:
            if not callable(rounding_func):
                raise TypeError("Rounding function must be callable")
            self.rounding_func = rounding_func

    def set_boundary_behavior(self, boundary_behavior: BoundaryBehavior) -> None:
        """Set how to handle out-of-bounds indices.

        Args:
            boundary_behavior: How to handle out-of-bounds indices.
                Must be a BoundaryBehavior enum value.
        """
        if not isinstance(boundary_behavior, BoundaryBehavior):
            raise TypeError("Boundary behavior must be a BoundaryBehavior enum value")
        self.boundary_behavior = boundary_behavior

    def __getitem__(
        self,
        indices: TableIndex,
    ) -> T:
        """Get value using original indices.

        Args:
            indices: Tuple of (temp, rh).

        Returns:
            Value at the specified coordinates.

        Raises:
            TypeError: If indices are not integers or floats.
            TemperatureError: If temp. index is out of bounds and cannot be clamped.
            HumidityError: If humidity index is out of bounds and cannot be clamped.
        """
        temp, rh = self._validate_index_types(indices)
        temp = self._handle_temperature_bounds(temp)
        rh = self._handle_humidity_bounds(rh)

        # Calculate indices
        temp_idx = self.rounding_func(temp) - self.temp_min
        rh_idx = self.rounding_func(rh) - self.rh_min

        return cast(T, self.data[temp_idx, rh_idx])

    def _validate_index_types(self, indices: TableIndex) -> tuple[float, float]:
        """Validate that indices are of correct type.

        Args:
            indices: Tuple of (temp, rh).

        Returns:
            Tuple of validated temperature and humidity values.

        Raises:
            TypeError: If indices are not integers or floats.
        """
        temp, rh = indices
        if type(temp) not in (int, float) or type(rh) not in (int, float):
            raise TypeError(
                f"Input must be integer or float, "
                f"got temp: {type(temp)}, rh: {type(rh)}"
            )
        return float(temp), float(rh)

    def _handle_temperature_bounds(self, temp: float) -> float:
        """Handle temperature boundary conditions.

        Args:
            temp: Temperature value.

        Returns:
            Temperature value after boundary handling.

        Raises:
            TemperatureError: If temperature is out of bounds and cannot be clamped.
        """
        if temp < self.temp_min:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping temperature from {temp} to minimum {self.temp_min}"
                    )
                return self.temp_min
            raise TemperatureError(f"Temperature {temp} below minimum {self.temp_min}")

        if temp > self.temp_max:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping temperature from {temp} to maximum {self.temp_max}"
                    )
                return self.temp_max
            raise TemperatureError(f"Temperature {temp} above maximum {self.temp_max}")

        return temp

    def _handle_humidity_bounds(self, rh: float) -> float:
        """Handle humidity boundary conditions.

        Args:
            rh: Relative humidity value.

        Returns:
            Humidity value after boundary handling.

        Raises:
            HumidityError: If humidity is out of bounds and cannot be clamped.
        """
        if rh < self.rh_min:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping relative humidity from {rh} to minimum {self.rh_min}"
                    )
                return self.rh_min
            raise HumidityError(f"RH {rh} below minimum {self.rh_min}")

        if rh > self.rh_max:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                if BoundaryBehavior.LOG in self.boundary_behavior:
                    self._logger.warning(
                        f"Clamping relative humidity from {rh} to maximum {self.rh_max}"
                    )
                return self.rh_max
            raise HumidityError(f"RH {rh} above maximum {self.rh_max}")

        return rh

    def __str__(self) -> str:
        """Return a string representation of the LookupTable."""
        return (
            f"LookupTable {self.data.shape} {self.data.dtype}\n"
            f"  Temp range: {self.temp_min}..{self.temp_max}\n"
            f"  RH range: {self.rh_min}..{self.rh_max}"
        )

    @staticmethod
    def _round_half_up(n: float) -> int:
        """Round a number to the nearest integer with ties towards positive infinity.

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
