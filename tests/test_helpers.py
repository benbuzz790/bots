"""Test suite for helper functions in bots.utils.helpers.
This module contains tests for file system helper functions, specifically
focusing on the _get_new_files function which tracks file creation and
modification times. Tests cover basic functionality, file filtering,
directory traversal, and edge cases.
"""

import os
import shutil
import tempfile
import time
from typing import Generator

import pytest

from bots.utils.helpers import _get_new_files


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
