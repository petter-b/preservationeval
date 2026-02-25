"""Tests for preservationeval.install.extract."""

import hashlib
from typing import Any, Final
from unittest.mock import patch

import numpy as np
import pytest
import requests
import requests_mock

from preservationeval.install.const import MAX_DOWNLOAD_RETRIES
from preservationeval.install.extract import (
    ExtractionError,
    _validate_table_values,
    extract_tables_from_js,
    fetch_and_extract_tables,
)
from preservationeval.types import (
    BoundaryBehavior,
    EMCTable,
    LookupTable,
    MoldTable,
    PITable,
)

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

# Known test values used in mock_js_content fixture
MOCK_PI_VALUE: Final[int] = 45
MOCK_MOLD_VALUE: Final[int] = 7
MOCK_EMC_VALUE: Final[float] = 5.5

# Value range bounds for integration tests
PI_MAX_VALUE: Final[int] = 9999
EMC_MAX_VALUE: Final[float] = 30.0


@pytest.fixture
def mock_js_content() -> str:
    """Minimal JS that mimics dp.js structure with known values.

    PI values are all 45, mold values are all 7, EMC values are all 5.5.
    """
    pi_values = [MOCK_PI_VALUE] * (PI_ROWS * PI_COLS)
    mold_values = [MOCK_MOLD_VALUE] * (MOLD_ROWS * MOLD_COLS)
    emc_values = [MOCK_EMC_VALUE] * EMC_ARRAY_SIZE

    pi_data = ",".join(str(x) for x in pi_values + mold_values)
    emc_data = ",".join(str(x) for x in emc_values)
    pi_offset = abs(PI_TEMP_MIN)
    mold_offset = PI_ROWS * PI_COLS

    # Build JS lines separately to avoid E501 in the f-string
    lines = [
        "var $ = function() {};",
        f"pitable = new Array({PI_ARRAY_SIZE});",
        f"emctable = new Array({EMC_ARRAY_SIZE});",
        "var pi = function(t,rh) {",
        f"  var ti = (Math.max({PI_TEMP_MIN},"
        f"Math.min({PI_TEMP_MAX},Math.round(t)))"
        f"+{pi_offset})*{PI_COLS};",
        f"  var ri = Math.max({PI_RH_MIN},"
        f"Math.min({PI_RH_MAX},Math.round(rh)))"
        f"-{PI_RH_MIN};",
        "  return pitable[ti+ri];",
        "};",
        "var mold = function(t,rh) {",
        f"  if(t>{MOLD_TEMP_MAX}||t<{MOLD_TEMP_MIN}||rh<{MOLD_RH_MIN}) return 0;",
        f"  return pitable[{mold_offset}"
        f"+(Math.round(t)-{MOLD_TEMP_MIN})*{MOLD_COLS}"
        f"+Math.round(rh)-{MOLD_RH_MIN}];",
        "};",
        "var emc = function(t,rh) {",
        f"  var ti = (Math.max({EMC_TEMP_MIN},"
        f"Math.min({EMC_TEMP_MAX},Math.round(t)))"
        f"+{abs(EMC_TEMP_MIN)})*{EMC_COLS};",
        "  return emctable[ti+Math.round(rh)];",
        "};",
        f"pitable = [{pi_data}];",
        f"emctable = [{emc_data}];",
    ]
    return "\n".join(lines)


@pytest.fixture
def mock_js_hash(mock_js_content: str) -> str:
    """SHA-256 hash of mock_js_content, for patching DP_JS_SHA256."""
    return hashlib.sha256(mock_js_content.encode()).hexdigest()


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
        assert pi[20, 50] == MOCK_PI_VALUE

    def test_emc_values(self, mock_js_content: str) -> None:
        """EMC values should be correctly extracted."""
        _, emc, _ = extract_tables_from_js(mock_js_content)
        assert float(emc[20, 50]) == pytest.approx(MOCK_EMC_VALUE, abs=0.1)

    def test_mold_values(self, mock_js_content: str) -> None:
        """Mold values should be correctly extracted."""
        _, _, mold = extract_tables_from_js(mock_js_content)
        assert mold[20, 70] == MOCK_MOLD_VALUE


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

    def test_pitable_size_mismatch(self) -> None:
        """Raise ExtractionError when pitable has wrong size."""
        js = "pitable = [1, 2, 3]; emctable = [1.0, 2.0, 3.0];"
        with pytest.raises(ExtractionError, match="pitable size mismatch"):
            extract_tables_from_js(js)

    def test_emctable_size_mismatch(self) -> None:
        """Raise ExtractionError when emctable has wrong size."""
        pi_size = PI_ROWS * PI_COLS + MOLD_ROWS * MOLD_COLS
        values = ",".join(["1"] * pi_size)
        js = f"pitable = [{values}]; emctable = [1.0, 2.0, 3.0];"
        with pytest.raises(ExtractionError, match="emctable size mismatch"):
            extract_tables_from_js(js)


@pytest.mark.unit
class TestFetchAndExtract:
    """Test the full fetch + extract pipeline."""

    def test_fetch_success(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
        mock_js_hash: str,
    ) -> None:
        """Successful fetch should return three LookupTables."""
        requests_mock.get("http://www.dpcalc.org/dp.js", text=mock_js_content)
        with patch("preservationeval.install.extract.DP_JS_SHA256", mock_js_hash):
            pi, emc, mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert isinstance(pi, LookupTable)
        assert isinstance(emc, LookupTable)
        assert isinstance(mold, LookupTable)

    def test_fetch_network_error(self, requests_mock: requests_mock.Mocker) -> None:
        """Network error should raise requests exception after retries."""
        requests_mock.get(
            "http://www.dpcalc.org/dp.js",
            exc=requests.ConnectionError("Network unreachable"),
        )
        with (
            patch("preservationeval.install.extract.time.sleep"),
            pytest.raises(requests.ConnectionError),
        ):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

    def test_fetch_http_error(self, requests_mock: requests_mock.Mocker) -> None:
        """HTTP error should raise."""
        requests_mock.get("http://www.dpcalc.org/dp.js", status_code=404)
        with pytest.raises(requests.HTTPError):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")


@pytest.mark.unit
class TestHashVerification:
    """Test SHA-256 integrity verification of downloaded dp.js."""

    def test_matching_hash_succeeds(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
    ) -> None:
        """Download should succeed when content hash matches expected."""
        content_hash = hashlib.sha256(mock_js_content.encode()).hexdigest()
        requests_mock.get("http://test.example/dp.js", text=mock_js_content)

        with patch("preservationeval.install.extract.DP_JS_SHA256", content_hash):
            pi, _emc, _mold = fetch_and_extract_tables("http://test.example/dp.js")
        assert isinstance(pi, LookupTable)

    def test_mismatched_hash_raises(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
    ) -> None:
        """Download should fail with ExtractionError when hash doesn't match."""
        requests_mock.get("http://test.example/dp.js", text=mock_js_content)

        with (
            patch(
                "preservationeval.install.extract.DP_JS_SHA256",
                "0" * 64,
            ),
            pytest.raises(ExtractionError, match="integrity check failed"),
        ):
            fetch_and_extract_tables("http://test.example/dp.js")

    def test_hash_mismatch_not_retried(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
    ) -> None:
        """Hash mismatch should fail immediately without retrying."""
        requests_mock.get("http://test.example/dp.js", text=mock_js_content)

        with (
            patch(
                "preservationeval.install.extract.DP_JS_SHA256",
                "0" * 64,
            ),
            pytest.raises(ExtractionError),
        ):
            fetch_and_extract_tables("http://test.example/dp.js")

        assert requests_mock.call_count == 1


@pytest.mark.integration
class TestRealDpJs:
    """Integration tests using real dp.js from dpcalc.org.

    These tests download the actual dp.js and verify the extraction
    produces tables with expected shapes and value ranges.
    """

    def test_real_extraction_shapes(self) -> None:
        """Real dp.js should produce tables with expected dimensions."""
        pi, emc, mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert pi.data.shape == (PI_ROWS, PI_COLS)
        assert emc.data.shape == (EMC_ROWS, EMC_COLS)
        assert mold.data.shape == (MOLD_ROWS, MOLD_COLS)

    def test_real_extraction_value_ranges(self) -> None:
        """Real dp.js values should be within expected ranges."""
        pi, emc, mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert np.all(pi.data >= 0)
        assert np.all(pi.data <= PI_MAX_VALUE)
        assert np.all(emc.data >= 0.0)
        assert np.all(emc.data <= EMC_MAX_VALUE)
        assert np.all((mold.data == 0) | (mold.data >= 1))

    def test_real_extraction_table_relationships(self) -> None:
        """Mold table should be a subset of PI table ranges."""
        pi, emc, mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert mold.temp_min > pi.temp_min
        assert mold.temp_max < pi.temp_max
        assert emc.rh_min == EMC_RH_MIN
        assert emc.rh_max == EMC_RH_MAX


@pytest.mark.unit
class TestJSExecutionTimeout:
    """Test that JS execution has a timeout."""

    def test_timeout_passed_to_eval(self, mock_js_content: str) -> None:
        """MiniRacer.eval() should be called with timeout_sec."""
        with patch("preservationeval.install.extract.MiniRacer") as mock_mr:
            mock_ctx = mock_mr.return_value
            # eval returns different things depending on the call
            mock_ctx.eval.side_effect = [
                None,  # browser stubs
                None,  # js_content
                None,  # dp_init
                list(range(PI_ARRAY_SIZE)),  # pitable
                [5.5] * EMC_ARRAY_SIZE,  # emctable
            ]
            extract_tables_from_js(mock_js_content)

            # All eval calls should include timeout_sec
            for call in mock_ctx.eval.call_args_list:
                assert "timeout_sec" in call.kwargs, (
                    f"eval() called without timeout_sec: {call}"
                )


@pytest.mark.unit
class TestValueRangeValidation:
    """Test that extracted table values are validated against physical ranges."""

    def test_valid_values_pass(self, mock_js_content: str) -> None:
        """Mock data with valid values should pass validation."""
        # mock_js_content uses PI=45, EMC=5.5, Mold=7 — all valid
        pi, _emc, _mold = extract_tables_from_js(mock_js_content)
        assert pi is not None  # no ExtractionError raised

    def test_pi_over_max_rejected(self) -> None:
        """PI values above 9999 should raise ExtractionError."""
        pi_data = np.array([[10000]], dtype=np.int16)
        pi_table: PITable = LookupTable(pi_data, -23, 6, BoundaryBehavior.CLAMP)
        emc_data = np.array([[5.5]], dtype=np.float16)
        emc_table: EMCTable = LookupTable(emc_data, -20, 0, BoundaryBehavior.CLAMP)
        mold_data = np.array([[7]], dtype=np.int16)
        mold_table: MoldTable = LookupTable(mold_data, 2, 65, BoundaryBehavior.RAISE)

        with pytest.raises(ExtractionError, match="PI values out of range"):
            _validate_table_values(pi_table, emc_table, mold_table)

    def test_emc_over_max_rejected(self) -> None:
        """EMC values above 30.0 should raise ExtractionError."""
        pi_data = np.array([[45]], dtype=np.int16)
        pi_table: PITable = LookupTable(pi_data, -23, 6, BoundaryBehavior.CLAMP)
        emc_data = np.array([[31.0]], dtype=np.float16)
        emc_table: EMCTable = LookupTable(emc_data, -20, 0, BoundaryBehavior.CLAMP)
        mold_data = np.array([[7]], dtype=np.int16)
        mold_table: MoldTable = LookupTable(mold_data, 2, 65, BoundaryBehavior.RAISE)

        with pytest.raises(ExtractionError, match="EMC values out of range"):
            _validate_table_values(pi_table, emc_table, mold_table)

    def test_mold_negative_rejected(self) -> None:
        """Mold values below 0 should raise ExtractionError."""
        pi_data = np.array([[45]], dtype=np.int16)
        pi_table: PITable = LookupTable(pi_data, -23, 6, BoundaryBehavior.CLAMP)
        emc_data = np.array([[5.5]], dtype=np.float16)
        emc_table: EMCTable = LookupTable(emc_data, -20, 0, BoundaryBehavior.CLAMP)
        mold_data = np.array([[-1]], dtype=np.int16)
        mold_table: MoldTable = LookupTable(mold_data, 2, 65, BoundaryBehavior.RAISE)

        with pytest.raises(ExtractionError, match="Mold values contain negatives"):
            _validate_table_values(pi_table, emc_table, mold_table)

    def test_pi_negative_rejected(self) -> None:
        """PI values below 0 should raise ExtractionError."""
        pi_data = np.array([[-1]], dtype=np.int16)
        pi_table: PITable = LookupTable(pi_data, -23, 6, BoundaryBehavior.CLAMP)
        emc_data = np.array([[5.5]], dtype=np.float16)
        emc_table: EMCTable = LookupTable(emc_data, -20, 0, BoundaryBehavior.CLAMP)
        mold_data = np.array([[7]], dtype=np.int16)
        mold_table: MoldTable = LookupTable(mold_data, 2, 65, BoundaryBehavior.RAISE)

        with pytest.raises(ExtractionError, match="PI values out of range"):
            _validate_table_values(pi_table, emc_table, mold_table)

    def test_emc_negative_rejected(self) -> None:
        """EMC values below 0 should raise ExtractionError."""
        pi_data = np.array([[45]], dtype=np.int16)
        pi_table: PITable = LookupTable(pi_data, -23, 6, BoundaryBehavior.CLAMP)
        emc_data = np.array([[-1.0]], dtype=np.float16)
        emc_table: EMCTable = LookupTable(emc_data, -20, 0, BoundaryBehavior.CLAMP)
        mold_data = np.array([[7]], dtype=np.int16)
        mold_table: MoldTable = LookupTable(mold_data, 2, 65, BoundaryBehavior.RAISE)

        with pytest.raises(ExtractionError, match="EMC values out of range"):
            _validate_table_values(pi_table, emc_table, mold_table)


@pytest.mark.unit
class TestRetryLogic:
    """Test network retry behavior in fetch_and_extract_tables."""

    def test_retries_on_connection_error(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
        mock_js_hash: str,
    ) -> None:
        """Should retry on ConnectionError and succeed on last attempt."""
        responses = [
            {"exc": requests.ConnectionError("Network unreachable")},
            {"exc": requests.ConnectionError("Network unreachable")},
            {"text": mock_js_content, "status_code": 200},
        ]
        requests_mock.get("http://www.dpcalc.org/dp.js", responses)

        with (
            patch("preservationeval.install.extract.time.sleep"),
            patch("preservationeval.install.extract.DP_JS_SHA256", mock_js_hash),
        ):
            pi, _emc, _mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert isinstance(pi, LookupTable)

    def test_retries_on_timeout(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
        mock_js_hash: str,
    ) -> None:
        """Should retry on Timeout and succeed on last attempt."""
        responses = [
            {"exc": requests.Timeout("Request timed out")},
            {"text": mock_js_content, "status_code": 200},
        ]
        requests_mock.get("http://www.dpcalc.org/dp.js", responses)

        with (
            patch("preservationeval.install.extract.time.sleep"),
            patch("preservationeval.install.extract.DP_JS_SHA256", mock_js_hash),
        ):
            pi, _emc, _mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert isinstance(pi, LookupTable)

    @pytest.mark.parametrize("status_code", [500, 502, 503])
    def test_retries_on_server_error(
        self,
        requests_mock: requests_mock.Mocker,
        mock_js_content: str,
        mock_js_hash: str,
        status_code: int,
    ) -> None:
        """Should retry on HTTP 5xx and succeed on subsequent attempt."""
        responses: list[dict[str, Any]] = [
            {"status_code": status_code},
            {"text": mock_js_content, "status_code": 200},
        ]
        requests_mock.get("http://www.dpcalc.org/dp.js", responses)

        with (
            patch("preservationeval.install.extract.time.sleep"),
            patch("preservationeval.install.extract.DP_JS_SHA256", mock_js_hash),
        ):
            pi, _emc, _mold = fetch_and_extract_tables("http://www.dpcalc.org/dp.js")
        assert isinstance(pi, LookupTable)

    def test_no_retry_on_http_error_without_response(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """Should NOT retry when HTTPError has response=None."""
        requests_mock.get(
            "http://www.dpcalc.org/dp.js",
            exc=requests.HTTPError("No response"),
        )

        with pytest.raises(requests.HTTPError, match="No response"):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

        assert requests_mock.call_count == 1  # No retries

    def test_no_retry_on_client_error(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """Should NOT retry on HTTP 404 (client error)."""
        requests_mock.get("http://www.dpcalc.org/dp.js", status_code=404)

        with pytest.raises(requests.HTTPError):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

        assert requests_mock.call_count == 1  # No retries

    def test_raises_after_max_retries(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """Should re-raise original error after exhausting all retry attempts."""
        requests_mock.get(
            "http://www.dpcalc.org/dp.js",
            exc=requests.ConnectionError("Network unreachable"),
        )

        with (
            patch("preservationeval.install.extract.time.sleep"),
            pytest.raises(requests.ConnectionError, match="Network unreachable"),
        ):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

        assert requests_mock.call_count == MAX_DOWNLOAD_RETRIES

    def test_raises_http_error_after_5xx_exhaustion(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """Should raise HTTPError (not ConnectionError) when 5xx retries exhausted."""
        requests_mock.get("http://www.dpcalc.org/dp.js", status_code=503)

        with (
            patch("preservationeval.install.extract.time.sleep"),
            pytest.raises(requests.HTTPError),
        ):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

        assert requests_mock.call_count == MAX_DOWNLOAD_RETRIES

    def test_exponential_backoff_timing(
        self, requests_mock: requests_mock.Mocker
    ) -> None:
        """Backoff delays should double each retry: 1s, 2s."""
        requests_mock.get(
            "http://www.dpcalc.org/dp.js",
            exc=requests.ConnectionError("Network unreachable"),
        )
        sleep_calls: list[float] = []

        with (
            patch(
                "preservationeval.install.extract.time.sleep",
                side_effect=sleep_calls.append,
            ),
            pytest.raises(requests.ConnectionError),
        ):
            fetch_and_extract_tables("http://www.dpcalc.org/dp.js")

        # 3 attempts = 2 sleeps (no sleep after final failure)
        assert len(sleep_calls) == MAX_DOWNLOAD_RETRIES - 1
        assert sleep_calls[0] == pytest.approx(1.0)
        assert sleep_calls[1] == pytest.approx(2.0)
