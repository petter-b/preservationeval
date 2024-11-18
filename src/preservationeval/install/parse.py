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
from typing import Any, Final

import numpy as np
import requests

from preservationeval.pyutils.logging import setup_logging
from preservationeval.table_types import (
    BoundaryBehavior,
    EMCTable,
    LookupTable,
    MoldTable,
    PITable,
)

from .patterns import COMPILED_PATTERNS


# Custom exeptions
class TableMetadataError(Exception):
    """Base exception for TableMetadata errors."""

    ...


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
logger = setup_logging(__name__)


def to_int(value: str) -> int:
    """Convert string to int, removing whitespace in case of negative numbers."""
    return int(value.replace(" ", ""))


def extract_array_sizes(js_content: str) -> tuple[int, int]:
    """Extract the size of the pitable and emctable arrays from JavaScript code.

    The size of the arrays is extracted by matching the pattern defined in the
    'pi_array_size' and 'emc_array_size' regular expressions. The extracted
    data is then returned as a tuple of integers.

    :param js_content: JavaScript source code to be parsed
    :return: A tuple containing the size of the pitable and emctable arrays
    """
    logger.debug("Starting to extract array sizes from JavaScript")
    try:
        # Extract pitable array size
        pi_size_match = COMPILED_PATTERNS["pi_array_size"].search(js_content)
        if pi_size_match:
            groups = pi_size_match.groupdict()
            pi_array_size = int(groups["size"])
            if type(pi_array_size) is int and pi_array_size > 0:
                logger.debug(f"pitable array size: {pi_array_size}")
            else:
                raise ExtractionError("Failed to extract pitable array size")
        else:
            raise ExtractionError(
                "Failed to extract pitable array size, no pi_size_match"
            )

        # Extract emctable array size
        emc_size_match = COMPILED_PATTERNS["emc_array_size"].search(js_content)
        if emc_size_match:
            groups = emc_size_match.groupdict()
            emc_array_size = int(groups["size"])
            if type(emc_array_size) is int and emc_array_size > 0:
                logger.debug(f"emc array size: {emc_array_size}")
            else:
                raise ExtractionError("Failed to extract emc array size")
        else:
            raise ExtractionError("Failed to extract emc array size, no emc_size_match")

    except Exception as e:
        logger.exception(e)
        raise

    return pi_array_size, emc_array_size


def extract_pi_meta_data(js_content: str) -> TableMetaData:
    """Extract PI table ranges from JavaScript code.

    PI ranges are extracted by matching the pattern defined in the
    'pi_ranges' regular expression. The extracted data is then used to
    create a `_TableMetaData` object.

    :param js_content: JavaScript source code to be parsed
    :return: A `_TableMetaData` object containing the PI table ranges
    """
    logger.debug("Attempting to match PI ranges pattern")
    try:
        pi_match = COMPILED_PATTERNS["pi_ranges"].search(js_content)
        if pi_match:
            # Extract values from matched groups
            groups = pi_match.groupdict()
            logger.debug(f"Found PI ranges match: {groups}")

            pi_data = TableMetaData(
                temp_min=to_int(groups["temp_min"]),
                _temp_max=to_int(groups["temp_max"]),
                _temp_offset=to_int(groups["temp_offset"]),
                rh_range=int(groups["rh_size"]),
                _rh_min=int(groups["rh_min"]),
                _rh_max=int(groups["rh_max"]),
                _rh_offset=to_int(groups["rh_offset"]),
            )
            logger.debug(f"Extracted PI meta data: {pi_data}")
        else:
            # Raise error if no match is found
            raise ExtractionError("Failed to extract PI meta data, no pi_match")
    except Exception as e:
        logger.exception(e)
        raise

    return pi_data


def extract_emc_meta_data(js_content: str) -> TableMetaData:
    """Extract EMC table ranges from JavaScript code.

    EMC ranges are extracted by matching the pattern defined in the
    'emc_ranges' regular expression. The extracted data is then used to
    create a `_TableMetaData` object.

    :param js_content: JavaScript source code to be parsed
    :return: A `_TableMetaData` object containing the EMC table ranges
    """
    logger.debug("Attempting to match EMC ranges pattern")
    try:
        emc_match = COMPILED_PATTERNS["emc_ranges"].search(js_content)
        if emc_match:
            # Extract values from matched groups
            groups = emc_match.groupdict()
            logger.debug(f"Found EMC ranges match: {groups}")

            emc_data = TableMetaData(
                temp_min=to_int(groups["temp_min"]),
                _temp_max=to_int(groups["temp_max"]),
                _temp_offset=to_int(groups["temp_offset"]),
                rh_range=int(groups["rh_size"]),
            )
            logger.debug(f"Extracted EMC meta data: {emc_data}")
        else:
            # Raise error if no match is found
            raise ExtractionError("Failed to extract EMC meta data, no emc_match")
    except Exception as e:
        logger.exception(e)
        raise

    return emc_data


def extract_mold_meta_data(js_content: str) -> TableMetaData:
    """Extracts metadata for mold risk factor calculations.

    Args:
        js_content (str): The JavaScript code to extract metadata from.

    Returns:
        # Add return type and description as needed
    """
    logger.debug("Attempting to match Mold ranges pattern")
    try:
        mold_match = COMPILED_PATTERNS["mold_ranges"].search(js_content)
        if mold_match:
            # Extract values from matched groups
            groups = mold_match.groupdict()
            logger.debug(f"Found Mold ranges match: {groups}")

            mold_data = TableMetaData(
                _temp_max=to_int(groups["temp_max"]),
                temp_min=to_int(groups["temp_min"]),
                _rh_min=int(groups["rh_min"]),
                array_offset=int(groups["offset"]),
                rh_range=int(groups["rh_size"]),
                _rh_offset=to_int(groups["rh_offset"]),
            )

            logger.debug(f"Extracted Mold meta data: {mold_data}")
        else:
            # Raise error if no match is found
            raise ExtractionError("Failed to extract Mold meta data, no mold_match")
    except Exception as e:
        logger.exception(e)
        raise

    return mold_data


def cross_check_meta_data(
    meta_data: dict[TableType, TableMetaData], pi_array_size: int, emc_array_size: int
) -> None:
    """Validate table metadata against array sizes.

    The following checks are performed:
    - PI table size + Mold table size == pi_array_size
    - PI table size == Mold table array offset
    - EMC table size == emc_array_size
    """
    try:
        # - PI temp_size * rh_size + MOLD temp_size * rh_size == pi_array_size

        if (
            meta_data[TableType.PI].size + meta_data[TableType.MOLD].size
            != pi_array_size
        ):
            raise ValidationError("PI and Mold table sizes mismatch with pi_array_size")

        # - PI temp_size * rh_size == MOLD array_offset
        if meta_data[TableType.PI].size != meta_data[TableType.MOLD].array_offset:
            raise ValidationError("PI table size mismatch with MOLD array offset")

        # - EMC temp_size * rh_size == emc_array_size
        if meta_data[TableType.EMC].size != emc_array_size:
            raise ValidationError("EMC table size mismatch with emc_array_size")
    except Exception as e:
        logger.exception(e)
        raise


def extract_table_meta_data(js_content: str) -> dict[TableType, TableMetaData]:
    """Extracts table metadata from the given JavaScript source code.

    The function extracts the PI, EMC, and Mold table metadata, and stores them
    in a dictionary. The dictionary is then returned.

    :param js_content: The JavaScript source code to extract metadata from
    :return: A dictionary containing the extracted table metadata
    """
    logger.debug("Starting to extract table ranges from JavaScript")
    meta_data = {}

    try:
        # Extract PI and EMC array sizes for validation purposes
        pi_array_size, emc_array_size = extract_array_sizes(js_content)

        # Extract PI ranges
        meta_data[TableType.PI] = extract_pi_meta_data(js_content)

        # Extract EMC ranges
        meta_data[TableType.EMC] = extract_emc_meta_data(js_content)

        # Extract Mold ranges
        meta_data[TableType.MOLD] = extract_mold_meta_data(js_content)

        # Cross-check extracted meta data
        # TODO: Add function to validate extracted data

    except Exception as e:
        # Handle exceptions and log them
        logger.exception(e)
        raise e

    return meta_data


def extract_raw_arrays(
    js_content: str, meta_data: dict[TableType, TableMetaData]
) -> tuple[array[Any], array[Any]]:
    """Extract raw arrays from JavaScript content.

    Returns:
        Tuple of (pi_array, emc_array) as array.array objects
    """
    # Extract PI data
    pi_match = COMPILED_PATTERNS["pi_data"].search(js_content)
    if not pi_match:
        raise ExtractionError("Could not find PI table data in JavaScript")
    pi_values = [int(x.strip()) for x in pi_match.group(1).split(",")]
    pi_array = array("i", pi_values)  # 'i' for signed int
    logger.info(f"Extracted {len(pi_array)} PI values")

    # Extract EMC data
    emc_match = COMPILED_PATTERNS["emc_data"].search(js_content)
    if not emc_match:
        raise ExtractionError("Could not find EMC table data in JavaScript")
    emc_values = [float(x.strip()) for x in emc_match.group(1).split(",")]
    emc_array = array("d", emc_values)  # 'd' for double
    logger.info(f"Extracted {len(emc_array)} EMC values")

    # Validate array sizes
    pi_array_size = meta_data[TableType.PI].size + meta_data[TableType.MOLD].size
    if pi_array_size != len(pi_array):
        raise ValidationError(
            f"PI array size mismatch: {pi_array_size} != {len(pi_array)}"
        )
    emc_array_size = meta_data[TableType.EMC].size
    if emc_array_size != len(emc_array):
        raise ValidationError(
            f"EMC array size mismatch: {emc_array_size} != {len(emc_array)}"
        )

    return pi_array, emc_array


def fetch_and_validate_tables(
    url: str,
) -> tuple[PITable, EMCTable, MoldTable]:
    """Fetch and process all tables.

    Args:
        url: URL to fetch the JavaScript file containing table data

    Returns:
        Tuple of (pi_table, emc_table, mold_table) as ShiftedArrays

    Raises:
        requests.RequestException: If table download fails
        ValueError: If table data is invalid or missing
    """
    try:
        # Fetch JavaScript content
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        js_content = response.text
        logger.debug(f"Content length: {len(js_content)} characters")

        # Extract table information and data
        table_info = extract_table_meta_data(js_content)
        logger.debug(f"Extracted table info: {table_info}")

        # Log table dimensions
        for table_type, info in table_info.items():
            logger.debug(
                f"{table_type.value} dimensions:" f"{info.temp_range}x{info.rh_range}"
            )

        # Extract raw arrays
        pi_array, emc_array = extract_raw_arrays(js_content, table_info)

        # Initialize ShiftedArrays
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

        return pi_table, emc_table, mold_table

    except requests.RequestException as e:
        logger.error(f"Failed to download tables: {e}")
        raise
    except KeyError as e:
        logger.error(f"Missing table information for {e}")
        raise
    except Exception as e:
        logger.error(f"Unexpected error while processing tables: {e}")
        raise
