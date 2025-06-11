import os
import tempfile
import shutil
import pytest
from pathlib import Path
import glob
@pytest.fixture(autouse=True)
def track_and_cleanup_files():
    """Automatically track files created during tests and clean them up."""
    # Get initial state
    initial_files = set()
    for pattern in ['*.py', '*.txt', '*.bot', '*.tmp', '*.log']:
        initial_files.update(glob.glob(pattern))
        initial_files.update(glob.glob(f'**/{pattern}', recursive=True))
    # Also track specific directories that might be created
    initial_dirs = set()
    for root, dirs, files in os.walk('.'):
        if any(test_dir in root for test_dir in ['test_', 'temp_', 'tmp_']):
            initial_dirs.add(root)
    yield  # Run the test
    # Cleanup after test
    current_files = set()
    for pattern in ['*.py', '*.txt', '*.bot', '*.tmp', '*.log']:
        current_files.update(glob.glob(pattern))
        current_files.update(glob.glob(f'**/{pattern}', recursive=True))
    # Remove new files
    new_files = current_files - initial_files
    for file_path in new_files:
        try:
            if os.path.isfile(file_path):
                os.remove(file_path)
                print(f"Auto-cleaned: {file_path}")
        except Exception as e:
            print(f"Warning: Could not auto-clean {file_path}: {e}")
    # Remove new test directories
    current_dirs = set()
    for root, dirs, files in os.walk('.'):
        if any(test_dir in root for test_dir in ['test_', 'temp_', 'tmp_']):
            current_dirs.add(root)
    new_dirs = current_dirs - initial_dirs
    for dir_path in new_dirs:
        try:
            if os.path.isdir(dir_path):
                shutil.rmtree(dir_path)
                print(f"Auto-cleaned directory: {dir_path}")
        except Exception as e:
            print(f"Warning: Could not auto-clean {dir_path}: {e}")
@pytest.fixture
def temp_workspace():
    """Provide a temporary workspace for tests that gets automatically cleaned up."""
    temp_dir = tempfile.mkdtemp(prefix="test_workspace_")
    original_cwd = os.getcwd()
    yield temp_dir
    # Cleanup
    os.chdir(original_cwd)
    try:
        shutil.rmtree(temp_dir)
    except Exception as e:
        print(f"Warning: Could not clean temp workspace {temp_dir}: {e}")
