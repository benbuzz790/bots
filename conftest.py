"""
Root conftest.py for pytest configuration and shared fixtures.
"""

import cProfile
import io
import os
import pstats
import sys
import time
from pathlib import Path

import pytest

# Add project root to path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Test mode environment variable
os.environ["BOTS_TEST_MODE"] = "1"


# ============================================================================
# PROFILING PLUGIN
# ============================================================================


class TestProfiler:
    """Collects profiling data for each test."""

    def __init__(self):
        self.test_profiles = []
        self.current_profile = None
        self.current_test_name = None
        self.start_time = None

    def start_profiling(self, test_name):
        """Start profiling a test."""
        self.current_test_name = test_name
        self.start_time = time.time()
        self.current_profile = cProfile.Profile()
        self.current_profile.enable()

    def stop_profiling(self, outcome="passed"):
        """Stop profiling and save results."""
        if self.current_profile is None:
            return

        try:
            self.current_profile.disable()
        except Exception:
            # If disabling fails, at least try to save what we have
            pass

        duration = time.time() - self.start_time

        # Capture profile stats
        try:
            s = io.StringIO()
            ps = pstats.Stats(self.current_profile, stream=s)
            ps.sort_stats("cumulative")
        except Exception:
            # If stats fail, create a minimal entry
            ps = None

        self.test_profiles.append(
            {
                "name": self.current_test_name,
                "duration": duration,
                "outcome": outcome,
                "profile": self.current_profile,
                "stats": ps,
            }
        )

        # Reset
        self.current_profile = None
        self.current_test_name = None
        self.start_time = None

        # Write incremental report after each test
        # This ensures we have data even if pytest is interrupted
        try:
            self.generate_report()
        except Exception:
            pass  # Don't fail the test if report generation fails

    def save_current_if_running(self):
        """Save current profiling data if a test is still running (e.g., timeout)."""
        if self.current_profile is not None and self.current_test_name is not None:
            # Test is still running, save what we have
            self.stop_profiling("timeout/interrupted")

    def generate_report(self, output_file="test_profile_report.txt", top_n=50):
        """Generate a profiling report."""
        # Save any currently running test first
        self.save_current_if_running()

        if not self.test_profiles:
            return

        # Sort by duration
        sorted_tests = sorted(self.test_profiles, key=lambda x: x["duration"], reverse=True)

        with open(output_file, "w") as f:
            f.write("=" * 80 + "\n")
            f.write("PYTEST PROFILING REPORT\n")
            f.write("=" * 80 + "\n\n")

            f.write(f"Total tests profiled: {len(self.test_profiles)}\n")
            f.write(f"Total time: {sum(t['duration'] for t in self.test_profiles):.2f}s\n\n")

            # Summary of slowest tests
            f.write("=" * 80 + "\n")
            f.write(f"TOP {min(top_n, len(sorted_tests))} SLOWEST TESTS\n")
            f.write("=" * 80 + "\n\n")

            for i, test in enumerate(sorted_tests[:top_n], 1):
                f.write(f"{i}. {test['name']}\n")
                f.write(f"   Duration: {test['duration']:.2f}s\n")
                f.write(f"   Outcome: {test['outcome']}\n")
                f.write("\n")

            # Detailed profiles for top 10
            f.write("\n" + "=" * 80 + "\n")
            f.write("DETAILED PROFILES (TOP 10)\n")
            f.write("=" * 80 + "\n\n")

            for i, test in enumerate(sorted_tests[:10], 1):
                f.write(f"\n{'=' * 80}\n")
                f.write(f"{i}. {test['name']} ({test['duration']:.2f}s)\n")
                f.write(f"{'=' * 80}\n\n")

                # Print top functions if stats available
                if test["stats"] is not None:
                    try:
                        s = io.StringIO()
                        ps = pstats.Stats(test["profile"], stream=s)
                        ps.sort_stats("cumulative")
                        ps.print_stats(20)  # Top 20 functions
                        f.write(s.getvalue())
                    except Exception as e:
                        f.write(f"(Profile data unavailable: {e})\n")
                else:
                    f.write("(Profile data unavailable - test may have been interrupted)\n")
                f.write("\n")


@pytest.fixture(scope="session")
def test_profiler(request):
    """Session-scoped fixture for test profiling."""
    # Get or create the shared profiler instance from config
    if not hasattr(request.config, "_test_profiler"):
        request.config._test_profiler = TestProfiler()

    profiler = request.config._test_profiler

    # Register report generation at session end
    def generate_report():
        profiler.generate_report()
        print("\n\nProfile report generated: test_profile_report.txt")

    request.addfinalizer(generate_report)

    return profiler


@pytest.hookimpl(hookwrapper=True, tryfirst=True)
def pytest_runtest_protocol(item, nextitem):
    """Hook to profile each test."""
    # Check if profiling is enabled
    if not item.config.getoption("--profile-tests", default=False):
        yield
        return

    # Get or create profiler
    if not hasattr(item.config, "_test_profiler"):
        item.config._test_profiler = TestProfiler()

    profiler = item.config._test_profiler
    test_name = item.nodeid

    # Start profiling
    profiler.start_profiling(test_name)

    result = "unknown"

    try:
        # Run the test and capture the outcome
        outcome = yield

        # Get the test report to determine actual outcome
        try:
            reports = outcome.get_result()
            # Find the 'call' phase report (the actual test execution)
            for report in reports:
                if report.when == "call":
                    if report.outcome == "passed":
                        result = "passed"
                    elif report.outcome == "failed":
                        result = "failed"
                    elif report.outcome == "skipped":
                        result = "skipped"
                    else:
                        result = "error"
                    break
            else:
                # No call phase found, check if test was skipped in setup
                for report in reports:
                    if report.outcome == "skipped":
                        result = "skipped"
                        break
        except Exception:
            # If we can't get the outcome, mark as error
            result = "error"

    except KeyboardInterrupt:
        result = "interrupted"
        raise

    except Exception:
        result = "error"
        # Re-raise the exception so pytest can properly register the failure
        raise

    finally:
        # Always stop profiling, even if test times out or crashes
        try:
            profiler.stop_profiling(result)
        except Exception as e:
            # If profiling itself fails, at least record that we tried
            print(f"\nWarning: Failed to stop profiling for {test_name}: {e}")


def pytest_sessionfinish(session, exitstatus):
    """Generate report at end of session."""
    if hasattr(session.config, "_test_profiler"):
        profiler = session.config._test_profiler
        try:
            profiler.generate_report()
            print(f"\n\n{'=' * 80}")
            print("Profile report generated: test_profile_report.txt")
            print(f"Total tests profiled: {len(profiler.test_profiles)}")
            print(f"{'=' * 80}\n")
        except Exception as e:
            print(f"\n\nWarning: Failed to generate profile report: {e}")
            print(f"Tests profiled before error: {len(profiler.test_profiles) if profiler.test_profiles else 0}\n")


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--profile-tests",
        action="store_true",
        default=False,
        help="Enable test profiling",
    )
    parser.addoption(
        "--profile-timeout",
        action="store",
        type=int,
        default=None,
        help="Override timeout for profiling runs (in seconds)",
    )


def pytest_configure(config):
    """Configure pytest with custom settings."""
    # Override timeout if profiling with custom timeout
    if config.getoption("--profile-tests") and config.getoption("--profile-timeout"):
        timeout = config.getoption("--profile-timeout")
        config.option.timeout = timeout
        print(f"\n{'=' * 80}")
        print(f"PROFILING MODE: Timeout set to {timeout}s")
        print(f"{'=' * 80}\n")

    # If profiling is enabled, create the profiler early
    if config.getoption("--profile-tests", default=False):
        config._test_profiler = TestProfiler()
        print(f"\n{'=' * 80}")
        print("PROFILING ENABLED: Test profiler initialized")
        print(f"{'=' * 80}\n")


def pytest_collection_modifyitems(config, items):
    """
    Modify test items to set custom timeouts based on markers.

    This hook sets timeouts for tests marked with specific markers:
    - @pytest.mark.installation: 1200 seconds (20 minutes)
    - @pytest.mark.api: 600 seconds (10 minutes) - already default
    """
    for item in items:
        # Check if test has installation marker
        if item.get_closest_marker("installation"):
            # Set 20-minute timeout for installation tests
            item.add_marker(pytest.mark.timeout(1200))
