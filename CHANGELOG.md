# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [Unreleased]

### Fixed
- Replaced broken pepy.tech downloads badge with PyPI monthly downloads
- Deferred `validate_core` import in conftest to fix CI smoke test against installed sdist

## [1.2.0] - 2026-02-26

### Added
- Weekly GitHub Actions monitor for upstream dp.js changes
- SHA-256 integrity verification for dp.js downloads
- dp.js hash provenance embedded in generated `tables.py`
- Hatch custom build hook (`hatch_build.py`) for wheel-time table generation
- Pre-upload metadata validation with `twine check`
- Post-release PyPI install verification with retry and backoff
- DEBUG logging in `eval_functions.py` and `util_functions.py` for tracing rating/conversion results
- `NullHandler` at package root (library best practice, already present)
- Evaluation functions usage example in README
- dp.js monitor badge in README Automation section

### Changed
- CI: automate CHANGELOG `[Unreleased]` stamping during production releases
- Migrated build backend from setuptools to hatchling + hatch-vcs
- Migrated all CI/CD from pip to uv (`astral-sh/setup-uv`, `uv sync`, `uv build`, `uv publish`)
- Standardized logging conventions: library modules use `logging.getLogger(__name__)`, build scripts use `setup_logging` with `Environment.INSTALL`

### Removed
- Removed `setup.py` (replaced by hatchling build backend)
- Removed `BoundaryBehavior.LOG` flag from `LookupTable` (dead code; clamping is normal domain behavior, not a warning)

### Fixed
- CI: add `--wildcards` to `tar` PKG-INFO extraction (required by GNU tar on Ubuntu runners)
- Security: dp.js content is now verified against a pinned SHA-256 hash before V8 execution
- Strengthened array size validation from `<` to `!=` for exact match in table extraction
- Updated outdated docstring in `generate_tables.py`
- Added tests for pitable/emctable size mismatch error paths (100% coverage)
- Corrected CI badge URLs in README (`ci.yml` → `python-cicd.yml`)
- Updated dev setup commands in README from pip to uv
- Fixed "Restults" typo in README
- Removed dead eClimateNotebook link from README
- Updated README Details section to describe current build pipeline (PyMiniRacer, SHA-256 verification)

## [1.1.0] - 2026-02-23

### Changed
- **Simplified install pipeline**: replaced ~1,100 lines of regex parsing with PyMiniRacer (embedded V8) to execute dp.js directly and extract table data (net -700 LOC)
- Removed legacy CI workflows (`ci.yml`, `publish.yml`) in favor of unified `python-cicd.yml`

### Added
- Claude Code GitHub workflow for automated PR review
- Claude as automated PR reviewer for Renovate PRs
- Claude Code configuration and documentation (`CLAUDE.md`, `AGENTS.md`)

### Fixed
- Version validation logic for edge cases
- Renamed `LICENCE` to `LICENSE` for consistency
- PAT-based PR approvals to satisfy branch protection rules
- Relaxed mypy decorator typing for test files

## [1.0.1] - 2025-08-30

### Changed
- Unified CI/CD into single `python-cicd.yml` workflow
- Updated numpy to v2
- Updated Python support to 3.13
- Moved `license-files` to `[project]` section, removing deprecated `[tool.setuptools]` config
- Adopted Renovate `config:best-practices` and added `minimumReleaseAge`

### Added
- Renovate dependency management with pinned dependencies
- Pre-commit auto-update workflow
- CodeQL security analysis (v3)

## [1.0.0] - 2025-07-10

### Added
- First stable release of preservationeval
- Complete Python implementation of dpcalc.org calculations
- Core functions: `pi()`, `emc()`, and `mold()` for preservation metrics
- Comprehensive validation framework comparing against original JavaScript
- Automatic lookup table download and conversion during installation
- Full test coverage with pytest integration
- Type checking with mypy
- Code quality tools (ruff for formatting and linting)
- Pre-commit hooks for code quality assurance
- CI/CD workflows for testing and publishing
- Development container support
- Comprehensive documentation and usage examples

### Changed
- Improved test coverage and validation accuracy
- Updated CI/CD workflows to use latest GitHub runners
- Enhanced development environment setup
- Refined package structure and organization

### Fixed
- Resolved pytest configuration issues
- Fixed trailing whitespace and formatting issues
- Corrected CI workflow errors
- Improved error handling in table generation

## [0.3.1] - 2024-11-25

### Changed
- Updated README and TODO documentation
- Minor improvements to publish workflow

## [0.3.0] - 2024-11-25

### Added
- Automatic publishing workflow triggered on new tags
- Additional test cases for better coverage

### Changed
- Enhanced publish workflow configuration

## [0.2.1] - 2024-11-24

### Added
- Automatic packet versioning functionality

### Fixed
- Minor updates to version generation process

## [0.2.0] - 2024-11-24

### Added
- Automatic version generation from git tags
- Enhanced versioning workflow

## [0.1.3-beta] - 2024-11-23

### Fixed
- Debugging and improvements to publish workflow

## [0.1.2-beta] - 2024-11-23

### Fixed
- Further publish workflow debugging

## [0.1.1-beta] - 2024-11-23

### Fixed
- Initial publish workflow debugging

## [0.1.0] - 2024-11-23

### Added
- Initial release
- Basic PI, EMC, and Mold risk calculations
- tables.py is generated at install time
- Only sdist is included in PyPI release
