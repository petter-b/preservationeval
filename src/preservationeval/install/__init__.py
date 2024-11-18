"""Table installation package for preservationeval.

This package is used during installation to generate lookup tables
and is designed to be removed after successful installation.
"""

from .installer import install_tables

__all__ = ["install_tables"]
