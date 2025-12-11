# Agent Instructions

This file provides guidance to AI agents (Claude Code, Cursor, and other AI coding assistants) working in this repository.

## Development Philosophy

### KISS (Keep It Simple, Stupid)

Simplicity should be a key goal in design. Choose straightforward solutions over complex ones whenever possible.

### YAGNI (You Aren't Gonna Need It)

Implement features only when needed, not when you anticipate they might be useful.

### Design Principles

- **Dependency Inversion**: High-level modules depend on abstractions, not low-level modules
- **Open/Closed**: Open for extension, closed for modification
- **Single Responsibility**: Each function, class, and module should have one clear purpose
- **Fail Fast**: Check for errors early and raise exceptions immediately

### Code Structure Limits

- **Files**: Never exceed 500 lines of code
- **Functions**: Under 50 lines with single responsibility
- **Classes**: Under 100 lines representing a single concept

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

## Tool Requirements

| Tool                    | Use For                            |
| ----------------------- | ---------------------------------- |
| **exa**                 | Web search                         |
| **sequential-thinking** | Planning and decisions             |
| **serena**              | Semantic code operations           |
| **context7**            | Third-party library documentation  |

MCP servers are configured in `.mcp.json`.

## Search Commands

Use `rg` (ripgrep) instead of `grep`/`find`:

```bash
rg "pattern"                    # Instead of: grep -r "pattern" .
rg --files -g "*.py"            # Instead of: find . -name "*.py"
rg -A 5 "def pi" src/           # Search with context
```

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

### Utility Modules (`src/preservationeval/utils/`)

- **safepath.py**: Safe path handling utilities for file operations
- **logging/**: Structured logging configuration and utilities

### Build-Time Table Generation (`src/preservationeval/install/`)

Pipeline: Download dp.js → parse JS arrays → construct typed LookupTables → emit `tables.py`

- **generate_tables.py**: Main entry point for table generation
- **parse.py**: JavaScript parsing logic with regex patterns
- **export.py**: Emit the tables.py module with formatted code
- **paths.py**: Path handling for build process (cache, data directories)
- **patterns.py**: Regex patterns for parsing JavaScript lookup tables
- **const.py**: Build-time constants (URLs, file names, table metadata)

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

## Agent Boundaries

### ✅ Always

- Run `ruff check` and `mypy` before committing
- Use type annotations on all functions
- Follow existing code patterns and conventions
- Verify file paths and module names before use
- Test your code - no feature is complete without tests

### ⚠️ Ask First

- When in doubt about requirements or approach
- Changes to public API (`pi()`, `emc()`, `mold()`)
- Modifications to `tables.py` generation pipeline
- Changes to CI/CD workflow
- Deleting or overwriting existing code

### 🚫 Never

- Assume or guess - ask for clarification instead
- Hallucinate libraries or functions - only use verified packages
- Commit secrets or credentials
- Modify `tables.py` directly (auto-generated)
- Skip pre-commit hooks
