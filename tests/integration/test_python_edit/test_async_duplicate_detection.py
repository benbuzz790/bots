"""
Test for async method duplicate overwrite in Issue #160/#210
"""

import os
import tempfile

from bots.tools.python_edit import python_edit


def test_duplicate_async_method_detection():
    """Test that duplicate async methods are overwritten."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_async.py")

        # Add a class with two methods, one async
        _ = python_edit(
            test_file,
            """
class MyClass:
    def other_method(self):
        return "other"

    async def my_async_method(self):
        return "original"
""",
        )

        # Try to add the same async method again to the class - should overwrite
        # Insert after other_method (which won't be removed)
        result2 = python_edit(
            f"{test_file}::MyClass",
            """
async def my_async_method(self):
    return "duplicate"
""",
            coscope_with="other_method",
        )

        # Check that overwrite message is present
        assert "overwrote" in result2.lower(), f"Expected overwrite message, got: {result2}"

        # Verify the file content - should only have one my_async_method with "duplicate"
        with open(test_file, "r") as f:
            content = f.read()

        # Should have only one my_async_method definition
        assert content.count("async def my_async_method") == 1, f"Expected only one my_async_method, got: {content}"
        # Should have "duplicate" (new), not "original" (old)
        assert 'return "duplicate"' in content, f"Expected new code in content, got: {content}"
        assert 'return "original"' not in content, f"Expected old code to be removed, got: {content}"
        # other_method should still exist
        assert "def other_method" in content, f"Expected other_method to remain, got: {content}"

        print(f"✓ Async method overwrite successful: {result2}")


if __name__ == "__main__":
    test_duplicate_async_method_detection()
    print("\n✓ Async method duplicate overwrite test passed!")
