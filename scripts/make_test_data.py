"""Generate fresh test data from online source."""

from tests.validate_core import ValidationTest


def main() -> None:
    """Generate fresh test data from online source."""
    tester = ValidationTest(force_update=True)
    tester.run_tests()


if __name__ == "__main__":
    main()
