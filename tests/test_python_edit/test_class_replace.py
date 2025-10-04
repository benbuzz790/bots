import sys
import tempfile
import os
from pathlib import Path

from bots.tools.python_edit import python_edit

# Create a temporary directory for this test
with tempfile.TemporaryDirectory() as temp_dir:
    # Create the test file in the temp directory
    test_file_path = Path(temp_dir) / "test_replace_behavior.py"

    # Write initial content to the test file
    initial_content = '''class TestClass:
    def old_method(self):
        return "old class"

    def another_method(self):
        return "another"
'''
    test_file_path.write_text(initial_content)

    print("=== Test 2: Replace entire class ===")
    print(f"Test file created at: {test_file_path}")

    # Perform the replacement
    result = python_edit(
        target_scope=f"{test_file_path}::TestClass",
        code='class TestClass:\n    def new_method(self):\n        return "completely new class"',
    )
    print("Result:", result)

    # Read and display the result
    with open(test_file_path, "r") as f:
        content = f.read()
    print("File content after class replacement:")
    print(content)

    print(f"\nTest completed. Temp directory will be cleaned up automatically.")
