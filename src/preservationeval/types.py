"""Types and exceptions for preservation evaluation.

Defines annotated types for domain-specific values and custom exceptions for
preservation calculation errors.
"""

from typing import Annotated

# Domain-specific types with documentation
Temperature = Annotated[float, "Temperature in Celsius"]
RelativeHumidity = Annotated[float, "Relative Humidity in %"]
PreservationIndex = Annotated[int, "PI value in years"]
MoldRisk = Annotated[float, "Mold risk factor"]
MoistureContent = Annotated[float, "EMC value in %"]


# Custom Exceptions
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
