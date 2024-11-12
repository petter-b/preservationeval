# scripts/make_test_data.py
from preservationeval.validate_core import PreservationTester


def main():
    """Generate fresh test data from online source."""
    tester = PreservationTester(use_local=False)
    tester.run_validation()


if __name__ == "__main__":
    main()
