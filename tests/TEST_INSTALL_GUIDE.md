# Quick Test Guide for test_install_in_fresh_environment.py
## Running the Tests
### Run all installation tests (takes 5-10 minutes):
```bash
pytest tests/test_install_in_fresh_environment.py -v
```
### Run a specific test:
```bash
# Test core requirements only
pytest tests/test_install_in_fresh_environment.py::test_core_requirements -v
# Test basic imports
pytest tests/test_install_in_fresh_environment.py::test_basic_import -v
# Test dev requirements
pytest tests/test_install_in_fresh_environment.py::test_dev_requirements -v
```
### Run with more output:
```bash
pytest tests/test_install_in_fresh_environment.py -vv -s
```
### Run with custom timeout (default is 300 seconds per test):
```bash
pytest tests/test_install_in_fresh_environment.py -v --timeout=600
```
## What Each Test Does
| Test | Duration | Purpose |
|------|----------|---------|
| test_core_requirements | ~2-3 min | Installs requirements.txt and verifies all packages |
| test_package_installation | ~2-3 min | Tests pip install -e . works |
| test_basic_import | ~2-3 min | Tests all main modules can be imported |
| test_dev_requirements | ~3-4 min | Installs requirements-dev.txt and verifies packages |
| test_pytest_runs | ~3-4 min | Tests that pytest works after installation |
| test_setup_py_install | ~3-4 min | Tests pip install .[dev] works |
## Expected Behavior
✅ **Success**: All tests pass, indicating requirements files are complete
❌ **Failure**: Missing dependencies or import errors
## Common Issues
### Test times out
- Increase timeout: --timeout=600
- Check internet connection (downloads packages)
- Check disk space for virtual environments
### Import errors
- Missing dependency in requirements.txt
- Add the missing package and re-run tests
### Package not found
- Typo in package name
- Package version not available
- Check PyPI for correct package name
## CI/CD Integration
Add to your CI pipeline:
```yaml
- name: Test requirements completeness
  run: pytest tests/test_install_in_fresh_environment.py -v --timeout=600
```
## Maintenance
Run these tests:
- ✅ Before committing changes to requirements files
- ✅ After adding new dependencies
- ✅ Before releasing new versions
- ✅ When updating Python version requirements
