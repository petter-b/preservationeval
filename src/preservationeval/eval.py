"""Evaluation functions for preservation environments.

This module provides functions to evaluate the risk of various types of damage
to materials in a preservation environment, based on factors such as temperature,
relative humidity, and moisture content.

The functions in this module return an `EnvironmentalRating` enum value,
indicating the level of risk associated with the given conditions.
"""

from enum import Enum

from .types import MoistureContent, MoldRisk, PreservationIndex

__all__ = [
    "EnvironmentalRating",
    "rate_mold_growth",
    "rate_natural_aging",
    "rate_mechanical_damage",
    "rate_metal_corrosion",
]


class EnvironmentalRating(Enum):
    """Enum for environmental ratings.

    Values:
        GOOD: No damage risk
        OK: Low damage risk
        RISK: High damage risk
    """

    GOOD = "GOOD"
    OK = "OK"
    RISK = "RISK"


def rate_natural_aging(pi: PreservationIndex) -> EnvironmentalRating:
    """Evaluate Natural Aging risk as a function of Preservation Index (PI).

    Natural Aging is the chemical breakdown of materials over time. A higher
    Preservation Index (PI) indicates a slower rate of chemical breakdown.

    Args:
        pi (PreservationIndex): The Preservation Index value.

    Returns:
        EnvironmentalRating: The environmental rating based on PI.
            - GOOD: If PI is ≥75, indicating low risk
            - OK: If PI is between 45 and 75, indicating moderate risk
            - RISK: If PI is <45, indicating high risk
    """
    if not isinstance(pi, (int | float)):
        raise TypeError(f"Preservation Index must be numeric, got {type(pi).__name__}")
    if pi < 0:
        raise ValueError(f"Preservation Index must be non-negative, got {pi}")
    if pi >= 75:
        return EnvironmentalRating.GOOD
    elif pi < 45:
        return EnvironmentalRating.RISK
    else:
        return EnvironmentalRating.OK


def rate_mechanical_damage(emc: MoistureContent) -> EnvironmentalRating:
    """Evaluate the risk of Mechanical Damage as a function of EMC.

    Args:
        emc (MoistureContent): The Equilibrium Moisture Content (EMC) value.

    Returns:
        EnvironmentalRating: The environmental rating based on EMC.
            - OK: If EMC is between 5 and 12.5
            - RISK: If EMC is outside the range 5-12.5
    """
    if not isinstance(emc, (int | float)):
        raise TypeError(f"Moisture Content must be numeric, got {type(emc).__name__}")
    if emc < 0:
        raise ValueError(f"Moisture Content must be non-negative, got {emc}")
    if 5 <= emc <= 12.5:
        return EnvironmentalRating.OK
    else:
        return EnvironmentalRating.RISK


def rate_mold_growth(mrf: MoldRisk) -> EnvironmentalRating:
    """Evaluate the risk of Mold Growth as a function of Mold Risk Factor (MRF).

    Args:
        mrf (MoldRisk): The Mold Risk Factor value.

    Returns:
        EnvironmentalRating: The environmental rating based on MRF.
            - GOOD: If MRF is 0 (No Risk)
            - RISK: If MRF is >0 (Risk, value represents days to mold)
    """
    if not isinstance(mrf, (int | float)):
        raise TypeError(f"Mold Risk Factor must be numeric, got {type(mrf).__name__}")
    if mrf < 0:
        raise ValueError(f"Mold Risk Factor must be non-negative, got {mrf}")
    if mrf == 0:
        return EnvironmentalRating.GOOD
    else:
        return EnvironmentalRating.RISK


def rate_metal_corrosion(emc: MoistureContent) -> EnvironmentalRating:
    """Evaluate the risk of Metal Corrosion as a function of EMC.

    Args:
        emc (MoistureContent): The Equilibrium Moisture Content (EMC) value.

    Returns:
        EnvironmentalRating: The environmental rating based on EMC.
            - GOOD: If EMC is <7.0
            - OK: If EMC is between 7.0 and 10.5
            - RISK: If EMC is ≥10.5
    """
    if not isinstance(emc, (int | float)):
        raise TypeError(f"Moisture Content must be numeric, got {type(emc).__name__}")
    if emc < 0:
        raise ValueError(f"Moisture Content must be non-negative, got {emc}")
    if emc < 7.0:
        return EnvironmentalRating.GOOD
    elif emc < 10.5:
        return EnvironmentalRating.OK
    else:
        return EnvironmentalRating.RISK
