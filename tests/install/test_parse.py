"""Test module for preservationeval.install.parse."""

from typing import Final

import numpy as np
import pytest
import requests_mock

from preservationeval.install.parse import (
    ExtractionError,
    TableMetadataError,
    TableType,
    ValidationError,
    extract_array_sizes,
    extract_raw_arrays,
    extract_table_meta_data,
    fetch_and_validate_tables,
)
from preservationeval.types import LookupTable

# Constants from dp.js for validation
PI_ARRAY_SIZE: Final[int] = 9594
EMC_ARRAY_SIZE: Final[int] = 8686
PI_TEMP_RANGE: Final[dict[str, int]] = {"min": -23, "max": 65}
PI_RH_RANGE: Final[dict[str, int]] = {"min": 6, "max": 95}
MOLD_TEMP_RANGE: Final[dict[str, int]] = {"min": 2, "max": 45}
MOLD_RH_RANGE: Final[dict[str, int | None]] = {"min": 65, "max": None}
EMC_TEMP_RANGE: Final[dict[str, int]] = {"min": -20, "max": 65}
EMC_RH_RANGE: Final[dict[str, int]] = {"min": 0, "max": 100}
EXPECTED_EMC_MIN: Final[float] = 0.0
EXPECTED_EMC_MAX: Final[float] = 30.0
EXPECTED_PI_MIN: Final[int] = 0
EXPECTED_PI_MAX: Final[int] = 9999


# Test fixtures
@pytest.fixture
def valid_js_content() -> str:
    """Return sample JavaScript content matching dp.js structure."""
    # Create test arrays of correct size with known values
    pi_values = [45] * (PI_ARRAY_SIZE - 1584)  # Main PI values
    pi_values.extend([0] * 1584)  # Mold risk values (44 * 36)
    emc_values = [5.0] * EMC_ARRAY_SIZE  # EMC values

    return f"""
        pitable = new Array({PI_ARRAY_SIZE});
        emctable = new Array({EMC_ARRAY_SIZE});

        var pi = function(t,rh) {{
            return pitable[((t<-23 ? -23 : t>65 ? 65 : Math.round(t))+23) * 90 +
                         (rh<6 ? 6 : rh>95 ? 95 : Math.round(rh)) - 6];
        }};

        var mold = function(t,rh) {{
            if(t > 45 || t < 2 || rh < 65) return 0;
            return pitable[8010 + (Math.round(t) - 2) * 36 + Math.round(rh) - 65];
        }};

        var emc = function(t,rh) {{
            return emctable[(Math.max(-20,Math.min(65,Math.round(t)))+20) * 101 +
                          Math.round(rh)]
        }};

        pitable = [{",".join(str(x) for x in pi_values)}];
        emctable = [{",".join(str(x) for x in emc_values)}];
    """


@pytest.fixture
def mock_url_response(
    requests_mock: requests_mock.Mocker, valid_js_content: str
) -> None:
    """Mock HTTP response with test JavaScript content.

    Args:
        requests_mock: Pytest fixture for mocking requests
        valid_js_content: Fixture providing test JavaScript content
    """
    requests_mock.get("http://www.dpcalc.org/dp.js", text=valid_js_content)


# Unit tests
@pytest.mark.unit
class TestArrayExtraction:
    """Test table size extraction and array data validation."""

    def test_array_sizes(self, valid_js_content: str) -> None:
        """Verify array sizes match dp.js constants."""
        pi_size, emc_size = extract_array_sizes(valid_js_content)
        assert pi_size == PI_ARRAY_SIZE
        assert emc_size == EMC_ARRAY_SIZE

    def test_pi_range_extraction(self, valid_js_content: str) -> None:
        """Verify PI temperature and RH ranges match dp.js."""
        meta_data = extract_table_meta_data(valid_js_content)
        pi_info = meta_data[TableType.PI]

        assert pi_info.temp_min == PI_TEMP_RANGE["min"]
        assert pi_info._temp_max == PI_TEMP_RANGE["max"]
        assert pi_info.rh_min == PI_RH_RANGE["min"]
        assert pi_info._rh_max == PI_RH_RANGE["max"]

    def test_invalid_content(self) -> None:
        """Test handling of invalid JavaScript content."""
        with pytest.raises(TableMetadataError):
            extract_array_sizes("Invalid JavaScript")

    def test_array_shapes(self, valid_js_content: str) -> None:
        """Test that extracted arrays have correct shapes."""
        meta_data = extract_table_meta_data(valid_js_content)
        pi_array, emc_array = extract_raw_arrays(valid_js_content, meta_data)

        # Test PI array includes space for mold data
        assert len(pi_array) == (
            meta_data[TableType.PI].size + meta_data[TableType.MOLD].size
        )

        # Test EMC array size
        assert len(emc_array) == meta_data[TableType.EMC].size

    def test_array_content_types(self, valid_js_content: str) -> None:
        """Test that array values have correct types."""
        meta_data = extract_table_meta_data(valid_js_content)
        pi_array, emc_array = extract_raw_arrays(valid_js_content, meta_data)

        # Test PI values are integers
        assert all(isinstance(x, int) for x in pi_array)

        # Test EMC values are floats
        assert all(isinstance(x, float) for x in emc_array)


# Integration tests
@pytest.mark.integration
class TestTableExtraction:
    """Test complete table extraction process."""

    def test_fetch_and_validate(self, mock_url_response: None) -> None:
        """Test the complete table fetch and validation process."""
        pi_table, emc_table, mold_table = fetch_and_validate_tables(
            "http://www.dpcalc.org/dp.js"
        )

        # Test table types - using the concrete LookupTable class
        assert isinstance(pi_table, LookupTable)  # Not PITable generic
        assert isinstance(emc_table, LookupTable)  # Not EMCTable generic
        assert isinstance(mold_table, LookupTable)  # Not MoldTable generic

        # Test data types and shapes
        assert isinstance(pi_table.data, np.ndarray)  # Not NDArray generic
        assert pi_table.data.dtype in (np.int16, np.int32, np.int64)

        assert isinstance(emc_table.data, np.ndarray)
        assert emc_table.data.dtype in (np.float16, np.float32, np.float64)

        assert isinstance(mold_table.data, np.ndarray)
        assert mold_table.data.dtype in (np.int16, np.int32, np.int64)


# Validation tests
@pytest.mark.validation
class TestValueValidation:
    """Validate table values match dp.js behavior."""

    @pytest.mark.parametrize(
        "temp,rh,expected_value",
        [
            (20, 50, 45),  # Normal range
            (-23, 50, 45),  # At min temp
            (65, 50, 45),  # At max temp
            (20, 6, 45),  # At min RH
            (20, 95, 45),  # At max RH
        ],
    )
    def test_pi_values(
        self,
        mock_url_response: None,
        temp: int,
        rh: int,
        expected_value: int,
    ) -> None:
        """Test PI value extraction from parsed tables.

        Args:
            mock_url_response: Fixture providing mocked HTTP response
            temp: Temperature value to test
            rh: Relative humidity value to test
            expected_value: Expected PI value
        """
        pi_table, _, _ = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")
        value = pi_table[temp, rh]
        assert isinstance(value, (int | np.integer))
        assert value == expected_value

    @pytest.mark.parametrize(
        "temp,rh",
        [
            (20, 50),  # Normal range
            (-20, 0),  # Min bounds
            (65, 100),  # Max bounds
        ],
    )
    def test_emc_range(self, mock_url_response: None, temp: int, rh: int) -> None:
        """Verify EMC values are in valid range (0-30%)."""
        _, emc_table, _ = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")
        emc_value = emc_table[temp, rh]
        assert EXPECTED_EMC_MIN <= emc_value <= EXPECTED_EMC_MAX

    def test_mold_special_cases(self, mock_url_response: None) -> None:
        """Test mold risk special cases from dp.js."""
        _, _, mold_table = fetch_and_validate_tables("http://www.dpcalc.org/dp.js")

        # Test normal range value
        value = mold_table[20, 70]
        assert isinstance(value, (int | np.integer))
        assert EXPECTED_PI_MIN <= value <= EXPECTED_PI_MAX

        # Test special cases
        assert mold_table[2, 70] == 0  # At min temp
        assert mold_table[20, 65] == 0  # At min RH


# Performance tests
@pytest.mark.slow
def test_large_table_performance(mock_url_response: None) -> None:
    """Test performance with full-size tables."""
    pi_table, emc_table, _mold_table = fetch_and_validate_tables(
        "http://www.dpcalc.org/dp.js"
    )

    # Verify table shapes
    pi_rows = PI_TEMP_RANGE["max"] - PI_TEMP_RANGE["min"] + 1
    pi_cols = PI_RH_RANGE["max"] - PI_RH_RANGE["min"] + 1
    assert pi_table.data.shape == (pi_rows, pi_cols)

    emc_rows = EMC_TEMP_RANGE["max"] - EMC_TEMP_RANGE["min"] + 1
    emc_cols = EMC_RH_RANGE["max"] - EMC_RH_RANGE["min"] + 1
    assert emc_table.data.shape == (emc_rows, emc_cols)


@pytest.mark.unit
class TestMetadataExtraction:
    """Test metadata extraction edge cases and validation."""

    def test_array_offset_validation(self, valid_js_content: str) -> None:
        """Test that mold array offset matches PI table size."""
        meta_data = extract_table_meta_data(valid_js_content)
        pi_info = meta_data[TableType.PI]
        mold_info = meta_data[TableType.MOLD]

        assert mold_info.array_offset == pi_info.size

    def test_table_ranges(self, valid_js_content: str) -> None:
        """Test that tables have correct range relationships."""
        meta_data = extract_table_meta_data(valid_js_content)

        # PI ranges
        pi_info = meta_data[TableType.PI]
        assert pi_info.temp_min == PI_TEMP_RANGE["min"]
        assert pi_info._temp_max is not None  # First verify it's not None
        assert pi_info._temp_max == PI_TEMP_RANGE["max"]
        assert pi_info.rh_min == PI_RH_RANGE["min"]
        assert pi_info._rh_max == PI_RH_RANGE["max"]

        # EMC uses full RH range
        emc_info = meta_data[TableType.EMC]
        assert (
            emc_info.rh_range == EMC_RH_RANGE["max"] - EMC_RH_RANGE["min"] + 1
        )  # 0-100 inclusive

        # Mold range is subset of PI range
        mold_info = meta_data[TableType.MOLD]
        assert mold_info.temp_min > PI_TEMP_RANGE["min"]
        assert mold_info._temp_max is not None  # First verify it's not None
        assert mold_info._temp_max < PI_TEMP_RANGE["max"]


@pytest.mark.validation
class TestDataValidation:
    """Test data validation rules."""

    def test_value_ranges(self, mock_url_response: None) -> None:
        """Test that table values are within expected ranges."""
        pi_table, emc_table, mold_table = fetch_and_validate_tables(
            "http://www.dpcalc.org/dp.js"
        )

        # Test PI values
        assert np.all(pi_table.data >= EXPECTED_PI_MIN)
        assert np.all(pi_table.data <= EXPECTED_PI_MAX)

        # Test EMC values
        assert np.all(emc_table.data >= EXPECTED_EMC_MIN)
        assert np.all(emc_table.data <= EXPECTED_EMC_MAX)

        # Test Mold values (should be 0 or >= 1)
        assert np.all((mold_table.data == 0) | (mold_table.data >= 1))

    @pytest.mark.parametrize(
        "js_content",
        [
            "pitable = new Array(9594);\nemctable = new Array(8686);\n// No data",
            "pitable = [1,2];\nemctable = [1.0,2.0];\n// Incomplete data",
            "pitable = null;\nemctable = null;\n// Invalid data",
        ],
    )
    def test_invalid_data(self, js_content: str) -> None:
        """Test handling of invalid JavaScript content."""
        with pytest.raises((ExtractionError, ValidationError)):
            meta_data = extract_table_meta_data(js_content)
            extract_raw_arrays(js_content, meta_data)


@pytest.mark.integration
class TestTableCreation:
    """Test complete table creation process."""

    def test_table_relationships(self, mock_url_response: None) -> None:
        """Test relationships between different tables."""
        pi_table, emc_table, mold_table = fetch_and_validate_tables(
            "http://www.dpcalc.org/dp.js"
        )

        # Verify mold table dimensions are subset of PI dimensions
        assert mold_table.temp_min > pi_table.temp_min
        assert mold_table.temp_max < pi_table.temp_max

        # Verify EMC table has full RH range
        assert emc_table.rh_min == EMC_RH_RANGE["min"]
        assert emc_table.rh_max == EMC_RH_RANGE["max"]
