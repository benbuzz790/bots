import glob
import os
import shutil


def cleanup_test_artifacts():
    """Clean up test artifacts that may be left behind after test runs."""
    cleanup_patterns = [
        "test_patch_file.txt*",
        "test_clone_dir_*",
        "temp_test_repo_*",
        "test.txt",
        "lazy_*.py",
        "*.tmp",
        "temp_*",
        "*.bot",
        "ps_output*.txt",
        "minimal.py",
        "CICD.bot",
        "Claude.bot",
        "**/*_test_output*",
        "**/test_workspace_*",
        "**/*.pyc",
        "**/__pycache__",
    ]
    cleanup_dirs = [
        "test_patch_file.txt_dir",
        "test_patch_file.txt_newdir",
        ".pytest_cache",
        "__pycache__",
    ]
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
    print("Test artifact cleanup complete.")


def pytest_sessionfinish(session, exitstatus):
    """Pytest hook that runs after all tests complete."""
    cleanup_test_artifacts()


def pytest_runtest_teardown(item, nextitem):
    """Pytest hook that runs after each test."""
    # Quick cleanup of common LLM-generated files
    quick_patterns = ["*.tmp", "temp_*", "test_output_*"]
    for pattern in quick_patterns:
        for file_path in glob.glob(pattern):
            try:
                if os.path.isfile(file_path):
                    os.remove(file_path)
            except Exception:
                pass  # Ignore errors for quick cleanup


if __name__ == "__main__":
    cleanup_test_artifacts()
