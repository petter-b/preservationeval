# Standard library imports
import re

# Types
from typing import Final

# Regular expression patterns for extracting table information
_REGEX_PATTERNS: Final[dict[str, str]] = {
    "pi_array_size": r"""
        # PI table array initialization
        pitable\s*=\s*new\s*Array\s*\(\s*
            (?P<size>\d+)      # Total size including mold risk section
        \s*\)
    """,
    "emc_array_size": r"""
        # EMC table array initialization
        emctable\s*=\s*new\s*Array\s*\(\s*
            (?P<size>\d+)      # EMC lookup table size
        \s*\)
    """,
    "pi_ranges": r"""
    # PI function definition and calculation
    var\s+pi\s*=\s*function\s*\(\s*t\s*,\s*rh\s*\)\s*{
        \s*return\s+pitable\s*\[\s*
            \(\s*
                \(\s*
                    t\s*<\s*(?P<temp_min>-\d+)\s*\?\s*-\d+\s*:\s*  # Temperature minimum
                    t\s*>\s*(?P<temp_max>\d+)\s*\?\s*\d+\s*:\s*     # Temperature max.
                    Math\.round\s*\(\s*t\s*\)\s*
                \)\s*\+\s*
                (?P<temp_offset>\d+)      # Temperature offset
            \)\s*\*\s*
            (?P<rh_size>\d+)\s*\+\s*     # RH range size
            \(\s*
                rh\s*<\s*(?P<rh_min>\d+)\s*\?\s*\d+\s*:\s*         # RH minimum
                rh\s*>\s*(?P<rh_max>\d+)\s*\?\s*\d+\s*:\s*         # RH maximum
                Math\.round\s*\(\s*rh\s*\)\s*
            \)\s*
            (?P<rh_offset>-\s*\d+)       # Negative RH offset
        \]
    """,
    "mold_ranges": r"""
        # Mold risk calculation with bounds checking
        if\s*\(\s*
            t\s*>\s*(?P<temp_max>\d+)\s*\|\|\s*    # Maximum temperature for mold risk
            t\s*<\s*(?P<temp_min>\d+)\s*\|\|\s*    # Minimum temperature for mold risk
            rh\s*<\s*(?P<rh_min>\d+)               # Minimum RH for mold risk
        \s*\)\s*return\s*0\s*;
        \s*return\s+pitable\s*\[\s*
            (?P<offset>\d+)\s*\+\s*                # Offset in pitable for mold data
            \(\s*Math\.round\s*\(\s*t\s*\)\s*-\s*\d+\s*\)\s*\*\s*
            (?P<rh_size>\d+)\s*\+\s*              # RH range size for mold calculation
            Math\.round\s*\(\s*rh\s*\)\s*
            (?P<rh_offset>-\s*\d+)                # RH offset for array indexing
        \s*\]
    """,
    "emc_ranges": r"""
        # EMC calculation with bounds validation
        return\s+emctable\s*\[\s*
            \(\s*
                Math\.max\s*\(\s*
                    (?P<temp_min>-\d+)\s*,\s*      # Temperature minimum bound
                    Math\.min\s*\(\s*
                        (?P<temp_max>\d+)\s*,\s*   # Temperature maximum bound
                        Math\.round\s*\(\s*t\s*\)\s*
                    \)\s*
                \)\s*\+\s*
                (?P<temp_offset>\d+)               # Temperature offset for array index
            \)\s*\*\s*
            (?P<rh_size>\d+)\s*\+\s*              # RH range size for EMC table
            Math\.round\s*\(\s*rh\s*\)\s*         # Rounded RH value for indexing
        \s*\]
    """,
    "pi_data": r"""
        # PI table data array initialization
        pitable\s*=\s*\[\s*
            (?P<values>
                \d+\s*                  # First integer value
                (?:,\s*\d+\s*)*        # Subsequent comma-separated integers
            )
        \s*\]
    """,
    "emc_data": r"""
        # EMC table data array initialization
        emctable\s*=\s*\[\s*
            (?P<values>
                \d*\.?\d+\s*            # First decimal value
                (?:,\s*\d*\.?\d+\s*)*   # Subsequent comma-separated decimals
            )
        \s*\]
    """,
}

# Compile patterns with verbose flag for readability
COMPILED_PATTERNS: dict[str, re.Pattern[str]] = {
    name: re.compile(pattern, re.VERBOSE) for name, pattern in _REGEX_PATTERNS.items()
}
