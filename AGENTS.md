# Agent Instructions

## Project

Python implementation of IPI's Dew Point Calculator (dpcalc.org).
Preservation metrics (PI, EMC, mold risk) via lookup tables generated at build time.

## Architecture

### Core (`src/preservationeval/`)

- `core_functions.py` — Public API: `pi()`, `emc()`, `mold()`
- `eval_functions.py` — Numeric → `EnvironmentalRating` (GOOD/OK/RISK)
- `util_functions.py` — Temp conversion, dew point (Magnus), validation
- `const.py` — Valid ranges (temp: -20–65°C, RH: 0–100%)

### Types (`types/`)

- `lookuptable.py` — Generic `LookupTable[T]`, numpy backend
- `domain_types.py` — `Temperature`, `RelativeHumidity`, `PreservationIndex`, `MoldRisk`, `MoistureContent`
- `exceptions.py` — `PreservationError` hierarchy with boundary-specific errors

### Build-Time (`install/`)

`tables.py` is auto-generated. Never edit directly.
Pipeline: Download dp.js → PyMiniRacer execution → extract arrays → emit `tables.py`

### Tests

Markers: `unit`, `integration`, `validation`, `slow`.

## Design

KISS, YAGNI, DRY. Max: 500 lines/file, 50 lines/function, 100 lines/class.

## Decisions Requiring Approval

- Changes to public API (`pi()`, `emc()`, `mold()`)
- Modifications to table generation pipeline
- Deletions or major refactors of existing code
- CI/CD changes

## Non-Negotiable

- `tables.py` is auto-generated — never edit by hand
- Pre-commit hooks enforce quality gates (see `pyproject.toml`)
- Coverage regressions block CI
- Production releases require `CHANGELOG.md` `[Unreleased]` section to have entries

### Build Caveats

- RC builds use `SETUPTOOLS_SCM_PRETEND_VERSION` — this works because hatch-vcs
  delegates to setuptools-scm internally. Verify this env var still works after
  hatch-vcs major version bumps; a silent failure would publish an RC with the
  wrong version.

### Changelog Workflow

- Add entries under `## [Unreleased]` in `CHANGELOG.md` as changes are made
- Use [Keep a Changelog](https://keepachangelog.com/) format: `Added`, `Changed`, `Fixed`, `Removed`
- At release time, CI renames `[Unreleased]` to the new version — the section must not be empty
