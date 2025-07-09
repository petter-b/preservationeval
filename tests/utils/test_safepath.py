"""Test module for preservationeval.utils.safepath."""

from pathlib import Path

import pytest

from preservationeval.utils.safepath import create_safe_path


@pytest.mark.unit
def test_create_safe_path_exists_ok(tmp_path: Path) -> None:
    # Create a temporary directory
    dir_path = tmp_path / "existing_dir"
    dir_path.mkdir()

    # Try to create a safe path with exist_ok=True
    safe_path = create_safe_path(dir_path, exist_ok=True)
    assert safe_path == dir_path


@pytest.mark.unit
def test_create_safe_path_exists_not_ok(tmp_path: Path) -> None:
    # Create a temporary directory
    dir_path = tmp_path / "existing_dir"
    dir_path.mkdir()

    # Try to create a safe path with exist_ok=False
    with pytest.raises(FileExistsError):
        create_safe_path(dir_path, exist_ok=False)


@pytest.mark.unit
def test_create_safe_path_not_exists(tmp_path: Path) -> None:
    # Try to create a safe path that doesn't exist
    safe_path = create_safe_path(tmp_path, "non_existent_dir")
    assert safe_path == tmp_path / "non_existent_dir"
    assert not safe_path.exists()
