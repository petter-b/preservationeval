# TODO

## High Priority
- [ ] Code review
- [ ] Consistent use of logging
- [ ] Consider using secripts/generate_tables() for installation for tables.py.
- [?] Add proper SOURCES.txt handling
- [?] Robustness against errors during installation
- [ ] Security wrt execution of JS code
- [X] Restructuring
  - [X] Move all types into table_types package and rename to types
  - [X] Try to move all of main package up one level.
  - [ ] Consider merging const and config modules.
- [X] Improve test coverage.
- Improve docstrings and update based on https://s3.cad.rit.edu/ipi-assets/publications/understanding_preservation_metrics.pdf

## Features
- [ ] Add hash to tables.py
- [ ] Add caching for dp.js file
- [ ] Add validation of tables.py during installation
- [ ] Move configuration for installation from install.const to pyproject.toml and maybe rename remaining const.py to config.py.

## Documentation
- [ ] Revise README
  - [ ] Describe file / package structure
  - [ ] Make README more slim
- [ ] Document table generation process
