# Design: Migrate preservationeval to uv + hatchling

**Date:** 2026-02-23
**Branch:** `feature/simplify-install-pipeline`
**Status:** Approved

## Goal

Replace setuptools + pip with uv + hatchling across local dev, CI, and the build system.
Full modernization: faster installs, deterministic lockfile, modern build backend, clean versioning.

## Hard Constraint: IP Protection

The lookup tables in `tables.py` are derived from dpcalc.org's `dp.js` and **must never be redistributed**.
Table generation happens at install time on the user's machine only.

Enforcement:
- Only sdists are published to PyPI (never wheels)
- sdist explicitly excludes `tables.py`
- Build hook generates `tables.py` only when building a wheel (which happens locally when installing from sdist)
- CI verifies: no `tables.py` in sdist, no `.whl` files in `dist/`

## 1. Build Backend: setuptools → hatchling

### pyproject.toml build-system

```toml
[build-system]
requires = [
    "hatchling",
    "hatch-vcs",
    "numpy>=2.3.2",
    "requests>=2.31.0",
    "mini-racer>=0.12.4",
]
build-backend = "hatchling.build"
```

Remove `setuptools`, `wheel`, and `types-setuptools` from build requires.

### Package layout

```toml
[tool.hatch.build.targets.wheel]
packages = ["src/preservationeval"]

[tool.hatch.build.targets.sdist]
exclude = ["src/preservationeval/tables.py"]
```

### Custom build hook: `hatch_build.py`

```python
"""Custom build hook to generate lookup tables during build."""

import os
import sys
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
    """Generate preservationeval lookup tables at build time."""

    PLUGIN_NAME = "custom"

    def initialize(self, version: str, build_data: dict[str, Any]) -> None:
        """Generate tables.py before building the wheel."""
        # Only generate for wheel builds (not sdist — IP protection)
        if self.target_name != "wheel":
            return

        src_path = os.path.join(self.root, "src")
        sys.path.insert(0, src_path)
        try:
            from preservationeval.install.generate_tables import generate_tables
            generate_tables()
        finally:
            sys.path.remove(src_path)

        # For editable installs, tables.py is already in the source tree
        if version == "editable":
            return

        # For standard builds, inject via force_include
        tables_path = os.path.join(src_path, "preservationeval", "tables.py")
        build_data["force_include"][tables_path] = "preservationeval/tables.py"
```

Register in pyproject.toml:

```toml
[tool.hatch.build.hooks.custom]
# uses hatch_build.py at project root by default
```

### Hook ordering

vcs hook runs first (generates `_version.py`), then custom hook (generates `tables.py`):

```toml
[tool.hatch.build.hooks.vcs]
version-file = "src/preservationeval/_version.py"

[tool.hatch.build.hooks.custom]
```

### Delete

- `setup.py` — replaced entirely by `hatch_build.py` + pyproject.toml

### Cleanup

- Remove `[tool.setuptools.dynamic]` section from pyproject.toml
- Remove `[tool.setuptools.packages.find]` section from pyproject.toml
- Remove `"setup.py"` from `PACKAGE_ROOT_MARKERS` in `install/const.py`
- Remove `[tool.preservationeval]` section if nothing reads it
- Remove `types-setuptools` from `lint` optional dependency (if no longer needed)

## 2. Versioning: hatch-vcs

```toml
[project]
dynamic = ["version"]

[tool.hatch.version]
source = "vcs"
fallback-version = "0.0.0"

[tool.hatch.build.hooks.vcs]
version-file = "src/preservationeval/_version.py"
```

hatch-vcs derives version from git tags (`v1.2.3` → `1.2.3`).
Auto-generates `_version.py` with format:

```python
__version__ = version = '1.2.3'
__version_tuple__ = version_tuple = (1, 2, 3)
```

The existing `__init__.py` imports `version` from `_version.py` — this remains compatible.

`fallback-version` provides safety when git info is unavailable (e.g., building from sdist without `.git`).

## 3. Local Development

### Setup

```bash
uv sync --all-extras      # install all deps + editable package (generates tables.py)
uv run pre-commit install  # install pre-commit hooks
```

### `.python-version`

Pin to `3.13`.
uv auto-downloads the pinned version if not present.

### `uv.lock`

Committed to git.
Deterministic installs across machines.

### Daily workflow

```bash
uv run pytest                           # run tests
uv run ruff format .                    # format
uv run ruff check .                     # lint
uv run ruff check . --fix               # auto-fix
uv run mypy .                           # type check
uv run pre-commit run --all-files       # all hooks
```

### Build (local)

```bash
uv build --sdist                         # build sdist only (IP protection)
uv run python -m scripts.generate_tables # manual table regeneration
```

### Validation

```bash
uv run python -m tests.validate_core                # generate test data, run comparison
uv run pytest tests/test_validation.py               # run cached validation tests
uv run pytest tests/test_validation.py --force-update # regenerate test data
```

## 4. CI/CD Changes

### Test job

```yaml
- uses: astral-sh/setup-uv@v4
  with:
    version: "0.6.x"  # pin for reproducibility

- name: Set up Python ${{ matrix.python-version }}
  run: uv python install ${{ matrix.python-version }}

- name: Install dependencies
  run: uv sync --all-extras --python ${{ matrix.python-version }}

- name: Run pre-commit
  run: uv run pre-commit run --all-files

- name: Run tests
  run: uv run pytest --cov
```

Node.js setup step remains (needed for validation tests).

### Release job

- `uv build --sdist` (sdist only)
- Verify IP protection:
  ```bash
  test $(ls dist/*.whl 2>/dev/null | wc -l) -eq 0
  ! tar -tvf dist/*.tar.gz | grep 'tables\.py'
  ```
- Upload only `dist/*.tar.gz`
- RC builds: use lightweight git tags (hatch-vcs derives version from tags)
- Production builds: tag → hatch-vcs picks it up automatically

### RC versioning with hatch-vcs

The current CI manually writes `_version.py` for RC builds.
With hatch-vcs, use `SETUPTOOLS_SCM_PRETEND_VERSION` environment variable:

```bash
SETUPTOOLS_SCM_PRETEND_VERSION="${BASE_VERSION}rc${RC_NUMBER}" uv build --sdist
```

## 5. Files Changed

| Action | File | Notes |
|--------|------|-------|
| **Delete** | `setup.py` | Replaced by hatch_build.py |
| **Create** | `hatch_build.py` | Custom build hook |
| **Create** | `.python-version` | Pin to 3.13 |
| **Commit** | `uv.lock` | Deterministic lockfile |
| **Rewrite** | `pyproject.toml` | Build-system, hatch config, remove setuptools sections |
| **Rewrite** | `.github/workflows/python-cicd.yml` | pip → uv |
| **Update** | `AGENTS.md` | Dev setup, commands, key files |
| **Update** | `src/preservationeval/install/const.py` | Remove setup.py from root markers |
| **Update** | `.gitignore` | Add `_version.py` (auto-generated) |
| **Remove from git** | `_version.py` | Auto-generated by hatch-vcs |

## 6. Validation Strategy

1. **TDD the build hook** — test that `hatch_build.py` generates valid `tables.py` with expected structure
2. **Full test suite** — all existing unit/integration tests pass (zero regressions)
3. **dpcalc.org validation** — `uv run pytest -m validation` confirms Python matches JS reference
4. **Artifact verification** — sdist excludes `tables.py`, no `.whl` in dist
5. **Clean install test** — build sdist → install from sdist in fresh venv → run tests

## 7. Risk Areas

| Risk | Severity | Mitigation |
|------|----------|------------|
| Build isolation breaks imports in hook | High | `sys.path` manipulation in `hatch_build.py`, test end-to-end |
| `force_include` path mapping wrong | High | Inspect built wheel with `unzip -l`, TDD |
| Editable installs don't generate tables | High | Handle `version == "editable"` in hook |
| Network dependency during build (dpcalc.org down) | Medium | Existing risk, not new. Consider caching dp.js in sdist |
| Two build hooks ordering wrong | Medium | Verify vcs hook runs before custom hook |
| RC versioning with hatch-vcs | Medium | Use `SETUPTOOLS_SCM_PRETEND_VERSION` env var |

## 8. AGENTS.md Updates

- Development Setup: `pip install` → `uv sync --all-extras`
- All commands: prefix with `uv run`
- Build section: `python -m build` → `uv build --sdist`
- Key Files table: replace `setup.py` with `hatch_build.py`
- Architecture section: update install pipeline description
