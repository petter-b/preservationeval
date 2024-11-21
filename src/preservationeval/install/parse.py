"""Tables module for the Preservation Calculator.

This module handles the extraction, validation, and processing of lookup tables
from the Image Permanence Institute's Dew Point Calculator JavaScript code.
It processes three types of tables:

1. Preservation Index (PI) - Integer values indicating preservation quality
   - Higher values indicate better preservation conditions
   - Values typically range from 0 to 9999
   - Dimensions are determined by temperature and RH ranges

2. Equilibrium Moisture Content (EMC) - Float values for moisture content
   - Values represent percentage of moisture content
   - Typically ranges from 0% to 30%
   - Used to assess risk of moisture-related damage

3. Mold Risk - Integer values indicating days until likely mold growth
   - Values represent number of days
   - Located in the latter portion of the PI array
   - Dimensions determined by valid temperature and RH ranges for mold growth

The module follows these main steps:
1. Download JavaScript code from the IPI calculator
2. Extract table dimensions and ranges using regex patterns
3. Parse the raw table data into structured arrays
4. Validate the data against expected ranges and characteristics
5. Create ShiftedArray objects for convenient lookup

Note:
    The table data is extracted from JavaScript code that uses specific array
    indexing and range checking. The regular expressions in this module are
    designed to match these patterns and may need updating if the source
    code structure changes.
"""

# Standard library imports
from array import array

# Type hints
from dataclasses import dataclass
from enum import Enum
from typing import Final

import numpy as np
import requests

from preservationeval.types import (
    BoundaryBehavior,
    EMCTable,
    LookupTable,
    MoldTable,
    PITable,
)
from preservationeval.utils.logging import Environment, setup_logging

from .patterns import JS_PATTERNS


# Custom exeptions
class TableMetadataError(Exception):
    """Base exception for table metadata errors."""

    def __init__(self, message: str, original_error: Exception | None = None) -> None:
        """Initialize metadata error with message and original cause.

        Args:
            message: Human-readable error description
            original_error: The underlying exception that caused this error.
                Defaults to None if this is the root cause.
        """
        super().__init__(message)
        self.original_error = original_error


class ExtractionError(TableMetadataError):
    """Exception for table extraction errors."""

    ...


class ValidationError(TableMetadataError):
    """Exception for table validation errors."""

    ...


class TableType(Enum):
    """Types of lookup tables used in preservation calculations."""

    PI = "Preservation Index"  # Integer values, higher is better
    EMC = "Equilibrium Moisture Content"  # Float values, percentage
    MOLD = "Mold Risk"  # Integer values, days until mold growth


@dataclass
class TableMetaData:
    """Store meta data for a table lookup table.

    This class holds all the information about how table lookups are
    calculated, including range limits, offsets, and array dimensions.
    """

    temp_min: int
    rh_range: int
    _temp_max: int | None = None
    _temp_offset: int | None = None
    _temp_range: int | None = None
    _rh_min: int | None = None
    _rh_max: int | None = None
    _rh_offset: int | None = None
    array_offset: int = 0
    _MIN_RH_MIN: Final[int] = 0
    _MAX_RH_MAX: Final[int] = 100
    _MAX_RH_RANGE: Final[int] = 101

    def __post_init__(self) -> None:
        """Validate and calculate values after initialization."""
        try:
            self._initialize_temp_range()
            self._initialize_rh_min()
        except Exception as e:
            raise ValidationError(f"Initialization failed: {e!s}") from e
        try:
            self._validate_temp_offset()
            self._validate_rh_offset()
        except Exception as e:
            raise ValidationError(f"Validation failed: {e!s}") from e

    def _initialize_temp_range(self) -> None:
        """Initialize temperature size if not provided."""
        if self._temp_range is None:
            if self._temp_max is not None:
                try:
                    self._temp_range = self._temp_max - self.temp_min + 1
                except TypeError as e:
                    raise ValidationError(
                        f"Cannot calculate temp_size: temp_max={self._temp_max}, "
                        f"temp_min={self.temp_min}"
                    ) from e
            else:
                raise ValidationError("Cannot calculate temp_size: temp_max=None!")

    def _initialize_rh_min(self) -> None:
        """Initialize RH minimum if not provided."""
        if self._rh_min is None:
            if self._rh_max is not None:
                try:
                    self._rh_min = self._rh_max - self.rh_range + 1
                except TypeError as e:
                    raise ValidationError(
                        f"Cannot calculate rh_min: rh_max={self._rh_max}, "
                        f"rh_size={self.rh_range}"
                    ) from e
            elif self.rh_range == self._MAX_RH_RANGE:
                self._rh_min = self._MIN_RH_MIN
                self._rh_max = self._MAX_RH_MAX
            else:
                raise ValidationError("Cannot calculate rh_min: rh_max=None!")

    def _validate_temp_offset(self) -> None:
        """Validate temperature offset."""
        if self._temp_offset is not None:
            if self._temp_offset != -1 * self.temp_min:
                raise ValidationError(
                    f"Temperature offset ({self._temp_offset}) must equal "
                    f"to -1 * minimum temperature ({abs(self.temp_min)})"
                )

    def _validate_rh_offset(self) -> None:
        """Validate RH offset."""
        if self._rh_offset is not None and self._rh_min is not None:
            if self._rh_offset != -1 * self._rh_min:
                raise ValidationError(
                    f"RH offset ({self._rh_offset}) must equal "
                    f"to -1 * RH minimum ({self._rh_min})"
                )

    def __str__(self) -> str:
        """Human-readable representation of table metadata."""
        return (
            f"temp_min={self.temp_min}, temp_max={self._temp_max}, "
            f"temp_offset={self._temp_offset}, temp_range={self._temp_range}, "
            f"rh_min={self._rh_min}, rh_max={self._rh_max}, "
            f"rh_offset={self._rh_offset}, rh_range={self.rh_range}, "
            f"array_offset={self.array_offset}"
        )

    @property
    def temp_range(self) -> int:
        """Return temp_size that is guaranteed to be initialized."""
        if self._temp_range is None:
            raise ValueError("temp_size has not been initialized")
        return self._temp_range

    @property
    def rh_min(self) -> int:
        """Return rh_min that is guaranteed to be initialized."""
        if self._rh_min is None:
            raise ValueError("rh_min has not been initialized")
        return self._rh_min

    @property
    def size(self) -> int:
        """Return total number of elements in the table."""
        try:
            return self.temp_range * self.rh_range
        except TypeError as e:
            raise ValueError("temp_size or rh_size has not been initialized") from e


# Initialize module logger
logger = setup_logging(__name__, env=Environment.INSTALL)


def to_int(value: str) -> int:
    """Convert string to integer, handling negative numbers with whitespace.

    Args:
        value: String representation of an integer, possibly with whitespace
            between minus sign and digits (e.g., "- 45" or "-45")

    Returns:
        Integer value

    Raises:
        ValueError: If the string cannot be converted to an integer
    """
    try:
        return int(value.replace(" ", ""))
    except ValueError as e:
        raise ValueError(f"Cannot convert '{value}' to integer") from e


def extract_array_sizes(js_content: str) -> tuple[int, int]:
    """Extract the size of the pitable and emctable arrays.

    Args:
        js_content: JavaScript source code containing array initializations

    Returns:
        Tuple containing:
            - Size of the pitable array (including mold risk section)
            - Size of the emctable array

    Raises:
        ExtractionError: If array sizes cannot be extracted
        ValidationError: If extracted sizes are invalid
    """
    logger.debug("Starting array size extraction")

    try:
        # Extract pitable array size
        pi_size_match = JS_PATTERNS["pi_array_size"].search(js_content)
        if not pi_size_match:
            raise ExtractionError("PI array size pattern not found")

        pi_array_size = int(pi_size_match.group("size"))
        if pi_array_size <= 0:
            raise ValidationError(f"Invalid PI array size: {pi_array_size}")
        logger.debug(f"Extracted PI array size: {pi_array_size}")

        # Extract emctable array size
        emc_size_match = JS_PATTERNS["emc_array_size"].search(js_content)
        if not emc_size_match:
            raise ExtractionError("EMC array size pattern not found")

        emc_array_size = int(emc_size_match.group("size"))
        if emc_array_size <= 0:
            raise ValidationError(f"Invalid EMC array size: {emc_array_size}")
        logger.debug(f"Extracted EMC array size: {emc_array_size}")

        return pi_array_size, emc_array_size

    except (ValueError, AttributeError) as e:
        raise ExtractionError("Failed to parse array sizes") from e


def extract_xxx_meta_data(js_content: str, table_type: TableType) -> TableMetaData:
    """Extract table metadata from JavaScript code.

    Args:
        js_content: JavaScript source code to parse
        table_type: Type of table to extract metadata for

    Returns:
        TableMetaData object containing the extracted information

    Raises:
        ExtractionError: If metadata cannot be extracted
    """
    pattern_map = {
        TableType.PI: "pi_ranges",
        TableType.EMC: "emc_ranges",
        TableType.MOLD: "mold_ranges",
    }

    logger.debug(f"Attempting to match {table_type.value} ranges pattern")
    try:
        match = JS_PATTERNS[pattern_map[table_type]].search(js_content)
        if not match:
            raise ExtractionError(f"Failed to extract {table_type.value} metadata")

        groups = match.groupdict()
        logger.debug(f"Found {table_type.value} ranges match: {groups}")

        # Common metadata parameters
        metadata_args = {
            "temp_min": to_int(groups["temp_min"]),
            "_temp_max": to_int(groups["temp_max"]),
            "rh_range": int(groups["rh_size"]),
        }

        # Type-specific parameters
        if table_type in (TableType.PI, TableType.MOLD):
            metadata_args.update(
                {
                    "_rh_min": int(groups["rh_min"]),
                    "_rh_offset": to_int(groups["rh_offset"]),
                }
            )

        if table_type == TableType.MOLD:
            metadata_args["array_offset"] = int(groups["offset"])

        if table_type != TableType.MOLD:
            metadata_args["_temp_offset"] = to_int(groups["temp_offset"])

        if table_type == TableType.PI:
            metadata_args["_rh_max"] = int(groups["rh_max"])

        return TableMetaData(**metadata_args)

    except Exception as e:
        logger.exception(e)
        raise


def cross_check_meta_data(
    meta_data: dict[TableType, TableMetaData], pi_array_size: int, emc_array_size: int
) -> None:
    """Validate the consistency of table metadata with array sizes.

    Performs the following validation checks:

    1. Ensures that the sum of the Preservation Index (PI) table size
       and the Mold table size matches the expected `pi_array_size`.
    2. Confirms that the PI table size aligns with the Mold table's
       array offset.
    3. Verifies that the Equilibrium Moisture Content (EMC) table size
       equals the given `emc_array_size`.

    Args:
        meta_data (dict[TableType, TableMetaData]): A dictionary containing
            metadata for each table type.
        pi_array_size (int): The expected total size for the PI and Mold
            tables combined.
        emc_array_size (int): The expected size for the EMC table.

    Raises:
        ValidationError: If any of the checks fail, indicating a mismatch
            between the metadata and the actual array sizes.
    """
    try:
        if (
            meta_data[TableType.PI].size + meta_data[TableType.MOLD].size
            != pi_array_size
        ):
            raise ValidationError("PI and Mold table sizes mismatch with pi_array_size")

        if meta_data[TableType.PI].size != meta_data[TableType.MOLD].array_offset:
            raise ValidationError("PI table size mismatch with MOLD array offset")

        if meta_data[TableType.EMC].size != emc_array_size:
            raise ValidationError("EMC table size mismatch with emc_array_size")
    except Exception as e:
        logger.exception(e)
        raise


def extract_table_meta_data(js_content: str) -> dict[TableType, TableMetaData]:
    """Extract table metadata from JavaScript source code.

    Args:
        js_content: JavaScript source code containing table definitions

    Returns:
        Dictionary mapping TableType to corresponding TableMetaData

    Raises:
        ExtractionError: If metadata extraction fails
        ValidationError: If extracted metadata is invalid
    """
    logger.debug("Starting to extract table metadata")
    meta_data = {}

    try:
        # Extract array sizes first for validation
        pi_array_size, emc_array_size = extract_array_sizes(js_content)
        logger.debug(f"Array sizes - PI: {pi_array_size}, EMC: {emc_array_size}")

        # Extract metadata for each table type
        meta_data = {t: extract_xxx_meta_data(js_content, t) for t in TableType}

        # Validate extracted metadata
        cross_check_meta_data(meta_data, pi_array_size, emc_array_size)
        logger.debug("Metadata validation successful")

        return meta_data

    except (ExtractionError, ValidationError) as e:
        logger.error(f"Failed to extract table metadata: {e}")
        raise
    except Exception as e:
        error_msg = "Unexpected error during metadata extraction"
        logger.error(f"{error_msg}: {e}")
        raise ExtractionError(error_msg) from e


def _validate_array_sizes(
    pi_array: array,  # type: ignore
    emc_array: array,  # type: ignore
    meta_data: dict[TableType, TableMetaData],
) -> None:
    """Validate that extracted arrays match expected sizes.

    Args:
        pi_array: Array containing PI and mold risk data
        emc_array: Array containing EMC data
        meta_data: Dictionary of metadata for each table type

    Raises:
        ValidationError: If array sizes don't match metadata
    """
    pi_array_size = meta_data[TableType.PI].size + meta_data[TableType.MOLD].size
    if pi_array_size != len(pi_array):
        raise ValidationError(
            f"PI array size mismatch: expected {pi_array_size}, got {len(pi_array)}"
        )

    emc_array_size = meta_data[TableType.EMC].size
    if emc_array_size != len(emc_array):
        raise ValidationError(
            f"EMC array size mismatch: expected {emc_array_size}, got {len(emc_array)}"
        )


def extract_raw_arrays(
    js_content: str,
    meta_data: dict[TableType, TableMetaData],
) -> tuple[array, array]:  # type: ignore
    """Extract raw arrays from JavaScript content.

    Args:
        js_content: JavaScript source code containing table data.
        meta_data: Dictionary of metadata for each table type.

    Returns:
        Tuple of (pi_array, emc_array), where:
            - pi_array: array.array of integers representing preservation index data.
            - emc_array: array.array of floats representing equilibrium moisture content
                data.

    Raises:
        ExtractionError: If table data cannot be found or parsed.
        ValidationError: If array sizes don't match metadata.
    """
    try:
        # Extract PI data
        pi_match = JS_PATTERNS["pi_data"].search(js_content)
        if not pi_match:
            raise ExtractionError("Could not find PI table data in JavaScript")
        pi_values = [int(x.strip()) for x in pi_match.group(1).split(",")]
        pi_array = array("i", pi_values)  # 'i' for signed int
        logger.debug(f"Extracted {len(pi_array)} PI values")

        # Extract EMC data
        emc_match = JS_PATTERNS["emc_data"].search(js_content)
        if not emc_match:
            raise ExtractionError("Could not find EMC table data in JavaScript")
        emc_values = [float(x.strip()) for x in emc_match.group(1).split(",")]
        emc_array = array("d", emc_values)  # 'd' for double
        logger.debug(f"Extracted {len(emc_array)} EMC values")

        # Validate array sizes
        _validate_array_sizes(pi_array, emc_array, meta_data)

        return pi_array, emc_array

    except (ValueError, TypeError) as e:
        raise ExtractionError(f"Failed to parse array values: {e}") from e


def fetch_and_validate_tables(
    url: str,
) -> tuple[PITable, EMCTable, MoldTable]:
    """Fetch and process preservation lookup tables.

    Args:
        url: URL to fetch the JavaScript file containing table data

    Returns:
        Tuple containing:
            - PITable: Preservation Index lookup table
            - EMCTable: Equilibrium Moisture Content lookup table
            - MoldTable: Mold risk lookup table

    Raises:
        requests.RequestException: If table download fails
        ExtractionError: If table data cannot be extracted
        ValidationError: If table data is invalid
        TableMetadataError: If table metadata is invalid
    """
    try:
        # Fetch JavaScript content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        js_content = response.text
        logger.debug(f"Downloaded JavaScript source ({len(js_content)} bytes)")

        # Extract table information and data
        table_info = extract_table_meta_data(js_content)
        logger.debug("Successfully extracted table metadata")

        # Log table dimensions for debugging
        for table_type, info in table_info.items():
            logger.debug(
                f"{table_type.value}: {info.temp_range}x{info.rh_range} elements"
            )

        # Extract and validate raw arrays
        pi_array, emc_array = extract_raw_arrays(js_content, table_info)
        logger.debug("Successfully extracted and validated raw arrays")

        # Initialize lookup tables
        pi_info = table_info[TableType.PI]
        pi_table: PITable = LookupTable(
            np.array(pi_array[: pi_info.size], dtype=np.int16).reshape(
                pi_info.temp_range, pi_info.rh_range
            ),
            pi_info.temp_min,
            pi_info.rh_min,
            BoundaryBehavior.CLAMP,
        )

        mold_info = table_info[TableType.MOLD]
        mold_table: MoldTable = LookupTable(
            np.array(pi_array[mold_info.array_offset :], dtype=np.int16).reshape(
                mold_info.temp_range, mold_info.rh_range
            ),
            mold_info.temp_min,
            mold_info.rh_min,
            BoundaryBehavior.RAISE,
        )

        emc_info = table_info[TableType.EMC]
        emc_table: EMCTable = LookupTable(
            np.array(emc_array, dtype=np.float16).reshape(
                emc_info.temp_range, emc_info.rh_range
            ),
            emc_info.temp_min,
            emc_info.rh_min,
            BoundaryBehavior.CLAMP,
        )

        logger.debug("Successfully created all lookup tables")
        return pi_table, emc_table, mold_table

    except requests.RequestException as e:
        logger.error(f"Failed to download JavaScript source: {e}")
        raise
    except (ExtractionError, ValidationError, TableMetadataError) as e:
        logger.error(f"Failed to process table data: {e}")
        raise
    except Exception as e:
        error_msg = "Unexpected error while processing tables"
        logger.error(f"{error_msg}: {e}")
        raise ExtractionError(error_msg) from e
