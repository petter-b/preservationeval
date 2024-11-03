"""
Tables module for the Preservation Calculator

This module handles the extraction and processing of preservation-related
lookup tables from JavaScript source code. It processes three types of tables:
1. Preservation Index (PI) - Integer values indicating preservation quality
2. Equilibrium Moisture Content (EMC) - Float values for moisture content
3. Mold Risk - Integer values indicating mold growth risk

The module follows these main steps:
1. Extract table ranges and dimensions from JavaScript code
2. Parse the raw table data into structured format
3. Validate the table contents against expected ranges
4. Provide the tables in numpy array format for calculations
"""

import requests
import re
import numpy as np
from typing import Tuple, List, Dict
from dataclasses import dataclass
import logging
from enum import Enum

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)


class TableType(Enum):
    """Types of lookup tables used in preservation calculations."""
    PI = "Preservation Index"  # Integer values, higher is better
    EMC = "Equilibrium Moisture Content"  # Float values, percentage
    MOLD = "Mold Risk"  # Integer values, days until mold growth


@dataclass
class TableInfo:
    """Stores metadata and structure information for a lookup table.

    Attributes:
        type: The type of table (PI, EMC, or MOLD)
        temp_min: Minimum temperature in Celsius
        temp_max: Maximum temperature in Celsius
        rh_min: Minimum relative humidity percentage
        rh_max: Maximum relative humidity percentage
        temp_size: Number of temperature steps in table
        rh_size: Number of humidity steps in table
        offset: Optional offset for table indexing
        expected_min: Minimum expected value in table
        expected_max: Maximum expected value in table
    """
    type: TableType
    temp_min: int
    temp_max: int
    rh_min: int
    rh_max: int
    temp_size: int
    rh_size: int
    offset: int = 0
    expected_min: float = 0.0
    expected_max: float = 100.0

    @property
    def total_size(self) -> int:
        """Total number of elements in the table."""
        return self.temp_size * self.rh_size

    def __str__(self) -> str:
        """Human-readable representation of table information."""
        return (
            f"{self.type.value}:\n"
            f"  Temperature range: {self.temp_min}°C to {self.temp_max}°C\n"
            f"  Humidity range: {self.rh_min}% to {self.rh_max}%\n"
            f"  Size: {self.total_size} values"
            f"{f' (offset: {self.offset})' if self.offset else ''}"
        )


# Regular expression patterns for extracting table information
REGEX_PATTERNS = {
    'array_size': r'pitable\s*=\s*new\s*Array\((\d+)\)',
    'pi_ranges': r'return\s+pitable\[\(\(t<(-?\d+)\s*\?\s*(-?\d+)\s*:\s*t>(\d+)\s*\?\s*(\d+).+?rh<(\d+)\s*\?\s*(\d+)\s*:\s*rh\s*>\s*(\d+)\s*\?\s*(\d+)',  # noqa: E501
    'mold_ranges': r'if\s*\(t\s*>\s*(\d+)\s*\|\|\s*t\s*<\s*(\d+)\s*\|\|\s*rh\s*<\s*(\d+)\)',  # noqa: E501
    'emc_ranges': r'Math\.max\((-?\d+),Math\.min\((\d+)',
    'pi_data': r'pitable\s*=\s*\[([\d,\s]+)\]',
    'emc_data': r'emctable\s*=\s*\[([\d.,\s]+)\]',
    'mold_data': r'moldtable\s*=\s*\[([\d,\s]+)\]'
}


def find_factors(n: int) -> List[Tuple[int, int]]:
    """Find all factor pairs of a number to determine table dimensions."""
    factors = []
    for i in range(1, int(n ** 0.5) + 1):
        if n % i == 0:
            factors.append((i, n // i))
            if i != n // i:
                factors.append((n // i, i))
    return sorted(factors)


def extract_ranges_from_js(
    js_content: str
) -> Dict[TableType, Tuple[Tuple[int, int], Tuple[int, int]]]:
    """Extract temperature and RH ranges for each table from JavaScript code.

    Returns a dictionary mapping TableType to
    ((temp_min, temp_max), (rh_min, rh_max))
    """
    ranges = {}

    # Extract array size for validation
    array_match = re.search(REGEX_PATTERNS['array_size'], js_content)
    if array_match:
        logger.debug(f"Found pitable array size: {array_match.group(1)}")

    # Extract PI table ranges
    pi_match = re.search(REGEX_PATTERNS['pi_ranges'], js_content)
    if pi_match:
        t_min, t_min_val, t_max, t_max_val, rh_min, rh_min_val, rh_max, rh_max_val = map(int, pi_match.groups())  # noqa: E501
        ranges[TableType.PI] = ((t_min_val, t_max_val), (rh_min_val, rh_max_val))  # noqa: E501
        logger.debug(f"Found PI ranges - T: {t_min_val} to {t_max_val}, RH: {rh_min_val} to {rh_max_val}")  # noqa: E501

    # Extract Mold ranges
    mold_match = re.search(REGEX_PATTERNS['mold_ranges'], js_content)
    if mold_match:
        t_max, t_min, rh_min = map(int, mold_match.groups())
        ranges[TableType.MOLD] = ((t_min, t_max), (rh_min, 100))
        logger.debug(f"Found Mold ranges - T: {t_min} to {t_max}, RH: {rh_min} to 100")  # noqa: E501

    # Extract EMC ranges
    emc_match = re.search(REGEX_PATTERNS['emc_ranges'], js_content)
    if emc_match:
        t_min, t_max = map(int, emc_match.groups())
        ranges[TableType.EMC] = ((t_min, t_max), (0, 100))
        logger.debug(f"Found EMC ranges - T: {t_min} to {t_max}, RH: 0 to 100")

    return ranges


def validate_table_data(data: np.ndarray, info: TableInfo) -> None:
    """Validate table data against expected ranges and characteristics."""
    if data.size != info.total_size:
        raise ValueError(
            f"{info.type.value}: Invalid size {data.size}, "
            f"expected {info.total_size}"
        )

    # Check for NaN or infinite values
    if np.any(~np.isfinite(data)):
        raise ValueError(f"{info.type.value}: Contains NaN or infinite values")

    # Check value ranges
    data_min, data_max = np.min(data), np.max(data)
    if not (info.expected_min <= data_max <= info.expected_max):
        logger.warning(
            f"{info.type.value}: Values outside expected range "
            f"[{info.expected_min}, {info.expected_max}]: "
            f"found [{data_min}, {data_max}]"
        )

    # Check for discontinuities
    differences = np.abs(np.diff(data))
    max_diff = np.max(differences)
    if max_diff > (info.expected_max - info.expected_min) / 2:
        logger.warning(
            f"{info.type.value}: Large value jumps detected "
            f"(max difference: {max_diff})"
        )


def parse_table_info(js_content: str) -> Dict[TableType, TableInfo]:
    """Extract table information from JavaScript code.

    Args:
        js_content: JavaScript source code containing table definitions

    Returns:
        Dictionary mapping TableType to TableInfo objects
    """
    # Get ranges for all tables
    ranges = extract_ranges_from_js(js_content)
    tables = {}

    # Process PI table
    pi_match = re.search(REGEX_PATTERNS['pi_data'], js_content)
    if pi_match and TableType.PI in ranges:
        pi_values = [int(x.strip()) for x in pi_match.group(1).split(',')]
        (t_min, t_max), (rh_min, rh_max) = ranges[TableType.PI]
        factors = find_factors(len(pi_values))
        pi_dims = max(factors, key=lambda x: min(x))
        logger.debug(f"Found {len(pi_values)} PI values")
        tables[TableType.PI] = TableInfo(
            type=TableType.PI,
            temp_min=t_min,
            temp_max=t_max,
            rh_min=rh_min,
            rh_max=rh_max,
            temp_size=pi_dims[0],
            rh_size=pi_dims[1],
            expected_min=0,
            expected_max=9999
        )

    # Process EMC table
    emc_match = re.search(REGEX_PATTERNS['emc_data'], js_content)
    if emc_match and TableType.EMC in ranges:
        emc_values = [float(x.strip()) for x in emc_match.group(1).split(',')]
        (t_min, t_max), (rh_min, rh_max) = ranges[TableType.EMC]
        factors = find_factors(len(emc_values))
        emc_dims = max(factors, key=lambda x: min(x))
        logger.debug(f"Found {len(emc_values)} EMC values")
        tables[TableType.EMC] = TableInfo(
            type=TableType.EMC,
            temp_min=t_min,
            temp_max=t_max,
            rh_min=rh_min,
            rh_max=rh_max,
            temp_size=emc_dims[0],
            rh_size=emc_dims[1],
            expected_min=0.0,
            expected_max=30.0
        )

    return tables


def create_table_array(
        values: List[str],
        dtype: np.dtype,
        info: TableInfo
) -> np.ndarray:
    """Create and validate a numpy array for a table.

    Args:
        values: List of string values from JavaScript
        dtype: Numpy dtype (int32 for PI/MOLD, float64 for EMC)
        info: TableInfo object containing metadata
    """
    data = np.array([dtype(x.strip()) for x in values], dtype=dtype)  # type: ignore  # noqa: E501
    table = data[:info.total_size].reshape(info.temp_size, info.rh_size)
    validate_table_data(table, info)
    return table


def fetch_and_validate_tables(
    url: str
) -> Tuple[Dict[TableType, TableInfo], Dict[TableType, np.ndarray]]:
    """Main function to fetch and process all tables.

    Returns:
        Tuple of (table_info_dict, table_data_dict)
    """
    try:
        # Fetch JavaScript content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        js_content = response.text
        logger.debug(f"Content length: {len(js_content)} characters")

        # Extract table information and data
        table_info = parse_table_info(js_content)
        tables = {}

        # Process each table type
        for table_type, info in table_info.items():
            pattern = REGEX_PATTERNS[f'{table_type.name.lower()}_data']
            match = re.search(pattern, js_content)

            if match:
                dtype = np.int32 if table_type in (TableType.PI, TableType.MOLD) else np.float64  # noqa: E501
                tables[table_type] = create_table_array(
                    match.group(1).split(','),
                    dtype,  # type: ignore
                    info
                )
                logger.debug(f"{table_type.value} table processed - shape: {tables[table_type].shape}")  # noqa: E501

        return table_info, tables

    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to download tables: {e}")
