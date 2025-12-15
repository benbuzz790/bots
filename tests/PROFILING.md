# Test Profiling Guide
This guide explains how to profile pytest tests to identify slow or hanging tests.
## Quick Start
### Option 1: Using the Profiling Script (Recommended)
The profiling script provides timeout protection and is resilient to infinite loops:
```bash
# Profile all tests with 60s timeout per test
python tests/profile_tests.py --timeout 60
# Quick profile (10s timeout, stops on first failure)
python tests/profile_tests.py --quick
# Profile specific test directory
python tests/profile_tests.py tests/unit --timeout 30
# Profile integration tests with 120s timeout
python tests/profile_tests.py tests/integration --timeout 120
```
### Option 2: Using pytest directly
You can also use pytest with the `--profile-tests` flag:
```bash
# Profile all tests
pytest --profile-tests
# Profile with custom timeout
pytest --profile-tests --profile-timeout=60
# Profile specific tests
pytest tests/unit --profile-tests --timeout=30
```
## Understanding the Reports
### test_profile_report.txt
Detailed profiling report containing:
- **Top N Slowest Tests**: Ranked list of slowest tests with durations
- **Detailed Profiles**: cProfile output for the top 10 slowest tests showing:
  - Function call counts
  - Cumulative time spent in each function
  - Time per call
### test_profile_summary.txt
High-level summary with:
- **Duration Breakdown**: Tests categorized by speed
  - Very Slow (>60s) - **Investigate these first!**
  - Slow (10-60s)
  - Moderate (1-10s)
  - Fast (<1s)
- **Slowest Test Files**: Files ranked by total execution time
- **Patterns**: Identifies test files that need optimization
## Workflow for Finding Slow Tests
### Step 1: Quick Scan
Start with a quick profile to identify obviously slow tests:
```bash
python tests/profile_tests.py --quick
```
This runs with a 10s timeout and stops on first failure. Any test that times out is a candidate for investigation.
### Step 2: Full Profile
Run a full profile with reasonable timeouts:
```bash
python tests/profile_tests.py --timeout 60
```
### Step 3: Analyze Results
1. Open `test_profile_summary.txt`
2. Look at "VERY SLOW TESTS" section
3. Check "Slowest test files" to find problematic modules
### Step 4: Deep Dive
For specific slow tests, check `test_profile_report.txt` for detailed profiling data:
- Look for functions with high cumulative time
- Identify bottlenecks (API calls, file I/O, etc.)
- Check for unexpected loops or recursion
## Common Causes of Slow Tests
### 1. Real API Calls
**Symptom**: Tests in `tests/integration/` or `tests/e2e/` taking 10-60s
**Solution**:
- Expected for integration tests
- Consider mocking for unit tests
- Use `@pytest.mark.slow` marker
### 2. Infinite Loops
**Symptom**: Tests timeout at the configured limit
**Solution**:
- Review test logic for while loops
- Check for missing break conditions
- Add loop counters with assertions
### 3. Excessive File I/O
**Symptom**: High time in file operations in profile
**Solution**:
- Use in-memory fixtures
- Reduce file sizes in test data
- Mock file operations in unit tests
### 4. Parallel Execution Issues
**Symptom**: Tests slow when run individually but fast in suite
**Solution**:
- Check for resource contention
- Use `@pytest.mark.serial` if needed
- Review fixture scope
### 5. Heavy Setup/Teardown
**Symptom**: Profile shows time in fixtures
**Solution**:
- Use session or module-scoped fixtures
- Lazy initialization
- Share expensive resources
## Timeout Strategy
### Default Timeouts
- **Unit tests**: Should complete in <1s
- **Integration tests**: 1-10s typical, up to 60s acceptable
- **E2E tests**: 10-60s typical, up to 600s for complex workflows
### Profiling Timeouts
- **Quick scan**: 10s (catches obvious problems)
- **Normal profile**: 60s (reasonable for most tests)
- **Full profile**: 600s (default, allows slow E2E tests)
### Handling Timeouts
If a test times out during profiling:
1. **Check if it's expected**: Some E2E tests legitimately take time
2. **Increase timeout**: Use `--timeout` flag with higher value
3. **Investigate**: Look for infinite loops or blocking operations
4. **Fix or mark**: Either fix the test or mark with `@pytest.mark.slow`
## Best Practices
### 1. Profile Regularly
Run profiling after major changes or when tests feel slow:
```bash
python tests/profile_tests.py --quick
```
### 2. Set Expectations
- Unit tests: <1s
- Integration tests: <10s
- E2E tests: <60s (mark slower ones with `@pytest.mark.slow`)
### 3. Use Markers
Mark slow tests so they can be skipped:
```python
@pytest.mark.slow
def test_complex_workflow():
    # Long-running test
    pass
```
Skip slow tests during development:
```bash
pytest -m "not slow"
```
### 4. Optimize Incrementally
Focus on the slowest tests first - they have the biggest impact.
### 5. Profile Before and After
When optimizing, profile before and after to measure improvement:
```bash
# Before
python tests/profile_tests.py tests/unit --timeout 30
# Make changes...
# After
python tests/profile_tests.py tests/unit --timeout 30
```
## Troubleshooting
### "Profile report not found"
The profiling plugin didn't run. Make sure you're using `--profile-tests` flag.
### Tests hang indefinitely
Use the profiling script with a short timeout:
```bash
python tests/profile_tests.py --timeout 10
```
### Out of memory during profiling
Profiling adds overhead. Try profiling smaller test subsets:
```bash
python tests/profile_tests.py tests/unit/test_specific.py
```
### Profiling changes test behavior
This can happen with timing-sensitive tests. Profile with `-n 0` (no parallelization) which is the default for profiling.
## Examples
### Find all tests slower than 5 seconds
```bash
python tests/profile_tests.py --timeout 60
# Then check test_profile_summary.txt for "SLOW TESTS" section
```
### Profile a specific slow test
```bash
pytest tests/e2e/test_slow_workflow.py --profile-tests -v
```
### Profile with different timeout for different test types
```bash
# Unit tests - should be fast
python tests/profile_tests.py tests/unit --timeout 5
# Integration tests - moderate
python tests/profile_tests.py tests/integration --timeout 30
# E2E tests - can be slow
python tests/profile_tests.py tests/e2e --timeout 120
```
## Integration with CI/CD
Consider adding a profiling step to CI that fails if tests exceed thresholds:
```yaml
- name: Profile tests
  run: |
    python tests/profile_tests.py --timeout 60
    # Parse results and fail if too many slow tests
```
---
**Last Updated**: 2025-01-14
**Related**: TESTING.md, pytest.ini
