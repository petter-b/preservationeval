"""Table installation package for preservationeval.

This package handles the generation of lookup tables during package installation.
It downloads source data from IPI's Dew Point Calculator, parses the JavaScript
code, and generates Python lookup tables for:
- Preservation Index (PI)
- Equilibrium Moisture Content (EMC)
- Mold Risk

Note:
    While this package is primarily used during installation, it remains
    available for table regeneration if needed.
"""

from importlib.metadata import version

from .generate_tables import generate_tables

__all__ = ["generate_tables", "__version__"]

__version__ = version("preservationeval")
