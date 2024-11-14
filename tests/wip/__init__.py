"""# Interactive validation
from tests.validate_core import ValidationTest

# Check current implementation
validation = ValidationTest()
differences = validation.run_tests()

# If differences are found:
for func, diffs in differences.items():
    if diffs:
        print(f"\nDifferences in {func}:")
        for diff in diffs[:5]:  # Show first 5
            print(f"  T={diff['temp']}°C, RH={diff['rh']}%")
            print(f"    JS: {diff['js_value']}")
            print(f"    PY: {diff['py_value']}")


# .github/workflows/test.yml
name: Test

on: [push, pull_request]

jobs:
  test:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v4
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: "3.11"
    - name: Install dependencies
      run: |
        python -m pip install -e ".[dev]"
    - name: Run tests
      run: |
        pytest tests/test_validation.py -v

"""
