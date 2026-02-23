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

# Browser global stubs - dp.js references jQuery and DOM APIs at load time.
# We stub enough to let it parse without errors, then call dp_init()
# explicitly to populate the table arrays.
_JS_BROWSER_STUBS = """
var window = {};
var document = {
    createElement: function() { return {}; },
    getElementById: function() { return {}; },
    body: {appendChild: function(){}, removeChild: function(){}}
};
var $ = function() { return {
    ready: function() {},
    click: function() {},
    table2CSV: function() { return ''; }
}; };
var jQuery = $;
var navigator = {userAgent: ''};
"""

# After loading dp.js, call dp_init() to populate the table arrays.
# dp_init() assigns inline data first, then tries to create UI widgets
# (Slider, bri_id) which fail without a real DOM. The try-catch lets
# the table assignments succeed before the DOM code errors out.
_JS_INIT_TABLES = "try { dp_init(); } catch(e) {}"

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
        ctx.eval(_JS_INIT_TABLES)
    except Exception as e:
        raise ExtractionError(f"Failed to execute JavaScript: {e}") from e

    try:
        pi_raw = list(ctx.eval("pitable"))
        emc_raw = list(ctx.eval("emctable"))
    except Exception as e:
        raise ExtractionError(f"Failed to read JS globals: {e}") from e

    expected_pi_size = _PI_DATA_SIZE + _MOLD_DATA_SIZE
    if len(pi_raw) < expected_pi_size:
        raise ExtractionError(
            f"pitable too small: {len(pi_raw)}, expected >= {expected_pi_size}"
        )

    expected_emc_size = _EMC_ROWS * _EMC_COLS
    if len(emc_raw) < expected_emc_size:
        raise ExtractionError(
            f"emctable too small: {len(emc_raw)}, expected >= {expected_emc_size}"
        )

    pi_table: PITable = LookupTable(
        np.array(pi_raw[:_PI_DATA_SIZE], dtype=np.int16).reshape(_PI_ROWS, _PI_COLS),
        _PI_TEMP_MIN,
        _PI_RH_MIN,
        BoundaryBehavior.CLAMP,
    )

    mold_start = _PI_DATA_SIZE
    mold_end = _PI_DATA_SIZE + _MOLD_DATA_SIZE
    mold_table: MoldTable = LookupTable(
        np.array(pi_raw[mold_start:mold_end], dtype=np.int16).reshape(
            _MOLD_ROWS, _MOLD_COLS
        ),
        _MOLD_TEMP_MIN,
        _MOLD_RH_MIN,
        BoundaryBehavior.RAISE,
    )

    emc_table: EMCTable = LookupTable(
        np.array(emc_raw[:expected_emc_size], dtype=np.float16).reshape(
            _EMC_ROWS, _EMC_COLS
        ),
        _EMC_TEMP_MIN,
        _EMC_RH_MIN,
        BoundaryBehavior.CLAMP,
    )

    logger.debug(
        "Extracted tables: PI=%s, EMC=%s, Mold=%s",
        pi_table.data.shape,
        emc_table.data.shape,
        mold_table.data.shape,
    )
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
