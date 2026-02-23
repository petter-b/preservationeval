# Design: Simplify Install Pipeline with PyMiniRacer

**Date:** 2026-02-23
**Status:** Approved

## Problem

The current install pipeline uses ~1,100 lines of Python regex parsing (`parse.py` + `patterns.py`) to extract lookup table data from `dp.js` (dpcalc.org).
This is overengineered, fragile in theory, and adds unnecessary build-time complexity for what amounts to reading arrays out of a JavaScript file.

## Constraints

- **Never redistribute dp.js or the table data** — tables are generated at build time from a fresh download, never committed or published.
- **Keep the Python interface** — public API (`pi()`, `emc()`, `mold()`) unchanged.
- **Keep PyPI publishing** — same distribution model.
- **TDD approach** — tests first, high coverage.

## Decision

Replace the regex parsing pipeline with PyMiniRacer (`mini-racer`), an embedded V8 engine for Python.
Instead of regex-parsing dp.js to extract data, we execute dp.js in V8 and read the global arrays directly.

### Why PyMiniRacer over alternatives

| Option | Verdict |
|---|---|
| **Node.js subprocess** | Adds system-level dependency for all users at build time |
| **dukpy (Duktape)** | ES5.1 only, "Alpha" status, risk if dp.js uses modern JS |
| **PyMiniRacer (V8)** | Full modern JS, production/stable, pip-installable, active maintenance |

## Architecture

### Current flow (regex)

```
dp.js --> regex patterns --> extract metadata --> extract arrays --> LookupTable --> tables.py
           (1,100 LOC)
```

### New flow (PyMiniRacer)

```
dp.js --> MiniRacer.eval() --> read JS globals --> LookupTable --> tables.py
           (~80 LOC)
```

### New `install/extract.py` — core replacement module

1. Download dp.js from dpcalc.org (reuse existing `requests` call)
2. Stub minimal browser globals (`var window = {}; var document = {}; var $ = function(){};`)
3. `ctx.eval(dp_js_content)` — execute dp.js in V8
4. Read raw arrays: `ctx.eval("pitable")`, `ctx.eval("emctable")`
5. Read metadata: temp/RH ranges from JS globals
6. Construct `LookupTable` objects with proper shapes, dtypes, and `BoundaryBehavior`
7. Pass to `generate_tables_module()` (from `export.py`)

## File Changes

### Delete

| File | LOC | Reason |
|---|---|---|
| `install/parse.py` | 578 | Regex extraction replaced by PyMiniRacer |
| `install/patterns.py` | 159 | Regex patterns no longer needed |
| `tests/test_parse.py` | ~200 | Tests for deleted code |

### Add

| File | LOC (est.) | Purpose |
|---|---|---|
| `install/extract.py` | ~80 | Download dp.js, execute in MiniRacer, extract tables |
| `tests/test_extract.py` | ~150 | Unit + integration tests for extraction |

### Modify

| File | Change |
|---|---|
| `install/generate_tables.py` | Call `extract.py` instead of `parse.py` |
| `install/__init__.py` | Update imports |
| `pyproject.toml` | Add `mini-racer` to `[build-system] requires` |

### Unchanged

- `core_functions.py`, `eval_functions.py`, `util_functions.py`
- `types/` (LookupTable, domain_types, exceptions)
- `utils/` (safepath, logging)
- `tables.py` (still auto-generated, same format)
- `setup.py` (still calls `generate_tables()`)
- All non-parse tests

### Net impact

~940 LOC deleted, ~230 LOC added. Roughly **-700 LOC**.

## Testing Strategy (TDD)

### Tests to delete

- `test_parse.py` — tests the regex pipeline we're removing.

### Tests to add (`tests/test_extract.py`)

1. **Unit: JS global stubbing** — browser globals stubbed without errors
2. **Unit: table extraction** — mock dp.js with known small arrays, verify correct extraction
3. **Unit: error handling** — invalid JS content, missing globals, network failures
4. **Unit: LookupTable construction** — correct dtypes, boundary behaviors, offsets
5. **Integration: real dp.js** — download actual dp.js, verify shapes and value ranges (`@pytest.mark.integration`)

### Tests unchanged

- `test_core.py` — public API
- `test_lookuptable.py` — LookupTable internals
- `test_validation.py` — Puppeteer JS/Python comparison (ultimate correctness gate)
- All other test files

### Correctness gate

After refactor, `test_validation.py` (Puppeteer comparison against original dp.js) must still pass.
This proves the new extraction produces identical tables.

## Risks & Mitigation

| Risk | Likelihood | Mitigation |
|---|---|---|
| dp.js references jQuery/DOM at load time | Medium | Stub `window`, `document`, `$` before eval. Test early. |
| PyMiniRacer can't read JS global arrays | Low | V8 handles standard arrays. Fallback: `JSON.stringify()` in JS. |
| Table data differs between old and new extraction | Low | Validation tests (Puppeteer) catch any difference. |
| `mini-racer` binary size (~30MB) | Low | Build-time only, not shipped to users. |
| dp.js variable names change | Low | Site is stable per owner. Extraction has clear, testable assumptions. |

## Implementation Order (TDD)

1. Add `mini-racer` to build dependencies
2. Write `test_extract.py` — unit tests first (with mock JS content)
3. Implement `extract.py` — make unit tests pass
4. Write integration test — real dp.js download + extraction
5. Wire up `generate_tables.py` to use `extract.py`
6. Run full test suite — especially `test_validation.py`
7. Delete `parse.py`, `patterns.py`, `test_parse.py`
8. Final cleanup and verification

## Future Considerations (backlog, not for this refactor)

- **CLI with JSON output** for AI agents — add `cli.py` + `[project.scripts]` entry
- **TypeScript SDK** — separate package in same repo, directly wraps dp.js
- Neither requires preparation in this refactor (YAGNI)
