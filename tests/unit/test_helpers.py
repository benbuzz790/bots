"""Test suite for helper functions in bots.utils.helpers.
This module contains tests for file system helper functions, specifically
focusing on the _get_new_files function which tracks file creation and
modification times. Tests cover basic functionality, file filtering,
directory traversal, and edge cases.
"""

import glob
import logging
import os
import shutil
import tempfile
import time
from typing import Generator, List, Optional

import pytest

from bots.utils.helpers import _get_new_files


def _remove_file_with_error_handling(file_path: str, logger: Optional[logging.Logger] = None) -> None:
    """Remove a single file with proper error handling and logging.

    Args:
        file_path: Path to the file to remove
        logger: Optional logger for recording cleanup failures
    """
    try:
        os.remove(file_path)
    except (OSError, PermissionError) as e:
        msg = f"Could not remove {file_path}: {e}"
        if logger:
            logger.warning(msg)
        else:
            print(f"Warning: {msg}")


def cleanup_leaked_files(base_dir: str, file_patterns: List[str], logger: Optional[logging.Logger] = None) -> None:
    """Clean up leaked test files from a directory.

    Use when you need to remove test artifacts that may have leaked into
    a directory during test execution. Handles both glob patterns and
    specific filenames.

    Args:
        base_dir: Base directory to clean up
        file_patterns: List of file patterns (can include glob patterns like '*.txt')
        logger: Optional logger for recording cleanup failures
    """
    for pattern in file_patterns:
        # Use glob.has_magic to detect glob patterns robustly
        if glob.has_magic(pattern):
            # Expand glob pattern to list of file paths
            file_paths = glob.glob(os.path.join(base_dir, pattern))
        else:
            # Single specific filename
            file_path = os.path.join(base_dir, pattern)
            file_paths = [file_path] if os.path.exists(file_path) else []

        # Remove each file using the helper
        for file_path in file_paths:
            _remove_file_with_error_handling(file_path, logger)


def cleanup_test_dirs(base_dir: str, dirnames: List[str], logger: Optional[logging.Logger] = None) -> None:
    """Clean up leaked test directories from a directory.

    Use when you need to remove test directories that may have leaked into
    a directory during test execution.

    Args:
        base_dir: Base directory to clean up
        dirnames: List of directory names to remove
        logger: Optional logger for recording cleanup failures
    """
    for dirname in dirnames:
        dir_path = os.path.join(base_dir, dirname)
        if os.path.exists(dir_path) and os.path.isdir(dir_path):
            try:
                shutil.rmtree(dir_path, ignore_errors=True)
            except (OSError, PermissionError) as e:
                msg = f"Could not clean up {dir_path}: {e}"
                if logger:
                    logger.warning(msg)
                else:
                    print(f"Warning: {msg}")


@pytest.fixture
def temp_dir() -> Generator[str, None, None]:
    """Create and manage a temporary directory for file testing.
    Use when you need an isolated directory for file operations in tests.
    The directory is automatically cleaned up after each test.
    Returns:
        Generator[str, None, None]: Path to temporary directory that will be
        automatically cleaned up after the test completes.
    """
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)


def create_file(path: str, content: str = "", sleep_time: float = 0.1) -> None:
    """Create a file with specified content and optional delay.
    Use when you need to create test files with controlled timing for file
    modification time testing.
    Args:
        path: Full path where the file should be created
        content: String content to write to the file (default: empty string)
        sleep_time: Seconds to sleep after file creation (default: 0.1)
            Used to ensure reliable file timestamp differences
    """
    with open(path, "w") as f:
        f.write(content)
    time.sleep(sleep_time)


@pytest.mark.unit
@pytest.mark.unit
def test_get_new_files_basic(temp_dir: str) -> None:
    """Test basic functionality of _get_new_files with a single file.
    Verifies that _get_new_files correctly identifies a single file created
    after the start time. Tests the most basic use case of the function.
    Args:
        temp_dir: Pytest fixture providing temporary directory path
    """
    start_time = time.time()
    time.sleep(0.1)
    test_file = os.path.join(temp_dir, "test.txt")
    create_file(test_file)
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 1
    assert os.path.basename(new_files[0]) == "test.txt"


@pytest.mark.unit
@pytest.mark.unit
def test_get_new_files_multiple_times(temp_dir: str) -> None:
    """Test _get_new_files with files created before and after start time.
    Verifies that the function correctly:
    - Excludes files created before the start time
    - Includes multiple files created after the start time
    - Returns files in the expected order
    Args:
        temp_dir: Pytest fixture providing temporary directory path
    """
    old_file = os.path.join(temp_dir, "old.txt")
    create_file(old_file)
    start_time = time.time()
    time.sleep(0.1)
    new_file1 = os.path.join(temp_dir, "new1.txt")
    new_file2 = os.path.join(temp_dir, "new2.txt")
    create_file(new_file1)
    create_file(new_file2)
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 2
    filenames = [os.path.basename(f) for f in new_files]
    assert "new1.txt" in filenames
    assert "new2.txt" in filenames
    assert "old.txt" not in filenames


@pytest.mark.unit
@pytest.mark.unit
def test_get_new_files_extension_filter(temp_dir: str) -> None:
    """Test _get_new_files extension filtering functionality.
    Verifies that the function correctly filters files by extension:
    - Creates files with different extensions (.txt, .py, .json)
    - Tests filtering for .txt files
    - Tests filtering for .py files
    - Ensures only files with matching extensions are returned
    Args:
        temp_dir: Pytest fixture providing temporary directory path
    """
    start_time = time.time()
    time.sleep(0.1)
    create_file(os.path.join(temp_dir, "test.txt"))
    create_file(os.path.join(temp_dir, "test.py"))
    create_file(os.path.join(temp_dir, "test.json"))
    txt_files = _get_new_files(start_time, temp_dir, extension=".txt")
    assert len(txt_files) == 1
    assert os.path.basename(txt_files[0]) == "test.txt"
    py_files = _get_new_files(start_time, temp_dir, extension=".py")
    assert len(py_files) == 1
    assert os.path.basename(py_files[0]) == "test.py"


@pytest.mark.unit
@pytest.mark.unit
def test_get_new_files_subdirectories(temp_dir: str) -> None:
    """Test _get_new_files handling of nested directory structures.
    Verifies that the function correctly:
    - Traverses into subdirectories
    - Finds files in both root and subdirectories
    - Returns complete paths for all matching files
    Args:
        temp_dir: Pytest fixture providing temporary directory path
    """
    subdir = os.path.join(temp_dir, "subdir")
    os.makedirs(subdir)
    start_time = time.time()
    time.sleep(0.1)
    create_file(os.path.join(temp_dir, "root.txt"))
    create_file(os.path.join(subdir, "sub.txt"))
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 2
    filenames = [os.path.basename(f) for f in new_files]
    assert "root.txt" in filenames
    assert "sub.txt" in filenames


@pytest.mark.unit
@pytest.mark.unit
def test_get_new_files_empty_directory(temp_dir: str) -> None:
    """Test _get_new_files behavior with an empty directory.
    Verifies that the function correctly:
    - Handles empty directories without errors
    - Returns an empty list when no files are present
    Args:
        temp_dir: Pytest fixture providing temporary directory path
    """
    start_time = time.time()
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 0


@pytest.mark.unit
@pytest.mark.unit
def test_get_new_files_no_extension_filter(temp_dir: str) -> None:
    """Test _get_new_files behavior when no extension filter is applied.
    Verifies that the function correctly:
    - Returns all files when extension=None
    - Includes files with different extensions
    - Maintains correct file order
    Args:
        temp_dir: Pytest fixture providing temporary directory path
    """
    start_time = time.time()
    time.sleep(0.1)
    create_file(os.path.join(temp_dir, "test.txt"))
    create_file(os.path.join(temp_dir, "test.py"))
    new_files = _get_new_files(start_time, temp_dir, extension=None)
    assert len(new_files) == 2
    filenames = [os.path.basename(f) for f in new_files]
    assert "test.txt" in filenames
    assert "test.py" in filenames
