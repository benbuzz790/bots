"""
Test for async method duplicate detection in Issue #160
"""

import os
import tempfile

from bots.tools.python_edit import python_edit


def test_duplicate_async_method_detection():
    """Test that duplicate async methods are detected."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_async.py")

        # Add a class with an async method
        _ = python_edit(
            test_file,
            """
class MyClass:
    async def my_async_method(self):
        return "original"
""",
        )

        # Try to add the same async method again to the class
        # Use coscope_with to insert after the existing method (triggers duplicate detection)
        result2 = python_edit(
            f"{test_file}::MyClass",
            """
async def my_async_method(self):
    return "duplicate"
""",
            coscope_with="my_async_method",
        )

        # Check if warning is present
        has_warning = ("warning" in result2.lower() and "duplicate" in result2.lower()) or "already exists" in result2.lower()
        assert has_warning, f"Expected warning about duplicate async method, got: {result2}"
        print(f"✓ Async method duplicate detection working: {result2}")


if __name__ == "__main__":
    test_duplicate_async_method_detection()
    print("\n✓ Async method duplicate detection test passed!")
