"""Test module for __version__ import errors."""

import builtins
import importlib
import sys

import pytest


@pytest.mark.unit
@pytest.mark.parametrize(
    "module_path, version_attr",
    [
        ("preservationeval.utils", "__version__"),
        ("preservationeval.types", "__version__"),
        ("preservationeval.install", "__version__"),
    ],
)
def test_import_error_sets_version_unknown(
    monkeypatch: pytest.MonkeyPatch, module_path: str, version_attr: str
) -> None:
    """Test that import errors set the version to 'unknown'."""
    sys.modules.pop(module_path, None)
    sys.modules.pop("preservationeval._version", None)

    real_import = builtins.__import__

    def import_side_effect(name: str, *args: object, **kwargs: object) -> object:
        if name == "preservationeval._version":
            raise ImportError
        return real_import(name, *args, **kwargs)  # type: ignore

    monkeypatch.setattr(builtins, "__import__", import_side_effect)
    module = importlib.import_module(module_path)
    importlib.reload(module)
    assert getattr(module, version_attr) == "unknown"
