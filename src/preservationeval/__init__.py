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

from importlib.metadata import version

from .main.core import emc, mold, pi
from .main.eval import (
    EnvironmentalRating,
    rate_mechanical_damage,
    rate_metal_corrosion,
    rate_mold_growth,
    rate_natural_aging,
)
from .main.types import (
    MoistureContent,
    MoldRisk,
    PreservationIndex,
    RelativeHumidity,
    Temperature,
)
from .table_types import (
    HumidityError,
    IndexRangeError,
    PreservationError,
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

__version__ = version("preservationeval")
