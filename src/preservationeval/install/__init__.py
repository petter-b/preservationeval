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

from .generate_tables import generate_tables

__all__ = ["__version__", "generate_tables"]

try:
    from preservationeval._version import version as __version__
except ImportError:
    __version__ = "unknown"
