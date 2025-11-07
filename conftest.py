import atexit
import os
import shutil
import tempfile
import uuid
from pathlib import Path
from typing import Set

import pytest

# Global set to track all test-created files and directories
_test_created_files: Set[str] = set()
_test_created_dirs: Set[str] = set()


def pytest_configure(config):
    """Configure pytest to use a custom temp directory in the project root.

    This avoids Windows permission issues with the default system temp directory,
    especially when using pytest-xdist for parallel test execution.
    """
    # Set custom basetemp in project root to avoid Windows permission issues
    project_root = Path(__file__).parent
    custom_temp = project_root / ".pytest_tmp"

    # Create the directory if it doesn't exist, handling race conditions
    try:
        custom_temp.mkdir(exist_ok=True, parents=True)
    except FileExistsError:
        # Another worker already created it, that's fine
        pass

    # Configure pytest to use this directory
    config.option.basetemp = str(custom_temp)


def register_test_file(filepath: str) -> str:
    """Register a file as test-created for cleanup."""
    abs_path = os.path.abspath(filepath)
    _test_created_files.add(abs_path)
    return filepath


def register_test_dir(dirpath: str) -> str:
    """Register a directory as test-created for cleanup."""
    abs_path = os.path.abspath(dirpath)
    _test_created_dirs.add(abs_path)
    return dirpath


def create_test_file(content: str, prefix: str = "test", extension: str = "py", directory: str = None) -> str:
    """Create a test file that will be automatically cleaned up."""
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}_{unique_id}.{extension}"
    if directory:
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
    else:
        filepath = filename
    with open(filepath, "w", encoding="utf-8") as f:
        f.write(content)
    return register_test_file(filepath)


def create_test_dir(prefix: str = "test_dir") -> str:
    """Create a test directory that will be automatically cleaned up."""
    unique_id = str(uuid.uuid4())[:8]
    dirname = f"{prefix}_{unique_id}"
    os.makedirs(dirname, exist_ok=True)
    return register_test_dir(dirname)


def cleanup_test_artifacts():
    """Clean up all registered test artifacts."""
    # Clean up files
    for filepath in _test_created_files.copy():
        try:
            if os.path.exists(filepath):
                os.remove(filepath)
                print(f"Cleaned up test file: {filepath}")
        except Exception as e:
            print(f"Warning: Could not clean up {filepath}: {e}")
        finally:
            _test_created_files.discard(filepath)
    # Clean up directories
    for dirpath in _test_created_dirs.copy():
        try:
            if os.path.exists(dirpath):
                shutil.rmtree(dirpath)
                print(f"Cleaned up test directory: {dirpath}")
        except Exception as e:
            print(f"Warning: Could not clean up {dirpath}: {e}")
        finally:
            _test_created_dirs.discard(dirpath)


# Register cleanup function to run at exit
atexit.register(cleanup_test_artifacts)


@pytest.fixture(scope="session", autouse=True)
def cleanup_session():
    """Session-level fixture to ensure cleanup happens."""
    yield
    cleanup_test_artifacts()


@pytest.fixture(autouse=True)
def patch_input_with_esc_for_tests(monkeypatch):
    """Automatically patch input_with_esc to use builtins.input in tests.

    This prevents tests from hanging when they mock builtins.input, since
    input_with_esc() uses platform-specific keyboard input that doesn't
    call builtins.input.

    This fixture runs automatically for all tests.
    """
    from bots.dev import cli

    # Replace input_with_esc with standard input for test compatibility
    def test_input_with_esc(prompt: str = "") -> str:
        return input(prompt)

    monkeypatch.setattr(cli, "input_with_esc", test_input_with_esc)
    yield


@pytest.fixture
def test_file_factory():
    """Factory fixture for creating test files."""
    return create_test_file


@pytest.fixture
def test_dir_factory():
    """Factory fixture for creating test directories."""
    return create_test_dir


@pytest.fixture
def safe_temp_dir():
    """Create a temporary directory that will be automatically cleaned up."""
    temp_dir = tempfile.mkdtemp(prefix="pytest_temp_")
    register_test_dir(temp_dir)
    yield temp_dir
    # Cleanup happens automatically via atexit


@pytest.fixture
def safe_temp_file():
    """Create a temporary file that will be automatically cleaned up."""
    fd, temp_file = tempfile.mkstemp(prefix="pytest_temp_", suffix=".py")
    os.close(fd)  # Close the file descriptor
    register_test_file(temp_file)
    yield temp_file
    # Cleanup happens automatically via atexit


def pytest_addoption(parser):
    """Add custom command line options."""
    parser.addoption(
        "--no-cleanup",
        action="store_true",
        default=False,
        help="Disable automatic cleanup of test files (useful for debugging)",
    )


def pytest_runtest_teardown(item, nextitem):
    """Clean up after each test."""
    # This runs after each test, but we'll rely on the session cleanup
    # for now to avoid interfering with tests that need files between test methods
    pass


def pytest_sessionfinish(session, exitstatus):
    """Clean up at the end of the test session."""
    cleanup_test_artifacts()

    # Note: We don't clean up .pytest_tmp here because with pytest-xdist,
    # multiple workers share this directory. Cleaning it up when one worker
    # finishes would break other workers that are still running.
    # The directory will be cleaned up on the next pytest run when
    # pytest_configure creates a fresh one.


@pytest.fixture
def clean_otel_env(monkeypatch):
    """Clean OpenTelemetry-related environment variables for testing.

    This fixture removes all OpenTelemetry and bots-specific environment
    variables to ensure tests start with a clean slate. This prevents
    environment variables from the host system from affecting test results.

    Use this fixture in tests that need to verify default configuration
    or test specific environment variable combinations.

    Example:
        def test_my_config(clean_otel_env, monkeypatch):
            monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
            # Test with clean environment
    """
    # List of all OpenTelemetry and bots-related env vars to clean
    otel_env_vars = [
        "OTEL_SDK_DISABLED",
        "OTEL_SERVICE_NAME",
        "OTEL_EXPORTER_OTLP_ENDPOINT",
        "OTEL_EXPORTER_OTLP_PROTOCOL",
        "OTEL_EXPORTER_OTLP_HEADERS",
        "OTEL_TRACES_EXPORTER",
        "OTEL_METRICS_EXPORTER",
        "OTEL_LOGS_EXPORTER",
        "BOTS_OTEL_EXPORTER",
        "BOTS_ENABLE_TRACING",
    ]

    # Remove each env var if it exists
    for var in otel_env_vars:
        monkeypatch.delenv(var, raising=False)

    yield

    # Cleanup happens automatically via monkeypatch