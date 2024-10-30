import requests
import re
import numpy as np
from typing import Tuple, List, Dict, Optional, Any
from dataclasses import dataclass
import logging
from enum import Enum

logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

class TableType(Enum):
    """Types of available lookup tables."""
    PI = "Preservation Index"
    EMC = "Equilibrium Moisture Content"
    MOLD = "Mold Risk"

@dataclass
class TableInfo:
    """Information about a lookup table's structure."""
    type: TableType
    temp_min: int
    temp_max: int
    rh_min: int
    rh_max: int
    offset: int = 0
    expected_min: float = 0.0
    expected_max: float = 100.0
    
    @property
    def temp_size(self) -> int:
        return self.temp_max - self.temp_min + 1
        
    @property
    def rh_size(self) -> int:
        return self.rh_max - self.rh_min + 1
        
    @property
    def total_size(self) -> int:
        return self.temp_size * self.rh_size
    
    def __str__(self) -> str:
        return (
            f"{self.type.value}:\n"
            f"  Temperature range: {self.temp_min}°C to {self.temp_max}°C\n"
            f"  Humidity range: {self.rh_min}% to {self.rh_max}%\n"
            f"  Size: {self.total_size} values"
            f"{f' (offset: {self.offset})' if self.offset else ''}"
        )

def extract_numeric_ranges(js_content: str, variable: str) -> Tuple[Optional[int], Optional[int]]:
    """Extract minimum and maximum values for a variable from JavaScript code."""
    # Pattern matches both forms:
    # if (t<-23) t=-23; else if (t>65) t=65;
    # if (t>65) t=65; else if (t<-23) t=-23;
    pattern = rf"""
        if\s*\({variable}\s*([<>])\s*(-?\d+)\)\s*
        {variable}\s*=\s*(-?\d+)\s*;\s*
        else\s*if\s*\({variable}\s*([<>])\s*(-?\d+)\)\s*
        {variable}\s*=\s*(-?\d+)
    """
    match = re.search(pattern, js_content, re.VERBOSE)
    if not match:
        return None, None
    
    # Determine which is min/max based on operators
    op1, val1, _, op2, val2, _ = match.groups()
    val1, val2 = int(val1), int(val2)
    
    if op1 == '<':
        return val1, val2
    return val2, val1

def parse_table_info(js_content: str) -> Dict[TableType, TableInfo]:
    """Extract table information from JavaScript code with enhanced validation."""
    tables = {}
    
    # Extract ranges
    temp_min, temp_max = extract_numeric_ranges(js_content, 't')
    rh_min, rh_max = extract_numeric_ranges(js_content, 'rh')
    
    if temp_min is not None and temp_max is not None and rh_min is not None and rh_max is not None:
        tables[TableType.PI] = TableInfo(
            type=TableType.PI,
            temp_min=temp_min,
            temp_max=temp_max,
            rh_min=rh_min,
            rh_max=rh_max,
            expected_min=0.0,
            expected_max=100.0
        )
    
    # Find EMC ranges
    emc_pattern = r'function\s+EMC\s*\([^)]*\)\s*{([^}]*)}'
    emc_match = re.search(emc_pattern, js_content)
    if emc_match:
        emc_code = emc_match.group(1)
        emc_temp_min, emc_temp_max = extract_numeric_ranges(emc_code, 't')
        # EMC typically uses full RH range
        tables[TableType.EMC] = TableInfo(
            type=TableType.EMC,
            temp_min=emc_temp_min or -20,
            temp_max=emc_temp_max or 65,
            rh_min=0,
            rh_max=100,
            expected_min=0.0,
            expected_max=30.0  # EMC is typically under 30%
        )
    
    # Find MOLD table offset and ranges
    mold_pattern = r'function\s+mold\s*\([^)]*\)\s*{([^}]*)}'
    mold_match = re.search(mold_pattern, js_content)
    if mold_match:
        mold_code = mold_match.group(1)
        offset_match = re.search(r'idx\s*=\s*(\d+)', mold_code)
        if offset_match:
            offset = int(offset_match.group(1))
            # Extract mold-specific ranges or use defaults
            mold_temp_min, mold_temp_max = extract_numeric_ranges(mold_code, 't')
            mold_rh_min, mold_rh_max = extract_numeric_ranges(mold_code, 'rh')
            tables[TableType.MOLD] = TableInfo(
                type=TableType.MOLD,
                temp_min=mold_temp_min or 2,
                temp_max=mold_temp_max or 45,
                rh_min=mold_rh_min or 65,
                rh_max=mold_rh_max or 100,
                offset=offset,
                expected_min=0.0,
                expected_max=100.0
            )
    
    return tables

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

def fetch_and_validate_tables(url: str) -> Tuple[Dict[TableType, TableInfo], Dict[TableType, np.ndarray]]:
    """Fetch, parse, and validate tables from JavaScript source."""
    try:
        logger.debug("Log level = DEBUG")

        response = requests.get(url, timeout=10)
        response.raise_for_status()
        js_content = response.text
        
        # Debug logging
        logger.debug("Fetched JavaScript content (first 200 chars):")
        logger.debug(js_content[:200])

        # Get table information
        table_info = parse_table_info(js_content)
        logger.debug("Parsed table information:")
        for table_type, info in table_info.items():
            logger.debug(f"{info}")

        # Extract table data
        pi_match = re.search(r'var\s+pitable\s*=\s*\[(.*?)\];', js_content, re.DOTALL)
        emc_match = re.search(r'var\s+emctable\s*=\s*\[(.*?)\];', js_content, re.DOTALL)
        
        # Debug logging for pattern matching
        logger.debug("Table pattern matches found:")
        logger.debug(f"PI table found: {pi_match is not None}")
        logger.debug(f"EMC table found: {emc_match is not None}")

        if not pi_match or not emc_match:
            raise ValueError("Could not find table data in JavaScript")
        
        # Convert to numpy arrays
        pi_data = np.array([int(x) for x in pi_match.group(1).split(',')])
        emc_data = np.array([float(x) for x in emc_match.group(1).split(',')])
        
        # Create dictionary for processed tables
        tables = {}
        
        # Process PI table
        if TableType.PI in table_info:
            info = table_info[TableType.PI]
            pi_table = pi_data[:info.total_size].reshape(info.temp_size, info.rh_size)
            validate_table_data(pi_table, info)
            tables[TableType.PI] = pi_table
        
        # Process MOLD table
        if TableType.MOLD in table_info:
            info = table_info[TableType.MOLD]
            mold_table = pi_data[info.offset:info.offset + info.total_size].reshape(info.temp_size, info.rh_size)
            validate_table_data(mold_table, info)
            tables[TableType.MOLD] = mold_table
        
        # Process EMC table
        if TableType.EMC in table_info:
            info = table_info[TableType.EMC]
            emc_table = emc_data[:info.total_size].reshape(info.temp_size, info.rh_size)
            validate_table_data(emc_table, info)
            tables[TableType.EMC] = emc_table
        
        return table_info, tables
        
    except requests.RequestException as e:
        raise requests.RequestException(f"Failed to download tables: {e}")
