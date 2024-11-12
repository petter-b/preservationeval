from typing import List, Protocol, Tuple

import pytest

from preservationeval.lookup import (
    EMCTable,
    LookupTable,
    TableIndex,
    emc,
    emc_table,
    mold,
    pi,
)
from preservationeval.types import RelativeHumidity, Temperature


@pytest.mark.parametrize(
    "input_val,expected",
    [
        (3.5, 4),  # Round up
        (3.4, 3),  # Round down
        (-3.5, -3),  # Negative round up
        (-3.6, -4),  # Negative round down
        (0.5, 1),  # Half way positive
        (-0.5, 0),  # Half way negative
        (0.0, 0),  # Zero
    ],
)
def test_round_half_up(input_val: float, expected: int) -> None:
    """Test rounding behavior matches JavaScript Math.round()."""
    assert LookupTable._round_half_up(input_val) == expected


def test_javascript_equivalence() -> None:
    """Test specific cases known to work in JavaScript."""
    cases = [
        # Format: (temp, rh, expected_pi, expected_emc, expected_mold)
        (-2.5, 45.5, 943, 9.2, 0),
        (-12.5, 24.0, 9124, 5.1, 0),
        (-6.5, 85.5, 483, 17.9, 0),
        # Add more cases from your difference logs
    ]

    EMC_TOLERANCE = 0.1  # EMC values are only accurate to 0.1

    for temp, rh, exp_pi, exp_emc, exp_mold in cases:
        # Test PI
        py_pi = pi(temp, rh)
        assert py_pi == exp_pi, (
            f"PI mismatch at T={temp}, RH={rh}: " f"got {py_pi}, expected {exp_pi}"
        )

        # Test EMC with appropriate tolerance
        py_emc = emc(temp, rh)
        assert abs(py_emc - exp_emc) < EMC_TOLERANCE, (
            f"EMC mismatch at T={temp}, RH={rh}: " f"got {py_emc}, expected {exp_emc}"
        )

        # Test Mold
        py_mold = mold(temp, rh)
        assert py_mold == exp_mold, (
            f"Mold mismatch at T={temp}, RH={rh}: "
            f"got {py_mold}, expected {exp_mold}"
        )


def test_emc_table_lookup() -> None:
    """Test EMC table lookup behavior."""
    from preservationeval.lookup import emc_table

    # Test specific points
    test_cases = [
        # (temp, rh, expected_emc)
        (-2.5, 45.5, 9.2),
        (-2.0, 45.0, 9.1),
        (-2.0, 46.0, 9.3),
    ]

    for temp, rh, expected in test_cases:
        result = emc_table[temp, rh]
        assert abs(result - expected) < 0.1, (
            f"EMC lookup mismatch at T={temp}, RH={rh}: "
            f"got {result}, expected {expected}"
        )


def test_emc_table_structure() -> None:
    """Verify EMC table structure and some known values."""
    from preservationeval.lookup import emc_table

    # Verify table properties
    assert emc_table.temp_min == -20, "EMC table should start at -20°C"
    assert emc_table.rh_min == 0, "EMC table should start at 0% RH"
    assert emc_table.data.shape == (86, 101), "EMC table should be 86x101"

    # Print some values around our test point
    t, rh = -2.5, 45.5
    t_idx = int(t - emc_table.temp_min + 0.5)
    rh_idx = int(rh - emc_table.rh_min + 0.5)

    print(f"\nEMC values around T={t}, RH={rh}:")
    for i in range(max(0, t_idx - 1), min(emc_table.data.shape[0], t_idx + 2)):
        for j in range(max(0, rh_idx - 1), min(emc_table.data.shape[1], rh_idx + 2)):
            actual_t = i + emc_table.temp_min
            actual_rh = j + emc_table.rh_min
            value = emc_table.data[i, j]
            print(f"T={actual_t:4.1f}, RH={actual_rh:4.1f}: {value:4.1f}")


def analyze_emc_lookup(temp: float, rh: float) -> None:
    """Analyze how EMC lookup works for specific values."""
    from preservationeval.lookup import emc_table

    # Calculate raw indices
    temp_raw = temp - emc_table.temp_min
    rh_raw = rh - emc_table.rh_min

    # Round indices
    temp_idx = int(temp_raw + 0.5)
    rh_idx = int(rh_raw + 0.5)

    print(f"\nEMC lookup analysis for T={temp}, RH={rh}:")
    print("Temperature:")
    print(f"  Base: {emc_table.temp_min}")
    print(f"  Raw index: {temp} - ({emc_table.temp_min}) = {temp_raw}")
    print(f"  Rounded index: int({temp_raw} + 0.5) = {temp_idx}")
    print(f"  Maps to temperature: {temp_idx + emc_table.temp_min}")

    print("\nRelative Humidity:")
    print(f"  Base: {emc_table.rh_min}")
    print(f"  Raw index: {rh} - {emc_table.rh_min} = {rh_raw}")
    print(f"  Rounded index: int({rh_raw} + 0.5) = {rh_idx}")
    print(f"  Maps to RH: {rh_idx + emc_table.rh_min}")

    value = emc_table.data[temp_idx, rh_idx]
    print(f"\nLookup value: {value}")


def test_emc_single_case() -> None:
    """Test one specific EMC case in detail."""
    from preservationeval.lookup import emc_table

    # Test case
    temp, rh = -2.5, 45.5
    expected = 9.2

    # Calculate indices
    temp_idx = int((temp - emc_table.temp_min) + 0.5)
    rh_idx = int((rh - emc_table.rh_min) + 0.5)

    print(f"\nEMC table lookup for T={temp}, RH={rh}:")
    print("Temperature:")
    print(f"  Raw: {temp} - ({emc_table.temp_min}) = {temp - emc_table.temp_min}")
    print(f"  Index: {temp_idx} (maps to {temp_idx + emc_table.temp_min}°C)")

    print("Relative Humidity:")
    print(f"  Raw: {rh} - {emc_table.rh_min} = {rh - emc_table.rh_min}")
    print(f"  Index: {rh_idx} (maps to {rh_idx + emc_table.rh_min}%)")

    # Get actual value
    result = emc_table.data[temp_idx, rh_idx]
    print(f"\nTable value at [{temp_idx}, {rh_idx}]: {result}")
    print(f"Expected value: {expected}")


def test_emc_table_values() -> None:
    """Verify some known EMC table values."""
    from preservationeval.lookup import emc_table

    # Print the actual data structure
    print("\nEMC table properties:")
    print(f"Shape: {emc_table.data.shape}")
    print(
        f"Temperature range: {emc_table.temp_min} to "
        f"{emc_table.temp_min + emc_table.data.shape[0] - 1}"
    )
    print(
        f"RH range: {emc_table.rh_min} to "
        f"{emc_table.rh_min + emc_table.data.shape[1] - 1}"
    )

    # Check a few known values
    known_values = [
        # temp, rh, expected_emc
        (-2.5, 45.5, 9.2),
        (-2.0, 45.0, 9.1),
        (-2.0, 46.0, 9.3),
    ]

    for temp, rh, expected in known_values:
        temp_idx = int((temp - emc_table.temp_min) + 0.5)
        rh_idx = int((rh - emc_table.rh_min) + 0.5)
        actual = emc_table.data[temp_idx, rh_idx]
        print(f"\nT={temp}, RH={rh}:")
        print(f"  Indices: [{temp_idx}, {rh_idx}]")
        print(f"  Value: {actual}")
        print(f"  Expected: {expected}")


class TableLookup(Protocol):
    def __call__(self, indices: TableIndex) -> float: ...


def test_emc_full_trace() -> None:
    """Trace the complete EMC calculation process."""

    temp: Temperature = -2.5
    rh: RelativeHumidity = 45.5
    expected: float = 9.2

    print("\nInput values:")
    print(f"Temperature: {temp}")
    print(f"RH: {rh}")

    # Define trace function with proper type hints
    def trace_lookup(indices: TableIndex) -> float:
        print(f"\nLookup called with: {indices}")
        return emc_table.__getitem__(indices)

    # Verify type compatibility
    lookup_func: TableLookup = trace_lookup

    # Temporarily replace the lookup function
    original_getitem = emc_table.__getitem__
    emc_table.__getitem__ = lookup_func  # type: ignore

    try:
        result = emc(temp, rh)
        print(f"\nResult: {result}")
        print(f"Expected: {expected}")
    finally:
        # Restore original function
        emc_table.__getitem__ = original_getitem  # type: ignore


def test_emc_table_values_around_point() -> None:
    """Print EMC table values around the test point."""
    from preservationeval.lookup import emc_table

    temp, rh = -2.5, 45.5

    # Calculate the base indices
    temp_idx = int((temp - emc_table.temp_min) + 0.5)
    rh_idx = int((rh - emc_table.rh_min) + 0.5)

    print(f"\nEMC table values around T={temp}, RH={rh}:")
    print(f"Base indices: [{temp_idx}, {rh_idx}]")

    # Look at values in a 3x3 grid around the point
    for t_offset in [-1, 0, 1]:
        t_idx = temp_idx + t_offset
        actual_t = t_idx + emc_table.temp_min
        for rh_offset in [-1, 0, 1]:
            r_idx = rh_idx + rh_offset
            actual_rh = r_idx + emc_table.rh_min
            value = emc_table.data[t_idx, r_idx]
            print(f"T={actual_t:5.1f}, RH={actual_rh:5.1f}: {value:5.1f}")


def test_temperature_handling() -> None:
    """Test that temperature values are not pre-rounded."""
    from preservationeval.lookup import emc_table

    # Test cases with explicit temperature values
    cases = [
        # (input_temp, input_rh, expected_temp_in_lookup)
        (-2.5, 45.5, -2.5),  # Should remain -2.5, not -2.0
        (-12.5, 24.0, -12.5),  # Should remain -12.5
        (-6.5, 85.5, -6.5),  # Should remain -6.5
    ]

    def trace_temp(temp: float, rh: float) -> float:
        """Trace the actual temperature value used in lookup."""
        print(f"\nInput temperature: {temp}")
        return emc_table[temp, rh]

    for input_temp, input_rh, expected_temp in cases:
        print(f"\nTesting temperature: {input_temp}")
        result = trace_temp(input_temp, input_rh)
        print(f"Result: {result}")


def test_emc_input_preservation() -> None:
    """Test that EMC calculation preserves input values."""
    actual_inputs: List[Tuple[Temperature, RelativeHumidity]] = []
    original_getitem = emc_table.__getitem__

    # Add proper type hint for the test function
    def capture_inputs(
        self: EMCTable, indices: tuple[Temperature, RelativeHumidity]
    ) -> float:
        temp, rh = indices
        actual_inputs.append((temp, rh))
        return original_getitem(indices)

    try:
        # Replace just the method, not the entire table
        emc_table.__class__.__getitem__ = capture_inputs  # type: ignore

        # Test with specific values
        temp: Temperature = -2.5
        rh: RelativeHumidity = 45.5
        _ = emc(temp, rh)

        # Check captured inputs
        assert len(actual_inputs) == 1, "Expected exactly one table lookup"
        actual_temp, actual_rh = actual_inputs[0]
        assert actual_temp == temp, f"Temperature modified: {temp} -> {actual_temp}"
        assert actual_rh == rh, f"RH modified: {rh} -> {actual_rh}"

    finally:
        # Restore original method
        emc_table.__class__.__getitem__ = original_getitem  # type: ignore
