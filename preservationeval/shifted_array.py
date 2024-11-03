import logging
from typing import Tuple, TypeVar, Generic
from enum import auto, Flag
import numpy as np


T = TypeVar('T')


class BoundaryBehavior(Flag):
    """Defines how to handle indices outside array bounds."""
    RAISE = auto()  # Raise exception for out-of-bounds
    CLAMP_X = auto()  # Clamp x values to min/max, raise for y
    CLAMP_Y = auto()  # Clamp y values to min/max, raise for x
    CLAMP = CLAMP_X | CLAMP_Y  # Clamp both x and y values


class IndexRangeError(Exception):
    """Exception for index range violations."""
    pass


class XBelowMinError(IndexRangeError):
    """X index below minimum value."""
    pass


class XAboveMaxError(IndexRangeError):
    """X index above maximum value."""
    pass


class YBelowMinError(IndexRangeError):
    """Y index below minimum value."""
    pass


class YAboveMaxError(IndexRangeError):
    """Y index above maximum value."""
    pass


class ShiftedArray(Generic[T]):
    """
    Array with shifted index ranges, backed by numpy.array.
    """

    def __init__(self,
                 data: np.ndarray,
                 x_min: int,
                 y_min: int,
                 boundary_behavior: BoundaryBehavior = BoundaryBehavior.RAISE):
        """
        Args:
            data: 2D numpy array
            x_min: Minimum x index
            y_min: Minimum y index
            boundary: How to handle out-of-bounds indices
        """
        self._logger = logging.getLogger(self.__class__.__name__)

        if not isinstance(data, np.ndarray) or data.ndim != 2:
            raise TypeError("Data must be a 2D numpy array")

        self.data = data
        self.x_min = x_min
        self.y_min = y_min
        self.boundary_behavior = boundary_behavior

    @property
    def x_max(self) -> int:
        return self.x_min + self.data.shape[0] - 1

    @property
    def y_max(self) -> int:
        return self.y_min + self.data.shape[1] - 1

    def __getitem__(
            self,
            indices: Tuple[int, int],
    ) -> T:
        """
        Get value using original indices.

        Args:
            indices: Tuple of (x, y) coordinates.
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
        x, y = indices

        # Check for integer indices
        if not isinstance(x, int) or not isinstance(y, int):
            raise TypeError(
                f"Indices must be integers, got x: {type(x)}, y: {type(y)}"
            )

        # Check for out-of-bounds indices
        if x < self.x_min:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping x index from {x} to minimum {self.x_min}"
                )
                x = max(self.x_min, x)
            else:
                raise XBelowMinError(f"X index {x} below minimum {self.x_min}")

        if x > self.x_max:
            if BoundaryBehavior.CLAMP_X in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping x index from {x} to maximum {self.x_max}"
                )
                x = min(self.x_max, x)
            else:
                raise XAboveMaxError(f"X index {x} above maximum {self.x_max}")

        if y < self.y_min:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping y index from {y} to minimum {self.y_min}"
                )
                y = max(self.y_min, y)
            else:
                raise YBelowMinError(f"Y index {y} below minimum {self.y_min}")

        if y > self.y_max:
            if BoundaryBehavior.CLAMP_Y in self.boundary_behavior:
                self._logger.warning(
                    f"Clamping y index from {y} to maximum {self.y_max}"
                )
                y = min(self.y_max, y)
            else:
                raise YAboveMaxError(f"Y index {y} above maximum {self.y_max}")

        x_idx = int(x - self.x_min)
        y_idx = int(y - self.y_min)
        return self.data[x_idx, y_idx]

    def __str__(self) -> str:
        return (
            f"ShiftedArray {self.data.shape} {self.data.dtype}\n"
            f"  X range: {self.x_min}..{self.x_max}\n"
            f"  Y range: {self.y_min}..{self.y_max}"
        )
