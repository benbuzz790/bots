import tempfile
from pathlib import Path

from bots.tools.python_edit import python_edit
import pytest


pytestmark = pytest.mark.integration

def test_class_method_replacement():
    """Test replacing a method in a class using python_edit."""
    # Use a temporary directory for the test file
    with tempfile.TemporaryDirectory() as temp_dir:
        # Create the test file in the temp directory
        test_file = Path(temp_dir) / "test_replace_behavior.py"

        # Initial content with a sample class
        initial_content = """class TestClass:
    def existing_method(self):
        return "original"
"""
        test_file.write_text(initial_content)

        # Test: Replace the existing_method
        result = python_edit(
            target_scope=f"{test_file}::TestClass::existing_method",
            code='''def existing_method(self):
        return "replaced"''',
        )

        print("Result:", result)

        # Verify the replacement
        content = test_file.read_text()
        print("File content after replacement:")
        print(content)

        # Basic assertion
        assert "replaced" in content
        assert "original" not in content

        print("\nTest completed. Temp directory will be cleaned up automatically.")
