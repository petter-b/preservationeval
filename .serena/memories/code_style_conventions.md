# Code Style Conventions (Extended)

> For design principles and structure limits, see `AGENTS.md`. This memory contains tool-specific details.

## Type Checking (Strict mypy)

- `disallow_untyped_defs` - All functions must have type annotations
- `disallow_incomplete_defs` - Complete type signatures required
- `strict` mode enabled
- `disallow_any_generics` - Explicit generic parameters
- `warn_return_any` - Explicit return types

## Test File Relaxations

Test files (`tests/**/*`) have:

- `D103` ignored - docstrings not required in test functions
- `S101` ignored - `assert` allowed in tests
- `disallow_untyped_decorators = false` in mypy

## Import Order (isort)

1. Standard library
2. Third-party packages
3. First-party (`preservationeval`)
