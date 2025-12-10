# Task Completion Checklist

When completing a task, ensure the following steps are done:

## 1. Code Quality
- [ ] Code follows style conventions (88 char lines, Google docstrings)
- [ ] Type annotations are complete and correct
- [ ] No security vulnerabilities (OWASP top 10)
- [ ] No over-engineering - only necessary changes made

## 2. Format and Lint
```bash
ruff format .           # Format code
ruff check . --fix      # Fix auto-fixable issues
ruff check .            # Verify no remaining issues
```

## 3. Type Checking
```bash
mypy .                  # Must pass with no errors
```

## 4. Testing
```bash
pytest                  # All tests must pass
pytest --cov            # Check coverage if relevant
```

## 5. Pre-commit (Full Check)
```bash
pre-commit run --all-files  # Runs all hooks
```

## 6. Git
- [ ] Meaningful commit messages
- [ ] Changes are properly staged
- [ ] No commits directly to `main` branch (protected)

## Important Notes
- Tests are automatically run with mypy and coverage (`--mypy --cov` in pytest config)
- Pre-commit hooks run automatically on commit (ruff format, ruff check, mypy)
- Excluded paths: `tables.py`, `version.py`, `wip/**`, `build/**`, `dist/**`
