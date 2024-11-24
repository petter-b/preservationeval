"""Preservation environment calculation and evaluation.

This package provides tools to calculate and evaluate indoor climate conditions
for preservation of materials and objects. It also provides tools for
evaluating the risk of various types of damage to materials, such as mold,
mechanical damage, and metal corrosion, based on temperature and relative
humidity.

Main functions:
    pi(): Calculate Preservation Index
    emc(): Calculate Equilibrium Moisture Content
    mold(): Calculate Mold Risk Factor
    rate_*(): Evaluate environmental ratings
"""

from .core_functions import emc, mold, pi
from .eval_functions import (
    EnvironmentalRating,
    rate_mechanical_damage,
    rate_metal_corrosion,
    rate_mold_growth,
    rate_natural_aging,
)
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
    # Evaluation functions
    "EnvironmentalRating",
    "HumidityError",
    "IndexRangeError",
    "MoistureContent",
    "MoldRisk",
    # Exceptions
    "PreservationError",
    "PreservationIndex",
    "RelativeHumidity",
    # Types
    "Temperature",
    "TemperatureError",
    # Version
    "__version__",
    "emc",
    "mold",
    # Core functions
    "pi",
    "rate_mechanical_damage",
    "rate_metal_corrosion",
    "rate_mold_growth",
    "rate_natural_aging",
]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0"
