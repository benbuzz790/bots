#!/usr/bin/env python3
"""
Helper script to run installation tests correctly.

The installation tests in test_install_in_fresh_environment.py must run serially
because they create virtual environments and install packages, which can cause
worker crashes and timeouts when run in parallel.
"""

import subprocess
import sys


def run_install_tests():
    """Run installation tests with correct settings."""
    print("=" * 70)
    print("Running Installation Tests (Serial Mode)")
    print("=" * 70)
    print()
    print("These tests create virtual environments and must run serially.")
    print("Using -n0 to disable parallel execution...")
    print()

    cmd = [
        sys.executable,
        "-m",
        "pytest",
        "tests/test_install_in_fresh_environment.py",
        "-n0",  # Disable parallel execution
        "-v",  # Verbose output
        "--tb=short",  # Short traceback format
    ]

    # Add any additional arguments passed to this script
    if len(sys.argv) > 1:
        cmd.extend(sys.argv[1:])

    print(f"Command: {' '.join(cmd)}")
    print()

    result = subprocess.run(cmd)
    return result.returncode


if __name__ == "__main__":
    sys.exit(run_install_tests())
