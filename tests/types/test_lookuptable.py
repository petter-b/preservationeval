"""Test module for preservationeval.table_types.lookuptable."""

from typing import Any, Final

import numpy as np
import pytest
from numpy import floating, integer
from numpy.typing import NDArray

from preservationeval.table_types.exceptions import HumidityError, TemperatureError
from preservationeval.table_types.lookuptable import (
    BoundaryBehavior,
    LookupTable,
    TableIndex,
)

# Test Constants
TEMP_MIN: Final[int] = -20
TEMP_MAX: Final[int] = 65
RH_MIN: Final[int] = 0
RH_MAX: Final[int] = 100


# Test Fixtures
@pytest.fixture
def int_test_data() -> NDArray[integer[Any]]:
    """Create test data for integer table."""
    rows = TEMP_MAX - TEMP_MIN + 1
    cols = RH_MAX - RH_MIN + 1
    return np.arange(rows * cols, dtype=np.int32).reshape(rows, cols)


@pytest.fixture
def float_test_data() -> NDArray[floating[Any]]:
    """Create test data for float table."""
    rows = TEMP_MAX - TEMP_MIN + 1
    cols = RH_MAX - RH_MIN + 1
    return np.arange(rows * cols, dtype=np.float32).reshape(rows, cols) / 10.0


@pytest.fixture
def int_table(int_test_data: NDArray[integer[Any]]) -> LookupTable[int]:
    """Create integer lookup table."""
    return LookupTable[int](int_test_data, TEMP_MIN, RH_MIN)


@pytest.fixture
def float_table(float_test_data: NDArray[floating[Any]]) -> LookupTable[float]:
    """Create float lookup table."""
    return LookupTable[float](float_test_data, TEMP_MIN, RH_MIN)


@pytest.fixture
def clamp_table(int_test_data: NDArray[integer[Any]]) -> LookupTable[int]:
    """Create table with clamping behavior."""
    return LookupTable[int](
        int_test_data, TEMP_MIN, RH_MIN, boundary_behavior=BoundaryBehavior.CLAMP
    )


# Test Classes
@pytest.mark.unit
class TestLookupTableBasics:
    """Test basic LookupTable functionality."""

    def test_creation(self, int_test_data: NDArray[integer[Any]]) -> None:
        """Test table creation with valid data."""
        table = LookupTable[int](int_test_data, TEMP_MIN, RH_MIN)
        assert table.temp_min == TEMP_MIN
        assert table.temp_max == TEMP_MAX
        assert table.rh_min == RH_MIN
        assert table.rh_max == RH_MAX

    def test_invalid_data(self) -> None:
        """Test table creation with invalid data."""
        with pytest.raises(TypeError):
            LookupTable[int]([1, 2, 3], 0, 0)  # type: ignore

        with pytest.raises(ValueError):
            LookupTable[int](np.array([1, 2, 3]), 0, 0)  # 1D array

    def test_str_representation(self, int_table: LookupTable[int]) -> None:
        """Test string representation."""
        str_rep = str(int_table)
        assert str(int_table.data.shape) in str_rep
        assert str(int_table.data.dtype) in str_rep
        assert f"{TEMP_MIN}..{TEMP_MAX}" in str_rep
        assert f"{RH_MIN}..{RH_MAX}" in str_rep


@pytest.mark.unit
class TestLookupTableAccess:
    """Test table access and indexing."""

    @pytest.mark.parametrize(
        "indices",
        [
            (0, 50),  # Integer indices
            (0.0, 50.0),  # Float indices
            (-10, 75),  # Negative temperature
            (20.5, 49.8),  # Fractional values
        ],
    )
    def test_valid_access(
        self, int_table: LookupTable[int], indices: TableIndex
    ) -> None:
        """Test valid table access."""
        value = int_table[indices]
        assert isinstance(value, (int | np.integer))

    @pytest.mark.parametrize(
        "indices",
        [
            ("20", 50),  # String temperature
            (20, "50"),  # String humidity
            ([20], 50),  # List temperature
            (20, [50]),  # List humidity
        ],
    )
    def test_invalid_types(
        self, int_table: LookupTable[int], indices: tuple[Any, Any]
    ) -> None:
        """Test access with invalid index types."""
        with pytest.raises(TypeError):
            _ = int_table[indices]


@pytest.mark.unit
class TestBoundaryBehavior:
    """Test boundary handling behavior."""

    @pytest.mark.parametrize(
        "indices,expected_error",
        [
            ((TEMP_MIN - 1, 50), TemperatureError),  # Below temp min
            ((TEMP_MAX + 1, 50), TemperatureError),  # Above temp max
            ((20, RH_MIN - 1), HumidityError),  # Below RH min
            ((20, RH_MAX + 1), HumidityError),  # Above RH max
        ],
    )
    def test_raise_behavior(
        self,
        int_table: LookupTable[int],
        indices: TableIndex,
        expected_error: type[Exception],
    ) -> None:
        """Test RAISE boundary behavior."""
        with pytest.raises(expected_error):
            _ = int_table[indices]

    @pytest.mark.parametrize(
        "indices,expected_indices",
        [
            ((TEMP_MIN - 1, 50), (TEMP_MIN, 50)),  # Clamp temp below
            ((TEMP_MAX + 1, 50), (TEMP_MAX, 50)),  # Clamp temp above
            ((20, RH_MIN - 1), (20, RH_MIN)),  # Clamp RH below
            ((20, RH_MAX + 1), (20, RH_MAX)),  # Clamp RH above
        ],
    )
    def test_clamp_behavior(
        self,
        clamp_table: LookupTable[int],
        indices: TableIndex,
        expected_indices: TableIndex,
    ) -> None:
        """Test CLAMP boundary behavior."""
        value = clamp_table[indices]
        expected_value = clamp_table[expected_indices]
        assert value == expected_value


@pytest.mark.unit
class TestRounding:
    """Test rounding behavior."""

    @pytest.mark.parametrize(
        "value,expected",
        [
            (1.4, 1),  # Round down
            (1.5, 2),  # Round up at .5
            (1.6, 2),  # Round up
            (-1.4, -1),  # Negative round down
            (-1.5, -1),  # Negative round up at .5
            (-1.6, -2),  # Negative round up
        ],
    )
    def test_round_half_up(
        self, int_table: LookupTable[int], value: float, expected: int
    ) -> None:
        """Test round half up function."""
        assert int_table._round_half_up(value) == expected

    def test_custom_rounding(self, int_test_data: NDArray[integer[Any]]) -> None:
        """Test custom rounding function."""
        table = LookupTable[int](
            int_test_data,
            TEMP_MIN,
            RH_MIN,
            rounding_func=lambda x: int(x),  # Simple truncation
        )
        assert table[(1.8, 50.0)] == table[(1.0, 50.0)]
