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

# Add tests directory to path for test-specific imports
tests_dir = project_root / "tests"
sys.path.insert(0, str(tests_dir))

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
            duration = time.time() - self.start_time

            # Get stats
            s = io.StringIO()
            ps = pstats.Stats(self.current_profile, stream=s)
            ps.sort_stats("cumulative")

            self.test_profiles.append(
                {
                    "test_name": self.current_test_name,
                    "duration": duration,
                    "outcome": outcome,
                    "stats": ps,
                    "stats_str": s.getvalue(),
                }
            )
        finally:
            self.current_profile = None
            self.current_test_name = None
            self.start_time = None

    def get_slowest_tests(self, n=10):
        """Get the n slowest tests."""
        sorted_tests = sorted(self.test_profiles, key=lambda x: x["duration"], reverse=True)
        return sorted_tests[:n]


# Global profiler instance
_profiler = TestProfiler()


def pytest_configure(config):
    """Register custom markers."""
    config.addinivalue_line("markers", "profile: mark test to be profiled")
    config.addinivalue_line("markers", "slow: mark test as slow running")
    config.addinivalue_line("markers", "integration: mark test as integration test")
    config.addinivalue_line("markers", "e2e: mark test as end-to-end test")
    config.addinivalue_line("markers", "no_isolation: mark test to run without process isolation")


# Profiling hooks disabled to avoid pytest hookwrapper issues
# @pytest.hookimpl(tryfirst=True)
# def pytest_runtest_protocol(item, nextitem):
#     """Profile tests marked with @pytest.mark.profile."""
#     if item.get_closest_marker("profile"):
#         _profiler.start_profiling(item.nodeid)


# @pytest.hookimpl(hookwrapper=True, trylast=True)
# def pytest_runtest_makereport(item, call):
#     """Stop profiling after test execution."""
#     outcome = yield
#     if item.get_closest_marker("profile") and call.when == "call":
#         report = outcome.get_result()
#         _profiler.stop_profiling("passed" if report.passed else "failed")


def pytest_sessionfinish(session, exitstatus):
    """Print profiling summary at end of session."""
    if _profiler.test_profiles:
        print("\n" + "=" * 80)
        print("PROFILING SUMMARY")
        print("=" * 80)

        slowest = _profiler.get_slowest_tests(10)
        print(f"\nTop {len(slowest)} slowest tests:")
        for i, test in enumerate(slowest, 1):
            print(f"{i}. {test['test_name']}: {test['duration']:.3f}s ({test['outcome']})")

        # Optionally write detailed stats to file
        if os.environ.get("WRITE_PROFILE_STATS"):
            profile_dir = Path("test_profiles")
            profile_dir.mkdir(exist_ok=True)

            for test in _profiler.test_profiles:
                safe_name = test["test_name"].replace("::", "_").replace("/", "_")
                profile_file = profile_dir / f"{safe_name}.txt"

                with open(profile_file, "w") as f:
                    f.write(f"Test: {test['test_name']}\n")
                    f.write(f"Duration: {test['duration']:.3f}s\n")
                    f.write(f"Outcome: {test['outcome']}\n")
                    f.write("\n" + "=" * 80 + "\n")
                    f.write(test["stats_str"])

            print(f"\nDetailed profiling stats written to {profile_dir}/")


# ============================================================================
# SHARED FIXTURES
# ============================================================================


@pytest.fixture
def temp_dir(tmp_path):
    """Provide a temporary directory for tests."""
    return tmp_path


@pytest.fixture
def clean_env(monkeypatch):
    """Provide a clean environment for tests."""
    # Remove any environment variables that might affect tests
    env_vars_to_remove = [
        "ANTHROPIC_API_KEY",
        "OPENAI_API_KEY",
        "GOOGLE_API_KEY",
    ]

    for var in env_vars_to_remove:
        monkeypatch.delenv(var, raising=False)

    return monkeypatch


@pytest.fixture(scope="session")
def test_profiler(request):
    """Session-scoped fixture for test profiling."""
    # Get or create the shared profiler instance from config
    if not hasattr(request.config, "_test_profiler"):
        request.config._test_profiler = TestProfiler()

    profiler = request.config._test_profiler

    # Register report generation at session end
    def generate_report():
        if profiler.test_profiles:
            slowest = profiler.get_slowest_tests(10)
            print("\n" + "=" * 80)
            print("TEST PROFILING REPORT")
            print("=" * 80)
            print(f"\nTop {len(slowest)} slowest tests:")
            for i, test in enumerate(slowest, 1):
                print(f"{i}. {test['test_name']}: {test['duration']:.3f}s")

    request.addfinalizer(generate_report)

    return profiler


# pytest_addoption removed - defined in tests/conftest.py instead


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
