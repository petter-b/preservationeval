"""
Module for exporting lookup tables for preservation calculations.

This module provides functions to export lookup tables for preservation calculations
as Python modules. The tables include Preservation Index (PI), Mold Risk Factor (MRF),
and Equilibrium Moisture Content (EMC) tables. The tables are exported as Python
modules with the following variables:

- `PI_DATA`: NumPy array representing the PI table data.
- `EMC_DATA`: NumPy array representing the EMC table data.
- `MOLD_DATA`: NumPy array representing the Mold table data.
- `PI_TEMP_MIN`: Minimum temperature value for the PI table.
- `PI_RH_MIN`: Minimum relative humidity value for the PI table.
- `EMC_TEMP_MIN`: Minimum temperature value for the EMC table.
- `EMC_RH_MIN`: Minimum relative humidity value for the EMC table.
- `MOLD_TEMP_MIN`: Minimum temperature value for the Mold table.
- `MOLD_RH_MIN`: Minimum relative humidity value for the Mold table.
"""

from pathlib import Path
from textwrap import dedent

from preservationeval.lookup import EMCTable, MoldTable, PITable

NUM_EMC_DECIMALS: int = 1


def generate_tables_module(
    pi_table: PITable,
    emc_table: EMCTable,
    mold_table: MoldTable,
    module_name: str = "lookup_tables",
    output_path: Path | None = None,
) -> None:
    """
    Generate a Python module for the lookup tables.

    Args:
        pi_table: LookupTable for Preservation Index (PI)
        emc_table: LookupTable for Equilibrium Moisture Content (EMC)
        mold_table: LookupTable for Mold Risk
        module_name: Name of the module to generate
        output_path: Directory to write the module to (default: current working dir.)
    """
    # Round EMC data to 2 decimal places (keeping as floats)
    emc_data_rounded = [
        [round(float(x), NUM_EMC_DECIMALS) for x in row]
        for row in emc_table.data.tolist()
    ]

    code = dedent(
        f'''
        """Generated lookup tables for preservation calculations.

        This module is auto-generated during package installation.
        """
        from typing import Final

        import numpy as np

        from preservationeval.lookup import (
            BoundaryBehavior,
            EMCTable,
            LookupTable,
            MoldTable,
            PITable,
        )

        # ------------------------------------------------------------------------------
        # ---------------------->  DO NOT EDIT MANUALLY BELOW THIS <--------------------
        # ------------------------------------------------------------------------------

        # PI table data ({pi_table.data.shape})
        pi_table: Final[PITable] = LookupTable(
            np.array({repr(pi_table.data.tolist())}, dtype=np.int16),  # noqa: E501
            {pi_table.temp_min},
            {pi_table.rh_min},
            BoundaryBehavior.CLAMP
        )

        # Mold table data ({mold_table.data.shape})
        mold_table: Final[MoldTable] = LookupTable(
            np.array({repr(mold_table.data.tolist())}, dtype=np.int16),  # noqa: E501
            {mold_table.temp_min},
            {mold_table.rh_min},
            BoundaryBehavior.RAISE
        )

        # EMC table data ({emc_table.data.shape})
        emc_table: Final[EMCTable] = LookupTable(
            np.array({repr(emc_data_rounded)}, dtype=np.float16),  # noqa: E501
            {emc_table.temp_min},
            {emc_table.rh_min},
            BoundaryBehavior.CLAMP
        )

        _INITIALIZED: bool = True
        '''
    )

    # Write to file
    if output_path is None:
        output_path = Path.cwd()
    output_path.mkdir(parents=True, exist_ok=True)
    output_file = output_path / f"{module_name}.py"
    try:
        with output_file.open("w", encoding="utf-8") as f:
            f.write(code)
    except OSError as e:
        raise OSError(f"Error writing to file {output_file!s}: {e.strerror}") from e