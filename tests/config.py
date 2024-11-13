"""
Configuration settings for preservation calculation validation.

This module contains all configuration parameters used in the validation
process, including test ranges, JavaScript environment settings, and comparison
tolerances.

TODO: Replace constants with dataclasses
"""

# Test parameters for temperature and relative humidity ranges
TEST_CONFIG = {
    "temp_range": (-30, 71, 0.1),  # (start, stop, step) in Celsius
    "rh_range": (0, 100, 0.1),  # (start, stop, step) in percentage
    "num_tests": 10000,  # Number of random tests to run
}

# JavaScript environment configuration
JS_CONFIG = {
    "package_json": {
        "name": "dp-test",
        "version": "1.0.0",
        "dependencies": {"puppeteer": "^19.0.0"},
    },
}

# Comparison settings
COMPARISON_CONFIG = {
    "emc_tolerance": 0.0001,  # Tolerance for floating-point comparisons
    "max_differences_shown": 5,  # Number of differences to show in reports
}


# from dataclasses import dataclass
# from typing import Tuple

# @dataclass(frozen=True)
# class TestConfig:
#     temp_range: Tuple[float, float, float] = (-30, 70, 0.1)
#     rh_range: Tuple[float, float, float] = (0, 100, 0.1)
#     num_tests: int = 10000

# @dataclass(frozen=True)
# class ComparisonConfig:
#     emc_tolerance: float = 0.0001
#     max_differences: int = 5

# @dataclass(frozen=True)
# class ValidationConfig:
#     test: TestConfig = TestConfig()
#     comparison: ComparisonConfig = ComparisonConfig()
