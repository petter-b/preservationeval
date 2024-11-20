"""Types and utilities for preservation calculation tables.

This package provides the core LookupTable implementation and related types
used for preservation calculations.
"""

from importlib.metadata import version

from .domain_specific import (
    MoistureContent,
    MoldRisk,
    PreservationIndex,
    RelativeHumidity,
    Temperature,
)
from .exceptions import (
    HumidityError,
    IndexRangeError,
    PreservationError,
    TemperatureError,
)
from .lookuptable import (
    BoundaryBehavior,
    EMCTable,
    LookupTable,
    MoldTable,
    PITable,
    TableIndex,
)

__all__ = [
    # Core table implementation
    "LookupTable",
    "BoundaryBehavior",
    "TableIndex",
    # Specific table types
    "PITable",
    "EMCTable",
    "MoldTable",
    # Exceptions
    "PreservationError",
    "IndexRangeError",
    "TemperatureError",
    "HumidityError",
    # Domain specific types
    "Temperature",
    "RelativeHumidity",
    "PreservationIndex",
    "MoldRisk",
    "MoistureContent",
]

__version__ = version("preservationeval")
