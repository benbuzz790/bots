"""
Test for Issue #160: python_edit should warn when adding duplicate definitions
"""

import os
import tempfile

from bots.tools.python_edit import python_edit


def test_duplicate_class_detection():
    """Test that python_edit warns when adding a duplicate class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_class.py")

        # Create initial file with a class
        _ = python_edit(
            test_file,
            """
class MyClass:
    def method1(self):
        return "original"
""",
        )

        # Try to add the same class again
        result2 = python_edit(
            test_file,
            """
class MyClass:
    def method2(self):
        return "duplicate"
""",
            coscope_with="__FILE_END__",
        )

        # Check if warning is present
        has_warning = ("warning" in result2.lower() and "duplicate" in result2.lower()) or "already exists" in result2.lower()
        assert has_warning, f"Expected warning about duplicate class, got: {result2}"
        print(f"✓ Class duplicate warning: {result2}")


def test_duplicate_function_detection():
    """Test that python_edit warns when adding a duplicate function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_func.py")

        # Create initial file with a function
        _ = python_edit(
            test_file,
            """
def my_function():
    return "original"
""",
        )

        # Try to add the same function again
        result2 = python_edit(
            test_file,
            """
def my_function():
    return "duplicate"
""",
            coscope_with="__FILE_END__",
        )

        # Check if warning is present
        has_warning = ("warning" in result2.lower() and "duplicate" in result2.lower()) or "already exists" in result2.lower()
        assert has_warning, f"Expected warning about duplicate function, got: {result2}"
        print(f"✓ Function duplicate warning: {result2}")


def test_duplicate_method_detection():
    """Test that python_edit warns when adding a duplicate method to a class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_method.py")

        # Create initial file with a class and method
        _ = python_edit(
            test_file,
            """
class MyClass:
    def my_method(self):
        return "original"
""",
        )

        # Try to add the same method again to the class
        result2 = python_edit(
            f"{test_file}::MyClass",
            """
def my_method(self):
    return "duplicate"
""",
            coscope_with="__FILE_END__",
        )

        # Check if warning is present
        has_warning = ("warning" in result2.lower() and "duplicate" in result2.lower()) or "already exists" in result2.lower()
        assert has_warning, f"Expected warning about duplicate method, got: {result2}"
        print(f"✓ Method duplicate warning: {result2}")


def test_no_warning_for_different_names():
    """Test that no warning is given when adding different definitions."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_no_duplicate.py")

        # Create initial file with a class
        _ = python_edit(
            test_file,
            """
class MyClass:
    def method1(self):
        return "first"
""",
        )

        # Add a different class - should not warn
        result2 = python_edit(
            test_file,
            """
class AnotherClass:
    def method2(self):
        return "second"
""",
            coscope_with="__FILE_END__",
        )

        # Check that no warning is present
        has_warning = "warning" in result2.lower() and "duplicate" in result2.lower()
        assert not has_warning, f"Should not warn for different class names, got: {result2}"
        print(f"✓ No warning for different names: {result2}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Issue #160 Fix: Duplicate Detection")
    print("=" * 60)

    failed_tests = []

    try:
        test_duplicate_class_detection()
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed_tests.append("test_duplicate_class_detection")

    try:
        test_duplicate_function_detection()
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed_tests.append("test_duplicate_function_detection")

    try:
        test_duplicate_method_detection()
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed_tests.append("test_duplicate_method_detection")

    try:
        test_no_warning_for_different_names()
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed_tests.append("test_no_warning_for_different_names")

    print("\n" + "=" * 60)
    if failed_tests:
        print(f"FAILED: {len(failed_tests)} test(s) failed:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print("=" * 60)
        exit(1)
    else:
        print("All tests passed! Issue #160 is fixed.")
        print("=" * 60)
