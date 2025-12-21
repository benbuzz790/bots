"""
Test for Issue #160/#210: python_edit should overwrite duplicate definitions
"""

"""
Test for Issue #160: python_edit should warn when adding duplicate definitions
"""

import os
import tempfile

from bots.tools.python_edit import python_edit


def test_duplicate_class_detection():
    """Test that python_edit overwrites when adding a duplicate class."""
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

        # Try to add the same class again - should overwrite
        result2 = python_edit(
            test_file,
            """
class MyClass:
    def method2(self):
        return "duplicate"
""",
            coscope_with="__FILE_END__",
        )

        # Check that overwrite message is present
        assert "overwrote" in result2.lower(), f"Expected overwrite message, got: {result2}"

        # Verify the file content - should only have one MyClass with method2
        with open(test_file, "r") as f:
            content = f.read()

        # Should have only one MyClass definition
        assert content.count("class MyClass") == 1, f"Expected only one MyClass, got: {content}"
        # Should have method2 (new), not method1 (old)
        assert "method2" in content, f"Expected method2 in content, got: {content}"
        assert "method1" not in content, f"Expected method1 to be removed, got: {content}"

        print(f"✓ Class overwrite successful: {result2}")


def test_duplicate_function_detection():
    """Test that python_edit overwrites when adding a duplicate function."""
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

        # Try to add the same function again - should overwrite
        result2 = python_edit(
            test_file,
            """
def my_function():
    return "duplicate"
""",
            coscope_with="__FILE_END__",
        )

        # Check that overwrite message is present
        assert "overwrote" in result2.lower(), f"Expected overwrite message, got: {result2}"

        # Verify the file content - should only have one my_function with "duplicate"
        with open(test_file, "r") as f:
            content = f.read()

        # Should have only one my_function definition
        assert content.count("def my_function") == 1, f"Expected only one my_function, got: {content}"
        # Should have "duplicate" (new), not "original" (old)
        assert 'return "duplicate"' in content, f"Expected new code in content, got: {content}"
        assert 'return "original"' not in content, f"Expected old code to be removed, got: {content}"

        print(f"✓ Function overwrite successful: {result2}")


def test_duplicate_method_detection():
    """Test that python_edit overwrites when adding a duplicate method to a class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_method.py")

        # Create initial file with a class and two methods
        _ = python_edit(
            test_file,
            """
class MyClass:
    def other_method(self):
        return "other"

    def my_method(self):
        return "original"
""",
        )

        # Try to add the same method again to the class - should overwrite
        # Insert after other_method (which won't be removed)
        result2 = python_edit(
            f"{test_file}::MyClass",
            """
def my_method(self):
    return "duplicate"
""",
            coscope_with="other_method",
        )

        # Check that overwrite message is present
        assert "overwrote" in result2.lower(), f"Expected overwrite message, got: {result2}"

        # Verify the file content - should only have one my_method with "duplicate"
        with open(test_file, "r") as f:
            content = f.read()

        # Should have only one my_method definition
        assert content.count("def my_method") == 1, f"Expected only one my_method, got: {content}"
        # Should have "duplicate" (new), not "original" (old)
        assert 'return "duplicate"' in content, f"Expected new code in content, got: {content}"
        assert 'return "original"' not in content, f"Expected old code to be removed, got: {content}"
        # other_method should still exist
        assert "def other_method" in content, f"Expected other_method to remain, got: {content}"

        print(f"✓ Method overwrite successful: {result2}")


def test_no_warning_for_different_names():
    """Test that no overwrite occurs when adding different definitions."""
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

        # Add a different class - should not overwrite
        result2 = python_edit(
            test_file,
            """
class AnotherClass:
    def method2(self):
        return "second"
""",
            coscope_with="__FILE_END__",
        )

        # Check that no overwrite message is present
        assert "overwrote" not in result2.lower(), f"Should not overwrite for different class names, got: {result2}"

        # Verify both classes exist
        with open(test_file, "r") as f:
            content = f.read()

        assert "class MyClass" in content, f"Expected MyClass to remain, got: {content}"
        assert "class AnotherClass" in content, f"Expected AnotherClass to be added, got: {content}"

        print(f"✓ No overwrite for different names: {result2}")


def test_overwrite_removes_old_definition_completely():
    """Test that overwrite completely removes the old definition from its original location."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_removal.py")

        # Create initial file with multiple functions
        _ = python_edit(
            test_file,
            """
def function_a():
    return "a"

def function_b():
    return "b"

def function_c():
    return "c"
""",
        )

        # Add function_b again at the end - should remove the middle one
        result = python_edit(
            test_file,
            """
def function_b():
    return "b_new"
""",
            coscope_with="__FILE_END__",
        )

        # Check that overwrite message is present
        assert "overwrote" in result.lower(), f"Expected overwrite message, got: {result}"

        # Verify the file content
        with open(test_file, "r") as f:
            content = f.read()

        # Should have only one function_b definition
        assert content.count("def function_b") == 1, f"Expected only one function_b, got: {content}"
        # Should have the new version
        assert 'return "b_new"' in content, f"Expected new code, got: {content}"
        assert 'return "b"' not in content or content.count('return "b"') == 0, f"Expected old code removed, got: {content}"
        # Other functions should remain
        assert "def function_a" in content, f"Expected function_a to remain, got: {content}"
        assert "def function_c" in content, f"Expected function_c to remain, got: {content}"
        # function_b should be at the end (after function_c)
        pos_c = content.find("def function_c")
        pos_b = content.find("def function_b")
        assert pos_b > pos_c, f"Expected function_b after function_c, got: {content}"

        print(f"✓ Old definition completely removed: {result}")


def test_multiple_duplicates_all_removed():
    """Test that when multiple duplicates exist, all are removed."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_multiple.py")

        # Create file with duplicate functions (edge case)
        with open(test_file, "w") as f:
            f.write(
                """
def my_func():
    return "first"

def my_func():
    return "second"

def other_func():
    return "other"
"""
            )

        # Add my_func again - should remove both existing ones
        result = python_edit(
            test_file,
            """
def my_func():
    return "third"
""",
            coscope_with="__FILE_END__",
        )

        # Check that overwrite message is present
        assert "overwrote" in result.lower(), f"Expected overwrite message, got: {result}"

        # Verify the file content
        with open(test_file, "r") as f:
            content = f.read()

        # Should have only one my_func definition
        assert content.count("def my_func") == 1, f"Expected only one my_func, got: {content}"
        # Should have the new version
        assert 'return "third"' in content, f"Expected new code, got: {content}"
        assert 'return "first"' not in content, f"Expected first duplicate removed, got: {content}"
        assert 'return "second"' not in content, f"Expected second duplicate removed, got: {content}"
        # other_func should remain
        assert "def other_func" in content, f"Expected other_func to remain, got: {content}"

        print(f"✓ Multiple duplicates all removed: {result}")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Issue #160/#210 Fix: Duplicate Overwrite")
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

    try:
        test_overwrite_removes_old_definition_completely()
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed_tests.append("test_overwrite_removes_old_definition_completely")

    try:
        test_multiple_duplicates_all_removed()
    except AssertionError as e:
        print(f"✗ FAILED: {e}")
        failed_tests.append("test_multiple_duplicates_all_removed")

    print("\n" + "=" * 60)
    if failed_tests:
        print(f"FAILED: {len(failed_tests)} test(s) failed:")
        for test_name in failed_tests:
            print(f"  - {test_name}")
        print("=" * 60)
        exit(1)
    else:
        print("All tests passed! Issue #160/#210 is fixed - overwrites working correctly.")
        print("=" * 60)
