"""
Configuration settings for preservation calculation validation.

This module contains all configuration parameters used in the validation
process, including test ranges, JavaScript environment settings, and comparison
tolerances.
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
    }
}

# Comparison settings
COMPARISON_CONFIG = {
    "emc_tolerance": 0.0001,  # Tolerance for floating-point comparisons
    "max_differences_shown": 5,  # Number of differences to show in reports
}
