# Running Installation Tests
The tests in 	est_install_in_fresh_environment.py verify that the package dependencies are correctly specified.
## Important: These tests MUST run serially
These tests create virtual environments and install packages, which can cause issues when run in parallel.
## How to run these tests:
`ash
# Run all installation tests (serially)
pytest tests/test_install_in_fresh_environment.py -n0 -v
# Run a specific test
pytest tests/test_install_in_fresh_environment.py::test_core_requirements -n0 -v
# Run with increased timeout
pytest tests/test_install_in_fresh_environment.py -n0 -v --timeout=600
`
## Why -n0?
The -n0 flag disables pytest-xdist parallel execution. Without it, pytest will try to run these tests in parallel, which causes:
- Worker crashes
- Timeout errors
- KeyError exceptions in pytest-xdist scheduler
## What was fixed:
1. Added @pytest.mark.slow to all tests
2. Improved timeout handling in
un_command() to catch subprocess.TimeoutExpired
3. Updated docstring to emphasize serial execution requirement
4. Changed __main__ block to use -n0 by default
