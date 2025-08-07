import pytest
import subprocess
import sys
import os
import tempfile
import shutil
from pathlib import Path
import atexit
import uuid
from typing import Set, List


# Global set to track all test-created files and directories
_test_created_files: Set[str] = set()
_test_created_dirs: Set[str] = set()


def is_docker_available():
    """Check if Docker is installed and running."""
    try:
        result = subprocess.run(['docker', '--version'], 
                              capture_output=True, text=True, timeout=5)
        return result.returncode == 0
    except (subprocess.TimeoutExpired, FileNotFoundError, subprocess.SubprocessError):
        return False


def is_running_in_docker():
    """Check if we're already running inside a Docker container."""
    return os.path.exists('/.dockerenv') or os.path.exists('/proc/self/cgroup')


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


def create_test_file(content: str, prefix: str = "test", extension: str = "py", 
                    directory: str = None) -> str:
    """Create a test file that will be automatically cleaned up."""
    unique_id = str(uuid.uuid4())[:8]
    filename = f"{prefix}_{unique_id}.{extension}"

    if directory:
        os.makedirs(directory, exist_ok=True)
        filepath = os.path.join(directory, filename)
    else:
        filepath = filename

    with open(filepath, 'w', encoding='utf-8') as f:
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


def pytest_configure(config):
    """Configure pytest to use Docker if available and not already in container."""
    # Skip if already in Docker or if Docker not available
    if is_running_in_docker() or not is_docker_available():
        return

    # Skip if user explicitly disabled Docker mode
    if config.getoption("--no-docker", default=False):
        return

    # Skip if user wants to run in Docker mode
    if not config.getoption("--use-docker", default=False):
        return

    print("🐳 Docker detected! Re-running tests in container...")

    # Build container if needed
    build_result = subprocess.run(['docker', 'build', '-t', 'pytest-container', '.'],
                                capture_output=True, text=True)

    if build_result.returncode != 0:
        print(f"❌ Failed to build Docker container: {build_result.stderr}")
        return

    # Get original pytest arguments
    original_args = sys.argv[1:]  # Remove script name
    # Remove our custom Docker flags
    filtered_args = [arg for arg in original_args 
                    if not arg.startswith('--use-docker') and not arg.startswith('--no-docker')]

    # Run tests in Docker - fix Windows TTY issues and pass environment variables
    docker_cmd = ['docker', 'run', '--rm', '--env-file', '.env', 'pytest-container', 
                  'python', '-m', 'pytest'] + filtered_args

    print(f"Running: {' '.join(docker_cmd)}")

    # Use different approach for Windows to avoid TTY issues
    if os.name == 'nt':  # Windows
        # Don't use -it flags on Windows, and handle encoding properly
        result = subprocess.run(docker_cmd, 
                              encoding='utf-8', 
                              errors='replace',
                              text=True)
    else:
        result = subprocess.run(docker_cmd)

    # Exit with same code as Docker container
    sys.exit(result.returncode)


def pytest_addoption(parser):
    """Add Docker-related command line options."""
    parser.addoption(
        "--use-docker",
        action="store_true",
        default=False,
        help="Force running tests in Docker container"
    )
    parser.addoption(
        "--no-docker", 
        action="store_true",
        default=False,
        help="Disable Docker mode even if Docker is available"
    )
    parser.addoption(
        "--no-cleanup",
        action="store_true", 
        default=False,
        help="Disable automatic cleanup of test files (useful for debugging)"
    )


def pytest_runtest_teardown(item, nextitem):
    """Clean up after each test."""
    # This runs after each test, but we'll rely on the session cleanup
    # for now to avoid interfering with tests that need files between test methods
    pass


def pytest_sessionfinish(session, exitstatus):
    """Clean up at the end of the test session."""
    cleanup_test_artifacts()