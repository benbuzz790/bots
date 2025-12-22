# Test Patching Hard Wall - Issue Documentation
## Problem
The test_fp_handler.py tests are causing pytest-xdist workers to crash with INTERNALERROR.
## Root Cause
- Tests use `@patch("builtins.input")` to mock user input
- pytest-xdist distributes tests to worker processes
- Patching `builtins.input` in a worker process causes the worker to crash
- Even with `@pytest.mark.serial`, xdist still tries to assign tests to workers
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
- The worker process crashes when it tries to patch builtins.input
- This is a fundamental incompatibility between input patching and process-based parallelism
## Solutions (in order of preference)
### 1. Skip tests when running with xdist (RECOMMENDED)
Mark tests to skip when xdist is active:
```python
import sys
import pytest
# At module level
pytestmark = pytest.mark.skipif(
    'xdist' in sys.modules,
    reason="Input patching incompatible with xdist workers"
)
```
### 2. Refactor to use dependency injection (BEST LONG-TERM)
Instead of patching builtins.input, inject the input function:
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
### 3. Run tests in main process only
Use pytest-xdist's `@pytest.mark.xdist_group` to force main process:
```python
@pytest.mark.xdist_group(name="main_process_only")
class TestDynamicFunctionalPromptHandlerDataFormat:
    ...
```
But this may not work reliably for input patching.
## Recommendation
**Skip these tests when xdist is active** (Solution 1). They test CLI interaction which is inherently difficult to test in parallel workers. The functionality is better tested through integration tests or manual testing.
Long-term: Refactor to use dependency injection (Solution 2).
## Files Affected
- tests/unit/test_fp_handler.py (all 3 test classes)
