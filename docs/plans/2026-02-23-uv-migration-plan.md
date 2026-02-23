# uv + hatchling Migration Implementation Plan

> **For Claude:** REQUIRED SUB-SKILL: Use superpowers:executing-plans to implement this plan task-by-task.

**Goal:** Replace setuptools + pip with uv + hatchling across local dev, CI, and the build system.

**Architecture:** Hatchling replaces setuptools as PEP 517 build backend. A custom `hatch_build.py` hook generates `tables.py` at wheel-build time (never in sdist). hatch-vcs replaces custom git-tag version logic. uv replaces pip for all install/run/sync operations. Only sdists are published to PyPI — tables are never redistributed.

**Tech Stack:** uv, hatchling, hatch-vcs, hatch custom build hooks

**Design doc:** `docs/plans/2026-02-23-uv-migration-design.md`

---

### Task 1: Bootstrap uv project files

**Files:**
- Create: `.python-version`
- Commit: `uv.lock` (already exists as untracked)

**Step 1: Create `.python-version`**

Create `.python-version` with content:
```
3.13
```

**Step 2: Verify uv recognizes the project**

Run: `uv python list --only-installed`
Expected: Python 3.13 is listed.

Run: `uv sync --dry-run`
Expected: uv reads `pyproject.toml` and reports what it would install (may fail at this point since we haven't migrated the build backend yet — that's OK, we just want to confirm uv sees the project).

**Step 3: Commit**

```bash
git add .python-version uv.lock
git commit -m "chore: add .python-version and uv.lock for uv project management"
```

---

### Task 2: Migrate pyproject.toml build-system to hatchling

**Files:**
- Modify: `pyproject.toml` (lines 1-68 primarily)

**Step 1: Replace `[build-system]` section**

Replace lines 52-61:
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

**Step 2: Replace `dynamic` and add hatch version config**

Change line 3 from `dynamic = ["version"]` — keep this as-is (already correct).

After the `[project.optional-dependencies]` section, add:

```toml
[tool.hatch.version]
source = "vcs"
fallback-version = "0.0.0"

[tool.hatch.build.targets.wheel]
packages = ["src/preservationeval"]

[tool.hatch.build.targets.sdist]
exclude = ["src/preservationeval/tables.py"]

[tool.hatch.build.hooks.vcs]
version-file = "src/preservationeval/_version.py"

[tool.hatch.build.hooks.custom]
```

**Step 3: Remove setuptools-specific sections**

Delete these sections entirely:
- `[tool.setuptools.dynamic]` (line 63-64)
- `[tool.setuptools.packages.find]` (line 66-68)
- `[tool.preservationeval]` (lines 70-74) — confirmed unreferenced by any code

**Step 4: Remove `types-setuptools` from lint deps**

In `[project.optional-dependencies]`, remove `"types-setuptools>=69.0.0"` from the `lint` list (line 45).

**Step 5: Verify toml is valid**

Run: `python -c "import tomllib; tomllib.load(open('pyproject.toml', 'rb'))"`
Expected: No error.

**Step 6: Commit**

```bash
git add pyproject.toml
git commit -m "refactor: migrate build-system from setuptools to hatchling"
```

---

### Task 3: Write failing test for build hook

**Files:**
- Create: `tests/install/test_build_hook.py`

**Step 1: Write the failing test**

```python
"""Tests for the hatch custom build hook."""

import os
import sys
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

# The hook file lives at project root, not in a package.
# We need to import it directly.
PROJECT_ROOT = Path(__file__).resolve().parents[2]


def _import_hook_module():
    """Import hatch_build.py from project root."""
    hook_path = PROJECT_ROOT / "hatch_build.py"
    if not hook_path.exists():
        pytest.skip("hatch_build.py not yet created")

    import importlib.util

    spec = importlib.util.spec_from_file_location("hatch_build", hook_path)
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
        hook._target_name = "sdist"

        build_data: dict = {"force_include": {}}
        with patch.object(type(hook), "target_name", new_callable=lambda: property(lambda self: "sdist")):
            with patch.object(type(hook), "root", new_callable=lambda: property(lambda self: str(PROJECT_ROOT))):
                hook.initialize("standard", build_data)

        assert build_data["force_include"] == {}

    def test_generates_tables_for_wheel(self, tmp_path: Path) -> None:
        """Hook should call generate_tables for wheel builds."""
        mod = _import_hook_module()
        hook = mod.CustomBuildHook.__new__(mod.CustomBuildHook)

        build_data: dict = {"force_include": {}}
        src_path = str(PROJECT_ROOT / "src")
        tables_path = os.path.join(src_path, "preservationeval", "tables.py")

        with (
            patch.object(type(hook), "target_name", new_callable=lambda: property(lambda self: "wheel")),
            patch.object(type(hook), "root", new_callable=lambda: property(lambda self: str(PROJECT_ROOT))),
            patch("preservationeval.install.generate_tables.generate_tables") as mock_gen,
        ):
            hook.initialize("standard", build_data)

        mock_gen.assert_called_once()
        assert tables_path in build_data["force_include"]
        assert build_data["force_include"][tables_path] == "preservationeval/tables.py"

    def test_editable_does_not_force_include(self) -> None:
        """Editable installs should generate tables but not use force_include."""
        mod = _import_hook_module()
        hook = mod.CustomBuildHook.__new__(mod.CustomBuildHook)

        build_data: dict = {"force_include": {}}

        with (
            patch.object(type(hook), "target_name", new_callable=lambda: property(lambda self: "wheel")),
            patch.object(type(hook), "root", new_callable=lambda: property(lambda self: str(PROJECT_ROOT))),
            patch("preservationeval.install.generate_tables.generate_tables") as mock_gen,
        ):
            hook.initialize("editable", build_data)

        mock_gen.assert_called_once()
        assert build_data["force_include"] == {}
```

**Step 2: Run test to verify it fails**

Run: `uv run pytest tests/install/test_build_hook.py -v`
Expected: Tests skip with "hatch_build.py not yet created".

**Step 3: Commit**

```bash
git add tests/install/test_build_hook.py
git commit -m "test: add failing tests for hatch custom build hook"
```

---

### Task 4: Implement `hatch_build.py`

**Files:**
- Create: `hatch_build.py` (project root)

**Step 1: Write the build hook**

```python
"""Custom build hook to generate lookup tables during build.

This hook runs during wheel builds (not sdist) to download dp.js from
dpcalc.org and generate the tables.py module. This ensures lookup tables
are never redistributed — they are generated on the user's machine at
install time.
"""

import os
import sys
from typing import Any

from hatchling.builders.hooks.plugin.interface import BuildHookInterface


class CustomBuildHook(BuildHookInterface):
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

        src_path = os.path.join(self.root, "src")
        sys.path.insert(0, src_path)
        try:
            from preservationeval.install.generate_tables import (
                generate_tables,
            )

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

**Step 2: Run tests to verify they pass**

Run: `uv run pytest tests/install/test_build_hook.py -v`
Expected: All 3 tests PASS.

**Step 3: Commit**

```bash
git add hatch_build.py
git commit -m "feat: add hatch custom build hook for table generation"
```

---

### Task 5: Clean up install/const.py and remove setup.py

**Files:**
- Modify: `src/preservationeval/install/const.py:22-25`
- Delete: `setup.py`

**Step 1: Remove `"setup.py"` from PACKAGE_ROOT_MARKERS**

In `src/preservationeval/install/const.py`, change:
```python
PACKAGE_ROOT_MARKERS: Final[tuple[str, ...]] = (
    "pyproject.toml",
    "setup.py",
)  # Files that indicate package root
```
to:
```python
PACKAGE_ROOT_MARKERS: Final[tuple[str, ...]] = (
    "pyproject.toml",
)  # Files that indicate package root
```

**Step 2: Run existing tests to verify no regression**

Run: `uv run pytest tests/install/ -v`
Expected: All tests pass.

**Step 3: Delete setup.py**

```bash
git rm setup.py
```

**Step 4: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass.

**Step 5: Commit**

```bash
git add src/preservationeval/install/const.py
git commit -m "refactor: remove setup.py and update root markers for hatchling"
```

---

### Task 6: Verify build artifacts (IP protection)

**Files:** None (verification only)

**Step 1: Build sdist**

Run: `uv build --sdist`
Expected: Creates `dist/preservationeval-*.tar.gz`.

**Step 2: Verify tables.py is NOT in sdist**

Run: `tar -tvf dist/*.tar.gz | grep tables.py || echo "PASS: no tables.py in sdist"`
Expected: "PASS: no tables.py in sdist"

**Step 3: Verify no wheel was created**

Run: `ls dist/*.whl 2>/dev/null && echo "FAIL: wheel found" || echo "PASS: no wheel"`
Expected: "PASS: no wheel"

**Step 4: Build wheel (locally) and verify tables.py IS included**

Run: `uv build --wheel`
Expected: Creates `dist/preservationeval-*.whl`.

Run: `unzip -l dist/*.whl | grep tables.py`
Expected: `preservationeval/tables.py` is listed.

**Step 5: Clean up**

Run: `rm -rf dist/`

**Step 6: Commit (no files changed — verification only)**

No commit needed.

---

### Task 7: Test clean install from sdist

**Files:** None (verification only)

**Step 1: Build sdist**

Run: `uv build --sdist`

**Step 2: Install from sdist in a temporary venv**

```bash
TMPDIR=$(mktemp -d)
uv venv "$TMPDIR/.venv"
uv pip install --python "$TMPDIR/.venv/bin/python" "dist/preservationeval-*.tar.gz[test]"
```

**Step 3: Run tests against installed package**

```bash
uv run --python "$TMPDIR/.venv/bin/python" pytest tests/ -v -m "not validation and not slow"
```

Expected: All unit and integration tests pass.

**Step 4: Clean up**

```bash
rm -rf "$TMPDIR" dist/
```

---

### Task 8: Update CI workflow

**Files:**
- Modify: `.github/workflows/python-cicd.yml`

**Step 1: Update test job**

Replace the test job steps (lines 30-74) with:

```yaml
    steps:
    - uses: actions/checkout@93cb6efe18208431cddfb8368fd83d5badbf9bfd # v5
      with:
        fetch-depth: 0
        fetch-tags: true

    - name: Set up uv
      uses: astral-sh/setup-uv@v4

    - name: Set up Python ${{ matrix.python-version }}
      run: uv python install ${{ matrix.python-version }}

    - name: Set up Node.js
      uses: actions/setup-node@49933ea5288caeca8642d1e84afbd3f7d6820020 # v4
      with:
        node-version: '22'

    - name: Install package and dependencies
      run: uv sync --all-extras --python ${{ matrix.python-version }}

    - name: Cache pre-commit hooks
      uses: actions/cache@0057852bfaa89a56745cba8c7296529d2fc39830 # v4
      with:
        path: ~/.cache/pre-commit
        key: pre-commit-${{ hashFiles('.pre-commit-config.yaml') }}

    - name: Run pre-commit
      env:
        SKIP: no-commit-to-branch
      run: uv run pre-commit run --all-files

    - name: Run tests
      run: uv run pytest --cov

    - name: Upload coverage reports to Codecov
      uses: codecov/codecov-action@5a1091511ad55cbe89839c7260b706298ca349f7 # v5
      env:
        CODECOV_TOKEN: ${{ secrets.CODECOV_TOKEN }}
```

**Step 2: Update release job — install deps**

Replace lines 113-118 (install build dependencies):
```yaml
      - name: Set up uv
        uses: astral-sh/setup-uv@v4

      - name: Set up Python
        run: uv python install 3.13

      - name: Install build dependencies
        run: uv sync --all-extras
```

**Step 3: Update release job — validate step**

Replace the "Validate before release" step. Remove the `setup.py` check (line 137-139) since `setup.py` no longer exists. Keep the git tag version logic.

**Step 4: Update release job — RC build**

Replace the RC build step to use `uv build --sdist` and `SETUPTOOLS_SCM_PRETEND_VERSION`:
```bash
SETUPTOOLS_SCM_PRETEND_VERSION="${RC_VERSION}" uv build --sdist
```

Remove the manual `_version.py` writing. Remove the `twine check` (use `uv publish` or keep `twine` — decide based on preference).

**Step 5: Update release job — production build**

Replace `python -m build` with `uv build --sdist`.
Replace `twine upload dist/*.gz` with the same but ensure only `.tar.gz` is uploaded.
Add IP verification step:
```yaml
      - name: Verify IP protection
        run: |
          test $(ls dist/*.whl 2>/dev/null | wc -l) -eq 0
          ! tar -tvf dist/*.tar.gz | grep 'tables\.py'
```

Replace the test-from-wheel section to use `uv`:
```yaml
      - name: Test built artifact
        run: |
          TMPDIR=$(mktemp -d)
          uv venv "$TMPDIR/.venv"
          uv pip install --python "$TMPDIR/.venv/bin/python" dist/*.tar.gz
          uv run --python "$TMPDIR/.venv/bin/python" python -c "from preservationeval import pi; print(pi(20, 50))"
          rm -rf "$TMPDIR"
```

**Step 6: Run linter on the workflow**

Run: `uv run pre-commit run check-yaml --all-files`
Expected: PASS.

**Step 7: Commit**

```bash
git add .github/workflows/python-cicd.yml
git commit -m "ci: migrate GitHub Actions from pip to uv"
```

---

### Task 9: Update AGENTS.md

**Files:**
- Modify: `AGENTS.md`

**Step 1: Update Development Setup section (lines 39-45)**

Replace:
```markdown
## Development Setup

\`\`\`bash
pip install -e ".[dev]"
pre-commit install
\`\`\`

Requires Python >=3.11 (tested on 3.11, 3.12, 3.13).
```

With:
```markdown
## Development Setup

\`\`\`bash
uv sync --all-extras             # install all deps + editable package
uv run pre-commit install        # install pre-commit hooks
\`\`\`

Requires Python >=3.11 (tested on 3.11, 3.12, 3.13). Python 3.13 is pinned via `.python-version`.
```

**Step 2: Update Common Commands — Lint and Format section (lines 70-78)**

Prefix all commands with `uv run`:
```markdown
### Lint and Format

\`\`\`bash
uv run ruff format .                    # Format code
uv run ruff check .                     # Check for issues
uv run ruff check . --fix               # Apply safe auto-fixes
uv run mypy .                           # Type checking
uv run pre-commit run --all-files       # Run all pre-commit hooks
\`\`\`
```

**Step 3: Update Common Commands — Testing section (lines 80-90)**

Prefix all commands with `uv run`:
```markdown
### Testing

\`\`\`bash
uv run pytest                           # Run all tests (includes mypy + coverage)
uv run pytest -v                        # Verbose output
uv run pytest tests/test_core.py        # Single test file
uv run pytest tests/test_core.py::TestValidatedCases::test_validated_cases  # Single test
uv run pytest -m "unit"                 # Only unit tests
uv run pytest -m "not slow and not validation"  # Skip slow/validation tests
uv run pytest --cov                     # With coverage report
\`\`\`
```

**Step 4: Update Validation Testing section (lines 92-101)**

Prefix all commands with `uv run`:
```markdown
### Validation Testing (Python vs JavaScript)

Requires Node.js + npm (puppeteer is used for headless JS execution).

\`\`\`bash
uv run python -m tests.validate_core              # Generate test data, run comparison
uv run pytest tests/test_validation.py            # Run cached validation tests
uv run pytest tests/test_validation.py --force-update  # Regenerate test data
\`\`\`
```

**Step 5: Update Build section (lines 103-107)**

Replace:
```markdown
### Build

\`\`\`bash
uv build --sdist                          # Build sdist only (IP protection — never publish wheels)
uv run python -m scripts.generate_tables  # Manual table regeneration
\`\`\`
```

**Step 6: Update Architecture — Build-Time Table Generation section (lines 129-138)**

Update to mention `hatch_build.py`:
```markdown
### Build-Time Table Generation (`src/preservationeval/install/`)

Pipeline: hatch_build.py hook → Download dp.js → execute in V8 (PyMiniRacer) → construct typed LookupTables → emit `tables.py`

- **hatch_build.py** (project root): Hatch custom build hook — triggers table generation for wheel builds only
- **generate_tables.py**: Main entry point for table generation
- **extract.py**: PyMiniRacer-based JavaScript execution and table extraction
- **export.py**: Emit the tables.py module with formatted code
- **paths.py**: Path handling for build process (cache, data directories)
- **const.py**: Build-time constants (URLs, file names, table metadata)
```

**Step 7: Update Key Files table (lines 155-163)**

Replace `setup.py` row with `hatch_build.py`:
```markdown
| File | Purpose |
|------|---------|
| `core_functions.py` | Public API (pi, emc, mold) |
| `types/lookuptable.py` | Generic lookup table implementation |
| `types/exceptions.py` | Domain-specific exception hierarchy |
| `hatch_build.py` | Custom build hook for table generation |
| `install/generate_tables.py` | Build-time table generation entry |
| `tables.py` | Generated lookup tables (88KB, auto-built) |
| `tests/validate_core.py` | JS validation framework |
```

**Step 8: Run pre-commit on AGENTS.md**

Run: `uv run pre-commit run --files AGENTS.md`
Expected: PASS.

**Step 9: Commit**

```bash
git add AGENTS.md
git commit -m "docs: update AGENTS.md for uv + hatchling workflow"
```

---

### Task 10: Full validation

**Files:** None (verification only)

**Step 1: Run full test suite**

Run: `uv run pytest -v`
Expected: All tests pass. Zero regressions.

**Step 2: Run pre-commit**

Run: `uv run pre-commit run --all-files`
Expected: All hooks pass.

**Step 3: Run dpcalc.org validation (if Node.js available)**

Run: `uv run pytest tests/test_validation.py -v`
Expected: Python results match JavaScript reference implementation.

**Step 4: Build and verify artifacts**

```bash
uv build --sdist
! tar -tvf dist/*.tar.gz | grep 'tables\.py'
test $(ls dist/*.whl 2>/dev/null | wc -l) -eq 0
rm -rf dist/
```

Expected: sdist has no tables.py, no wheel was produced.

**Step 5: Log summary**

Report: which tests passed, build artifact verification, any issues found.

---

### Task 11: Update .gitignore and clean up

**Files:**
- Modify: `.gitignore`

**Step 1: Verify `_version.py` is already in .gitignore**

Check `.gitignore` line 10: `src/preservationeval/_version.py` — already present.

**Step 2: Ensure `uv.lock` is NOT in .gitignore**

Verify `uv.lock` does not appear in `.gitignore`. It should be committed.

**Step 3: Commit if any changes**

```bash
git add .gitignore
git commit -m "chore: update .gitignore for uv + hatchling"
```

(Skip if no changes needed.)
