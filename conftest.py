import atexit
import os
import shutil
import tempfile
import time
import uuid
from pathlib import Path
from typing import Set

import pytest

# Global set to track all test-created files and directories
_test_created_files: Set[str] = set()
_test_created_dirs: Set[str] = set()


def pytest_configure(config):
    """Configure pytest with custom temp directory handling."""
    # Get the project root (where conftest.py is located)
    project_root = Path(__file__).parent

    # Define temp directory path
    temp_dir = project_root / ".pytest_tmp"

    # Try to handle existing directory
    if temp_dir.exists():
        try:
            # Try to remove it
            shutil.rmtree(temp_dir)
        except (PermissionError, OSError):
            # If locked, rename it with timestamp
            timestamp = int(time.time())
            locked_dir = project_root / f".pytest_tmp_locked_{timestamp}"
            try:
                temp_dir.rename(locked_dir)
            except (PermissionError, OSError):
                pass  # If rename fails, pytest will handle directory creation

    # Create fresh temp directory
    temp_dir.mkdir(exist_ok=True)

    # Configure pytest to use this directory - THIS IS THE KEY LINE!
    config.option.basetemp = str(temp_dir)

    # Set PYTEST_TEMP_DIR for tests to use
    os.environ["PYTEST_TEMP_DIR"] = str(temp_dir)

    # Only register cleanup in main process (not in xdist workers)
    if not hasattr(config, "workerinput"):

        def cleanup_temp_on_exit():
            """Clean up temp directory when Python exits."""
            try:
                # Give a moment for any lingering file handles to close
                time.sleep(0.2)

                # Remove all worker subdirectories
                if temp_dir.exists():
                    for item in temp_dir.iterdir():
                        if item.is_dir():
                            try:
                                shutil.rmtree(item)
                            except (PermissionError, OSError):
                                pass  # Ignore if still locked
            except (PermissionError, OSError):
                pass  # Ignore cleanup failures

        atexit.register(cleanup_temp_on_exit)

    # Clean up old locked directories (older than 1 hour)
    if not hasattr(config, "workerinput"):
        for old_dir in project_root.glob(".pytest_tmp_locked_*"):
            try:
                if old_dir.is_dir():
                    # Only try to remove if it's older than 1 hour
                    dir_age = time.time() - old_dir.stat().st_mtime
                    if dir_age > 3600:  # 1 hour
                        shutil.rmtree(old_dir)
            except Exception:
                # Ignore cleanup failures
                pass


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

    # Give Windows a moment to release file handles
    time.sleep(0.1)

    # Note: We don't clean up .pytest_tmp here because with pytest-xdist,
    # multiple workers share this directory. Even in the main process,
    # workers may not have fully released their file handles yet.
    # The directory will be cleaned up on the next pytest run when
    # pytest_configure detects it and either:
    # 1. Successfully removes it (if unlocked)
    # 2. Renames it and creates a fresh one (if still locked)
    # Old locked directories are cleaned up after 1 hour.


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


def get_unique_filename(prefix="test", extension="py"):
    """Generate a unique filename for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}.{extension}"


def create_safe_test_file(content, prefix="test", extension="py", directory=None):
    """Create a safe test file with given content in specified or temp directory."""
    if directory is None:
        # Create in temp directory
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{extension}", prefix=f"{prefix}_", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            return f.name
    else:
        # Create in specified directory
        if directory == "tmp":
            # Use system temp directory
            directory = tempfile.gettempdir()

        # Ensure directory exists
        os.makedirs(directory, exist_ok=True)

        # Generate unique filename
        filename = get_unique_filename(prefix, extension)
        filepath = os.path.join(directory, filename)

        # Write content to file
        with open(filepath, "w", encoding="utf-8") as f:
            f.write(content)

        return filepath
