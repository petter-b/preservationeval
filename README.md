# preservationeval
A Python module to mimic the calculations done by the Dew Point Calculator from Image Permanence Institute (IPI).

## Details
The preservation evaluation code was taken from the [Dew point calulator](http://www.dpcalc.org) created by the Image Permanence Institute. For details of the calculations see:
 - http://www.dpcalc.org/howtouse_step2.php
 - http://www.dpcalc.org/dp.js


## Installation

```bash
pip install preservationeval
´´´

## Usage
```python
from preservationeval import pi, emc, mold

# Calculate Preservation Index
pi_value = pi(20, 50)  # temperature=20°C, RH=50%

# Calculate EMC
emc_value = emc(20, 50)

# Calculate Mold Risk
mold_risk = mold(20, 50)
```

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/petter-b/preservationeval
cd preservationeval

# Install development dependencies
pip install -e ".[dev]"
```

## Testing

### Validation Testing
The package includes a validation framework that compares our Python implementation
against the original JavaScript implementation from dpcalc.org.

#### Requirements
- Node.js and npm must be installed ([download](https://nodejs.org/))
- Python test dependencies: `pip install -e ".[test]"`

#### Test Data Setup
The test framework automatically:
- Creates the `tests/data` directory (git-ignored)
- Downloads the JavaScript reference implementation
- Generates and saves test cases
- Caches results for future test runs

You can manually trigger this setup:
```bash
# Download JavaScript reference implementation
# This happens automatically when running tests, or manually:
python -m tests.validate_core

# Run all tests
pytest

# Run only validation tests
pytest tests/test_validation.py

# Run with verbose output
pytest -v tests/test_validation.py

# Generate new test cases (ignore cached)
pytest tests/test_validation.py --force-update
```

## Development Notes

This project was developed with assistance from Claude AI (Anthropic) and to some extent GitHub Copilot. All code has been validated and tested for accuracy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.