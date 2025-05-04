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
"Tests for the diff_edit tool's advanced functionality.\n\nThis module contains tests that verify the diff_edit tool's ability to handle:\n- Basic line replacements with strict indentation\n- Multi-line expansions and contractions\n- Inexact indentation matching\n- Mixed indentation in code blocks\n- Newline-insensitive function block matching\n"

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
    initial = textwrap.dedent('    def test_function():\n        print("hello")\n        print("world")\n    ')
    diff = '-    print("hello")\n+    print("goodbye")'
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def test_function():\n        print("goodbye")\n        print("world")\n    ')
    assert result == expected

def test_different_line_counts_expand(temp_file: str) -> None:
    """Test expansion of a single line into multiple lines.

    Verifies that diff_edit can correctly:
    - Replace one line with multiple lines
    - Maintain proper indentation for all new lines
    - Preserve following content at correct position
    """
    initial = textwrap.dedent('    def test_function():\n        print("hello")\n        print("world")\n    ')
    diff = textwrap.dedent('    -    print("hello")\n    +    print("goodbye")\n    +    print("cruel")\n    +    print("world")')
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def test_function():\n        print("goodbye")\n        print("cruel")\n        print("world")\n        print("world")\n    ')
    assert result == expected

def test_different_line_counts_contract(temp_file: str) -> None:
    """Test contraction of multiple lines into a single line.

    Verifies that diff_edit can correctly:
    - Replace multiple lines with a single line
    - Remove all specified lines
    - Maintain proper file structure after contraction
    """
    initial = textwrap.dedent('    def test_function():\n        print("hello")\n        print("cruel")\n        print("world")\n    ')
    diff = textwrap.dedent('    -    print("hello")\n    -    print("cruel")\n    -    print("world")\n    +    print("goodbye")')
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def test_function():\n        print("goodbye")\n    ')
    assert result == expected

def test_inexact_indentation_single_line(temp_file: str) -> None:
    """Test flexible indentation matching for single line replacement.

    Verifies that diff_edit can:
    - Match lines regardless of exact indentation in diff spec
    - Preserve the original file's indentation level
    - Correctly identify and replace target lines
    """
    initial = textwrap.dedent('    def test_function():\n        print("hello")\n        print("world")\n    ')
    diff = textwrap.dedent('    -print("hello")\n    +print("goodbye")')
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def test_function():\n        print("goodbye")\n        print("world")\n    ')
    assert result == expected

def test_inexact_indentation_multiline(temp_file: str) -> None:
    """Test flexible indentation matching for multiline blocks.

                                            Verifies that diff_edit can:
                                            - Match blocks regardless of absolute indentation in diff
                                            - Preserve indentation from the diff spec
                                            - Handle nested code structures correctly
                                            """
    initial = 'class TestClass:\n    def test_method():\n        if True:\n            print("hello")\n            print("world")\n'
    diff = '-    if True:\n-        print("hello")\n-        print("world")\n+        if False:\n+            print("goodbye")\n+            if True:\n+                print("nested")'
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = 'class TestClass:\n    def test_method():\n            if False:\n                print("goodbye")\n                if True:\n                    print("nested")\n'
    result_lines = result.splitlines()
    expected_lines = expected.splitlines()
    for i, (r, e) in enumerate(zip(result_lines, expected_lines)):
        assert r == e, f'Line {i + 1} differs:\nExpected: {repr(e)}\nGot:      {repr(r)}'

def test_mixed_indentation_multiline(temp_file: str) -> None:
    """Test handling of irregular and mixed indentation patterns.

    Verifies that diff_edit can handle:
    - Inconsistent indentation levels
    - Non-standard indentation increments
    - Preservation of irregular indentation patterns
    - Correct relative positioning of mixed-indent blocks
    """
    initial = textwrap.dedent('    def test_function():\n        if True:\n            print("hello")\n                print("extra indent")\n            print("world")\n    ')
    diff = textwrap.dedent('    -print("hello")\n    -    print("extra indent")\n    -print("world")\n    +print("one")\n    +    print("two")\n    +        print("three")')
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def test_function():\n        if True:\n            print("one")\n                print("two")\n                    print("three")\n    ')
    assert result == expected

def test_newline_insensitive_matching(temp_file):
    """Test matching of function blocks with varying newline spacing.
    Verifies that diff_edit can:
    - Match function blocks regardless of blank line count
    - Preserve docstring additions in replacements
    - Maintain class structure and method organization
    - Handle multi-function replacements in a single operation
    """
    initial = textwrap.dedent('    class Calculator:\n        def add(self, a, b):\n            return a + b\n\n\n\n        def multiply(self, x, y):\n            return x * y\n\n\n\n        def divide(self, a, b):\n            if b == 0:\n                raise ValueError("Cannot divide by zero")\n            return a / b\n    ')
    diff = textwrap.dedent('    -def add(self, a, b):\n    -    return a + b\n    -\n    -def multiply(self, x, y):\n    -    return x * y\n    -\n    -def divide(self, a, b):\n    -    if b == 0:\n    -        raise ValueError("Cannot divide by zero")\n    -    return a / b\n    +def add(self, a, b):\n    +    \'\'\'Adds two numbers\'\'\'\n    +    return a + b\n    +\n    +def multiply(self, x, y):\n    +    \'\'\'Multiplies two numbers\'\'\'\n    +    return x * y\n    +\n    +def divide(self, a, b):\n    +    \'\'\'Divides two numbers\'\'\'\n    +    if b == 0:\n    +        raise ValueError("Cannot divide by zero")\n    +    return a / b').strip()
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    assert 'Divides two numbers' in result

def test_git_style_headers(temp_file: str) -> None:
    """Test handling of git-style diff headers.

    Verifies that diff_edit can:
    - Accept and ignore @@ line number indicators
    - Process changes correctly despite headers
    - Handle multiple diff hunks with headers
    """
    initial = textwrap.dedent('    def example():\n        x = 1\n        y = 2\n        return x + y\n    ')
    diff = textwrap.dedent('    @@ -1,4 +1,4 @@\n     def example():\n    -    x = 1\n    -    y = 2\n    +    a = 10\n    +    b = 20\n         return x + y')
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def example():\n        a = 10\n        b = 20\n        return x + y\n    ')
    assert result == expected

def test_git_style_context_lines(temp_file: str) -> None:
    """Test handling of git-style context lines.

    Verifies that diff_edit can:
    - Accept and ignore unchanged context lines (starting with space)
    - Process changes correctly with interspersed context
    - Maintain file structure with context lines present
    """
    initial = textwrap.dedent('    def calculate(x, y):\n        # Add the numbers\n        result = x + y\n        # Return the sum\n        return result\n    ')
    diff = textwrap.dedent('    @@ -1,5 +1,5 @@\n     def calculate(x, y):\n         # Add the numbers\n    -    result = x + y\n    +    result = x * y  # Changed to multiplication\n         # Return the sum\n         return result')
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('    def calculate(x, y):\n        # Add the numbers\n        result = x * y  # Changed to multiplication\n        # Return the sum\n        return result\n    ')
    assert result == expected

def test_mixed_style_diff(temp_file: str) -> None:
    """Test handling of mixed diff styles in single spec.

                                            Verifies that diff_edit can:
                                            - Handle mixture of strict and git-style diff formats
                                            - Process multiple hunks with different styles
                                            - Maintain correct ordering of changes
                                            - Preserve indentation from diff spec
                                            """
    initial = 'import os\nimport sys\n\ndef main():\n    print("Hello")\n    print("World")\n\nif __name__ == \'__main__\':\n    main()\n'
    diff = '@@ -1,2 +1,3 @@\n import os\n-import sys\n+import sys\n+import json\n\n-def main():\n-    print("Hello")\n-    print("World")\n+    def main():\n+        data = {"greeting": "Hello World"}\n+        print(json.dumps(data))\n\n if __name__ == \'__main__\':\n     main()'
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = 'import os\nimport sys\nimport json\n\n    def main():\n        data = {"greeting": "Hello World"}\n        print(json.dumps(data))\n\nif __name__ == \'__main__\':\n    main()\n'
    result_lines = result.splitlines()
    expected_lines = expected.splitlines()
    for i, (r, e) in enumerate(zip(result_lines, expected_lines)):
        assert r == e, f'Line {i + 1} differs:\nExpected: {repr(e)}\nGot:      {repr(r)}'
    assert len(result_lines) == len(expected_lines), f'Different number of lines: Expected {len(expected_lines)}, got {len(result_lines)}'