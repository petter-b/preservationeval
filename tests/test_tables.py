# Standard library imports

# Third-party imports
import numpy as np
import pytest

# Package imports
from preservationeval.tables import fetch_and_validate_tables
from preservationeval.shifted_array import (
    IndexRangeError,
)


def test_table_shapes() -> None:
    """Test if tables have expected shapes and dimensions."""
    pi_table, emc_table, mold_table = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")

    # Check shapes
    assert pi_table.data.shape == (89, 90)  # PI table shape
    assert emc_table.data.shape == (86, 101)  # EMC table shape
    assert mold_table.data.shape == (44, 36)  # Mold table shape


def test_table_ranges() -> None:
    """Test if tables have correct index ranges."""
    pi_table, emc_table, mold_table = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")

    # Check ranges
    assert pi_table.x_min == -23
    assert pi_table.y_min == 6

    assert emc_table.x_min == -20
    assert emc_table.y_min == 0

    assert mold_table.x_min == 2
    assert mold_table.y_min == 65


def test_boundary_behavior() -> None:
    """Test boundary behaviors of tables."""
    pi_table, emc_table, mold_table = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")

    # PI table should clamp
    assert pi_table[-24, 7] == pi_table[-23, 7]  # x below min
    assert pi_table[-23, 5] == pi_table[-23, 6]  # y below min

    # EMC table should clamp
    assert emc_table[-21, 0] == emc_table[-20, 0]  # x below min
    assert emc_table[-20, -1] == emc_table[-20, 0]  # y below min

    # Mold table should raise
    with pytest.raises(IndexRangeError):
        mold_table[1, 65]  # x below min
    with pytest.raises(IndexRangeError):
        mold_table[2, 64]  # y below min


def test_valid_lookups() -> None:
    """Test some known valid lookup values."""
    pi_table, emc_table, mold_table = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")

    # Test some known values (you'll need to replace these with actual known values)
    assert pi_table[20, 50] > 0
    assert 0 <= emc_table[20, 50] <= 30
    assert mold_table[20, 80] >= 0


def test_data_types() -> None:
    """Test if tables have correct data types."""
    pi_table, emc_table, mold_table = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")

    assert pi_table.data.dtype == np.int32
    assert emc_table.data.dtype == np.float64
    assert mold_table.data.dtype == np.int32
