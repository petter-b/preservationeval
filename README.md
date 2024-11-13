# preservationeval

<!-- Status -->
[![Project Status](https://img.shields.io/pypi/status/preservationeval?style=flat&color=blue&label=status)](https://pypi.org/project/preservationeval/)
[![Maintained](https://img.shields.io/badge/maintained-yes-brightgreen?style=flat)](https://github.com/petter-b/preservationeval/graphs/commit-activity)
[![Issues](https://img.shields.io/github/issues/petter-b/preservationeval?style=flat&color=yellow)](https://github.com/petter-b/preservationeval/issues/)

<!-- Package -->
[![PyPI](https://img.shields.io/pypi/v/preservationeval?style=flat&color=blue&label=pypi)](https://pypi.org/project/preservationeval/)
[![Python](https://img.shields.io/pypi/pyversions/preservationeval?style=flat&color=blue)](https://pypi.org/project/preservationeval/)
[![Downloads](https://img.shields.io/pepy/dt/preservationeval?style=flat&color=blue&label=downloads)](https://pepy.tech/project/preservationeval)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat)](https://opensource.org/licenses/MIT)

<!-- CI/CD -->
[![CI](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/ci.yml?style=flat&label=ci)](https://github.com/petter-b/preservationeval/actions/workflows/ci.yml)
[![Coverage](https://img.shields.io/codecov/c/github/petter-b/preservationeval?style=flat&color=brightgreen&label=coverage)](https://codecov.io/gh/petter-b/preservationeval)
[![Pre-commit CI](https://img.shields.io/badge/pre--commit%20ci-passing-brightgreen?style=flat)](https://results.pre-commit.ci/latest/github/petter-b/preservationeval/main)

<!-- Security -->
[![CodeQL](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/codeql.yml?style=flat&label=codeql)](https://github.com/petter-b/preservationeval/actions/workflows/codeql.yml)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen?style=flat&logo=renovatebot)](https://renovatebot.com)

<!-- Quality -->
[![Black](https://img.shields.io/badge/code%20style-black-000000?style=flat)](https://github.com/psf/black)
[![Ruff](https://img.shields.io/badge/ruff-recommended-red?style=flat&logo=ruff)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/mypy-typed-blue?style=flat&logo=python)](http://mypy-lang.org/)
[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat&logo=pre-commit)](https://github.com/petter-b/preservationeval/blob/main/.pre-commit-config.yaml)

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
