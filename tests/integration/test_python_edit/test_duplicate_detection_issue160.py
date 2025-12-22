"""
Test for Issue #160/#210: python_edit should overwrite duplicate definitions
"""

import os
import tempfile

from bots.tools.python_edit import python_edit


def test_duplicate_class_detection():
    """Test that python_edit overwrites when adding a duplicate class."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_class.py")

        # Create initial file with a class
        initial_content = """
class MyClass:
    def method1(self):
        return "original"
"""
        with open(test_file, "w") as f:
            f.write(initial_content)

        # Try to add a duplicate class - should overwrite
        new_class = """
class MyClass:
    def method2(self):
        return "new"
"""
        result = python_edit(test_file, new_class)

        # Check result - python_edit returns "Code replaced at..." message
        assert "Code replaced" in result

        # Verify file content - should have new class, not both
        with open(test_file, "r") as f:
            content = f.read()

        assert "method2" in content
        assert "method1" not in content  # Old method should be gone


def test_duplicate_function_detection():
    """Test that python_edit overwrites when adding a duplicate function."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_func.py")

        # Create initial file with a function
        initial_content = """
def my_function():
    return "original"
"""
        with open(test_file, "w") as f:
            f.write(initial_content)

        # Try to add a duplicate function - should overwrite
        new_function = """
def my_function():
    return "new"
"""
        result = python_edit(test_file, new_function)

        # Check result - python_edit returns "Code replaced at..." message
        assert "Code replaced" in result

        # Verify file content - should have new function, not both
        with open(test_file, "r") as f:
            content = f.read()

        assert content.count("def my_function") == 1
        assert '"new"' in content
        assert '"original"' not in content


def test_duplicate_method_detection():
    """Test that python_edit overwrites when adding a duplicate method."""
    with tempfile.TemporaryDirectory() as tmpdir:
        test_file = os.path.join(tmpdir, "test_duplicate_method.py")

        # Create initial file with a class and method
        initial_content = """
class MyClass:
    def my_method(self):
        return "original"
"""
        with open(test_file, "w") as f:
            f.write(initial_content)

        # Try to add a duplicate method - should overwrite
        new_method = """
def my_method(self):
    return "new"
"""
        result = python_edit(f"{test_file}::MyClass", new_method)

        # Check result - python_edit returns "Code replaced at..." message
        assert "Code replaced" in result

        # Verify file content - should have new method, not both
        with open(test_file, "r") as f:
            content = f.read()

        assert content.count("def my_method") == 1
        assert '"new"' in content
        assert '"original"' not in content
