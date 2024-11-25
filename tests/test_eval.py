"""Unit tests for preservation environment evaluation functions.

This module provides unit tests for the evaluation functions in the
preservationeval.eval module, covering various scenarios and edge cases.
"""

# pylint: disable=missing-docstring

import pytest

from preservationeval.eval_functions import (
    EnvironmentalRating,
    rate_mechanical_damage,
    rate_metal_corrosion,
    rate_mold_growth,
    rate_natural_aging,
)


@pytest.mark.unit
def test_pi_is_numeric() -> None:
    with pytest.raises(TypeError):
        rate_natural_aging("string")  # type: ignore


@pytest.mark.unit
def test_pi_is_non_negative() -> None:
    with pytest.raises(ValueError):
        rate_natural_aging(-1)


@pytest.mark.unit
def test_pi_good() -> None:
    assert rate_natural_aging(75) == EnvironmentalRating.GOOD
    assert rate_natural_aging(100) == EnvironmentalRating.GOOD


@pytest.mark.unit
def test_pi_ok() -> None:
    assert rate_natural_aging(50) == EnvironmentalRating.OK
    assert rate_natural_aging(74) == EnvironmentalRating.OK


@pytest.mark.unit
def test_pi_risk() -> None:
    assert rate_natural_aging(0) == EnvironmentalRating.RISK
    assert rate_natural_aging(44) == EnvironmentalRating.RISK


@pytest.mark.unit
def test_rate_mechanical_damage_within_range() -> None:
    assert rate_mechanical_damage(5) == EnvironmentalRating.OK
    assert rate_mechanical_damage(10) == EnvironmentalRating.OK
    assert rate_mechanical_damage(12.5) == EnvironmentalRating.OK


@pytest.mark.unit
def test_rate_mechanical_damage_below_range() -> None:
    assert rate_mechanical_damage(4.9) == EnvironmentalRating.RISK


@pytest.mark.unit
def test_rate_mechanical_damage_above_range() -> None:
    assert rate_mechanical_damage(12.6) == EnvironmentalRating.RISK


@pytest.mark.unit
def test_rate_mechanical_damage_non_numeric_input() -> None:
    with pytest.raises(TypeError):
        rate_mechanical_damage("non-numeric")  # type: ignore


@pytest.mark.unit
def test_rate_mechanical_damage_negative_input() -> None:
    with pytest.raises(ValueError):
        rate_mechanical_damage(-1.0)


@pytest.mark.unit
def test_rate_mold_growth_no_risk() -> None:
    assert rate_mold_growth(0) == EnvironmentalRating.GOOD


@pytest.mark.unit
def test_rate_mold_growth_with_risk() -> None:
    assert rate_mold_growth(1) == EnvironmentalRating.RISK
    assert rate_mold_growth(10) == EnvironmentalRating.RISK


@pytest.mark.unit
def test_rate_mold_growth_non_numeric_input() -> None:
    with pytest.raises(TypeError):
        rate_mold_growth("non-numeric")  # type: ignore


@pytest.mark.unit
def test_rate_mold_growth_negative_input() -> None:
    with pytest.raises(ValueError):
        rate_mold_growth(-1.0)


@pytest.mark.unit
def test_rate_metal_corrosion_good() -> None:
    assert rate_metal_corrosion(6) == EnvironmentalRating.GOOD
    assert rate_metal_corrosion(0) == EnvironmentalRating.GOOD
    assert rate_metal_corrosion(6.98) == EnvironmentalRating.GOOD


@pytest.mark.unit
def test_rate_metal_corrosion_ok() -> None:
    assert rate_metal_corrosion(7.1) == EnvironmentalRating.OK
    assert rate_metal_corrosion(10.4) == EnvironmentalRating.OK
    assert rate_metal_corrosion(7) == EnvironmentalRating.OK
    assert rate_metal_corrosion(10) == EnvironmentalRating.OK
    assert rate_metal_corrosion(7.0) == EnvironmentalRating.OK


@pytest.mark.unit
def test_rate_metal_corrosion_risk() -> None:
    assert rate_metal_corrosion(10.5) == EnvironmentalRating.RISK
    assert rate_metal_corrosion(11) == EnvironmentalRating.RISK


@pytest.mark.unit
def test_rate_metal_corrosion_non_numeric_input() -> None:
    with pytest.raises(TypeError):
        rate_metal_corrosion("non-numeric")  # type: ignore


@pytest.mark.unit
def test_rate_metal_corrosion_negative_input() -> None:
    with pytest.raises(ValueError):
        rate_metal_corrosion(-1.0)
