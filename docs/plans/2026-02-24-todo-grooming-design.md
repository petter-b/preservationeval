# Design: Groom and Relocate TODO.md

**Date:** 2026-02-24
**Status:** Approved

## Goal

Prune obsolete/completed items from `TODO.md`, reorganize surviving items, and move the file to `docs/TODO.md`.

## Items Removed

| Item | Reason |
|------|--------|
| `[X] Restructuring` | Completed |
| `[X] Improve test coverage` | Completed |
| `[ ] Consider using scripts/generate_tables()` | Superseded by PyMiniRacer pipeline (v1.1.0) |
| `[?] Add proper SOURCES.txt handling` | Superseded by hatchling sdist config |
| `[ ] Add validation of tables.py during installation` | Covered by validation tests (Puppeteer comparison) |
| `[ ] Move config from install.const to pyproject.toml` | Covered by uv migration plan |
| `[ ] Code review` | Too vague to track |

## Items Reworded

| Original | New |
|----------|-----|
| `Robustness against errors during installation` | `Install pipeline robustness: retry logic, JS execution timeout, value-range validation, atomic file writes` |
| `Security wrt execution of JS code` | `Security review of PyMiniRacer JS execution` |
| `Improve docstrings and update based on <long URL>` | `Improve docstrings (ref: Understanding Preservation Metrics PDF)` |

## Items Kept

- Consistent use of logging
- Add hash verification to tables.py
- Cache dp.js for offline builds
- Consider merging const and config modules
- Revise README (describe structure, slim down)
- Document table generation process

## New Structure

Flat categories: `High Priority` / `Features` / `Documentation`.
Same grouping as before, just pruned and updated.

## File Operations

1. Create `docs/TODO.md` with groomed content
2. Delete root `TODO.md`

## Separate Bug-Fix Commit

Issues found during exploration (not TODO items — fix immediately):

- Missing `f`-prefix on error messages in `core_functions.py` and `util_functions.py`
- Typo "preservationevlal" in `export.py`
- ANSI escape codes in `generate_tables.py` logging
- Unlinked TODO comment in `__init__.py`
