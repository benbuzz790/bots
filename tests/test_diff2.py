"""Tests for the diff_edit tool's advanced functionality.

This module contains tests that verify the diff_edit tool's ability to handle:
- Basic line replacements with strict indentation
- Multi-line expansions and contractions
- Inexact indentation matching
- Mixed indentation in code blocks
- Newline-insensitive function block matching
"""

import pytest
import textwrap
from bots.tools.code_tools import diff_edit

@pytest.fixture
def temp_file(tmp_path) -> str:
    """Create a temporary file path for testing.

    Use when you need a fresh, empty file path for each test case.
    The file itself is not created, only the path is provided.

    Parameters:
    - tmp_path (Path): pytest fixture providing temporary directory path

    Returns:
    str: Path to a temporary file that can be used for testing
    """
    file_path = tmp_path / 'test_file.py'
    return str(file_path)


def write_and_edit(file_path: str, initial_content: str, diff_spec: str) -> str:
    """Write content to a file and apply a diff specification in one step.

    Use when you need to set up a test file with initial content and immediately
    apply changes via diff_edit.

    Parameters:
    - file_path (str): Path to the file to create and modify
    - initial_content (str): Content to write to the file initially
    - diff_spec (str): Diff specification to apply to the content

    Returns:
    str: Result from the diff_edit operation
    """
    with open(file_path, 'w') as f:
        f.write(initial_content)
    return diff_edit(file_path, diff_spec)


def read_file(file_path: str) -> str:
    """Read and return the entire contents of a file.

    Use when you need to verify the contents of a file after making modifications.

    Parameters:
    - file_path (str): Path to the file to read

    Returns:
    str: The complete contents of the file as a string
    """
    with open(file_path, 'r') as f:
        return f.read()


def test_basic_replacement(temp_file: str) -> None:
    """Test basic single-line replacement with strict indentation matching.

    Verifies that diff_edit can replace a single line while preserving:
    - Exact indentation level
    - Surrounding context
    - File structure
    """
    initial = """def test_function():
    print("hello")
    print("world")
"""
    diff = '-    print("hello")\n+    print("goodbye")'
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = """def test_function():
    print("goodbye")
    print("world")
"""
    assert result == expected


def test_different_line_counts_expand(temp_file: str) -> None:
    """Test expansion of a single line into multiple lines.

    Verifies that diff_edit can correctly:
    - Replace one line with multiple lines
    - Maintain proper indentation for all new lines
    - Preserve following content at correct position
    """
    initial = """def test_function():
    print("hello")
    print("world")
"""
    diff = (
        '-    print("hello")\n+    print("goodbye")\n+    print("cruel")\n+    print("world")'
    )
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = """def test_function():
    print("goodbye")
    print("cruel")
    print("world")
    print("world")
"""
    assert result == expected


def test_different_line_counts_contract(temp_file: str) -> None:
    """Test contraction of multiple lines into a single line.

    Verifies that diff_edit can correctly:
    - Replace multiple lines with a single line
    - Remove all specified lines
    - Maintain proper file structure after contraction
    """
    initial = """def test_function():
    print("hello")
    print("cruel")
    print("world")
"""
    diff = (
        '-    print("hello")\n-    print("cruel")\n-    print("world")\n+    print("goodbye")'
    )
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = """def test_function():
    print("goodbye")
"""
    assert result == expected


def test_inexact_indentation_single_line(temp_file: str) -> None:
    """Test flexible indentation matching for single line replacement.

    Verifies that diff_edit can:
    - Match lines regardless of exact indentation in diff spec
    - Preserve the original file's indentation level
    - Correctly identify and replace target lines
    """
    initial = """def test_function():
        print("hello")
    print("world")
"""
    diff = '-print("hello")\n+print("goodbye")'
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = """def test_function():
        print("goodbye")
    print("world")
"""
    assert result == expected


def test_inexact_indentation_multiline(temp_file: str) -> None:
    """Test flexible indentation matching for multiline blocks.

    Verifies that diff_edit can:
    - Match multiline blocks regardless of absolute indentation
    - Preserve relative indentation between lines
    - Handle nested code structures correctly
    - Maintain proper indentation hierarchy
    """
    initial = """class TestClass:
        def test_method():
            if True:
                print("hello")
                print("world")
"""
    diff = """-if True:
-    print("hello")
-    print("world")
+if False:
+    print("goodbye")
+    if True:
+        print("nested")"""
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = """class TestClass:
        def test_method():
            if False:
                print("goodbye")
                if True:
                    print("nested")
"""
    assert result == expected


def test_mixed_indentation_multiline(temp_file: str) -> None:
    """Test handling of irregular and mixed indentation patterns.

    Verifies that diff_edit can handle:
    - Inconsistent indentation levels
    - Non-standard indentation increments
    - Preservation of irregular indentation patterns
    - Correct relative positioning of mixed-indent blocks
    """
    initial = """def test_function():
        if True:
            print("hello")
                print("extra indent")
            print("world")
"""
    diff = """-print("hello")
-    print("extra indent")
-print("world")
+print("one")
+    print("two")
+        print("three")"""
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = """def test_function():
        if True:
            print("one")
                print("two")
                    print("three")
"""
    assert result == expected

def test_newline_insensitive_matching(temp_file):
    """Test matching of function blocks with varying newline spacing.
    Verifies that diff_edit can:
    - Match function blocks regardless of blank line count
    - Preserve docstring additions in replacements
    - Maintain class structure and method organization
    - Handle multi-function replacements in a single operation
    """
    initial = textwrap.dedent("""
    class Calculator:
        def add(self, a, b):
            return a + b



        def multiply(self, x, y):
            return x * y



        def divide(self, a, b):
            if b == 0:
                raise ValueError("Cannot divide by zero")
            return a / b""")

    # Try to match with different newline counts
    diff = """
-def add(self, a, b):
-    return a + b
-
-def multiply(self, x, y):
-    return x * y
-
-def divide(self, a, b):
-    if b == 0:
-        raise ValueError("Cannot divide by zero")
-    return a / b
+def add(self, a, b):
+    '''Adds two numbers'''
+    return a + b
+
+def multiply(self, x, y):
+    '''Multiplies two numbers'''
+    return x * y
+
+def divide(self, a, b):
+    '''Divides two numbers'''
+    if b == 0:
+        raise ValueError("Cannot divide by zero")
+    return a / b"""

    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    assert('''Divides two numbers''' in result)
