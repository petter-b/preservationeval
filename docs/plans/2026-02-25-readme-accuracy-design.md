# README Accuracy Pass

**Date:** 2026-02-25
**Status:** Approved

## Problem

The README has not been updated since the uv migration and recent pipeline hardening work.
CI badges are broken, dev setup commands reference pip, and several sections are stale or incomplete.

## Changes

### 1. Fix CI badges (lines 5, 91)

`ci.yml` no longer exists; the workflow is `python-cicd.yml`.
Update both badge references.

### 2. Keep pip install for end users (line 18)

No change.
`pip install preservationeval` is correct for package consumers.

### 3. Update dev setup to uv (line 63)

Replace `pip install -e ".[dev]"` with `uv sync --extra dev`.

### 4. Update test deps to uv (line 103)

Replace `pip install -e ".[test]"` with `uv sync --extra test`.

### 5. Fix typo (line 41)

"Restults" -> "Results".

### 6. Remove dead eClimateNotebook link (line 46)

`fundamentals_nl.php` 301-redirects to the homepage (content gone).
Remove the link; keep the dpcalc.org and IPI PDF links.

### 7. Update Details section (line 13)

Rewrite to mention PyMiniRacer V8 execution and SHA-256 integrity verification.
Current text is vague about the mechanism.

### 8. Add dp.js monitor badge to Automation section

Add a badge for `dpjs-monitor.yml` (assumes PR #191 merged).

### 9. Add evaluation functions to Usage section

Add a second example block showing `rate_natural_aging()`, `rate_mold_growth()`, and `EnvironmentalRating`.
The package exports these but the README only documents `pi()`, `emc()`, `mold()`.

## Out of Scope

- Restructuring the README
- Adding package structure diagram
- Documenting the table generation pipeline in detail (separate TODO item)
- Docstring improvements (separate TODO item)
