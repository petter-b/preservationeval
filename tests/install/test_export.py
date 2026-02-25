"""Tests for preservationeval.install.export."""

from pathlib import Path
from unittest.mock import patch

import numpy as np
import pytest

from preservationeval.install.export import generate_tables_module
from preservationeval.types import (
    BoundaryBehavior,
    EMCTable,
    LookupTable,
    MoldTable,
    PITable,
)


@pytest.fixture
def dummy_tables() -> tuple[PITable, EMCTable, MoldTable]:
    """Create minimal valid tables for testing export."""
    pi: PITable = LookupTable(
        np.array([[45]], dtype=np.int16), -23, 6, BoundaryBehavior.CLAMP
    )
    emc: EMCTable = LookupTable(
        np.array([[5.5]], dtype=np.float16), -20, 0, BoundaryBehavior.CLAMP
    )
    mold: MoldTable = LookupTable(
        np.array([[7]], dtype=np.int16), 2, 65, BoundaryBehavior.RAISE
    )
    return pi, emc, mold


@pytest.mark.unit
class TestAtomicWrite:
    """Test that table export uses atomic file writes."""

    def test_creates_output_file(
        self, tmp_path: Path, dummy_tables: tuple[PITable, EMCTable, MoldTable]
    ) -> None:
        """generate_tables_module should create the output file."""
        pi, emc, mold = dummy_tables
        generate_tables_module(
            pi, emc, mold, module_name="tables", output_path=tmp_path
        )
        assert (tmp_path / "tables.py").exists()

    def test_output_contains_initialized_flag(
        self, tmp_path: Path, dummy_tables: tuple[PITable, EMCTable, MoldTable]
    ) -> None:
        """Generated module should contain _INITIALIZED = True."""
        pi, emc, mold = dummy_tables
        generate_tables_module(
            pi, emc, mold, module_name="tables", output_path=tmp_path
        )
        content = (tmp_path / "tables.py").read_text()
        assert "_INITIALIZED: bool = True" in content

    def test_no_temp_files_left_on_success(
        self, tmp_path: Path, dummy_tables: tuple[PITable, EMCTable, MoldTable]
    ) -> None:
        """No temporary files should remain after successful write."""
        pi, emc, mold = dummy_tables
        generate_tables_module(
            pi, emc, mold, module_name="tables", output_path=tmp_path
        )
        tmp_files = list(tmp_path.glob(".tables_*"))
        assert tmp_files == []

    def test_original_preserved_on_write_failure(
        self, tmp_path: Path, dummy_tables: tuple[PITable, EMCTable, MoldTable]
    ) -> None:
        """Original file should be preserved if write fails."""
        pi, emc, mold = dummy_tables
        output_file = tmp_path / "tables.py"
        output_file.write_text("original content")

        with (
            patch(
                "preservationeval.install.export.os.fdopen",
                side_effect=OSError("disk full"),
            ),
            pytest.raises(OSError),
        ):
            generate_tables_module(
                pi, emc, mold, module_name="tables", output_path=tmp_path
            )

        assert output_file.read_text() == "original content"

    def test_no_temp_files_left_on_failure(
        self, tmp_path: Path, dummy_tables: tuple[PITable, EMCTable, MoldTable]
    ) -> None:
        """No temporary files should remain after failed write."""
        pi, emc, mold = dummy_tables

        with (
            patch(
                "preservationeval.install.export.os.fdopen",
                side_effect=OSError("disk full"),
            ),
            pytest.raises(OSError),
        ):
            generate_tables_module(
                pi, emc, mold, module_name="tables", output_path=tmp_path
            )

        tmp_files = list(tmp_path.glob(".tables_*"))
        assert tmp_files == []

    def test_uses_path_replace_for_atomicity(
        self, tmp_path: Path, dummy_tables: tuple[PITable, EMCTable, MoldTable]
    ) -> None:
        """Should use Path.replace() for atomic rename."""
        pi, emc, mold = dummy_tables
        replace_calls: list[Path] = []
        original_replace = Path.replace

        def tracking_replace(self: Path, target: Path) -> Path:
            replace_calls.append(target)
            return original_replace(self, target)

        with patch.object(Path, "replace", tracking_replace):
            generate_tables_module(
                pi, emc, mold, module_name="tables", output_path=tmp_path
            )

        assert len(replace_calls) == 1
        assert replace_calls[0] == tmp_path / "tables.py"
