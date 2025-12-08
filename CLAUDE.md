# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

**preservationeval** is a Python implementation of the Image Permanence Institute's Dew Point Calculator (dpcalc.org). It calculates preservation metrics for museum/archive environments:
- **Preservation Index (PI)**: Rate of chemical decay in organic materials (years)
- **Equilibrium Moisture Content (EMC)**: Moisture content as percentage
- **Mold Risk Factor**: Mold growth risk assessment

Lookup tables are downloaded from dpcalc.org and converted to a Python module during package installation.

## Development Setup

```bash
pip install -e ".[dev]"
pre-commit install
```

Requires Python ≥3.11 (tested on 3.11, 3.12, 3.13).

## Common Commands

### Lint and Format
```bash
ruff format .                    # Format code
ruff check .                     # Check for issues
ruff check . --fix               # Apply safe auto-fixes
mypy .                           # Type checking
pre-commit run --all-files       # Run all pre-commit hooks
```

### Testing
```bash
pytest                           # Run all tests (includes mypy + coverage)
pytest -v                        # Verbose output
pytest tests/test_core.py        # Single test file
pytest tests/test_core.py::TestValidatedCases::test_validated_cases  # Single test
pytest -m "unit"                 # Only unit tests
pytest -m "not slow and not validation"  # Skip slow/validation tests
pytest --cov                     # With coverage report
```

### Validation Testing (Python vs JavaScript)
Requires Node.js + npm (puppeteer is used for headless JS execution).
```bash
python -m tests.validate_core              # Generate test data, run comparison
pytest tests/test_validation.py            # Run cached validation tests
pytest tests/test_validation.py --force-update  # Regenerate test data
```

### Build
```bash
python -m build                  # Build wheel + sdist
python -m scripts.generate_tables  # Manual table regeneration
```

## Architecture

### Core Modules (`src/preservationeval/`)
- **core_functions.py**: Public API - `pi()`, `emc()`, `mold()` lookups with input validation
- **eval_functions.py**: Map numeric values → `EnvironmentalRating` (GOOD/OK/RISK)
- **util_functions.py**: Temperature conversion, dew point calculation (Magnus formula), validation
- **const.py**: Valid ranges (temperature: -20 to 65°C, RH: 0-100%), URLs

### Type System (`src/preservationeval/types/`)
- **lookuptable.py**: Generic `LookupTable[T]` with numpy backend, boundary handling enum
- **domain_types.py**: Annotated types - `Temperature`, `RelativeHumidity`, `PreservationIndex`, `MoldRisk`, `MoistureContent`
- **exceptions.py**: Hierarchy - `PreservationError` → `IndexRangeError` → `TemperatureError`/`HumidityError`

### Build-Time Table Generation (`src/preservationeval/install/`)
Pipeline: Download dp.js → parse JS arrays → construct typed LookupTables → emit `tables.py`
- **generate_tables.py**: Main entry point
- **parse.py**: JavaScript parsing logic with regex
- **export.py**: Emit the tables.py module

### Test Framework (`tests/`)
- **conftest.py**: Pytest fixtures (validation data, test directories)
- **validate_core.py**: `ValidationTest` class runs Python & JS side-by-side via puppeteer
- Markers: `@pytest.mark.unit`, `@pytest.mark.integration`, `@pytest.mark.validation`, `@pytest.mark.slow`

## Code Standards

- **Line length**: 88 characters
- **Docstrings**: Google convention
- **Type checking**: Strict mypy (`disallow_untyped_defs`, etc.)
- **Ruff rules**: D (pydocstyle), E/F (pycodestyle/pyflakes), B (bugbear), I (isort), N (pep8-naming), UP (pyupgrade), S (bandit), C4, PL, RUF, PTH, ERA

## Key Files

| File | Purpose |
|------|---------|
| `core_functions.py` | Public API (pi, emc, mold) |
| `types/lookuptable.py` | Generic lookup table implementation |
| `types/exceptions.py` | Domain-specific exception hierarchy |
| `install/generate_tables.py` | Build-time table generation entry |
| `tables.py` | Generated lookup tables (88KB, auto-built) |
| `tests/validate_core.py` | JS validation framework |

## CI/CD

GitHub Actions workflow (`.github/workflows/python-cicd.yml`):
- Runs pre-commit + pytest across Python 3.11-3.13
- Coverage uploaded to codecov
- Release modes: RC → TestPyPI, Production → PyPI + GitHub Release
