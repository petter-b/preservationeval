"""General purpose Python utilities focused on reusability.

This package provides project-independent utilities that can be used across
different Python projects. It is designed to be extracted into a standalone
package.

Components:
    logging: Structured logging with environment-aware configuration
    safepath: Safe path handling and validation

Package Structure:
    pyutils/
    ├── logging/           - Structured logging facilities
    │   ├── config.py     - Configuration classes
    │   └── structured.py - Logger implementation
    └── safepath.py       - Safe path handling

Design Principles:
    - Project independent
    - Focused on reusability
    - Strict typing
    - Comprehensive testing
"""

# TODO: Figure out if it is possible to NOT hardcode __version__

__version__ = "0.1.0"
__min_python__ = "3.11"
