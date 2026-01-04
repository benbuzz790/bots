"""
Isolated test runner for test_quiet_duplicate.py
Runs in a subprocess to prevent system crashes from affecting the main process.
Writes diagnostics to a file for investigation.
"""

import subprocess
import sys
import time
from pathlib import Path


def run_single_test(test_name):
    """Run a single test in isolation and capture results."""
    log_file = Path(f"test_crash_log_{test_name.split('::')[-1]}.txt")
    with open(log_file, "w") as f:
        f.write(f"Starting test: {test_name}\n")
        f.write(f"Time: {time.strftime('%Y-%m-%d %H:%M:%S')}\n")
        f.write("-" * 80 + "\n")
        f.flush()
        try:
            # Run test in subprocess with timeout
            result = subprocess.run(
                [sys.executable, "-m", "pytest", test_name, "-v", "-n0", "-s"],
                capture_output=True,
                text=True,
                timeout=30,
                cwd=Path(__file__).parent.parent,
            )
            f.write(f"Return code: {result.returncode}\n")
            f.write(f"STDOUT:\n{result.stdout}\n")
            f.write(f"STDERR:\n{result.stderr}\n")
            f.write("Test completed successfully\n")
            return result.returncode == 0
        except subprocess.TimeoutExpired as e:
            f.write("TEST TIMEOUT after 30 seconds\n")
            f.write(f"Partial stdout: {e.stdout}\n")
            f.write(f"Partial stderr: {e.stderr}\n")
            return False
        except Exception as e:
            f.write(f"EXCEPTION: {type(e).__name__}: {e}\n")
            import traceback

            f.write(traceback.format_exc())
            return False


if __name__ == "__main__":
    tests = [
        "tests/e2e/test_quiet_duplicate.py::TestQuietModeDuplicate::test_quiet_mode_shows_message_once_after_fix",
    ]
    print("Running tests in isolation...")
    results = {}
    for test in tests:
        test_name = test.split("::")[-1]
        print(f"\nRunning: {test_name}...")
        success = run_single_test(test)
        results[test_name] = success
        print(f"  Result: {'PASS' if success else 'FAIL/TIMEOUT'}")
        time.sleep(2)
    print("\nSUMMARY:")
    for test_name, success in results.items():
        status = "PASS" if success else "FAIL"
        print(f"  {status}: {test_name}")
    print("\nCheck test_crash_log_*.txt files for details")
