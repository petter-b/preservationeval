# preservationeval

<!-- Security -->
[![CodeQL](https://github.com/petter-b/preservationeval/actions/workflows/codeql.yml/badge.svg)](https://github.com/petter-b/preservationeval/actions/workflows/codeql.yml)

<!-- Build and Coverage Status -->
[![Tests](https://github.com/petter-b/preservationeval/actions/workflows/tests.yml/badge.svg)](https://github.com/petter-b/preservationeval/actions/workflows/tests.yml)
[![codecov](https://codecov.io/gh/petter-b/preservationeval/branch/main/graph/badge.svg)](https://codecov.io/gh/petter-b/preservationeval)

<!-- Package Information -->
[![PyPI version](https://badge.fury.io/py/preservationeval.svg)](https://badge.fury.io/py/preservationeval)
[![Python Version](https://img.shields.io/pypi/pyversions/preservationeval.svg)](https://pypi.org/project/preservationeval/)
[![Downloads](https://static.pepy.tech/badge/preservationeval)](https://pepy.tech/project/preservationeval)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

<!-- Code Quality -->
[![Code style: black](https://img.shields.io/badge/code%20style-black-000000.svg)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/endpoint?url=https://raw.githubusercontent.com/astral-sh/ruff/main/assets/badge/v2.json)](https://github.com/astral-sh/ruff)
[![mypy](https://img.shields.io/badge/mypy-typed-blue.svg)](http://mypy-lang.org/)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen.svg)](https://renovatebot.com)

<!-- Development Status -->
[![Development Status](https://img.shields.io/pypi/status/preservationeval.svg)](https://pypi.org/project/preservationeval/)
[![Maintenance](https://img.shields.io/badge/Maintained%3F-yes-green.svg)](https://github.com/petter-b/preservationeval/graphs/commit-activity)
[![GitHub issues](https://img.shields.io/github/issues/petter-b/preservationeval.svg)](https://github.com/petter-b/preservationeval/issues/)

A Python module to mimic the calculations done by the Dew Point Calculator from Image Permanence Institute (IPI).

## Details
The preservation evaluation code was taken from the [Dew point calulator](http://www.dpcalc.org) created by the Image Permanence Institute. For details of the calculations see:
 - http://www.dpcalc.org/howtouse_step2.php
 - http://www.dpcalc.org/dp.js


## Installation

```bash
pip install preservationeval
´´´

## Usage
```python
from preservationeval import pi, emc, mold

# Calculate Preservation Index
pi_value = pi(20, 50)  # temperature=20°C, RH=50%

# Calculate EMC
emc_value = emc(20, 50)

# Calculate Mold Risk
mold_risk = mold(20, 50)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/petter-b/preservationeval
cd preservationeval

# Install development dependencies
pip install -e ".[dev]"
```

## Testing

### Validation Testing
The package includes a validation framework that compares our Python implementation
against the original JavaScript implementation from dpcalc.org.

#### Requirements
- Node.js and npm must be installed ([download](https://nodejs.org/))
- Python test dependencies: `pip install -e ".[test]"`

#### Test Data Setup
The test framework automatically:
- Creates the `tests/data` directory (git-ignored)
- Downloads the JavaScript reference implementation
- Generates and saves test cases
- Caches results for future test runs

You can manually trigger this setup:
```bash
# Download JavaScript reference implementation
# This happens automatically when running tests, or manually:
python -m tests.validate_core

# Run all tests
pytest

# Run only validation tests
pytest tests/test_validation.py

# Run with verbose output
pytest -v tests/test_validation.py

# Generate new test cases (ignore cached)
pytest tests/test_validation.py --force-update
```

## Development Notes

This project was developed with assistance from Claude AI (Anthropic) and to some extent GitHub Copilot. All code has been validated and tested for accuracy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.
