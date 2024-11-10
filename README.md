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

### Testing
TBD

## Development Notes

This project was developed with assistance from Claude AI (Anthropic) and to some extent GitHub Copilot. All code has been validated and tested for accuracy.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.