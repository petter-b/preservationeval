# scripts/update_test_data.py
from tests.validate_core import ValidationTest


def main():
    """Update test data from JavaScript source."""
    validation = ValidationTest(force_update=True)
    validation.run_tests(num_cases=1000)
    print("Test data updated")


if __name__ == "__main__":
    main()
