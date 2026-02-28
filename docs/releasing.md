# Releasing

## Prerequisites

- [gh CLI](https://cli.github.com/) installed and authenticated
- Clean working tree (no uncommitted changes)
- On a feature branch with an open PR (not `main`)

## Quick start

```bash
# From your PR branch:
scripts/prep-release.sh patch   # 1.2.0 → 1.2.1
scripts/prep-release.sh minor   # 1.2.0 → 1.3.0
scripts/prep-release.sh major   # 1.2.0 → 2.0.0
```

## What the script does

1. Computes the next version from the latest git tag
2. Validates that `[Unreleased]` in `CHANGELOG.md` has entries
3. Stamps the changelog: inserts `## [X.Y.Z] - YYYY-MM-DD` below `[Unreleased]`
4. Commits the change (`chore: prepare changelog for release X.Y.Z`)
5. Pushes to the current branch
6. Labels the PR with `release-patch`, `release-minor`, or `release-major`

The script is idempotent — if the version is already stamped, it warns and exits cleanly.

## What CI does after labeling

1. Validates the stamped version exists in `CHANGELOG.md`
2. Merges the PR (squash + delete branch)
3. Creates and pushes the `vX.Y.Z` tag
4. Builds the sdist and runs smoke tests
5. Publishes to PyPI
6. Creates a GitHub Release
7. Verifies the package installs from PyPI

## Release candidates

Label a PR with `release-candidate` (or use the workflow dispatch) to publish an RC to TestPyPI.
RC builds do not require changelog stamping.

## Troubleshooting

| Problem | Fix |
|---------|-----|
| `Error: cannot run on 'main'` | Switch to a feature branch first |
| `Error: working tree is not clean` | Commit or stash your changes |
| `[Unreleased] section has no entries` | Add changelog entries before releasing |
| CI fails with "missing stamped section" | Run `scripts/prep-release.sh <type>` and push |
