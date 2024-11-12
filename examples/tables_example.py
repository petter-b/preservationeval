# Standard library imports

# Package imports
from preservationeval.install.parse import fetch_and_validate_tables
from preservationeval.logging import LogConfig, LogLevel, setup_logging
from preservationeval.lookup import EMCTable, MoldTable, PITable
from preservationeval.types import IndexRangeError

# Set up logging
config = LogConfig(
    level=LogLevel.DEBUG,
    console_output=True,
)

logger = setup_logging(__name__, config)


def example_usage() -> None:
    """Example of how to use the table fetching and validation code."""
    logger.debug("Starting example_usage function. Debug level == DEBUG")

    try:
        logger.debug("Attempting to fetch tables from website")

        # Fetch tables from the website
        pi_table, emc_table, mold_table = fetch_and_validate_tables(
            "http://www.dpcalc.org/dp.js"
        )

        # Print information about each table
        print("\nTable Information:")
        print("=================")

        print("\nPI Table:")
        print(f"Temperature range: {pi_table.temp_min}°C to {pi_table.temp_max}°C")
        print(f"RH range: {pi_table.rh_min}% to {pi_table.rh_max}%")
        print(f"Shape: {pi_table.data.shape}")
        print("Data statistics:")
        print(f"  Min value: {pi_table.data.min()}")
        print(f"  Max value: {pi_table.data.max()}")
        print(f"  Mean value: {pi_table.data.mean():.1f}")

        print("\nEMC Table:")
        print(f"Temperature range: {emc_table.temp_min}°C to {emc_table.temp_max}°C")
        print(f"RH range: {emc_table.rh_min}% to {emc_table.rh_max}%")
        print(f"Shape: {emc_table.data.shape}")
        print("Data statistics:")
        print(f"  Min value: {emc_table.data.min():.1f}")
        print(f"  Max value: {emc_table.data.max():.1f}")
        print(f"  Mean value: {emc_table.data.mean():.1f}")

        print("\nMold Table:")
        print(f"Temperature range: {mold_table.temp_min}°C to {mold_table.temp_max}°C")
        print(f"RH range: {mold_table.rh_min}% to {mold_table.rh_max}%")
        print(f"Shape: {mold_table.data.shape}")
        print("Data statistics:")
        print(f"  Min value: {mold_table.data.min()}")
        print(f"  Max value: {mold_table.data.max()}")
        print(f"  Mean value: {mold_table.data.mean():.1f}")

        print("\nValues at specific points:")
        print("=========================")

        # Test some specific temperature and RH combinations
        # Convert to integers for ShiftedArray
        test_points = [
            (20, 50),  # 20°C, 50% RH
            (25, 60),  # 25°C, 60% RH
            (15, 40),  # 15°C, 40% RH
        ]

        for temp, rh in test_points:
            print(f"\nAt {temp}°C, {rh}% RH:")
            try:
                print(f"  PI: {pi_table[temp, rh]}")
            except IndexRangeError as e:
                print(f"  PI: Out of range ({e})")

            try:
                print(f"  EMC: {emc_table[temp, rh]:.1f}%")
            except IndexRangeError as e:
                print(f"  EMC: Out of range ({e})")

            try:
                print(f"  Mold risk: {mold_table[temp, rh]} days")
            except IndexRangeError as e:
                print(f"  Mold risk: Out of range ({e})")

    except Exception as e:
        logger.error(f"Error in example_usage: {e}")
        raise


if __name__ == "__main__":
    example_usage()
