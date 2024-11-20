#!/usr/bin/env python3
"""Update test data from online JavaScript source."""

from tests.validate_core import ValidationTest


def main() -> None:
    """Update test data from JavaScript source."""
    validation = ValidationTest(force_update=True)
    validation.run_tests()


if __name__ == "__main__":
    main()
