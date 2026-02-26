# README Accuracy Pass — Implementation Plan

**Goal:** Update README.md to reflect the current state of the project after uv migration and pipeline hardening.

**Architecture:** Nine targeted edits to a single file (`README.md`), grouped into three commits by theme: fixes, content updates, new content.

**Tech Stack:** Markdown only. No code changes.

**Design doc:** `docs/plans/2026-02-25-readme-accuracy-design.md`

---

### Task 1: Fix CI badges, typo, and dev setup commands

These are factual corrections — broken badges, wrong commands, typo.

**Files:**
- Modify: `README.md`

**Step 1: Fix top CI badge (line 5)**

Replace `ci.yml` with `python-cicd.yml` in both the shield URL and the link target:

```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/python-cicd.yml?style=flat&label=CI&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/python-cicd.yml)
```

**Step 2: Fix Testing section CI badge (line 91)**

Same replacement — `ci.yml` → `python-cicd.yml`:

```markdown
[![CI](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/python-cicd.yml?style=flat&label=ci&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/python-cicd.yml)
```

**Step 3: Fix typo (line 41)**

```markdown
### Interpreting Results
```

**Step 4: Update dev setup command (line 62-63)**

Replace:
```markdown
# Install development dependencies
pip install -e ".[dev]"
```

With:
```markdown
# Install development dependencies
uv sync --extra dev
```

**Step 5: Update test deps command (line 103)**

Replace:
```markdown
- Python test dependencies: `pip install -e ".[test]"`
```

With:
```markdown
- Python test dependencies: `uv sync --extra test`
```

**Step 6: Verify badge URLs resolve**

Run:
```bash
curl -sI -o /dev/null -w "%{http_code}" "https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/python-cicd.yml"
```

Expected: `200` or `302` (shields.io redirect is normal).

**Step 7: Commit**

```bash
git add README.md
git commit -m "fix(docs): correct CI badges, dev commands, and typo in README"
```

---

### Task 2: Update stale content

Remove dead link and rewrite the vague Details section.

**Files:**
- Modify: `README.md`

**Step 1: Remove dead eClimateNotebook link (line 46)**

Remove the line:
```markdown
- https://www.eclimatenotebook.com/fundamentals_nl.php
```

Keep the other two links. The section becomes:

```markdown
### Interpreting Results

For details of how to use, see:

- http://www.dpcalc.org/howtouse_step2.php
- https://s3.cad.rit.edu/ipi-assets/publications/understanding_preservation_metrics.pdf
```

**Step 2: Rewrite Details section (line 11-13)**

Replace the current Details section with:

```markdown
## Details

This project is a Python implementation of the [Dew Point Calculator](http://www.dpcalc.org) created by the Image Permanence Institute.
The original lookup tables from their [published JavaScript](http://www.dpcalc.org/dp.js) are not redistributed.
Instead, during installation, `dp.js` is downloaded, its integrity is verified via a pinned SHA-256 hash, and the table data is extracted by executing the JavaScript in an embedded V8 engine ([PyMiniRacer](https://github.com/nicolo-ribaudo/pymi-racer)) and converted into a Python module.
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): update Details section and remove dead link"
```

---

### Task 3: Add new content — eval functions and dp.js monitor badge

**Files:**
- Modify: `README.md`

**Step 1: Add evaluation functions example after Basic Examples (after line 39)**

Insert a new subsection between the closing `` ``` `` of Basic Examples and `### Interpreting Results`:

```markdown
### Evaluating Conditions

The package also provides functions to rate environmental conditions:

```python
from preservationeval import (
    pi, mold, rate_natural_aging, rate_mold_growth, EnvironmentalRating
)

# Rate preservation conditions (returns GOOD, OK, or RISK)
aging_risk = rate_natural_aging(pi(20, 50))
print(f"Natural aging: {aging_risk}")  # EnvironmentalRating.GOOD

mold_risk = rate_mold_growth(mold(20, 50))
print(f"Mold risk: {mold_risk}")  # EnvironmentalRating.GOOD
```

**Step 2: Add dp.js monitor badge to Automation section (after line 144)**

Insert after the Renovate badge line:

```markdown
[![dp.js Monitor](https://img.shields.io/github/actions/workflow/status/petter-b/preservationeval/dpjs-monitor.yml?style=flat&label=dp.js%20monitor&logo=github-actions&logoColor=white)](https://github.com/petter-b/preservationeval/actions/workflows/dpjs-monitor.yml)
```

**Step 3: Commit**

```bash
git add README.md
git commit -m "docs(readme): add eval functions example and dp.js monitor badge"
```

---

### Task 4: Update CHANGELOG and final review

**Files:**
- Modify: `CHANGELOG.md`
- Review: `README.md`

**Step 1: Add changelog entry under `[Unreleased]`**

Under `### Fixed` (or create the section if needed):

```markdown
### Fixed
- Corrected CI badge URLs (`ci.yml` → `python-cicd.yml`)
- Updated dev setup commands from pip to uv
- Fixed "Restults" typo
- Removed dead eClimateNotebook link
- Updated Details section to describe current build pipeline (PyMiniRacer, SHA-256 verification)

### Added
- Evaluation functions usage example in README
- dp.js monitor badge in README Automation section
```

**Step 2: Read through the full README one more time**

Run: `cat README.md` and scan for any remaining inconsistencies.

**Step 3: Commit**

```bash
git add CHANGELOG.md
git commit -m "docs: add changelog entries for README accuracy pass"
```
