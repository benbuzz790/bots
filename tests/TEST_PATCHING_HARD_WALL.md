# Test Patching Hard Wall - Issue Documentation
## Status: ✅ RESOLVED
**Resolution Date**: January 2025
**Solution**: Auto-skip fixtures for incompatible tests
---
## Original Problem
The test_fp_handler.py tests (and test_install_in_fresh_environment.py) were causing pytest-xdist workers to crash with INTERNALERROR.
## Root Cause
- Tests use `@patch("builtins.input")` to mock user input
- test_install_in_fresh_environment.py creates virtual environments and installs packages
- pytest-xdist distributes tests to worker processes
- These operations are incompatible with worker processes
- Workers crash, get replaced, crash again → INTERNALERROR cascade
## Evidence
From test output:
```
[gw2] FAILED tests/unit/test_fp_handler.py::...::test_execute_returns_string_on_cancel
replacing crashed worker gw2
[gw8] node down: Not properly terminated
replacing crashed worker gw8
[gw11] node down: Not properly terminated
INTERNALERROR> KeyError: <WorkerController gw13>
```
## Why @pytest.mark.serial Didn't Work
- `@pytest.mark.serial` tells xdist "don't run these in parallel with each other"
- But xdist still assigns them to worker processes
- The worker process crashes when it tries to patch builtins.input or create venvs
- This is a fundamental incompatibility between these operations and process-based parallelism
## Solution Implemented
### Auto-skip fixtures for incompatible tests
**For input patching tests:**
```python
# At module level in test files
pytestmark = pytest.mark.skipif(
    'xdist' in sys.modules,
    reason="Input patching incompatible with xdist workers"
)
```
**For installation tests:**
```python
@pytest.fixture(autouse=True, scope="module")
def skip_if_xdist():
    if os.environ.get('PYTEST_XDIST_WORKER'):
        pytest.skip("Installation tests must run serially with -n0", allow_module_level=True)
```
## Files Fixed
### Input Patching Tests (already had skipif):
- tests/unit/test_fp_handler.py
- tests/unit/test_prompt_handler.py
- tests/unit/test_cli_frontend.py
- tests/unit/test_cli/test_fp_wizard_complete.py
- tests/unit/test_cli/test_save_auto_commands.py
### Installation Tests (new fix):
- tests/test_install_in_fresh_environment.py
## CI/CD Updates
### PR Checks (`.github/workflows/pr-checks.yml`):
- Runs tests in parallel with `-n 12` (incompatible tests auto-skip)
- Runs installation tests separately with `-n0` (serial mode)
### Main CI (`.github/workflows/main.yml`):
- Already uses `-n 0` (serial mode) so all tests run
## Verification
Run `python tests/test_skip_behavior.py` to verify:
```
1. Running with -n0 (serial mode - should RUN)...
   ✓ Test RAN and PASSED (correct)
2. Running with -n2 (parallel mode - should SKIP)...
   ✓ Test was SKIPPED (correct)
```
## Future Improvements
### Long-term solution for input patching:
Refactor to use dependency injection instead of patching builtins:
```python
class DynamicParameterCollector:
    def __init__(self, input_func=input):
        self._input = input_func
    def collect_parameters(self, func):
        user_input = self._input("Enter value: ")
        ...
```
Then tests can inject a mock without patching builtins:
```python
def test_with_mock_input():
    mock_input = MagicMock(return_value="test")
    collector = DynamicParameterCollector(input_func=mock_input)
    ...
```
## Documentation
- See `tests/TESTING.md` for updated testing guide
- See `tests/README_INSTALL_TESTS.md` for installation test details
- See `tests/FIX_SUMMARY_INSTALL_TESTS.md` for detailed fix explanation
---
*Issue resolved: January 2025*
*No more worker crashes or KeyError exceptions*
