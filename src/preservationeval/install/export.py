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

from preservationeval.types import LookupTable


def generate_tables_module(
    pi_table: LookupTable,
    emc_table: LookupTable,
    mold_table: LookupTable,
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
    code = dedent(
        f'''
        """Generated lookup tables for preservation calculations.

        This module is auto-generated during package installation.
        Do not edit manually.
        """
        import numpy as np
        from preservationeval.types import LookupTable, BoundaryBehavior

        # PI table data ({pi_table.data.shape})
        PI_DATA = {repr(pi_table.data.tolist())}

        # EMC table data ({emc_table.data.shape})
        EMC_DATA = {repr(emc_table.data.tolist())}

        # Mold table data ({mold_table.data.shape})
        MOLD_DATA = {repr(mold_table.data.tolist())}

        # Define LookupTables
        pi_table: Final[LookupTable] = LookupTable(
            np.array(PI_DATA, dtype=np.int16),
            {pi_table.temp_min},
            {pi_table.rh_min},
            BoundaryBehavior.CLAMP
        )

        mold_table: Final[LookupTable] = LookupTable(
            np.array(MOLD_DATA, dtype=np.int16),
            {mold_table.temp_min},
            {mold_table.rh_min},
            BoundaryBehavior.RAISE
        )

        emc_table: Final[LookupTable] = LookupTable(
            np.array(EMC_DATA, dtype=np.float16),
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
