# Code Style and Conventions

## General Style
- **Line length**: 88 characters (ruff)
- **Python version**: Target 3.13, support 3.11+
- **Docstrings**: Google convention
- **Quote style**: Double quotes
- **Indent style**: Spaces

## Type Checking (Strict mypy)
- `disallow_untyped_defs` - All functions must have type annotations
- `disallow_incomplete_defs` - Complete type signatures required
- `strict` mode enabled
- `disallow_any_generics` - Explicit generic parameters
- `warn_return_any` - Explicit return types

## Ruff Rules
| Rule Set | Description |
|----------|-------------|
| D | pydocstyle |
| E | pycodestyle |
| F | pyflakes |
| B | flake8-bugbear |
| I | isort |
| N | pep8-naming |
| UP | pyupgrade |
| S | flake8-bandit (security) |
| C4 | flake8-comprehensions |
| PL | Pylint |
| RUF | Ruff-specific |
| PTH | Path handling |
| ERA | Error handling |

## File and Function Limits
- **Files**: Never exceed 500 lines
- **Functions**: Under 50 lines, single responsibility
- **Classes**: Under 100 lines, single concept

## Design Principles
- **KISS**: Keep It Simple, Stupid
- **YAGNI**: You Aren't Gonna Need It
- **Dependency Inversion**: High-level modules depend on abstractions
- **Open/Closed**: Open for extension, closed for modification
- **Single Responsibility**: One clear purpose per unit
- **Fail Fast**: Check errors early, raise exceptions immediately

## Test File Relaxations
Test files (`tests/**/*`) have:
- `D103` ignored - docstrings not required in test functions
- `S101` ignored - `assert` allowed in tests
- `disallow_untyped_decorators = false` in mypy

## Import Order (isort)
1. Standard library
2. Third-party packages
3. First-party (`preservationeval`)
