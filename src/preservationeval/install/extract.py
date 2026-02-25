"""Extract lookup tables from dp.js using PyMiniRacer (embedded V8).

This module replaces the regex-based parser. Instead of parsing JavaScript
with regex patterns, it executes dp.js in an embedded V8 engine and reads
the populated global arrays directly.
"""

import time

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
from preservationeval.utils.logging import Environment, setup_logging

from .const import (
    DOWNLOAD_TIMEOUT,
    JS_EXECUTION_TIMEOUT_SEC,
    MAX_DOWNLOAD_RETRIES,
    RETRY_BACKOFF_BASE,
)

logger = setup_logging(__name__, env=Environment.INSTALL)

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


# Physical value ranges from IPI specification.
# Mold risk is days-to-mold, which has no defined upper bound in the IPI spec
# (high values = low risk). Only a lower-bound check is needed.
_PI_VALUE_MIN, _PI_VALUE_MAX = 0, 9999
_EMC_VALUE_MIN, _EMC_VALUE_MAX = 0.0, 30.0
_MOLD_VALUE_MIN = 0

# HTTP status code threshold for server errors (retryable)
_HTTP_SERVER_ERROR = 500


def _validate_table_values(
    pi_table: PITable, emc_table: EMCTable, mold_table: MoldTable
) -> None:
    """Validate extracted table values fall within expected physical ranges.

    Args:
        pi_table: Preservation Index lookup table.
        emc_table: Equilibrium Moisture Content lookup table.
        mold_table: Mold Risk lookup table.

    Raises:
        ExtractionError: If any table values are outside expected ranges.
    """
    pi_data = pi_table.data
    pi_min, pi_max = int(pi_data.min()), int(pi_data.max())
    if pi_min < _PI_VALUE_MIN or pi_max > _PI_VALUE_MAX:
        raise ExtractionError(
            f"PI values out of range [{_PI_VALUE_MIN}, {_PI_VALUE_MAX}]: "
            f"min={pi_min}, max={pi_max}"
        )

    emc_data = emc_table.data
    emc_min, emc_max = float(emc_data.min()), float(emc_data.max())
    if emc_min < _EMC_VALUE_MIN or emc_max > _EMC_VALUE_MAX:
        raise ExtractionError(
            f"EMC values out of range [{_EMC_VALUE_MIN}, {_EMC_VALUE_MAX}]: "
            f"min={emc_min}, max={emc_max}"
        )

    mold_data = mold_table.data
    mold_min = int(mold_data.min())
    if mold_min < _MOLD_VALUE_MIN:
        raise ExtractionError(f"Mold values contain negatives: min={mold_min}")


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
        ctx.eval(_JS_BROWSER_STUBS, timeout_sec=JS_EXECUTION_TIMEOUT_SEC)
        ctx.eval(js_content, timeout_sec=JS_EXECUTION_TIMEOUT_SEC)
        ctx.eval(_JS_INIT_TABLES, timeout_sec=JS_EXECUTION_TIMEOUT_SEC)
    except Exception as e:
        raise ExtractionError(f"Failed to execute JavaScript: {e}") from e

    try:
        pi_raw = list(ctx.eval("pitable", timeout_sec=JS_EXECUTION_TIMEOUT_SEC))
        emc_raw = list(ctx.eval("emctable", timeout_sec=JS_EXECUTION_TIMEOUT_SEC))
    except Exception as e:
        raise ExtractionError(f"Failed to read JS globals: {e}") from e

    expected_pi_size = _PI_DATA_SIZE + _MOLD_DATA_SIZE
    if len(pi_raw) != expected_pi_size:
        raise ExtractionError(
            f"pitable size mismatch: {len(pi_raw)}, expected {expected_pi_size}"
        )

    expected_emc_size = _EMC_ROWS * _EMC_COLS
    if len(emc_raw) != expected_emc_size:
        raise ExtractionError(
            f"emctable size mismatch: {len(emc_raw)}, expected {expected_emc_size}"
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
    _validate_table_values(pi_table, emc_table, mold_table)
    return pi_table, emc_table, mold_table


def _retry_delay(attempt: int) -> float:
    """Compute exponential backoff delay for a retry attempt."""
    return RETRY_BACKOFF_BASE * float(2 ** (attempt - 1))


def fetch_and_extract_tables(
    url: str,
) -> tuple[PITable, EMCTable, MoldTable]:
    """Download dp.js and extract lookup tables.

    Retries on transient network errors (ConnectionError, Timeout, HTTP 5xx)
    with exponential backoff. Does not retry on client errors (HTTP 4xx).

    ExtractionError is intentionally not retried — if the HTTP response was
    200 OK but the content is corrupted/truncated, re-downloading the same
    payload from a CDN cache won't help.

    Args:
        url: URL to download dp.js from.

    Returns:
        Tuple of (PITable, EMCTable, MoldTable).

    Raises:
        requests.ConnectionError: If all retry attempts fail due to network errors.
        requests.Timeout: If all retry attempts fail due to timeouts.
        requests.HTTPError: If a non-retryable HTTP error occurs (4xx), or
            all retry attempts fail due to server errors (5xx).
        ExtractionError: If extraction fails after successful download.
    """
    last_error: Exception | None = None
    for attempt in range(1, MAX_DOWNLOAD_RETRIES + 1):
        try:
            response = requests.get(url, timeout=DOWNLOAD_TIMEOUT)
            response.raise_for_status()
            logger.debug("Downloaded dp.js (%d bytes)", len(response.text))
            return extract_tables_from_js(response.text)
        except (requests.ConnectionError, requests.Timeout) as e:
            last_error = e
            if attempt < MAX_DOWNLOAD_RETRIES:
                delay = _retry_delay(attempt)
                logger.warning(
                    "Download attempt %d/%d failed: %s. Retrying in %.1fs...",
                    attempt,
                    MAX_DOWNLOAD_RETRIES,
                    e,
                    delay,
                )
                time.sleep(delay)
        except requests.HTTPError as e:
            if e.response is not None and e.response.status_code >= _HTTP_SERVER_ERROR:
                last_error = e
                if attempt < MAX_DOWNLOAD_RETRIES:
                    delay = _retry_delay(attempt)
                    logger.warning(
                        "Server error %d on attempt %d/%d. Retrying in %.1fs...",
                        e.response.status_code,
                        attempt,
                        MAX_DOWNLOAD_RETRIES,
                        delay,
                    )
                    time.sleep(delay)
            else:
                raise  # Non-retryable: client error (4xx) or missing response

    # last_error is always set — the loop only exits without returning
    # when at least one exception was caught.
    if last_error is None:  # pragma: no cover — defensive; can't happen
        raise RuntimeError("Bug: retry loop exited without setting last_error")
    logger.error(
        "All %d download attempts failed: %s", MAX_DOWNLOAD_RETRIES, last_error
    )
    raise last_error
