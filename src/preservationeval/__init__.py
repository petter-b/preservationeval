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

    TODO: Improve this docstring to explain the complete content of __all__.
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
from .util_functions import calculate_dew_point, to_celsius, validate_rh, validate_temp

__all__ = [
    "EnvironmentalRating",
    "HumidityError",
    "IndexRangeError",
    "MoistureContent",
    "MoldRisk",
    "PreservationError",
    "PreservationIndex",
    "RelativeHumidity",
    "Temperature",
    "TemperatureError",
    "__version__",
    "calculate_dew_point",
    "emc",
    "mold",
    "pi",
    "rate_mechanical_damage",
    "rate_metal_corrosion",
    "rate_mold_growth",
    "rate_natural_aging",
    "to_celsius",
    "validate_rh",
    "validate_temp",
]

try:
    from ._version import version as __version__
except ImportError:
    __version__ = "0.0.0"
