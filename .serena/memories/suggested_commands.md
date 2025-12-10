# Suggested Commands

## Development Setup
```bash
pip install -e ".[dev]"    # Install with all dev dependencies
pre-commit install         # Set up pre-commit hooks
```

## Linting and Formatting
```bash
ruff format .                    # Format code
ruff check .                     # Check for issues
ruff check . --fix               # Apply safe auto-fixes
mypy .                           # Type checking
pre-commit run --all-files       # Run all pre-commit hooks
```

## Testing
```bash
pytest                           # Run all tests (includes mypy + coverage)
pytest -v                        # Verbose output
pytest tests/test_core.py        # Single test file
pytest tests/test_core.py::TestValidatedCases::test_validated_cases  # Single test
pytest -m "unit"                 # Only unit tests
pytest -m "not slow and not validation"  # Skip slow/validation tests
pytest --cov                     # With coverage report
```

### Test Markers
- `@pytest.mark.unit` - Unit tests
- `@pytest.mark.integration` - Integration tests
- `@pytest.mark.validation` - JS validation tests
- `@pytest.mark.slow` - Long-running tests

## Validation Testing (Python vs JavaScript)
Requires Node.js + npm (puppeteer is used for headless JS execution).
```bash
python -m tests.validate_core              # Generate test data, run comparison
pytest tests/test_validation.py            # Run cached validation tests
pytest tests/test_validation.py --force-update  # Regenerate test data
```

## Build
```bash
python -m build                  # Build wheel + sdist
python -m scripts.generate_tables  # Manual table regeneration
```

## System Utilities (Darwin/macOS)
**CRITICAL**: Use `rg` (ripgrep) instead of `grep` and `find`:
```bash
# Search for pattern
rg "pattern"                     # NOT: grep -r "pattern" .

# Find files
rg --files | rg "\.py$"          # NOT: find . -name "*.py"
rg --files -g "*.py"             # Alternative

# Other common utilities
git status/add/commit/push       # Git operations
ls -la                           # List directory contents
```
