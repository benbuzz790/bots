#!/usr/bin/env python3
"""
Automated Docker Test Orchestrator (Updated)
Runs pytest in Docker containers automatically without user interaction.
Now with warning suppression for cleaner output.
"""

import subprocess
import sys
import time
from pathlib import Path

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
        result = subprocess.run(cmd, check=True, text=True, timeout=timeout_seconds)
        duration = time.time() - start_time
        print(f"\n✅ SUCCESS ({duration:.1f}s): {description}")
        return True, None
    except subprocess.TimeoutExpired:
        duration = time.time() - start_time
        print(f"\n⏰ TIMEOUT ({duration:.1f}s): {description}")
        return False, "TIMEOUT"
    except subprocess.CalledProcessError as e:
        duration = time.time() - start_time
        print(f"\n❌ FAILED ({duration:.1f}s): {description}")
        print(f"Exit code: {e.returncode}")
        return False, f"EXIT_CODE_{e.returncode}"
    except KeyboardInterrupt:
        print(f"\n⚠️  INTERRUPTED: {description}")
        return False, "INTERRUPTED"

def build_container():
    """Build the Docker test container."""
    success, error = run_command(
        ["docker", "build", "-t", "pytest-container", "."],
        "Building Docker test container",
        timeout_seconds=600  # 10 minutes for building
    )
    return success

def run_test_suite(test_args, description, timeout_seconds=300):
    """Run a test suite in Docker."""
    base_cmd = [
        "docker", "run", "--rm",
        "--memory=2g", "--cpus=2",
        "pytest-container",
        "python", "-m", "pytest"
    ]

    cmd = base_cmd + test_args
    return run_command(cmd, description, timeout_seconds)

def main():
    """Main orchestrator function - fully automated."""
    print("🤖 Automated Docker Test Orchestrator (v2 - Clean Output)")
    print("=" * 60)
    print("Running all tests automatically without user interaction...")

    # Check if Docker is available
    try:
        subprocess.run(["docker", "--version"], check=True, capture_output=True)
        print("✅ Docker is available")
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("❌ Docker is not available. Please install Docker Desktop.")
        sys.exit(1)

    # Build container first
    print("\n🔨 Building Docker container...")
    if not build_container():
        print("❌ Failed to build container. Exiting.")
        sys.exit(1)

    # Test configurations - ordered from safest to most complex
    # Added warning suppression flags for cleaner output
    test_configs = [
        {
            "args": ["-n", "1", "--timeout=30", "-v", "--disable-warnings", "--tb=short", "test_docker_permissions.py"],
            "description": "Docker permissions test (safe baseline)",
            "timeout": 60,
            "critical": True  # Must pass for others to be meaningful
        },
        {
            "args": ["-n", "1", "--timeout=30", "-v", "--disable-warnings", "--tb=short", "-k", "test_web_tool and not integration"],
            "description": "Web tool tests (basic functionality)",
            "timeout": 120,
            "critical": False
        },
        {
            "args": ["-n", "1", "--timeout=30", "-v", "--disable-warnings", "--tb=short", "-k", "test_toolify and not integration"],
            "description": "Toolify tests (core functionality)", 
            "timeout": 120,
            "critical": False
        },
        {
            "args": ["-n", "1", "--timeout=30", "-v", "--disable-warnings", "--tb=short", "tests/test_cli/test_broadcast_fp_comprehensive.py", "-x"],
            "description": "Broadcast FP tests (investigating failures)",
            "timeout": 180,
            "critical": False
        },
        {
            "args": ["-n", "1", "--timeout=30", "-v", "--disable-warnings", "--tb=short", "-k", "not (test_branch_self_recursive or test_real_ai_stash_message_generation)", "--maxfail=5"],
            "description": "Safe test subset (avoiding dangerous tests)",
            "timeout": 600,
            "critical": False
        }
    ]

    results = []
    total_start_time = time.time()

    print(f"\n🎯 Running {len(test_configs)} test configurations automatically...")
    print("📝 Note: Warnings are suppressed for cleaner output")

    for i, config in enumerate(test_configs, 1):
        print(f"\n📋 Configuration {i}/{len(test_configs)}")
        success, error_type = run_test_suite(
            config["args"], 
            config["description"],
            config.get("timeout", 300)
        )

        results.append({
            "description": config["description"],
            "success": success,
            "error_type": error_type,
            "critical": config.get("critical", False)
        })

        # If a critical test fails, note it but continue
        if not success and config.get("critical", False):
            print(f"⚠️  CRITICAL TEST FAILED: {config['description']}")
            print("   Continuing with remaining tests for diagnostic purposes...")

        # Brief pause between tests
        if i < len(test_configs):
            print("\n⏳ Pausing 3 seconds before next test...")
            time.sleep(3)

    total_duration = time.time() - total_start_time

    # Detailed Summary
    print(f"\n{'='*60}")
    print("📊 DETAILED TEST SUMMARY")
    print(f"{'='*60}")
    print(f"Total execution time: {total_duration:.1f}s")
    print()

    critical_failures = []
    regular_failures = []
    successes = []

    for result in results:
        status = "✅ PASS" if result["success"] else "❌ FAIL"
        critical_marker = " [CRITICAL]" if result["critical"] else ""
        error_info = f" ({result['error_type']})" if result["error_type"] else ""

        print(f"{status}: {result['description']}{critical_marker}{error_info}")

        if result["success"]:
            successes.append(result)
        elif result["critical"]:
            critical_failures.append(result)
        else:
            regular_failures.append(result)

    # Statistics
    print(f"\n📈 STATISTICS:")
    print(f"   ✅ Passed: {len(successes)}")
    print(f"   ❌ Failed: {len(regular_failures)}")
    print(f"   🚨 Critical Failed: {len(critical_failures)}")
    print(f"   📊 Success Rate: {len(successes)}/{len(results)} ({100*len(successes)/len(results):.1f}%)")

    # Recommendations
    print(f"\n💡 RECOMMENDATIONS:")
    if critical_failures:
        print("   🚨 Fix critical failures first - these indicate basic setup issues")
    if regular_failures:
        print("   🔧 Regular failures indicate specific feature issues")
        print("   📋 Common issues found:")
        print("      - CLI stdin handling in Docker environments")
        print("      - API interface changes (parameter names, token limits)")
        print("      - Error message format expectations")
        print("      - Import statement mismatches")
    if len(successes) == len(results):
        print("   🎉 All tests passed! System appears healthy.")
    elif len(successes) > len(regular_failures):
        print("   👍 More tests passed than failed - system mostly functional")
    else:
        print("   ⚠️  More tests failed than passed - significant issues present")

    # Exit code based on results
    if critical_failures:
        print("\n🚨 Exiting with error due to critical test failures")
        sys.exit(2)  # Critical failure
    elif regular_failures:
        print("\n⚠️  Exiting with warning due to test failures")
        sys.exit(1)  # Regular failure
    else:
        print("\n🎉 All tests completed successfully!")
        sys.exit(0)  # Success

if __name__ == "__main__":
    try:
        main()
    except KeyboardInterrupt:
        print("\n\n⚠️  Orchestrator interrupted by user.")
        sys.exit(130)  # Standard exit code for SIGINT
    except Exception as e:
        print(f"\n\n💥 Unexpected error: {e}")
        sys.exit(3)  # Unexpected error
