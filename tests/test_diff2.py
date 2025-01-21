import os
import pytest
from bots.tools.code_tools import diff_edit


@pytest.fixture
def temp_file(tmp_path):
    """Create a temporary file for testing."""
    file_path = tmp_path / 'test_file.py'
    return str(file_path)


def write_and_edit(file_path: str, initial_content: str, diff_spec: str,
    ignore_indentation: bool=False, preview: bool=False):
    """Helper to write content and apply diff in one step."""
    with open(file_path, 'w') as f:
        f.write(initial_content)
    return diff_edit(file_path, diff_spec, ignore_indentation=
        ignore_indentation, preview=preview)


def read_file(file_path: str) ->str:
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


def test_indentation_ignored_single_line(temp_file):
    """Test that ignore_indentation works for single line replacement."""
    initial = """def test_function():
        print("hello")
    print("world")
"""
    diff = '-print("hello")\n+print("goodbye")'
    write_and_edit(temp_file, initial, diff, ignore_indentation=True)
    result = read_file(temp_file)
    expected = """def test_function():
        print("goodbye")
    print("world")
"""
    assert result == expected


def test_indentation_ignored_multiline(temp_file):
    """Test that ignore_indentation works for multiline blocks and preserves relative indentation."""
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
    write_and_edit(temp_file, initial, diff, ignore_indentation=True)
    result = read_file(temp_file)
    expected = """class TestClass:
        def test_method():
            if False:
                print("goodbye")
                if True:
                    print("nested")
"""
    assert result == expected


def test_preview_mode(temp_file):
    """Test that preview mode shows changes without applying them."""
    initial = """def test_function():
    print("hello")
"""
    diff = '-    print("hello")\n+    print("goodbye")'
    preview_result = write_and_edit(temp_file, initial, diff, preview=True)
    assert 'Preview of changes to be made:' in preview_result
    result = read_file(temp_file)
    assert result == initial


def test_failed_match_reporting(temp_file):
    """Test that failed matches provide useful context."""
    initial = """def test_function():
        print("hello")
        print("world")
        print("again")
"""
    diff = '-    print("hello")\n-    print("world")\n+    print("goodbye")'
    result = write_and_edit(temp_file, initial, diff)
    assert 'Failed to apply' in result
    assert 'Could not find:' in result
    assert 'Nearest partial match' in result
    assert 'print("hello")' in result


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
    write_and_edit(temp_file, initial, diff, ignore_indentation=True)
    result = read_file(temp_file)
    expected = """def test_function():
        if True:
            print("one")
                print("two")
                    print("three")
"""
    assert result == expected
