"""Unit tests for core_functions moudle in the preservationeval package.

This module provides unit tests for the core functions in the
preservationeval package, covering various scenarios and edge cases.
"""

import numpy as np
import pytest

from preservationeval.core_functions import emc, mold, pi
from preservationeval.types import (
    LookupTable,
    MoistureContent,
    MoldRisk,
    PreservationIndex,
    RelativeHumidity,
    TableIndex,
    Temperature,
)
from preservationeval.types.exceptions import (
    HumidityError,
    PreservationError,
    TemperatureError,
)

# Test data
VALID_TEMP: Temperature = 20.0
VALID_RH: RelativeHumidity = 50.0


# Mock LookupTable instances for testing
class MockLookupTable(LookupTable):
    def __init__(self, data: list[list[float]], temp_min: int, rh_min: int):
        super().__init__(data, temp_min, rh_min)

    def __getitem__(self, index: TableIndex) -> float:
        return super().__getitem__(index)


def test_pi_valid_input() -> None:
    # Mock pi_table with valid data
    pi_table = MockLookupTable(np.array([[1.0, 2.0], [3.0, 4.0]]), 0, 0)
    result: PreservationIndex = pi(VALID_TEMP, VALID_RH)
    assert isinstance(result, (int | float))
    assert result > 0


def test_pi_invalid_temperature() -> None:
    with pytest.raises(TemperatureError):
        pi(1000.0, VALID_RH)


def test_pi_invalid_humidity() -> None:
    with pytest.raises(HumidityError):
        pi(VALID_TEMP, 150.0)


def test_pi_unexpected_error() -> None:
    # Mock pi_table to raise an unexpected error
    class MockPiTable(MockLookupTable):
        def __getitem__(self, index: TableIndex) -> float:
            raise Exception("Unexpected error")

    pi_table = MockPiTable([[1.0, 2.0], [3.0, 4.0]], 0, 0)
    with pytest.raises(PreservationError):
        pi(VALID_TEMP, VALID_RH)


def test_mold_valid_input() -> None:
    # Mock mold_table with valid data
    mold_table = MockLookupTable([[1.0, 2.0], [3.0, 4.0]], 0, 0)
    result: MoldRisk = mold(VALID_TEMP, VALID_RH)
    assert isinstance(result, (int, float))
    assert result >= 0


def test_mold_no_risk() -> None:
    result: MoldRisk = mold(1.0, 60.0)  # Below risk thresholds
    assert result == 0.0


def test_mold_invalid_input() -> None:
    with pytest.raises(ValueError):
        mold(VALID_TEMP, 150.0)


def test_mold_unexpected_error() -> None:
    # Mock mold_table to raise an unexpected error
    class MockMoldTable(MockLookupTable):
        def __getitem__(self, index: TableIndex) -> float:
            raise Exception("Unexpected error")

    mold_table = MockMoldTable([[1.0, 2.0], [3.0, 4.0]], 0, 0)
    with pytest.raises(PreservationError):
        mold(VALID_TEMP, VALID_RH)


def test_emc_valid_input() -> None:
    # Mock emc_table with valid data
    emc_table = MockLookupTable([[1.0, 2.0], [3.0, 4.0]], 0, 0)
    result: MoistureContent = emc(VALID_TEMP, VALID_RH)
    assert isinstance(result, float)
    assert 0 <= result <= 100


def test_emc_invalid_temperature() -> None:
    with pytest.raises(TemperatureError):
        emc(1000.0, VALID_RH)


def test_emc_invalid_humidity() -> None:
    with pytest.raises(HumidityError):
        emc(VALID_TEMP, 150.0)


def test_emc_unexpected_error() -> None:
    # Mock emc_table to raise an unexpected error
    class MockEmcTable(MockLookupTable):
        def __getitem__(self, index: TableIndex) -> float:
            raise Exception("Unexpected error")

    emc_table = MockEmcTable([[1.0, 2.0], [3.0, 4.0]], 0, 0)
    with pytest.raises(PreservationError):
        emc(VALID_TEMP, VALID_RH)


def test_lookup_table_init() -> None:
    # Test LookupTable initialization with valid data
    data = np.array([[1.0, 2.0], [3.0, 4.0]])
    temp_min = 0
    rh_min = 0
    table = LookupTable(data, temp_min, rh_min)
    assert table.data == data
    assert table.temp_min == temp_min
    assert table.rh_min == rh_min


def test_lookup_table_getitem() -> None:
    # Test LookupTable __getitem__ with valid index
    data = [[1.0, 2.0], [3.0, 4.0]]
    temp_min = 0
    rh_min = 0
    table = LookupTable(data, temp_min, rh_min)
    index = (0, 0)
    result = table[index]
    assert result == data[0][0]


def test_lookup_table_getitem_out_of_range() -> None:
    # Test LookupTable __getitem__ with out-of-range index
    data = [[1.0, 2.0], [3.0, 4.0]]
    temp_min = 0
    rh_min = 0
    table = LookupTable(data, temp_min, rh_min)
    index = (2, 2)  # Out of range
    with pytest.raises(IndexError):
        table[index]
