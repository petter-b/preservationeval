# Project Overview: preservationeval

## Purpose
A Python implementation of the Image Permanence Institute's Dew Point Calculator (dpcalc.org). It calculates preservation metrics for museum/archive environments:
- **Preservation Index (PI)**: Rate of chemical decay in organic materials (years)
- **Equilibrium Moisture Content (EMC)**: Moisture content as percentage
- **Mold Risk Factor**: Mold growth risk assessment

Lookup tables are downloaded from dpcalc.org and converted to a Python module during package installation.

## Tech Stack
- **Python**: ≥3.11 (tested on 3.11, 3.12, 3.13)
- **NumPy**: Core numerical library for lookup tables
- **Requests**: HTTP library for downloading tables
- **Build System**: setuptools with dynamic versioning

## Architecture

### Core Modules (`src/preservationeval/`)
| Module | Purpose |
|--------|---------|
| `core_functions.py` | Public API - `pi()`, `emc()`, `mold()` lookups with input validation |
| `eval_functions.py` | Map numeric values → `EnvironmentalRating` (GOOD/OK/RISK) |
| `util_functions.py` | Temperature conversion, dew point calculation (Magnus formula), validation |
| `const.py` | Valid ranges (temperature: -20 to 65°C, RH: 0-100%), URLs |
| `tables.py` | Generated lookup tables (auto-built during installation) |

### Type System (`src/preservationeval/types/`)
| Module | Purpose |
|--------|---------|
| `lookuptable.py` | Generic `LookupTable[T]` with numpy backend, boundary handling enum |
| `domain_types.py` | Annotated types - `Temperature`, `RelativeHumidity`, `PreservationIndex`, `MoldRisk`, `MoistureContent` |
| `exceptions.py` | Hierarchy - `PreservationError` → `IndexRangeError` → `TemperatureError`/`HumidityError` |

### Build-Time Table Generation (`src/preservationeval/install/`)
Pipeline: Download dp.js → parse JS arrays → construct typed LookupTables → emit `tables.py`
| Module | Purpose |
|--------|---------|
| `generate_tables.py` | Main entry point |
| `parse.py` | JavaScript parsing logic with regex |
| `export.py` | Emit the tables.py module |
| `patterns.py` | Regex patterns for parsing |
| `paths.py` | Path handling |
| `const.py` | Constants for installation |

### Test Framework (`tests/`)
| File | Purpose |
|------|---------|
| `conftest.py` | Pytest fixtures (validation data, test directories) |
| `validate_core.py` | `ValidationTest` class runs Python & JS side-by-side via puppeteer |
| `test_core.py` | Core function tests |
| `test_eval.py` | Evaluation function tests |
| `test_validation.py` | JS validation tests |

## CI/CD
GitHub Actions workflow (`.github/workflows/python-cicd.yml`):
- Runs pre-commit + pytest across Python 3.11-3.13
- Coverage uploaded to codecov
- Release modes: RC → TestPyPI, Production → PyPI + GitHub Release
