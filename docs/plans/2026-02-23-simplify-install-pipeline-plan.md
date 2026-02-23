# Simplify Install Pipeline Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace ~1,100 lines of regex-based dp.js parsing with ~80 lines using PyMiniRacer (embedded V8), keeping the same public API and distribution model.

**Architecture:** Download dp.js at build time, execute it in an embedded V8 engine (PyMiniRacer), read the populated JS global arrays directly, construct LookupTable objects, and emit `tables.py`. The public API (`pi()`, `emc()`, `mold()`) is completely unchanged.

**Tech Stack:** Python 3.11+, PyMiniRacer (mini-racer), numpy, requests, pytest, requests-mock

**Design doc:** `docs/plans/2026-02-23-simplify-install-pipeline-design.md`

---

### Task 1: Add mini-racer dependency

**Files:**
- Modify: `pyproject.toml:53-59` (build-system requires)
- Modify: `pyproject.toml:30-38` (test dependencies)

**Step 1: Add mini-racer to build-system requires**

In `pyproject.toml`, add `mini-racer` to the `[build-system] requires` list:

```toml
[build-system]
build-backend = "setuptools.build_meta"
requires = [
    "setuptools>=45",
    "wheel",
    "numpy>=1.26.0",
    "requests>=2.31.0",
    "mini-racer>=0.12.4",
    "types-setuptools>=69.0.0",
]
```

Also add to `[project.optional-dependencies] test` so it's available during testing:

```toml
test = [
    "pytest>=7.4.0",
    "pytest-mypy>=0.10.3",
    "pytest-cov>=4.1.0",
    "pytest-benchmark>=4.0.0",
    "requests-mock>=1.11.0",
    "mini-racer>=0.12.4",
]
```

**Step 2: Install the updated dependencies**

Run: `uv pip install -e ".[dev]"`
Expected: Installs mini-racer successfully

**Step 3: Verify import works**

Run: `python -c "from py_mini_racer import MiniRacer; ctx = MiniRacer(); print(ctx.eval('1+1'))"`
Expected: Prints `2`

**Step 4: Commit**

```bash
git add pyproject.toml
git commit -m "chore: add mini-racer dependency for V8-based table extraction"
```

---

### Task 2: Write failing unit tests for extract module

**Files:**
- Create: `tests/install/test_extract.py`

**Context:** These tests define the contract for the new `extract.py` module. They use mock JS content (not real dp.js) so they run fast and offline. The mock JS mimics the structure of dp.js: it declares `pitable` and `emctable` arrays, then populates them with known values, and defines `pi()`, `emc()`, `mold()` functions.

**Key knowledge from existing `test_parse.py`:**
- PI array size: 9594 (PI data: 8010 elements + mold data: 1584 elements)
- EMC array size: 8686
- PI: temp -23..65, RH 6..95 → 89 temps × 90 RH = 8010
- Mold: temp 2..45, RH 65..100 → 44 temps × 36 RH = 1584 (stored at offset 8010 in pitable)
- EMC: temp -20..65, RH 0..100 → 86 temps × 101 RH = 8686
- PI/Mold use int16, EMC uses float16
- PI/EMC use BoundaryBehavior.CLAMP, Mold uses BoundaryBehavior.RAISE

**Step 1: Write the test file**

```python
"""Tests for preservationeval.install.extract."""

from typing import Final
from unittest.mock import patch

import numpy as np
import pytest
import requests_mock

from preservationeval.install.extract import (
    ExtractionError,
    extract_tables_from_js,
    fetch_and_extract_tables,
)
from preservationeval.types import BoundaryBehavior, LookupTable

# Expected table dimensions (from dp.js structure)
PI_TEMP_MIN: Final[int] = -23
PI_TEMP_MAX: Final[int] = 65
PI_RH_MIN: Final[int] = 6
PI_RH_MAX: Final[int] = 95
PI_ROWS: Final[int] = PI_TEMP_MAX - PI_TEMP_MIN + 1  # 89
PI_COLS: Final[int] = PI_RH_MAX - PI_RH_MIN + 1  # 90

MOLD_TEMP_MIN: Final[int] = 2
MOLD_TEMP_MAX: Final[int] = 45
MOLD_RH_MIN: Final[int] = 65
MOLD_RH_MAX: Final[int] = 100
MOLD_ROWS: Final[int] = MOLD_TEMP_MAX - MOLD_TEMP_MIN + 1  # 44
MOLD_COLS: Final[int] = MOLD_RH_MAX - MOLD_RH_MIN + 1  # 36

EMC_TEMP_MIN: Final[int] = -20
EMC_TEMP_MAX: Final[int] = 65
EMC_RH_MIN: Final[int] = 0
EMC_RH_MAX: Final[int] = 100
EMC_ROWS: Final[int] = EMC_TEMP_MAX - EMC_TEMP_MIN + 1  # 86
EMC_COLS: Final[int] = EMC_RH_MAX - EMC_RH_MIN + 1  # 101

PI_ARRAY_SIZE: Final[int] = PI_ROWS * PI_COLS + MOLD_ROWS * MOLD_COLS  # 9594
EMC_ARRAY_SIZE: Final[int] = EMC_ROWS * EMC_COLS  # 8686


@pytest.fixture
def mock_js_content() -> str:
    """Minimal JS that mimics dp.js structure with known values.

    PI values are all 45, mold values are all 7, EMC values are all 5.5.
    """
    pi_values = [45] * (PI_ROWS * PI_COLS)
    mold_values = [7] * (MOLD_ROWS * MOLD_COLS)
    emc_values = [5.5] * EMC_ARRAY_SIZE

    return f"""
        var $ = function() {{}};
        pitable = new Array({PI_ARRAY_SIZE});
        emctable = new Array({EMC_ARRAY_SIZE});

        var pi = function(t,rh) {{
            return pitable[((t<{PI_TEMP_MIN} ? {PI_TEMP_MIN} : t>{PI_TEMP_MAX} ? {PI_TEMP_MAX} : Math.round(t))+{abs(PI_TEMP_MIN)}) * {PI_COLS} +
                         (rh<{PI_RH_MIN} ? {PI_RH_MIN} : rh>{PI_RH_MAX} ? {PI_RH_MAX} : Math.round(rh)) - {PI_RH_MIN}];
        }};

        var mold = function(t,rh) {{
            if(t > {MOLD_TEMP_MAX} || t < {MOLD_TEMP_MIN} || rh < {MOLD_RH_MIN}) return 0;
            return pitable[{PI_ROWS * PI_COLS} + (Math.round(t) - {MOLD_TEMP_MIN}) * {MOLD_COLS} + Math.round(rh) - {MOLD_RH_MIN}];
        }};

        var emc = function(t,rh) {{
            return emctable[(Math.max({EMC_TEMP_MIN},Math.min({EMC_TEMP_MAX},Math.round(t)))+{abs(EMC_TEMP_MIN)}) * {EMC_COLS} +
                          Math.round(rh)]
        }};

        pitable = [{",".join(str(x) for x in pi_values + mold_values)}];
        emctable = [{",".join(str(x) for x in emc_values)}];
    """


@pytest.mark.unit
class TestExtractTablesFromJS:
    """Test extraction of lookup tables from JavaScript content."""

    def test_returns_three_tables(self, mock_js_content: str) -> None:
        """Extract should return PI, EMC, and Mold LookupTables."""
        pi, emc, mold = extract_tables_from_js(mock_js_content)
        assert isinstance(pi, LookupTable)
        assert isinstance(emc, LookupTable)
        assert isinstance(mold, LookupTable)

    def test_pi_table_shape(self, mock_js_content: str) -> None:
        """PI table should be 89 rows x 90 cols."""
        pi, _, _ = extract_tables_from_js(mock_js_content)
        assert pi.data.shape == (PI_ROWS, PI_COLS)

    def test_emc_table_shape(self, mock_js_content: str) -> None:
        """EMC table should be 86 rows x 101 cols."""
        _, emc, _ = extract_tables_from_js(mock_js_content)
        assert emc.data.shape == (EMC_ROWS, EMC_COLS)

    def test_mold_table_shape(self, mock_js_content: str) -> None:
        """Mold table should be 44 rows x 36 cols."""
        _, _, mold = extract_tables_from_js(mock_js_content)
        assert mold.data.shape == (MOLD_ROWS, MOLD_COLS)

    def test_pi_table_dtypes(self, mock_js_content: str) -> None:
        """PI table should use int16 dtype."""
        pi, _, _ = extract_tables_from_js(mock_js_content)
        assert pi.data.dtype == np.int16

    def test_emc_table_dtypes(self, mock_js_content: str) -> None:
        """EMC table should use float16 dtype."""
        _, emc, _ = extract_tables_from_js(mock_js_content)
        assert emc.data.dtype == np.float16

    def test_mold_table_dtypes(self, mock_js_content: str) -> None:
        """Mold table should use int16 dtype."""
        _, _, mold = extract_tables_from_js(mock_js_content)
        assert mold.data.dtype == np.int16

    def test_pi_table_offsets(self, mock_js_content: str) -> None:
        """PI table should have correct temp_min and rh_min."""
        pi, _, _ = extract_tables_from_js(mock_js_content)
        assert pi.temp_min == PI_TEMP_MIN
        assert pi.rh_min == PI_RH_MIN

    def test_emc_table_offsets(self, mock_js_content: str) -> None:
        """EMC table should have correct temp_min and rh_min."""
        _, emc, _ = extract_tables_from_js(mock_js_content)
        assert emc.temp_min == EMC_TEMP_MIN
        assert emc.rh_min == EMC_RH_MIN

    def test_mold_table_offsets(self, mock_js_content: str) -> None:
        """Mold table should have correct temp_min and rh_min."""
        _, _, mold = extract_tables_from_js(mock_js_content)
        assert mold.temp_min == MOLD_TEMP_MIN
        assert mold.rh_min == MOLD_RH_MIN

    def test_pi_boundary_behavior(self, mock_js_content: str) -> None:
        """PI table should use CLAMP boundary behavior."""
        pi, _, _ = extract_tables_from_js(mock_js_content)
        assert pi.boundary_behavior == BoundaryBehavior.CLAMP

    def test_emc_boundary_behavior(self, mock_js_content: str) -> None:
        """EMC table should use CLAMP boundary behavior."""
        _, emc, _ = extract_tables_from_js(mock_js_content)
        assert emc.boundary_behavior == BoundaryBehavior.CLAMP

    def test_mold_boundary_behavior(self, mock_js_content: str) -> None:
        """Mold table should use RAISE boundary behavior."""
        _, _, mold = extract_tables_from_js(mock_js_content)
        assert mold.boundary_behavior == BoundaryBehavior.RAISE

    def test_pi_values(self, mock_js_content: str) -> None:
        """PI values should be correctly extracted."""
        pi, _, _ = extract_tables_from_js(mock_js_content)
        assert pi[20, 50] == 45

    def test_emc_values(self, mock_js_content: str) -> None:
        """EMC values should be correctly extracted."""
        _, emc, _ = extract_tables_from_js(mock_js_content)
        # float16 rounds 5.5 to 5.5
        assert float(emc[20, 50]) == pytest.approx(5.5, abs=0.1)

    def test_mold_values(self, mock_js_content: str) -> None:
        """Mold values should be correctly extracted."""
        _, _, mold = extract_tables_from_js(mock_js_content)
        assert mold[20, 70] == 7


@pytest.mark.unit
class TestExtractErrorHandling:
    """Test error handling for invalid JS content."""

    def test_empty_js_content(self) -> None:
        """Empty JS should raise ExtractionError."""
        with pytest.raises(ExtractionError):
            extract_tables_from_js("")

    def test_invalid_js_syntax(self) -> None:
        """Invalid JS syntax should raise ExtractionError."""
        with pytest.raises(ExtractionError):
            extract_tables_from_js("this is not { valid javascript <<<")

    def test_missing_pitable(self) -> None:
        """JS without pitable should raise ExtractionError."""
        js = "var emctable = [1.0, 2.0, 3.0];"
        with pytest.raises(ExtractionError):
            extract_tables_from_js(js)

    def test_missing_emctable(self) -> None:
        """JS without emctable should raise ExtractionError."""
        js = "var pitable = [1, 2, 3];"
        with pytest.raises(ExtractionError):
            extract_tables_from_js(js)


@pytest.mark.unit
class TestFetchAndExtract:
    """Test the full fetch + extract pipeline."""

    def test_fetch_success(
        self, requests_mock: requests_mock.Mocker, mock_js_content: str
    ) -> None:
        """Successful fetch should return three LookupTables."""
        requests_mock.get("http://www.dpcalc.org/dp.js", text=mock_js_content)
        pi, emc, mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert isinstance(pi, LookupTable)
        assert isinstance(emc, LookupTable)
        assert isinstance(mold, LookupTable)

    def test_fetch_network_error(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """Network error should raise requests exception."""
        requests_mock.get(
            "http://www.dpcalc.org/dp.js",
            exc=ConnectionError("Network unreachable"),
        )
        with pytest.raises(ConnectionError):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

    def test_fetch_http_error(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """HTTP error should raise."""
        requests_mock.get("http://www.dpcalc.org/dp.js", status_code=404)
        with pytest.raises(Exception):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")


@pytest.mark.integration
class TestRealDpJs:
    """Integration tests using real dp.js from dpcalc.org.

    These tests download the actual dp.js and verify the extraction
    produces tables with expected shapes and value ranges.
    """

    def test_real_extraction_shapes(self) -> None:
        """Real dp.js should produce tables with expected dimensions."""
        pi, emc, mold = fetch_and_extract_tables(
            "http://www.dpcalc.org/dp.js"
        )
        assert pi.data.shape == (PI_ROWS, PI_COLS)
        assert emc.data.shape == (EMC_ROWS, EMC_COLS)
        assert mold.data.shape == (MOLD_ROWS, MOLD_COLS)

    def test_real_extraction_value_ranges(self) -> None:
        """Real dp.js values should be within expected ranges."""
        pi, emc, mold = fetch_and_extract_tables(
            "http://www.dpcalc.org/dp.js"
        )
        # PI: 0-9999
        assert np.all(pi.data >= 0)
        assert np.all(pi.data <= 9999)
        # EMC: 0.0-30.0
        assert np.all(emc.data >= 0.0)
        assert np.all(emc.data <= 30.0)
        # Mold: 0 or >= 1
        assert np.all((mold.data == 0) | (mold.data >= 1))

    def test_real_extraction_table_relationships(self) -> None:
        """Mold table should be a subset of PI table ranges."""
        pi, emc, mold = fetch_and_extract_tables(
            "http://www.dpcalc.org/dp.js"
        )
        assert mold.temp_min > pi.temp_min
        assert mold.temp_max < pi.temp_max
        assert emc.rh_min == 0
        assert emc.rh_max == 100
```

**Step 2: Run tests to verify they fail**

Run: `pytest tests/install/test_extract.py -v`
Expected: FAIL — `ModuleNotFoundError: No module named 'preservationeval.install.extract'`

**Step 3: Commit**

```bash
git add tests/install/test_extract.py
git commit -m "test: add failing tests for PyMiniRacer-based table extraction"
```

---

### Task 3: Implement extract.py — make unit tests pass

**Files:**
- Create: `src/preservationeval/install/extract.py`

**Context:** This module replaces `parse.py` + `patterns.py`. It uses PyMiniRacer to execute dp.js in an embedded V8 engine, then reads the global `pitable` and `emctable` arrays. The function signatures must match what the tests expect: `extract_tables_from_js(js_content)` and `fetch_and_extract_tables(url)`.

**Key insight from dp.js structure:** The `pitable` array contains PI data (first 8010 elements) followed by mold data (last 1584 elements). The `emctable` is a flat array of 8686 floats. Both are 1D arrays that need reshaping into 2D.

**Step 1: Write the extract module**

```python
"""Extract lookup tables from dp.js using PyMiniRacer (embedded V8).

This module replaces the regex-based parser. Instead of parsing JavaScript
with regex patterns, it executes dp.js in an embedded V8 engine and reads
the populated global arrays directly.
"""

import logging

import numpy as np
import requests
from py_mini_racer import MiniRacer

from preservationeval.types import (
    BoundaryBehavior,
    EMCTable,
    LookupTable,
    MoldTable,
    PITable,
)

logger = logging.getLogger(__name__)

# Browser global stubs — dp.js may reference these at load time
_JS_BROWSER_STUBS = """
var window = {};
var document = {createElement: function() { return {}; }};
var $ = function() { return {ready: function() {}}; };
var jQuery = $;
var navigator = {userAgent: ''};
"""

# Table dimensions extracted from dp.js function signatures.
# These are physical constants of the IPI Dew Point Calculator.
_PI_TEMP_MIN = -23
_PI_TEMP_MAX = 65
_PI_RH_MIN = 6
_PI_RH_MAX = 95
_PI_ROWS = _PI_TEMP_MAX - _PI_TEMP_MIN + 1  # 89
_PI_COLS = _PI_RH_MAX - _PI_RH_MIN + 1  # 90

_MOLD_TEMP_MIN = 2
_MOLD_TEMP_MAX = 45
_MOLD_RH_MIN = 65
_MOLD_RH_MAX = 100
_MOLD_ROWS = _MOLD_TEMP_MAX - _MOLD_TEMP_MIN + 1  # 44
_MOLD_COLS = _MOLD_RH_MAX - _MOLD_RH_MIN + 1  # 36

_EMC_TEMP_MIN = -20
_EMC_TEMP_MAX = 65
_EMC_RH_MIN = 0
_EMC_RH_MAX = 100
_EMC_ROWS = _EMC_TEMP_MAX - _EMC_TEMP_MIN + 1  # 86
_EMC_COLS = _EMC_RH_MAX - _EMC_RH_MIN + 1  # 101

_PI_DATA_SIZE = _PI_ROWS * _PI_COLS  # 8010
_MOLD_DATA_SIZE = _MOLD_ROWS * _MOLD_COLS  # 1584


class ExtractionError(Exception):
    """Raised when table extraction from JavaScript fails."""


def extract_tables_from_js(
    js_content: str,
) -> tuple[PITable, EMCTable, MoldTable]:
    """Extract PI, EMC, and Mold lookup tables from dp.js content.

    Args:
        js_content: The JavaScript source code of dp.js.

    Returns:
        Tuple of (PITable, EMCTable, MoldTable).

    Raises:
        ExtractionError: If extraction fails for any reason.
    """
    try:
        ctx = MiniRacer()
        ctx.eval(_JS_BROWSER_STUBS)
        ctx.eval(js_content)
    except Exception as e:
        raise ExtractionError(f"Failed to execute JavaScript: {e}") from e

    try:
        pi_raw = list(ctx.eval("pitable"))
        emc_raw = list(ctx.eval("emctable"))
    except Exception as e:
        raise ExtractionError(f"Failed to read JS globals: {e}") from e

    if len(pi_raw) < _PI_DATA_SIZE + _MOLD_DATA_SIZE:
        raise ExtractionError(
            f"pitable too small: {len(pi_raw)}, "
            f"expected >= {_PI_DATA_SIZE + _MOLD_DATA_SIZE}"
        )
    if len(emc_raw) < _EMC_ROWS * _EMC_COLS:
        raise ExtractionError(
            f"emctable too small: {len(emc_raw)}, "
            f"expected >= {_EMC_ROWS * _EMC_COLS}"
        )

    pi_table: PITable = LookupTable(
        np.array(pi_raw[:_PI_DATA_SIZE], dtype=np.int16).reshape(
            _PI_ROWS, _PI_COLS
        ),
        _PI_TEMP_MIN,
        _PI_RH_MIN,
        BoundaryBehavior.CLAMP,
    )

    mold_table: MoldTable = LookupTable(
        np.array(pi_raw[_PI_DATA_SIZE:_PI_DATA_SIZE + _MOLD_DATA_SIZE],
                 dtype=np.int16).reshape(_MOLD_ROWS, _MOLD_COLS),
        _MOLD_TEMP_MIN,
        _MOLD_RH_MIN,
        BoundaryBehavior.RAISE,
    )

    emc_table: EMCTable = LookupTable(
        np.array(emc_raw[:_EMC_ROWS * _EMC_COLS], dtype=np.float16).reshape(
            _EMC_ROWS, _EMC_COLS
        ),
        _EMC_TEMP_MIN,
        _EMC_RH_MIN,
        BoundaryBehavior.CLAMP,
    )

    logger.debug("Extracted tables: PI=%s, EMC=%s, Mold=%s",
                 pi_table.data.shape, emc_table.data.shape, mold_table.data.shape)
    return pi_table, emc_table, mold_table


def fetch_and_extract_tables(
    url: str,
) -> tuple[PITable, EMCTable, MoldTable]:
    """Download dp.js and extract lookup tables.

    Args:
        url: URL to download dp.js from.

    Returns:
        Tuple of (PITable, EMCTable, MoldTable).

    Raises:
        requests.RequestException: If download fails.
        ExtractionError: If extraction fails.
    """
    response = requests.get(url, timeout=30)
    response.raise_for_status()
    logger.debug("Downloaded dp.js (%d bytes)", len(response.text))
    return extract_tables_from_js(response.text)
```

**Step 2: Run unit tests to verify they pass**

Run: `pytest tests/install/test_extract.py -m unit -v`
Expected: All unit tests PASS

**Step 3: Run integration tests**

Run: `pytest tests/install/test_extract.py -m integration -v`
Expected: All integration tests PASS (requires network)

**Step 4: Run linting**

Run: `ruff check src/preservationeval/install/extract.py && mypy src/preservationeval/install/extract.py`
Expected: No errors

**Step 5: Commit**

```bash
git add src/preservationeval/install/extract.py
git commit -m "feat: add PyMiniRacer-based table extraction module"
```

---

### Task 4: Wire up generate_tables.py to use extract.py

**Files:**
- Modify: `src/preservationeval/install/generate_tables.py:23` (change import)
- Modify: `src/preservationeval/install/generate_tables.py:85` (change function call)

**Step 1: Update the import**

In `generate_tables.py`, change line 23:

```python
# OLD:
from .parse import fetch_and_validate_tables

# NEW:
from .extract import fetch_and_extract_tables
```

**Step 2: Update the function call**

In `generate_tables.py`, change line 85:

```python
# OLD:
pi_table, emc_table, mold_table = fetch_and_validate_tables(DP_JS_URL)

# NEW:
pi_table, emc_table, mold_table = fetch_and_extract_tables(DP_JS_URL)
```

**Step 3: Run the existing test suite (excluding test_parse.py)**

Run: `pytest --ignore=tests/install/test_parse.py -v`
Expected: All tests PASS. This confirms the new extraction produces tables compatible with the rest of the codebase.

**Step 4: Commit**

```bash
git add src/preservationeval/install/generate_tables.py
git commit -m "refactor: wire generate_tables to use PyMiniRacer extraction"
```

---

### Task 5: Update install __init__.py

**Files:**
- Modify: `src/preservationeval/install/__init__.py`

**Step 1: Update the module docstring and imports**

The `__init__.py` currently just exports `generate_tables`. No references to `parse` module. But update the docstring to reflect the new approach:

```python
"""Table installation package for preservationeval.

This package handles the generation of lookup tables during package installation.
It downloads source data from IPI's Dew Point Calculator, executes the JavaScript
in an embedded V8 engine (PyMiniRacer), and generates Python lookup tables for:
- Preservation Index (PI)
- Equilibrium Moisture Content (EMC)
- Mold Risk

Note:
    While this package is primarily used during installation, it remains
    available for table regeneration if needed.
"""

from .generate_tables import generate_tables

__all__ = ["__version__", "generate_tables"]

try:
    from preservationeval._version import version as __version__
except ImportError:
    __version__ = "unknown"
```

**Step 2: Run tests**

Run: `pytest --ignore=tests/install/test_parse.py -v`
Expected: All tests PASS

**Step 3: Commit**

```bash
git add src/preservationeval/install/__init__.py
git commit -m "docs: update install package docstring for PyMiniRacer approach"
```

---

### Task 6: Regenerate tables.py and run full validation

**Step 1: Regenerate tables using the new pipeline**

Run: `python -m scripts.generate_tables`
Expected: "Tables generated successfully" (or similar success message)

**Step 2: Run the full test suite**

Run: `pytest --ignore=tests/install/test_parse.py -v`
Expected: All tests PASS including integration and validation tests

**Step 3: Run the validation tests specifically (if Node.js available)**

Run: `pytest tests/test_validation.py -v`
Expected: PASS — this is the ultimate correctness gate proving the new extraction produces identical results to the original JS

**Step 4: Commit regenerated tables**

No commit needed — `tables.py` is in `.gitignore`.

---

### Task 7: Delete old regex pipeline

**Files:**
- Delete: `src/preservationeval/install/parse.py`
- Delete: `src/preservationeval/install/patterns.py`
- Delete: `tests/install/test_parse.py`

**Step 1: Delete the files**

```bash
rm src/preservationeval/install/parse.py
rm src/preservationeval/install/patterns.py
rm tests/install/test_parse.py
```

**Step 2: Check for remaining references**

Run: `rg "from.*parse import\|from.*patterns import\|install\.parse\|install\.patterns" src/ tests/`
Expected: No matches. If any found, update those references.

**Step 3: Run the full test suite**

Run: `pytest -v`
Expected: All tests PASS (no more test_parse.py to skip)

**Step 4: Run linting on entire codebase**

Run: `ruff check . && mypy .`
Expected: No errors related to removed modules

**Step 5: Commit**

```bash
git add -A
git commit -m "refactor: remove regex-based parsing pipeline (parse.py, patterns.py)"
```

---

### Task 8: Final cleanup and verification

**Step 1: Run full pre-commit hooks**

Run: `pre-commit run --all-files`
Expected: All hooks PASS

**Step 2: Run full test suite with coverage**

Run: `pytest --cov -v`
Expected: All tests PASS. Coverage should not regress (we deleted code AND its tests, so ratio stays similar).

**Step 3: Verify the package installs cleanly**

Run: `uv pip install -e ".[dev]" --force-reinstall`
Expected: Installs successfully, tables.py regenerated

**Step 4: Quick smoke test**

Run: `python -c "from preservationeval import pi, emc, mold; print(pi(20, 50), emc(20, 50), mold(20, 70))"`
Expected: Prints valid values (e.g., `75 7.0 28` or similar known values)

**Step 5: Commit any final adjustments**

If any cleanup was needed, commit with:
```bash
git commit -m "chore: final cleanup after install pipeline refactor"
```

---

## Summary of Commits

1. `chore: add mini-racer dependency for V8-based table extraction`
2. `test: add failing tests for PyMiniRacer-based table extraction`
3. `feat: add PyMiniRacer-based table extraction module`
4. `refactor: wire generate_tables to use PyMiniRacer extraction`
5. `docs: update install package docstring for PyMiniRacer approach`
6. `refactor: remove regex-based parsing pipeline (parse.py, patterns.py)`
7. `chore: final cleanup after install pipeline refactor` (if needed)
