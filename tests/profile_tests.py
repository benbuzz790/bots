#!/usr/bin/env python3
"""
Robust test profiler that can handle infinite loops and stuck tests.

This script runs pytest tests individually with profiling and timeout protection.
It collects timing data even for tests that timeout or hang.

Usage:
    # Profile all tests with 60s timeout per test
    python tests/profile_tests.py --timeout 60

    # Profile specific test directory
    python tests/profile_tests.py tests/unit --timeout 30

    # Profile with default 600s timeout
    python tests/profile_tests.py

    # Quick profile (10s timeout)
    python tests/profile_tests.py --timeout 10
"""

import argparse
import subprocess
import sys
import time
from collections import defaultdict


def collect_tests(test_path):
    """Collect all test names from the given path."""
    # Use pytest's native collection with proper output format
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_path,
        "--collect-only",
        "-q",
        "-q",  # Double -q gives minimal output with just test node IDs
    ]

    try:
        result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)

        # Parse test names from output
        tests = []

        for line in result.stdout.split("\n"):
            line = line.strip()
            # Look for lines with :: which are test node IDs
            # Exclude lines that are summary/status messages
            if "::" in line and not any(x in line for x in ["=", "collected", "generated", "-"]):
                tests.append(line)

        return tests

    except Exception as e:
        print(f"Error collecting tests: {e}")
        return []


def run_single_test(test_name, timeout_per_test, verbose=True):
    """
    Run a single test with profiling and timeout.

    Returns dict with test results.
    """
    cmd = [
        sys.executable,
        "-m",
        "pytest",
        test_name,
        "--profile-tests",
        f"--timeout={timeout_per_test}",
        "--timeout-method=thread",
        "-v",
        "--tb=line",
        "-n",
        "0",
    ]

    start_time = time.time()

    try:
        result = subprocess.run(
            cmd,
            capture_output=True,
            text=True,
            # Give a bit of extra time for pytest overhead
            timeout=timeout_per_test + 5,
        )

        duration = time.time() - start_time
        output = result.stdout + result.stderr

        # Determine outcome
        if "PASSED" in output:
            outcome = "passed"
        elif "FAILED" in output:
            outcome = "failed"
        elif "SKIPPED" in output:
            outcome = "skipped"
        elif "Timeout" in output or "TIMEOUT" in output:
            outcome = "timeout"
        elif result.returncode != 0:
            outcome = "error"
        else:
            outcome = "unknown"

        return {
            "name": test_name,
            "duration": duration,
            "outcome": outcome,
            "output": output,
            "returncode": result.returncode,
        }

    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        if verbose:
            print(f"  ⏱️  TIMEOUT after {duration:.1f}s")

        return {
            "name": test_name,
            "duration": duration,
            "outcome": "timeout",
            "output": "(Test timed out)",
            "returncode": -1,
        }

    except Exception as e:
        duration = time.time() - start_time
        return {
            "name": test_name,
            "duration": duration,
            "outcome": "error",
            "output": str(e),
            "returncode": -1,
        }


def generate_summary_report(test_results, output_file="test_profile_summary.txt"):
    """Generate a summary report from test results."""

    if not test_results:
        print("No test results to report")
        return

    # Sort by duration
    sorted_tests = sorted(test_results, key=lambda x: x["duration"], reverse=True)

    with open(output_file, "w") as f:
        f.write("=" * 80 + "\n")
        f.write("TEST PROFILING SUMMARY\n")
        f.write("=" * 80 + "\n\n")

        f.write(f"Total tests run: {len(test_results)}\n")
        total_time = sum(t["duration"] for t in test_results)
        f.write(f"Total time: {total_time:.2f}s\n\n")

        # Count by outcome
        outcomes = defaultdict(int)
        for test in test_results:
            outcomes[test["outcome"]] += 1

        f.write("OUTCOMES:\n")
        for outcome, count in sorted(outcomes.items()):
            f.write(f"  {outcome}: {count}\n")
        f.write("\n")

        # Categorize by duration
        very_slow = [t for t in test_results if t["duration"] > 60]
        slow = [t for t in test_results if 10 < t["duration"] <= 60]
        moderate = [t for t in test_results if 1 < t["duration"] <= 10]
        fast = [t for t in test_results if t["duration"] <= 1]

        f.write("DURATION BREAKDOWN:\n")
        f.write(f"  Very Slow (>60s):  {len(very_slow)} tests\n")
        f.write(f"  Slow (10-60s):     {len(slow)} tests\n")
        f.write(f"  Moderate (1-10s):  {len(moderate)} tests\n")
        f.write(f"  Fast (<1s):        {len(fast)} tests\n\n")

        # Show very slow tests
        if very_slow:
            f.write("=" * 80 + "\n")
            f.write("VERY SLOW TESTS (>60s) - INVESTIGATE THESE FIRST\n")
            f.write("=" * 80 + "\n\n")

            for test in sorted(very_slow, key=lambda x: x["duration"], reverse=True):
                name = test["name"]
                duration = test["duration"]
                outcome = test["outcome"]
                f.write(f"  {duration:>7.2f}s  {outcome:>10s}  {name}\n")
            f.write("\n")

        # Show slow tests
        if slow:
            f.write("=" * 80 + "\n")
            f.write("SLOW TESTS (10-60s)\n")
            f.write("=" * 80 + "\n\n")

            for test in sorted(slow, key=lambda x: x["duration"], reverse=True):
                name = test["name"]
                duration = test["duration"]
                outcome = test["outcome"]
                f.write(f"  {duration:>7.2f}s  {outcome:>10s}  {name}\n")
            f.write("\n")

        # Show all tests sorted by duration
        f.write("=" * 80 + "\n")
        f.write("ALL TESTS (SORTED BY DURATION)\n")
        f.write("=" * 80 + "\n\n")

        for test in sorted_tests:
            name = test["name"]
            duration = test["duration"]
            outcome = test["outcome"]
            f.write(f"  {duration:>7.2f}s  {outcome:>10s}  {name}\n")

        # Identify patterns
        f.write("\n" + "=" * 80 + "\n")
        f.write("PATTERNS\n")
        f.write("=" * 80 + "\n\n")

        # Group by test file
        by_file = defaultdict(list)
        for test in test_results:
            file_name = test["name"].split("::")[0] if "::" in test["name"] else test["name"]
            by_file[file_name].append(test["duration"])

        # Find slowest files
        file_totals = [(f, sum(durations), len(durations)) for f, durations in by_file.items()]
        file_totals.sort(key=lambda x: x[1], reverse=True)

        f.write("Slowest test files (by total time):\n\n")
        for file_name, total, count in file_totals[:20]:
            avg = total / count if count > 0 else 0
            f.write(f"  {total:>7.2f}s total  " f"({count:>3d} tests, {avg:>6.2f}s avg)  {file_name}\n")

    print(f"\n✅ Summary report generated: {output_file}")


def main():
    parser = argparse.ArgumentParser(
        description="Profile pytest tests with timeout protection " "(runs tests individually)",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )

    parser.add_argument(
        "test_path",
        nargs="?",
        default="tests",
        help="Path to tests to profile (default: tests)",
    )

    parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Timeout per test in seconds (default: 60)",
    )

    parser.add_argument(
        "--quick",
        action="store_true",
        help="Quick profile mode (10s timeout)",
    )

    args = parser.parse_args()

    # Quick mode overrides
    if args.quick:
        args.timeout = 10
        print("QUICK MODE: 10s timeout per test")

    # Collect all tests
    print("=" * 80)
    print("COLLECTING TESTS")
    print("=" * 80)
    print(f"Test path: {args.test_path}")
    print(f"Timeout per test: {args.timeout}s")
    print()

    tests = collect_tests(args.test_path)

    if not tests:
        print("❌ No tests found!")
        return 1

    print(f"Found {len(tests)} tests\n")

    # Run each test individually
    print("=" * 80)
    print("RUNNING TESTS INDIVIDUALLY")
    print("=" * 80)
    print("(Each test runs in isolation with timeout protection)")
    print()

    test_results = []

    for i, test_name in enumerate(tests, 1):
        print(f"[{i}/{len(tests)}] {test_name}")

        result = run_single_test(test_name, args.timeout, verbose=True)
        test_results.append(result)

        # Print outcome
        outcome_symbol = {
            "passed": "✅",
            "failed": "❌",
            "skipped": "⏭️ ",
            "timeout": "⏱️ ",
            "error": "💥",
            "unknown": "❓",
        }.get(result["outcome"], "?")

        outcome = result["outcome"]
        duration = result["duration"]
        print(f"  {outcome_symbol} {outcome.upper()} ({duration:.2f}s)")
        print()

    # Generate summary
    print("\n" + "=" * 80)
    print("GENERATING SUMMARY")
    print("=" * 80)
    generate_summary_report(test_results)

    # Print summary to console
    print("\n" + "=" * 80)
    print("PROFILING COMPLETE")
    print("=" * 80)
    print(f"Total tests: {len(test_results)}")
    total_time = sum(t["duration"] for t in test_results)
    print(f"Total time: {total_time:.2f}s")

    # Count outcomes
    outcomes = defaultdict(int)
    for test in test_results:
        outcomes[test["outcome"]] += 1

    print("\nOutcomes:")
    for outcome, count in sorted(outcomes.items()):
        print(f"  {outcome}: {count}")

    print("\nDetailed report: test_profile_summary.txt")
    print("=" * 80)

    return 0


if __name__ == "__main__":
    sys.exit(main())
