"""Configuration settings for preservation calculation validation.

This module contains all configuration parameters used in the validation
process, including test ranges, JavaScript environment settings, and comparison
tolerances.

The configuration parameters are defined using dataclasses, which provide
frozen instances that can be used for type checking and immutability.
"""

from dataclasses import dataclass, field

# JavaScript environment configuration
JS_CONFIG = {
    "package_json": {
        "name": "dp-test",
        "version": "1.0.0",
        "dependencies": {"puppeteer": "^24.0.0"},
    },
}


@dataclass(frozen=True)
class TestConfig:
    """Test parameters for temperature and relative humidity ranges."""

    temp_range: tuple[float, float, float] = (
        -30,
        71,
        0.1,
    )  # (start, stop, step) in Celsius
    rh_range: tuple[float, float, float] = (
        0,
        100,
        0.1,
    )  # (start, stop, step) in percentage
    num_tests: int = 10000  # Number of random tests to run


@dataclass(frozen=True)
class ComparisonConfig:
    """Comparison settings."""

    emc_tolerance: float = 0.01  # Tolerance for floating-point comparisons
    max_differences: int = 5  # Number of differences to show in reports


@dataclass(frozen=True)
class ValidationConfig:
    """Configuration settings for the validation process."""

    test: TestConfig = field(default_factory=TestConfig)
    comparison: ComparisonConfig = field(default_factory=ComparisonConfig)
