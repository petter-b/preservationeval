"""Types and exceptions for preservationeval package.

This package provides the core LookupTable implementation and related types
used for preservation calculations.

Classes:
    LookupTable: A generic lookup table for efficient value retrieval based on
        temperature and humidity.
    BoundaryBehavior: An enumeration defining behavior for out-of-bounds lookups.
    TableIndex: A type alias for the (temperature, relative humidity) index used in
        lookup tables.
    PITable: A specialized LookupTable for Preservation Index calculations.
    EMCTable: A specialized LookupTable for Equilibrium Moisture Content calculations.
    MoldTable: A specialized LookupTable for Mold Risk calculations.

Exceptions:
    PreservationError: Base exception for preservation-related errors.
    IndexRangeError: Raised when an index is out of the valid range.
    TemperatureError: Raised for invalid temperature values.
    HumidityError: Raised for invalid relative humidity values.

Domain-specific types:
    Temperature: Type alias for temperature values in Celsius.
    RelativeHumidity: Type alias for relative humidity values in percentage.
    PreservationIndex: Type alias for Preservation Index values in years.
    MoldRisk: Type alias for Mold Risk factor values.
    MoistureContent: Type alias for Equilibrium Moisture Content values in percentage.

These types and classes form the foundation for preservation calculations
and provide a structured way to handle preservation-related data and operations.
"""

from .domain_types import (
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
    "BoundaryBehavior",
    "EMCTable",
    "HumidityError",
    "IndexRangeError",
    "LookupTable",
    "MoistureContent",
    "MoldRisk",
    "MoldTable",
    "PITable",
    "PreservationError",
    "PreservationIndex",
    "RelativeHumidity",
    "TableIndex",
    "Temperature",
    "TemperatureError",
]

try:
    from preservationeval._version import version as __version__
except ImportError:
    __version__ = "unknown"
