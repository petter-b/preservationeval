# preservationeval

[![PyPI](https://img.shields.io/pypi/v/preservationeval?style=flat&color=blue&label=pypi&logo=pypi)](https://pypi.org/project/preservationeval/)
[![Python](https://img.shields.io/pypi/pyversions/preservationeval?style=flat&color=blue&logo=python)](https://pypi.org/project/preservationeval/)
[![CI](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/python-cicd.yml?style=flat&label=CI&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/python-cicd.yml)
[![Coverage](https://img.shields.io/codecov/c/github/petter-b/preservationeval?style=flat&color=brightgreen&label=coverage&logo=codecov)](https://codecov.io/gh/petter-b/preservationeval)
[![License](https://img.shields.io/badge/license-MIT-blue?style=flat&logo=opensourceinitiative&logoColor=white)](https://opensource.org/licenses/MIT)

A Python implementation of the calculations and evaluations done by the Dew Point Calculator found at https://www.dpcalc.org/.

## Details

This project is a Python implementation of the [Dew Point Calculator](http://www.dpcalc.org) created by the Image Permanence Institute.
The original lookup tables from their [published JavaScript](http://www.dpcalc.org/dp.js) are not redistributed.
Instead, during installation, `dp.js` is downloaded, its integrity is verified via a pinned SHA-256 hash, and the table data is extracted by executing the JavaScript in an embedded V8 engine ([PyMiniRacer](https://github.com/nicolo-ribaudo/pymi-racer)) and converted into a Python module.

## Installation

```bash
pip install preservationeval
```

## Usage

### Basic Examples

```python
from preservationeval import pi, emc, mold

# Calculate Preservation Index
pi_value = pi(20, 50)  # temperature=20°C, RH=50%
print(f"Preservation Index: {pi_value}")

# Calculate EMC (Equilibrium Moisture Content)
emc_value = emc(20, 50)
print(f"EMC: {emc_value}%")

# Calculate Mold Risk
mold_risk = mold(20, 50)
print(f"Mold Risk: {mold_risk}")
```

### Evaluating Conditions

The package also provides functions to rate environmental conditions:

```python
from preservationeval import (
    pi, mold, rate_natural_aging, rate_mold_growth, EnvironmentalRating
)

# Rate preservation conditions (returns GOOD, OK, or RISK)
aging_risk = rate_natural_aging(pi(20, 50))
print(f"Natural aging: {aging_risk}")  # EnvironmentalRating.GOOD

mold_risk = rate_mold_growth(mold(20, 50))
print(f"Mold risk: {mold_risk}")  # EnvironmentalRating.GOOD
```

### Interpreting Results

For details of how to use, see:

- http://www.dpcalc.org/howtouse_step2.php
- https://s3.cad.rit.edu/ipi-assets/publications/understanding_preservation_metrics.pdf

## Development

[![Project Status](https://img.shields.io/pypi/status/preservationeval?style=flat&color=blue&label=status&logo=pypi)](https://pypi.org/project/preservationeval/)
[![Downloads](https://img.shields.io/pepy/dt/preservationeval?style=flat&color=blue&logo=python&logoColor=white)](https://pepy.tech/project/preservationeval)
[![Issues](https://img.shields.io/github/issues/petter-b/preservationeval?style=flat&color=yellow&logo=github)](https://github.com/petter-b/preservationeval/issues/)

### Setup

```bash
# Clone the repository
git clone https://github.com/petter-b/preservationeval
cd preservationeval

# Install development dependencies
uv sync --extra dev
```

### Development Tools

- `ruff`: Code formatting, linting and code quality
- `mypy`: Static type checking
- `pytest`: Testing framework
- `pre-commit`: Git hooks for code quality

### Common Tasks

```bash
# Format code
uv run ruff format .

# Run linter
uv run ruff check .

# Type checking
uv run mypy .

# Run tests with coverage
uv run pytest --cov
```

### Testing

[![CI](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/python-cicd.yml?style=flat&label=ci&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/python-cicd.yml)
[![Coverage](https://img.shields.io/codecov/c/github/petter-b/preservationeval?style=flat&color=brightgreen&label=coverage&logo=codecov)](https://codecov.io/gh/petter-b/preservationeval)
[![CodeQL](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/codeql.yml?style=flat&label=codeql&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/codeql.yml)

#### Validation Testing

The package includes a validation framework that compares the Python implementation
against the original JavaScript implementation from dpcalc.org.

##### Requirements

- Node.js and npm must be installed ([download](https://nodejs.org/))
- Python test dependencies: `uv sync --extra test`

##### Test Data Setup

The test framework automatically:

- Creates the `tests/data` directory (git-ignored)
- Downloads the JavaScript reference implementation
- Generates and saves test cases
- Caches results for future test runs

You can manually trigger this setup:

```bash
# Download JavaScript reference implementation
# This happens automatically when running tests, or manually:
uv run python -m tests.validate_core

# Run all tests
uv run pytest

# Run only validation tests
uv run pytest tests/test_validation.py

# Run with verbose output
uv run pytest -v tests/test_validation.py

# Generate new test cases (ignore cached)
uv run pytest tests/test_validation.py --force-update
```

### Code Quality

[![Ruff](https://img.shields.io/badge/code%20style-ruff-000000.svg)](https://github.com/astral-sh/ruff)
[![Ruff](https://img.shields.io/badge/ruff-recommended-red?style=flat&logo=ruff&logoColor=white)](https://github.com/astral-sh/ruff)
[![Mypy](https://img.shields.io/badge/mypy-typed-blue?style=flat&logo=python&logoColor=white)](http://mypy-lang.org/)

### Automation

[![Pre-commit](https://img.shields.io/badge/pre--commit-enabled-brightgreen?style=flat&logo=pre-commit&logoColor=white)](https://github.com/petter-b/preservationeval/blob/main/.pre-commit-config.yaml)
[![Pre-commit CI](https://img.shields.io/badge/pre--commit%20ci-passing-brightgreen?style=flat&logo=pre-commit&logoColor=white)](https://results.pre-commit.ci/latest/github/petter-b/preservationeval/main)
[![Renovate](https://img.shields.io/badge/renovate-enabled-brightgreen?style=flat&logo=renovatebot&logoColor=white)](https://renovatebot.com)
[![dp.js Monitor](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/dpjs-monitor.yml?style=flat&label=dp.js%20monitor&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/dpjs-monitor.yml)

## Development Notes

This project was developed with assistance from Claude AI (Anthropic) and to some extent Codeium and GitHub Copilot. All code has been validated and tested for accuracy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Changelog

See [CHANGELOG.md](CHANGELOG.md) for all changes and versioning details.
