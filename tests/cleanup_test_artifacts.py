import os
import shutil
import glob

def cleanup_test_artifacts():
    """Clean up test artifacts that may be left behind after test runs."""
    cleanup_patterns = ['test_patch_file.txt*', 'benbuzz790/private_tests', 'test.txt', 'lazy_*.py', '*.tmp', 'temp_*']
    cleanup_dirs = ['test_patch_file.txt_dir', 'test_patch_file.txt_newdir']
    print("Cleaning up test artifacts...")
    # Clean up files matching patterns
    for pattern in cleanup_patterns:
        for file_path in glob.glob(pattern, recursive=True):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
                    print(f"Removed file: {file_path}")
                elif os.path.isdir(file_path):
                    shutil.rmtree(file_path)
                    print(f"Removed directory: {file_path}")
            except Exception as e:
                print(f"Warning: Could not remove {file_path}: {e}")
    # Clean up specific directories
    for dir_path in cleanup_dirs:
        try:
            if os.path.exists(dir_path):
                shutil.rmtree(dir_path)
                print(f"Removed directory: {dir_path}")
        except Exception as e:
            print(f"Warning: Could not remove {dir_path}: {e}")
    # Clean up pytest cache
    try:
        if os.path.exists('.pytest_cache'):
            shutil.rmtree('.pytest_cache')
            print("Removed .pytest_cache directory")
    except Exception as e:
        print(f"Warning: Could not remove .pytest_cache: {e}")
    print("Test artifact cleanup complete.")
if __name__ == '__main__':
    cleanup_test_artifacts()