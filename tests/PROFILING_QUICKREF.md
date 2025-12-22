# Pytest Profiling - Quick Reference
## Common Commands
### Quick Scan (Recommended First Step)
```bash
python tests/profile_tests.py --quick
```
- 10s timeout per test
- **Continues profiling even if tests timeout** (this is what we want!)
- Fast identification of problem tests
### Full Profile
```bash
python tests/profile_tests.py --timeout 60
```
- 60s timeout per test
- Comprehensive analysis
- Generates detailed reports
- Continues through all tests
### Profile Specific Tests
```bash
# Unit tests (should be fast)
python tests/profile_tests.py tests/unit --timeout 5
# Integration tests
python tests/profile_tests.py tests/integration --timeout 30
# E2E tests
python tests/profile_tests.py tests/e2e --timeout 120
# Single test file
python tests/profile_tests.py tests/unit/test_specific.py --timeout 10
```
### Using pytest directly
```bash
pytest --profile-tests
pytest --profile-tests --profile-timeout=60
pytest tests/unit --profile-tests --timeout=30
```
## Reports
### test_profile_summary.txt
- Quick overview
- Tests by speed category
- Slowest files
- **Start here!**
### test_profile_report.txt
- Detailed cProfile data
- Function-level timing
- Top 10 slowest tests profiled
- Use for deep investigation
## Interpreting Results
### Speed Categories
- **Very Slow (>60s)**: Investigate immediately
- **Slow (10-60s)**: Review and optimize
- **Moderate (1-10s)**: Acceptable for integration/e2e
- **Fast (<1s)**: Good for unit tests
### Common Issues
- **Timeout**: Infinite loop or blocking operation (API call, network wait)
- **High cumtime**: Expensive function calls (API, I/O)
- **Many calls**: Inefficient algorithms or loops
- **File I/O**: Consider mocking or in-memory fixtures
## Workflow
1. Run quick scan: `python tests/profile_tests.py --quick`
2. Check summary: `cat test_profile_summary.txt`
3. Identify slow tests in "VERY SLOW" section
4. Review detailed profile for those tests
5. Fix issues (mock APIs, optimize loops, etc.)
6. Re-profile to verify improvement
## Important Notes
- **Timeouts are expected!** The profiler is designed to find slow/hanging tests
- The profiler will **continue** even when tests timeout
- Use `--fail-fast` only if you want to stop on first problem (not recommended)
- Profile reports show timing data for all tests, including timed-out ones
## Tips
- Profile regularly during development
- Set timeout based on test type (unit=5s, integration=30s, e2e=120s)
- Don't use `--fail-fast` when profiling (you want to see ALL slow tests)
- Mark legitimately slow tests with `@pytest.mark.slow`
- Profile before and after optimization to measure impact
## Help
```bash
python tests/profile_tests.py --help
```
Full documentation: tests/PROFILING.md
