# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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

## [0.3.1] - 2024-XX-XX

### Changed
- Updated README and TODO documentation
- Minor improvements to publish workflow

## [0.3.0] - 2024-XX-XX

### Added
- Automatic publishing workflow triggered on new tags
- Additional test cases for better coverage

### Changed
- Enhanced publish workflow configuration

## [0.2.1] - 2024-XX-XX

### Added
- Automatic packet versioning functionality

### Fixed
- Minor updates to version generation process

## [0.2.0] - 2024-XX-XX

### Added
- Automatic version generation from git tags
- Enhanced versioning workflow

## [0.1.3-beta] - 2024-XX-XX

### Fixed
- Debugging and improvements to publish workflow

## [0.1.2-beta] - 2024-XX-XX

### Fixed
- Further publish workflow debugging

## [0.1.1-beta] - 2024-XX-XX

### Fixed
- Initial publish workflow debugging

## [0.1.0] - 2024-11-23

### Added
- Initial release
- Basic PI, EMC, and Mold risk calculations
- tables.py is generated at install time
- Only sdist is included in PyPI release
