"""Domain-specific custom exceptions for preservation calculation errors."""


class PreservationError(Exception):
    """Base exception for preservation calculation errors."""

    ...


class IndexRangeError(PreservationError):
    """Exception for index range violations."""

    ...


class TemperatureError(IndexRangeError):
    """Exception for temperature range violations."""

    ...


class HumidityError(IndexRangeError):
    """Exception for humidity range violations."""

    ...
