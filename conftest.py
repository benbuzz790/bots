import atexit
import os
import shutil
import tempfile
import uuid
from typing import Set
import pytest
# Global set to track all test-created files and directories
_test_created_files: Set[str] = set()
_test_created_dirs: Set[str] = set()
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