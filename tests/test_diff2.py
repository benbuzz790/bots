import pytest
from bots.tools.code_tools import diff_edit

@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / 'test_file.py'
    return str(file_path)


def write_and_edit(file_path: str, initial_content: str, diff_spec: str):
    """Helper to write content and apply diff in one step."""
    with open(file_path, 'w') as f:
        f.write(initial_content)
    return diff_edit(file_path, diff_spec)


def read_file(file_path: str) -> str:
    """Helper to read file content."""
    with open(file_path, 'r') as f:
        return f.read()


def test_basic_replacement(temp_file):
    """Test basic single-line replacement with strict indentation."""
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


def test_different_line_counts_expand(temp_file):
    """Test replacing one line with multiple lines."""
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


def test_different_line_counts_contract(temp_file):
    """Test replacing multiple lines with one line."""
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


def test_inexact_indentation_single_line(temp_file):
    """Test that inexact indentation works for single line replacement."""
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


def test_inexact_indentation_multiline(temp_file):
    """Test that inexact indentation works for multiline blocks and preserves relative indentation."""
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


def test_mixed_indentation_multiline(temp_file):
    """Test handling of mixed indentation in multiline blocks."""
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

import textwrap
def test_newline_insensitive_matching(temp_file):
    """Test that function blocks match regardless of number of newlines between them."""
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