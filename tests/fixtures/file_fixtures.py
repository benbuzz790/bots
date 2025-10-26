"""File and directory fixtures for testing.

Provides temporary file/directory creation with automatic cleanup.
"""

import os
import tempfile
import uuid
from pathlib import Path

import pytest


@pytest.fixture
def temp_test_file():
    """Create a temporary test file that auto-cleans up.

    Returns a function that creates temp files with given content.
    All created files are automatically cleaned up after the test.

    Usage:
        def test_something(temp_test_file):
            filepath = temp_test_file("print('hello')", extension='py')
            # Use filepath...
            # Auto-cleanup happens after test
    """
    created_files = []

    def _create_file(content, prefix="test", extension="py"):
        """Create a temp file with given content."""
        with tempfile.NamedTemporaryFile(
            mode="w", suffix=f".{extension}", prefix=f"{prefix}_", delete=False, encoding="utf-8"
        ) as f:
            f.write(content)
            filepath = f.name
        created_files.append(filepath)
        return filepath

    yield _create_file

    # Cleanup
    for filepath in created_files:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass


@pytest.fixture
def temp_test_dir():
    """Create a temporary test directory that auto-cleans up.

    Returns a Path object for a temporary directory.
    The directory and all its contents are cleaned up after the test.

    Usage:
        def test_something(temp_test_dir):
            test_file = temp_test_dir / "test.py"
            test_file.write_text("print('hello')")
            # Use directory...
            # Auto-cleanup happens after test
    """
    temp_dir = tempfile.mkdtemp(prefix="test_")
    temp_path = Path(temp_dir)

    yield temp_path

    # Cleanup
    import shutil

    try:
        if temp_path.exists():
            shutil.rmtree(temp_path)
    except Exception:
        pass


@pytest.fixture
def cleanup_temp_files():
    """Track and cleanup temporary files created during tests.

    Returns a list that tests can append file paths to.
    All tracked files are automatically cleaned up after the test.

    Usage:
        def test_something(cleanup_temp_files):
            filepath = "temp_test.py"
            with open(filepath, 'w') as f:
                f.write("test")
            cleanup_temp_files.append(filepath)
            # Auto-cleanup happens after test
    """
    files_to_cleanup = []

    yield files_to_cleanup

    # Cleanup
    for filepath in files_to_cleanup:
        try:
            if os.path.exists(filepath):
                os.unlink(filepath)
        except Exception:
            pass


@pytest.fixture
def isolated_filesystem():
    """Create an isolated filesystem environment for tests.

    This fixture changes the current working directory to a temporary directory
    for the duration of the test, then restores the original working directory
    and cleans up all files created during the test.

    This is the recommended approach for tests that create files, especially
    E2E tests that use bots with file creation tools (python_edit, etc.).

    Benefits:
    ---------
    1. **Complete Isolation**: Tests can't accidentally modify real project files
    2. **No Artifact Pollution**: All created files are in temp dir, auto-cleaned
    3. **No Race Conditions**: Unlike snapshot-based approaches, this won't pick up
       files created by other processes during test execution
    4. **Simple for Tests**: Tests just create files normally, no special tracking

    Considerations:
    ---------------
    - Tests should use relative paths or os.getcwd() to find their working directory
    - Absolute paths to project files need to be resolved before entering the fixture
    - Perfect for E2E tests with bots that have file creation tools

    Usage:
    ------
        def test_bot_creates_files(isolated_filesystem):
            # Now in a temp directory
            bot.respond("Create a file called test.py")
            # File created in temp dir
            assert Path("test.py").exists()
            # After test: automatic cleanup, cwd restored

    Auto-usage:
    -----------
    This fixture is automatically used by all E2E tests via conftest.py
    to prevent test artifact pollution in the repository.

    Returns:
    --------
    Path
        Path object pointing to the temporary working directory
    """
    # Save original working directory
    original_cwd = os.getcwd()

    # Create temporary directory
    temp_dir = tempfile.mkdtemp(prefix="isolated_test_")
    temp_path = Path(temp_dir)

    # Change to temp directory
    os.chdir(temp_dir)

    try:
        yield temp_path
    finally:
        # Always restore original directory
        os.chdir(original_cwd)

        # Clean up temp directory
        try:
            if temp_path.exists():
                import shutil

                shutil.rmtree(temp_path)
        except Exception as e:
            # Log but don't fail the test if cleanup has issues
            print(f"Warning: Could not clean up isolated filesystem at {temp_path}: {e}")


def get_unique_filename(prefix="test", extension="py"):
    """Generate a unique filename for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}.{extension}"
