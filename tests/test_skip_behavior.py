import subprocess
import sys

print("=" * 70)
print("Testing skip behavior in parallel mode")
print("=" * 70)

# Test 1: Run with -n0 (should run)
print("\n1. Running with -n0 (serial mode - should RUN)...")
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_install_in_fresh_environment.py::test_scanner_detects_new_imports",
        "-n0",
        "-v",
        "--tb=line",
    ],
    capture_output=True,
    text=True,
    timeout=60,
)
if "PASSED" in result.stdout:
    print("   ✓ Test RAN and PASSED (correct)")
elif "SKIPPED" in result.stdout:
    print("   ✗ Test was SKIPPED (incorrect - should run with -n0)")
else:
    print(f"   ? Unexpected result: {result.stdout[:200]}")

# Test 2: Run with -n2 (should skip)
print("\n2. Running with -n2 (parallel mode - should SKIP)...")
result = subprocess.run(
    [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_install_in_fresh_environment.py::test_scanner_detects_new_imports",
        "-n2",
        "-v",
        "--tb=line",
    ],
    capture_output=True,
    text=True,
    timeout=60,
)
if "SKIPPED" in result.stdout:
    print("   ✓ Test was SKIPPED (correct)")
elif "PASSED" in result.stdout:
    print("   ✗ Test RAN (incorrect - should skip in parallel mode)")
else:
    print(f"   ? Unexpected result: {result.stdout[:200]}")

print("\n" + "=" * 70)
