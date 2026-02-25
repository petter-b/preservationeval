# TODO

## High Priority

- [x] Consistent use of logging
- [x] Install pipeline robustness: retry logic, JS execution timeout,
      value-range validation, atomic file writes
- [x] Security review of PyMiniRacer JS execution
      (HTTPS unavailable; SHA-256 hash pin mitigates MITM)

## Features

- [x] Add hash verification to tables.py
- [ ] Cache dp.js for offline builds
- [ ] Consider merging const and config modules

## Documentation

- [ ] Revise README (describe file/package structure, slim down)
- [ ] Document table generation process
- [ ] Improve docstrings
      (ref: [Understanding Preservation Metrics](https://s3.cad.rit.edu/ipi-assets/publications/understanding_preservation_metrics.pdf))
