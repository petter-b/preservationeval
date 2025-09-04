# WARP.md

This file provides guidance to WARP (warp.dev) when working with code in this repository.

Project overview
- A typed Python package that re-implements the Image Permanence Institute’s dew point calculator (dpcalc.org) and related preservation metrics (PI, EMC, mold risk). Lookup tables are fetched from dpcalc.org and converted to a Python module during build/install.

Development setup
- Python >= 3.11
- Install dev extras and set up hooks:
  - pip install -e ".[dev]"
  - pre-commit install

Common commands
- Format and lint
  - ruff format .
  - ruff check .
  - ruff check . --fix  # apply safe autofixes
- Type checking
  - mypy .
- Run tests (pytest is configured via pyproject)
  - pytest                 # runs with mypy plugin and coverage (per addopts)
  - pytest -q              # quieter
  - pytest -k "pattern"    # run tests by expression
  - pytest tests/test_core.py::test_name  # run a single test
- Markers (declared in pyproject/conftest): unit, integration, validation, slow
  - pytest -m "unit"
  - pytest -m "not slow and not validation"
- Coverage
  - pytest --cov
- Generate validation test data (compares Python vs the original JS)
  - python -m tests.validate_core                   # prepares tests/data, runs JS + Python comparison
  - pytest tests/test_validation.py                 # only validation tests
  - pytest tests/test_validation.py --force-update  # refresh cached JS cases
  - Note: Requires Node.js + npm (puppeteer is specified in package.json)
- Lookup table generation (manual)
  - python -m scripts.generate_tables
  - Normally triggered automatically during build/install.
- Build and local install
  - python -m build
  - pip install dist/*.whl

Big-picture architecture
- Build-time table generation pipeline
  - setup.py defines CustomBuildPy and CustomInstall. During build, preservationeval.install.generate_tables.generate_tables is invoked to:
    1) Download dp.js from dpcalc.org
    2) Parse metadata and raw arrays (preservationeval.install.parse + patterns)
    3) Construct typed LookupTable instances (PITable, EMCTable, MoldTable)
    4) Emit a module preservationeval/tables.py (install.export) with initialized tables and an _INITIALIZED flag
  - Versioning: setup.CustomDistribution writes/reads src/preservationeval/_version.py and derives the package version from git tags when available. pyproject sets version dynamic from preservationeval.__version__.
- Runtime modules
  - preservationeval.core_functions: Public API for PI, EMC, and mold(t, rh); uses the generated tables and validates inputs via util_functions
  - preservationeval.eval_functions: Maps numeric outputs to EnvironmentalRating (GOOD/OK/RISK) for natural aging, mechanical damage, mold growth, metal corrosion
  - preservationeval.util_functions: Helpers such as validate_rh/temp, to_celsius, calculate_dew_point
  - preservationeval.types: Domain types (Annotated), exceptions, and the generic LookupTable implementation with boundary handling and rounding semantics compatible with the JS reference
  - preservationeval.utils: Structured logging setup and safe path utilities used by installer and tests
- Tests and validation
  - pytest configured via pyproject (testpaths, markers, mypy plugin, coverage). tests/validate_core orchestrates cross-language validation by running the JS in a headless browser (puppeteer), caching inputs/outputs under tests/data. Use --force-update to refresh against latest dp.js
- Scripts
  - scripts/generate_tables.py: Convenience wrapper to regenerate tables on demand
  - scripts/update_test_data.py: Refresh validation cases by driving ValidationTest

CI and releases (reference)
- .github/workflows/python-cicd.yml runs pre-commit and pytest across Python 3.11–3.13, uploads coverage, and supports two release modes:
  - Release Candidate: builds with a PEP 440 rc version and optionally uploads to TestPyPI
  - Production Release: version bumped from latest tag, builds, uploads to PyPI, verifies install, and creates a GitHub Release
- CodeQL and a scheduled pre-commit autoupdate workflow are present.

Notes for future agents
- Tests relying on the JS reference require network access to download dp.js and a working Node.js + npm for puppeteer execution. The standard unit/integration suite runs fine without Node.

