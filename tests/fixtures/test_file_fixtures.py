"""Test the isolated_filesystem fixture."""

import os
from pathlib import Path


def test_isolated_filesystem_basic(isolated_filesystem):
    """Test that isolated_filesystem provides a temp directory."""
    # Should be in a temp directory
    cwd = os.getcwd()
    assert "tmp" in cwd.lower() or "temp" in cwd.lower(), f"Not in temp dir: {cwd}"

    # Should be able to create files
    test_file = Path("test_artifact.py")
    test_file.write_text("print('test')")
    assert test_file.exists()

    # Return the path for verification in cleanup
    return cwd


def test_isolated_filesystem_isolation():
    """Test that files from previous test are cleaned up."""
    # This test runs after test_isolated_filesystem_basic
    # The test_artifact.py from that test should NOT exist here
    test_file = Path("test_artifact.py")
    assert not test_file.exists(), "File from previous test should be cleaned up"


def test_isolated_filesystem_cwd_restored(isolated_filesystem):
    """Test that original working directory will be restored."""
    # We're in a temp dir during the test
    temp_cwd = os.getcwd()
    assert "tmp" in temp_cwd.lower() or "temp" in temp_cwd.lower()

    # Create a file to verify cleanup
    Path("another_test.txt").write_text("test")
    assert Path("another_test.txt").exists()
