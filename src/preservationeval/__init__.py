"""
preservationeval - Preservation Environment Calculator

A Python implementation of the dpcalc.org preservation calculator.
Evaluates preservation environments based on temperature and relative humidity.

Main functions:
    pi(): Calculate Preservation Index
    emc(): Calculate Equilibrium Moisture Content
    mold(): Calculate Mold Risk Factor
    rate_*(): Evaluate environmental ratings
"""

# Version management
try:
    from importlib.metadata import version

    __version__ = version("preservationeval")
except ImportError:  # pragma: no cover
    __version__ = "unknown"

# Public API - evaluation functions
from .eval import (
    EnvironmentalRating,
    rate_mechanical_damage,
    rate_metal_corrosion,
    rate_mold_growth,
    rate_natural_aging,
)

# Public API - core calculation functions
from .lookup import emc, mold, pi

# Public API - types for type hints
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

__all__ = [
    # Version
    "__version__",
    # Core functions
    "pi",
    "emc",
    "mold",
    # Evaluation functions
    "EnvironmentalRating",
    "rate_mechanical_damage",
    "rate_metal_corrosion",
    "rate_mold_growth",
    "rate_natural_aging",
    # Types
    "Temperature",
    "RelativeHumidity",
    "PreservationIndex",
    "MoldRisk",
    "MoistureContent",
    # Exceptions
    "PreservationError",
    "IndexRangeError",
    "TemperatureError",
    "HumidityError",
]
