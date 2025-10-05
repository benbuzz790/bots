#!/usr/bin/env python3
"""
Simple Docker Test Orchestrator (Fixed)
Safely runs pytest in Docker containers without timeout plugin dependency.
"""

import subprocess
import sys
import time


def run_command(cmd, description, timeout_seconds=300):
    """Run a command with timeout and return success status."""
    print(f"\n{'='*60}")
    print(f"🚀 {description}")
    print(f"{'='*60}")
    print(f"Command: {' '.join(cmd)}")
    print(f"Timeout: {timeout_seconds}s")
    print()

    start_time = time.time()
    try:
        subprocess.run(cmd, check=True, text=True, capture_output=False, timeout=timeout_seconds)
        duration = time.time() - start_time
        print(f"\n✅ SUCCESS ({duration:.1f}s): {description}")
        return True
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"\n⏰ TIMEOUT ({duration:.1f}s): {description}")
        return False
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
        "Building Docker test container",
        timeout_seconds=600,  # 10 minutes for building
    )


def run_test_suite(test_args, description, timeout_seconds=300):
    """Run a test suite in Docker."""
    base_cmd = ["docker", "run", "--rm", "-it", "--memory=2g", "--cpus=2", "pytest-container", "python", "-m", "pytest"]

    cmd = base_cmd + test_args
    return run_command(cmd, description, timeout_seconds)


def main():
    """Main orchestrator function."""
    print("🐳 Docker Test Orchestrator (Fixed)")
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

    # Test configurations (without --timeout flag)
    test_configs = [
        {
            "args": ["-v", "test_docker_permissions.py"],
            "description": "Docker permissions test (safe baseline)",
            "timeout": 60,
        },
        {
            "args": ["-v", "tests/test_cli/test_broadcast_fp_comprehensive.py", "-x"],
            "description": "Broadcast FP tests (stop on first failure)",
            "timeout": 180,
        },
        {
            "args": ["-v", "-k", "test_web_tool and not integration", "--tb=short"],
            "description": "Web tool tests (basic functionality)",
            "timeout": 120,
        },
        {
            "args": ["-v", "-k", "test_toolify and not integration", "--tb=short"],
            "description": "Toolify tests (core functionality)",
            "timeout": 120,
        },
        {
            "args": ["-v", "-k", "not (test_branch_self_recursive or test_real_ai_stash_message_generation)", "--maxfail=3"],
            "description": "Safe test subset (avoiding dangerous tests)",
            "timeout": 600,
        },
    ]

    results = []

    print(f"\n🎯 Running {len(test_configs)} test configurations...")

    for i, config in enumerate(test_configs, 1):
        print(f"\n📋 Configuration {i}/{len(test_configs)}")
        success = run_test_suite(config["args"], config["description"], config.get("timeout", 300))
        results.append((config["description"], success))

        if not success:
            response = input("\n⚠️  Test failed. Continue with remaining tests? (y/N): ")
            if response.lower() != "y":
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
