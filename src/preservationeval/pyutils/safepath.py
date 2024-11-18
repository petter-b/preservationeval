"""Create a safe, absolute path by joining path components."""

from pathlib import Path


def create_safe_path(
    base_path: str | Path,
    *path_parts: str,
    exist_ok: bool = True,
) -> Path:
    """Create a safe, absolute path by joining path components.

    Args:
        base_path: The root directory path to start from.
        *path_parts: Variable number of path segments to join.
        exist_ok: If True, don't raise error if path exists.

    Returns:
        A resolved Path object representing the full path.

    Raises:
        ValueError: If the resulting path would be outside base_path.
        FileExistsError: If path exists and exist_ok is False.
    """
    base_path = Path(base_path).resolve()
    full_path = base_path.joinpath(*path_parts).resolve()

    # Security check: ensure the path is within base directory
    try:
        full_path.relative_to(base_path)
    except ValueError as e:
        raise ValueError(
            f"Resulting path '{full_path}' is outside base path '{base_path}'"
        ) from e

    if full_path.exists() and not exist_ok:
        raise FileExistsError(f"Path already exists: {full_path}")

    return full_path
