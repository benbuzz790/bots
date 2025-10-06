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


def get_unique_filename(prefix="test", extension="py"):
    """Generate a unique filename for testing."""
    unique_id = str(uuid.uuid4())[:8]
    return f"{prefix}_{unique_id}.{extension}"
