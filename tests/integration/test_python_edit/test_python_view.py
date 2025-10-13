import ast
import os
import tempfile
import unittest

# Assuming the functions are imported from the main module
from bots.tools.python_edit import ScopeViewer, python_view


class TestPythonView(unittest.TestCase):
    """Test suite for the python_view function and ScopeViewer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.test_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.test_dir, "test_file.py")

        # Sample Python code for testing
        self.sample_code = '''# Top-level comment
"""Module docstring"""
import os
import sys
from typing import Dict, List

# Global variable
GLOBAL_VAR = 42

def standalone_function():
    """A standalone function."""
    return "hello"

class OuterClass:
    """An outer class."""

    def __init__(self):
        self.value = 10

    def outer_method(self):
        """Method in outer class."""
        return self.value * 2

    class InnerClass:
        """A nested inner class."""

        def __init__(self, data):
            self.data = data

        def inner_method(self):
            """Method in inner class."""
            return f"Inner: {self.data}"

        async def async_inner_method(self):
            """Async method in inner class."""
            return await some_async_call()

    def another_outer_method(self):
        """Another method in outer class."""
        def nested_function():
            """Function nested inside method."""
            return "nested"
        return nested_function()

async def async_standalone_function():
    """An async standalone function."""
    return "async hello"

class AnotherClass:
    """Another top-level class."""

    @property
    def prop(self):
        return self._prop

    @prop.setter
    def prop(self, value):
        self._prop = value
'''

    def tearDown(self):
        """Clean up test fixtures."""
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        os.rmdir(self.test_dir)

    def _write_test_file(self, content=None):
        """Helper to write content to test file."""
        content = content or self.sample_code
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write(content)

    def test_view_entire_file(self):
        """Test viewing an entire file."""
        self._write_test_file()
        result = python_view(self.test_file)

        # Should return the entire file content (allowing for potential trailing newline differences)
        self.assertEqual(result.rstrip(), self.sample_code.rstrip())

    def test_view_nonexistent_file(self):
        """Test viewing a file that doesn't exist."""
        nonexistent_file = os.path.join(self.test_dir, "nonexistent.py")
        result = python_view(nonexistent_file)

        self.assertIn("File not found", result)
        self.assertIn("Tool Failed", result)

    def test_view_empty_file(self):
        """Test viewing an empty file."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("")
        result = python_view(self.test_file)

        self.assertIn("is empty", result)

    def test_view_whitespace_only_file(self):
        """Test viewing a file with only whitespace."""
        with open(self.test_file, "w", encoding="utf-8") as f:
            f.write("   \n\n  \t  \n")
        result = python_view(self.test_file)

        self.assertIn("is empty", result)

    def test_view_standalone_function(self):
        """Test viewing a standalone function."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::standalone_function")

        self.assertIn("def standalone_function():", result)
        self.assertIn('return "hello"', result)
        self.assertIn("A standalone function.", result)

    def test_view_async_function(self):
        """Test viewing an async function."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::async_standalone_function")

        self.assertIn("async def async_standalone_function():", result)
        self.assertIn('return "async hello"', result)

    def test_view_class(self):
        """Test viewing a class."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass")

        self.assertIn("class OuterClass:", result)
        self.assertIn("def __init__(self):", result)
        self.assertIn("def outer_method(self):", result)
        self.assertIn("class InnerClass:", result)

    def test_view_class_method(self):
        """Test viewing a class method."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass::outer_method")

        self.assertIn("def outer_method(self):", result)
        self.assertIn("Method in outer class.", result)
        self.assertIn("return self.value * 2", result)
        # Should not contain other methods
        self.assertNotIn("def __init__", result)

    def test_view_nested_class(self):
        """Test viewing a nested class."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass::InnerClass")

        self.assertIn("class InnerClass:", result)
        self.assertIn("def inner_method(self):", result)
        self.assertIn("async def async_inner_method(self):", result)
        # Should not contain outer class methods
        self.assertNotIn("def outer_method", result)

    def test_view_nested_class_method(self):
        """Test viewing a method in a nested class."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass::InnerClass::inner_method")

        self.assertIn("def inner_method(self):", result)
        self.assertIn("Method in inner class.", result)
        self.assertIn('return f"Inner: {self.data}"', result)
        # Should not contain other methods
        self.assertNotIn("def __init__", result)
        self.assertNotIn("async def async_inner_method", result)

    def test_view_async_nested_method(self):
        """Test viewing an async method in a nested class."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass::InnerClass::async_inner_method")

        self.assertIn("async def async_inner_method(self):", result)
        self.assertIn("Async method in inner class.", result)

    def test_invalid_file_extension(self):
        """Test error handling for invalid file extension."""
        result = python_view("test_file.txt::SomeClass")

        self.assertIn("File path must end with .py", result)
        self.assertIn("Tool Failed", result)

    def test_invalid_identifier(self):
        """Test error handling for invalid identifiers in path."""
        result = python_view("test_file.py::123InvalidName")

        self.assertIn("Invalid identifier in path", result)
        self.assertIn("Tool Failed", result)

    def test_nonexistent_scope(self):
        """Test error handling for nonexistent scope."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::NonexistentClass")

        self.assertIn("Target scope not found", result)
        self.assertIn("Tool Failed", result)

    def test_nonexistent_method(self):
        """Test error handling for nonexistent method."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass::nonexistent_method")

        self.assertIn("Target scope not found", result)
        self.assertIn("Tool Failed", result)

    def test_malformed_python_file(self):
        """Test error handling for malformed Python files."""
        malformed_code = """
def broken_function(
    # Missing closing parenthesis and colon
    return "broken"
"""
        self._write_test_file(malformed_code)
        result = python_view(f"{self.test_file}::broken_function")

        # New error message format starts with "Tool Failed: Error parsing file"
        self.assertIn("Tool Failed: Error parsing file", result)

    def test_file_with_complex_strings(self):
        """Test viewing code with complex string literals."""
        complex_code = '''
def string_function():
    """Function with complex strings."""
    single = 'single quote string'
    double = "double quote string"
    fstring = f"formatted {single} string"
    multiline = """
    This is a
    multiline string
    """
    return fstring

class StringClass:
    def method_with_strings(self):
        return f"""
        Complex multiline
        f-string with {self.__class__.__name__}
        """
'''
        self._write_test_file(complex_code)
        result = python_view(f"{self.test_file}::StringClass::method_with_strings")

        self.assertIn("def method_with_strings(self):", result)
        self.assertIn("Complex multiline", result)
        self.assertIn("f-string with", result)

    def test_file_with_comments_and_decorators(self):
        """Test viewing code with comments and decorators."""
        decorated_code = '''from functools import wraps

def decorator(func):
    @wraps(func)
    def wrapper(*args, **kwargs):
        return func(*args, **kwargs)
    return wrapper

class DecoratedClass:
    """A class with decorated methods."""

    def __init__(self):
        self._value = None

    @property
    def value(self):
        """A property."""
        return self._value

    @value.setter
    def value(self, val):
        """Set the value."""
        self._value = val

    @decorator
    def decorated_method(self):
        """A decorated method."""
        # This does something
        return "decorated"
'''
        self._write_test_file(decorated_code)
        result = python_view(f"{self.test_file}::DecoratedClass::decorated_method")

        self.assertIn("@decorator", result)
        self.assertIn("def decorated_method(self):", result)
        self.assertIn("A decorated method.", result)
        self.assertIn("This does something", result)

    def test_max_lines_whole_file_no_truncation(self):
        """Test max_lines parameter with whole file when no truncation needed."""
        self._write_test_file()
        result = python_view(self.test_file, max_lines=100)
        # Should return the entire file content since it's under 100 lines
        self.assertEqual(result.rstrip(), self.sample_code.rstrip())
        self.assertNotIn("truncated", result)

    def test_max_lines_whole_file_with_truncation(self):
        """Test max_lines parameter with whole file when truncation is needed."""
        self._write_test_file()
        result = python_view(self.test_file, max_lines=10)
        # Should be truncated to an outline view
        lines = result.splitlines()
        self.assertLessEqual(len(lines), 10)  # Should be at most 10 lines
        # Verify it's actually truncated by checking we have fewer lines than original
        original_lines = self.sample_code.splitlines()
        self.assertLess(len(lines), len(original_lines), "Should be truncated from original")
        # Should show outline format with "..." markers
        self.assertIn("...", result, "Should contain truncation markers")

    def test_max_lines_scoped_view_no_truncation(self):
        """Test max_lines parameter with scoped view when no truncation needed."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::standalone_function", max_lines=50)
        # Should return the entire function since it's under 50 lines
        self.assertIn("def standalone_function():", result)
        self.assertIn('return "hello"', result)
        self.assertNotIn("truncated", result)

    def test_max_lines_scoped_view_with_truncation(self):
        """Test max_lines parameter with scoped view when truncation is needed."""
        self._write_test_file()
        result = python_view(f"{self.test_file}::OuterClass", max_lines=5)
        lines = result.splitlines()
        self.assertLessEqual(len(lines), 5)  # Should be at most 5 lines
        # Should show outline with truncation markers
        self.assertIn("...", result, "Should contain truncation markers")

    def test_max_lines_zero_disables_truncation(self):
        """Test that max_lines=0 disables truncation."""
        self._write_test_file()
        result = python_view(self.test_file, max_lines=0)
        # Should return the entire file content
        self.assertEqual(result.rstrip(), self.sample_code.rstrip())
        self.assertNotIn("truncated", result)

    def test_max_lines_negative_disables_truncation(self):
        """Test that negative max_lines disables truncation."""
        self._write_test_file()
        result = python_view(self.test_file, max_lines=-1)
        # Should return the entire file content
        self.assertEqual(result.rstrip(), self.sample_code.rstrip())
        self.assertNotIn("truncated", result)

    def test_max_lines_default_value(self):
        """Test that the default max_lines value is 500."""
        # Create a file with exactly 600 lines to test default truncation
        large_code = "\n".join([f"# Line {i+1}" for i in range(600)])
        self._write_test_file(large_code)
        result = python_view(self.test_file)  # No max_lines specified, should use default 500
        lines = result.splitlines()
        self.assertLessEqual(len(lines), 500)  # Should be at most 500 lines
        # Verify it's truncated from original 600 lines
        self.assertLess(len(lines), 600, "Should be truncated from original 600 lines")

    def test_max_lines_truncation_message_format(self):
        """Test that truncation works correctly."""
        # Create a file with exactly 25 lines
        test_code = "\n".join([f"# Line {i+1}" for i in range(25)])
        self._write_test_file(test_code)
        result = python_view(self.test_file, max_lines=10)
        lines = result.splitlines()
        # Should be truncated to at most 10 lines
        self.assertLessEqual(len(lines), 10)
        self.assertLess(len(lines), 25, "Should be truncated from original 25 lines")

    def test_max_lines_with_empty_lines(self):
        """Test max_lines counting includes empty lines."""
        code_with_empty_lines = """def func1():
    pass

def func2():
    pass

def func3():
    pass
"""
        self._write_test_file(code_with_empty_lines)
        result = python_view(self.test_file, max_lines=5)
        lines = result.splitlines()
        self.assertLessEqual(len(lines), 5)  # Should be at most 5 lines
        # Should show outline with truncation
        self.assertIn("...", result, "Should contain truncation markers")


class TestScopeViewer(unittest.TestCase):
    """Test suite for the ScopeViewer class."""

    def setUp(self):
        """Set up test fixtures."""
        self.sample_tree = ast.parse(
            """
def func1():
    pass

class Class1:
    def method1(self):
        pass

    class InnerClass:
        def inner_method(self):
            pass

def func2():
    pass
"""
        )

    def test_find_function(self):
        """Test finding a top-level function."""
        viewer = ScopeViewer(["func1"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ast.FunctionDef)
        self.assertEqual(result.name, "func1")

    def test_find_class(self):
        """Test finding a top-level class."""
        viewer = ScopeViewer(["Class1"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ast.ClassDef)
        self.assertEqual(result.name, "Class1")

    def test_find_method(self):
        """Test finding a method within a class."""
        viewer = ScopeViewer(["Class1", "method1"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ast.FunctionDef)
        self.assertEqual(result.name, "method1")

    def test_find_nested_class(self):
        """Test finding a nested class."""
        viewer = ScopeViewer(["Class1", "InnerClass"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ast.ClassDef)
        self.assertEqual(result.name, "InnerClass")

    def test_find_nested_method(self):
        """Test finding a method in a nested class."""
        viewer = ScopeViewer(["Class1", "InnerClass", "inner_method"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNotNone(result)
        self.assertIsInstance(result, ast.FunctionDef)
        self.assertEqual(result.name, "inner_method")

    def test_nonexistent_target(self):
        """Test searching for a nonexistent target."""
        viewer = ScopeViewer(["NonexistentClass"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNone(result)

    def test_partial_path_match(self):
        """Test that partial path matches don't return results."""
        viewer = ScopeViewer(["Class1", "NonexistentMethod"])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNone(result)

    def test_empty_path(self):
        """Test empty path handling."""
        viewer = ScopeViewer([])
        result = viewer.find_target(self.sample_tree)

        self.assertIsNone(result)


if __name__ == "__main__":
    # Run the tests using the modern approach
    unittest.main(verbosity=2)
