#!/usr/bin/env python3
"""
Simple Docker Test Orchestrator
Safely runs pytest in Docker containers with different configurations.
"""

import subprocess
import sys
import time
from pathlib import Path

def run_command(cmd, description):
    """Run a command and return success status."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print()

    start_time = time.time()
    try:
        result = subprocess.run(cmd, check=True, text=True, capture_output=False)
        duration = time.time() - start_time
        print(f"\n✅ SUCCESS ({duration:.1f}s): {description}")
        return True
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"\n❌ FAILED ({duration:.1f}s): {description}")
        print(f"Exit code: {e.returncode}")
        return False
    except KeyboardInterrupt:
        print(f"\n⚠️  INTERRUPTED: {description}")
        return False

def build_container():
    """Build the Docker test container."""
    return run_command(
        ["docker", "build", "-t", "pytest-container", "."],
        "Building Docker test container"
    )

def run_test_suite(test_args, description):
    """Run a test suite in Docker."""
    base_cmd = [
        "docker", "run", "--rm", "-it",
        "--memory=2g", "--cpus=2",
        "pytest-container",
        "python", "-m", "pytest"
    ]

    cmd = base_cmd + test_args
    return run_command(cmd, description)

def main():
    """Main orchestrator function."""
    print("🐳 Docker Test Orchestrator")
    print("=" * 60)

    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not available. Please install Docker Desktop.")
        sys.exit(1)

    # Build container first
    if not build_container():
        print("❌ Failed to build container. Exiting.")
        sys.exit(1)

    # Test configurations
    test_configs = [
        {
            "args": ["--timeout=30", "-v", "test_docker_permissions.py"],
            "description": "Docker permissions test (safe baseline)"
        },
        {
            "args": ["--timeout=30", "-v", "tests/test_cli/test_broadcast_fp_comprehensive.py"],
            "description": "Broadcast FP tests (investigating failures)"
        },
        {
            "args": ["--timeout=30", "-v", "-k", "test_web_tool and not integration"],
            "description": "Web tool tests (basic functionality)"
        },
        {
            "args": ["--timeout=30", "-v", "-k", "test_toolify and not integration"],
            "description": "Toolify tests (core functionality)"
        },
        {
            "args": ["--timeout=30", "-v", "-k", "not (test_branch_self_recursive or test_real_ai_stash_message_generation)"],
            "description": "Safe test subset (avoiding dangerous tests)"
        }
    ]

    results = []

    print(f"\n🎯 Running {len(test_configs)} test configurations...")

    for i, config in enumerate(test_configs, 1):
        print(f"\n📋 Configuration {i}/{len(test_configs)}")
        success = run_test_suite(config["args"], config["description"])
        results.append((config["description"], success))

        if not success:
            response = input(f"\n⚠️  Test failed. Continue with remaining tests? (y/N): ")
            if response.lower() != 'y':
                break

    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")

    for description, success in results:
        status = "✅ PASS" if success else "❌ FAIL"
        print(f"{status}: {description}")

    passed = sum(1 for _, success in results if success)
    total = len(results)
    print(f"\n🎯 Overall: {passed}/{total} test suites passed")

    if passed == total:
        print("🎉 All test suites completed successfully!")
        sys.exit(0)
    else:
        print("⚠️  Some test suites failed. Check output above for details.")
        sys.exit(1)

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Orchestrator interrupted by user.")
        sys.exit(1)
