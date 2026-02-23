"""Custom build hook to generate lookup tables during build.

This hook runs during wheel builds (not sdist) to download dp.js from
dpcalc.org and generate the tables.py module. This ensures lookup tables
are never redistributed — they are generated on the user's machine at
install time.
"""

import sys
from pathlib import Path
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):  # type: ignore[misc]
    """Generate preservationeval lookup tables at build time."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Generate tables.py before building the wheel.

        Args:
            version: Build version type ("standard" or "editable").
            build_data: Mutable dict for controlling build output.
        """
        # Only generate for wheel builds (not sdist — IP protection)
        if self.target_name != "wheel":
            return

        src_path = str(Path(self.root) / "src")
        sys.path.insert(0, src_path)
        try:
            from preservationeval.install.generate_tables import (  # noqa: PLC0415
                generate_tables,
            )

            generate_tables()
        finally:
            sys.path.remove(src_path)

        # For editable installs, tables.py is already in the source tree
        if version == "editable":
            return

        # For standard builds, inject via force_include
        tables_path = str(Path(src_path) / "preservationeval" / "tables.py")
        build_data["force_include"][tables_path] = "preservationeval/tables.py"
