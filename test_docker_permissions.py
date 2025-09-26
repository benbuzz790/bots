import os
import subprocess


def test_file_writing_permissions():
    """Test that we can write files in various directories"""
    test_dirs = ["/app/test_output", "/app/temp_files", "/app/storage", "/app/logs", "/app"]  # Current working directory

    results = []

    for test_dir in test_dirs:
        try:
            # Test directory creation
            sub_dir = os.path.join(test_dir, "test_subdir")
            os.makedirs(sub_dir, exist_ok=True)

            # Test file writing
            test_file = os.path.join(sub_dir, "test_file.txt")
            with open(test_file, "w") as f:
                f.write("Test content from Docker container")

            # Test file reading
            with open(test_file, "r") as f:
                f.read()

            # Test PowerShell file operations (if available)
            try:
                ps_file = os.path.join(sub_dir, "powershell_test.txt")
                subprocess.run(
                    [
                        "python",
                        "-c",
                        f"import subprocess; subprocess.run(['echo', 'PowerShell test'], "
                        f"shell=True, stdout=open('{ps_file}', 'w'))",
                    ],
                    capture_output=True,
                    text=True,
                )
                ps_success = os.path.exists(ps_file)
            except Exception:
                ps_success = False

            results.append(f"✓ {test_dir}: Directory ✓, File write ✓, File read ✓, PS operations {'✓' if ps_success else '✗'}")

        except Exception as e:
            results.append(f"✗ {test_dir}: FAILED - {str(e)}")

    return results


if __name__ == "__main__":
    print("Testing Docker file writing permissions...")
    print("=" * 50)

    results = test_file_writing_permissions()
    for result in results:
        print(result)

    print("=" * 50)
    print("Test completed!")
