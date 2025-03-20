import os
import time
import tempfile
import shutil
from datetime import datetime
import pytest
from bots.utils.helpers import _get_new_files

@pytest.fixture
def temp_dir():
    """Create a temporary directory for file testing"""
    temp_dir = tempfile.mkdtemp()
    yield temp_dir
    shutil.rmtree(temp_dir)

def create_file(path, content='', sleep_after=0.1):
    """Helper to create a file and optionally wait"""
    with open(path, 'w') as f:
        f.write(content)
    time.sleep(sleep_after)

def test_get_new_files_basic(temp_dir):
    """Test basic functionality with a single file"""
    start_time = time.time()
    time.sleep(0.1)
    test_file = os.path.join(temp_dir, 'test.txt')
    create_file(test_file)
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 1
    assert os.path.basename(new_files[0]) == 'test.txt'

def test_get_new_files_multiple_times(temp_dir):
    """Test with files created before and after start time"""
    old_file = os.path.join(temp_dir, 'old.txt')
    create_file(old_file)
    start_time = time.time()
    time.sleep(0.1)
    new_file1 = os.path.join(temp_dir, 'new1.txt')
    new_file2 = os.path.join(temp_dir, 'new2.txt')
    create_file(new_file1)
    create_file(new_file2)
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 2
    filenames = [os.path.basename(f) for f in new_files]
    assert 'new1.txt' in filenames
    assert 'new2.txt' in filenames
    assert 'old.txt' not in filenames

def test_get_new_files_extension_filter(temp_dir):
    """Test extension filtering"""
    start_time = time.time()
    time.sleep(0.1)
    create_file(os.path.join(temp_dir, 'test.txt'))
    create_file(os.path.join(temp_dir, 'test.py'))
    create_file(os.path.join(temp_dir, 'test.json'))
    txt_files = _get_new_files(start_time, temp_dir, extension='.txt')
    assert len(txt_files) == 1
    assert os.path.basename(txt_files[0]) == 'test.txt'
    py_files = _get_new_files(start_time, temp_dir, extension='.py')
    assert len(py_files) == 1
    assert os.path.basename(py_files[0]) == 'test.py'

def test_get_new_files_subdirectories(temp_dir):
    """Test handling of subdirectories"""
    subdir = os.path.join(temp_dir, 'subdir')
    os.makedirs(subdir)
    start_time = time.time()
    time.sleep(0.1)
    create_file(os.path.join(temp_dir, 'root.txt'))
    create_file(os.path.join(subdir, 'sub.txt'))
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 2
    filenames = [os.path.basename(f) for f in new_files]
    assert 'root.txt' in filenames
    assert 'sub.txt' in filenames

def test_get_new_files_empty_directory(temp_dir):
    """Test behavior with empty directory"""
    start_time = time.time()
    new_files = _get_new_files(start_time, temp_dir)
    assert len(new_files) == 0

def test_get_new_files_no_extension_filter(temp_dir):
    """Test behavior when extension is None"""
    start_time = time.time()
    time.sleep(0.1)
    create_file(os.path.join(temp_dir, 'test.txt'))
    create_file(os.path.join(temp_dir, 'test.py'))
    new_files = _get_new_files(start_time, temp_dir, extension=None)
    assert len(new_files) == 2
    filenames = [os.path.basename(f) for f in new_files]
    assert 'test.txt' in filenames
    assert 'test.py' in filenames