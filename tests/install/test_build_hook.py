"""Tests for the hatch custom build hook."""

import importlib.util
from pathlib import Path
from types import ModuleType
from unittest.mock import patch

import pytest

# The hook file lives at project root, not in a package.
# We need to import it directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _import_hook_module() -> ModuleType:
    """Import hatch_build.py from project root."""
    hook_path = PROJECT_ROOT / "hatch_build.py"
    if not hook_path.exists():
        pytest.skip("hatch_build.py not yet created")

    spec = importlib.util.spec_from_file_location("hatch_build", hook_path)
    assert spec is not None, "Failed to create module spec"
    assert spec.loader is not None, "Module spec has no loader"
    module = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(module)
    return module


@pytest.mark.unit
class TestCustomBuildHook:
    """Test the custom hatch build hook."""

    def test_skips_sdist_builds(self) -> None:
        """Hook should do nothing for sdist builds (IP protection)."""
        mod = _import_hook_module()
        hook = mod.CustomBuildHook.__new__(mod.CustomBuildHook)

        build_data: dict[str, dict[str, str]] = {"force_include": {}}
        with patch.object(
            type(hook),
            "target_name",
            new_callable=lambda: property(lambda self: "sdist"),
        ):
            with patch.object(
                type(hook),
                "root",
                new_callable=lambda: property(lambda self: str(PROJECT_ROOT)),
            ):
                hook.initialize("standard", build_data)

        assert build_data["force_include"] == {}

    def test_generates_tables_for_wheel(self) -> None:
        """Hook should call generate_tables for wheel builds."""
        mod = _import_hook_module()
        hook = mod.CustomBuildHook.__new__(mod.CustomBuildHook)

        build_data: dict[str, dict[str, str]] = {"force_include": {}}
        src_path = str(PROJECT_ROOT / "src")
        tables_path = str(Path(src_path) / "preservationeval" / "tables.py")

        with (
            patch.object(
                type(hook),
                "target_name",
                new_callable=lambda: property(lambda self: "wheel"),
            ),
            patch.object(
                type(hook),
                "root",
                new_callable=lambda: property(lambda self: str(PROJECT_ROOT)),
            ),
            patch(
                "preservationeval.install.generate_tables.generate_tables"
            ) as mock_gen,
        ):
            hook.initialize("standard", build_data)

        mock_gen.assert_called_once()
        assert tables_path in build_data["force_include"]
        assert build_data["force_include"][tables_path] == "preservationeval/tables.py"

    def test_editable_does_not_force_include(self) -> None:
        """Editable installs should generate tables but not force_include."""
        mod = _import_hook_module()
        hook = mod.CustomBuildHook.__new__(mod.CustomBuildHook)

        build_data: dict[str, dict[str, str]] = {"force_include": {}}

        with (
            patch.object(
                type(hook),
                "target_name",
                new_callable=lambda: property(lambda self: "wheel"),
            ),
            patch.object(
                type(hook),
                "root",
                new_callable=lambda: property(lambda self: str(PROJECT_ROOT)),
            ),
            patch(
                "preservationeval.install.generate_tables.generate_tables"
            ) as mock_gen,
        ):
            hook.initialize("editable", build_data)

        mock_gen.assert_called_once()
        assert build_data["force_include"] == {}
