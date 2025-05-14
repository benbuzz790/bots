import pytest
import textwrap
from bots.tools.code_tools import diff_edit
from bots.tools.code_tools import IndentationContext, DiffProgress, DiffState, _get_indentation, _find_matching_block
from bots.tools.code_tools import _determine_next_state, _process_line
from bots.tools.code_tools import DiffErrorType

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
    """Test basic single-line replacement with strict indentation matching."""
    from bots.tools.code_tools import DiffProgress, DiffState, _process_state_transition, diff_edit
    initial = 'def test_function():\n    print("hello")\n    print("world")\n'
    diff = ' def test_function():\n-    print("hello")\n+    print("goodbye")'
    with open(temp_file, 'w') as f:
        f.write(initial)
    print('\nInitial file:')
    with open(temp_file, 'r') as f:
        print(f.read())
    print('\nApplying diff:')
    print(diff)
    result_msg = diff_edit(temp_file, diff)
    print('\nDiff edit result:', result_msg)
    print('\nFinal file:')
    with open(temp_file, 'r') as f:
        result = f.read()
    print(result)
    expected = 'def test_function():\n    print("goodbye")\n    print("world")\n'
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
    - Preserve indentation from the original location
    - Handle nested code structures correctly
    """
    initial = 'class TestClass:\n    def test_method():\n        if True:\n            print("hello")\n            print("world")\n'
    diff = '-if True:\n-    print("hello")\n-    print("world")\n+if False:\n+    print("goodbye")\n+    if True:\n+        print("nested")'
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = 'class TestClass:\n    def test_method():\n        if False:\n            print("goodbye")\n            if True:\n                print("nested")\n'
    print('\nInitial:')
    print(initial)
    print('\nDiff:')
    print(diff)
    print('\nResult:')
    print(result)
    print('\nExpected:')
    print(expected)
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
    initial = textwrap.dedent('\n        class Calculator:\n            def add(self, a, b):\n                return a + b\n\n\n\n            def multiply(self, x, y):\n                return x * y\n\n\n\n            def divide(self, a, b):\n                if b == 0:\n                    raise ValueError("Cannot divide by zero")\n                return a / b\n    ')
    diff = textwrap.dedent('\n        -    def add(self, a, b):\n        -        return a + b\n        -\n        -    def multiply(self, x, y):\n        -        return x * y\n        -\n        -    def divide(self, a, b):\n        -        if b == 0:\n        -            raise ValueError("Cannot divide by zero")\n        -        return a / b\n        +    def add(self, a, b):\n        +        """Adds two numbers"""\n        +        return a + b\n        +\n        +    def multiply(self, x, y):\n        +        """Multiplies two numbers"""\n        +        return x * y\n        +\n        +    def divide(self, a, b):\n        +        """Divides two numbers"""\n        +        if b == 0:\n        +            raise ValueError("Cannot divide by zero")\n        +        return a / b\n    ').strip()
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    assert 'Adds two numbers' in result, 'First docstring missing'
    assert 'Multiplies two numbers' in result, 'Second docstring missing'
    assert 'Divides two numbers' in result, 'Third docstring missing'
    result_lines = result.splitlines()
    for line in result_lines:
        if 'def' in line:
            assert len(_get_indentation(line)) == 4, f'Method indentation wrong: {line}'
        elif '"""' in line:
            assert len(_get_indentation(line)) == 8, f'Docstring indentation wrong: {line}'

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

def test_context_aware_matching(temp_file: str) -> None:
    """Test that context lines are used for matching location.

    Verifies that diff_edit:
    - Uses context lines to find correct location
    - Only applies changes where context matches
    - Reports failure when context doesn't match
    """
    initial = textwrap.dedent('\n        def first_func():\n            # First block\n            x = 1\n            y = 2\n            z = x + y\n\n        def second_func():\n            # Second block\n            x = 1\n            y = 2\n            z = x + y\n    ').strip()
    diff = textwrap.dedent('\n         # Second block\n         x = 1\n        -y = 2\n        -z = x + y\n        +y = 20\n        +z = x * y\n    ').strip()
    write_and_edit(temp_file, initial, diff)
    result = read_file(temp_file)
    expected = textwrap.dedent('\n        def first_func():\n            # First block\n            x = 1\n            y = 2\n            z = x + y\n\n        def second_func():\n            # Second block\n            x = 1\n            y = 20\n            z = x * y\n    ').strip()
    assert result == expected

def test_context_aware_failure(temp_file: str) -> None:
    """Test that changes are not applied when context doesn't match.

    Verifies that diff_edit:
    - Refuses to apply changes when context doesn't match
    - Preserves file content when context check fails
    - Reports context mismatch in error message
    """
    initial = textwrap.dedent('\n        def calculate():\n            # Add numbers\n            x = 1\n            y = 2\n            return x + y\n    ').strip()
    diff = textwrap.dedent('\n         # Multiply numbers\n         x = 1\n        -y = 2\n        +y = 10\n         return x + y\n    ').strip()
    result = write_and_edit(temp_file, initial, diff)
    file_content = read_file(temp_file)
    assert file_content == initial
    assert 'Required pre-context not found' in result

def test_multiple_context_blocks(temp_file: str) -> None:
    """Test handling of multiple changes with different contexts.

    Verifies that diff_edit can:
    - Handle multiple change blocks with different contexts
    - Apply only changes where context matches
    - Report success/failure for each block separately
    """
    initial = textwrap.dedent('\n        x = 1\n        # First calculation\n        y = x + 2\n        z = y * 3\n\n        # Second calculation\n        a = x * 2\n        b = a + 3\n\n        # Third calculation\n        p = x + 5\n        q = p * 2\n    ').strip()
    diff = textwrap.dedent('\n         # First calculation\n         y = x + 2\n        -z = y * 3\n        +z = y * 30\n\n         # Second calculation\n         a = x * 2\n        -b = a + 3\n        +b = a + 30\n\n         # Wrong context\n         p = x + 5\n        -q = p * 2\n        +q = p * 20\n    ').strip()
    result = write_and_edit(temp_file, initial, diff)
    file_content = read_file(temp_file)
    expected = textwrap.dedent('\n        x = 1\n        # First calculation\n        y = x + 2\n        z = y * 30\n\n        # Second calculation\n        a = x * 2\n        b = a + 30\n\n        # Third calculation\n        p = x + 5\n        q = p * 2\n    ').strip()
    assert file_content == expected
    assert 'Successfully applied 2 changes' in result
    assert 'Failed to apply 1 changes' in result

def test_indentation_dedent():
    """Test that textwrap.dedent correctly normalizes indentation structure."""
    input_block = "    if True:\n        print('hello')\n            print('world')\n"
    expected = "if True:\n    print('hello')\n        print('world')\n"
    result = textwrap.dedent(input_block)
    assert result == expected, f'Dedent failed:\nExpected:\n{expected}\nGot:\n{result}'

def test_match_location_indent():
    """Test that we correctly identify the indentation at the match location."""
    file_content = 'def outer():\n    if True:\n        x = 1\n        y = 2\n'
    match_line = '        x = 1'
    indent = _get_indentation(match_line)
    assert len(indent) == 8, f'Expected 8 spaces, got {len(indent)}'
    assert indent == '        ', f'Expected spaces, got {repr(indent)}'

def test_relative_structure_preservation():
    """Test that relative indentation structure is preserved after adjustment."""
    original = "    if test:\n        print('a')\n            print('b')\n"
    target_indent = '        '
    ctx = IndentationContext.from_diff_lines(original.splitlines(), target_indent)
    adjusted = ctx.adjust_lines(textwrap.dedent(original).splitlines())
    expected = ['        if test:', "            print('a')", "                print('b')"]
    assert adjusted == expected, f'Structure not preserved:\nExpected:\n{expected}\nGot:\n{adjusted}'

def test_context_matching():
    """Test that context lines are correctly used to find match location."""
    file_content = ['def first():', '    # Block A', '    x = 1', '    y = 2', '', 'def second():', '    # Block A', '    x = 1', '    y = 2']
    context_lines = ['    # Block A', '    x = 1']
    progress = DiffProgress()
    progress.context_lines = context_lines
    progress.pending_remove = ['    y = 2']
    match_pos, ctx = _find_matching_block(file_content, progress)
    assert match_pos == 8, f'Matched wrong position: {match_pos}'

def test_block_replacement():
    """Test that block replacement maintains correct line count."""
    file_lines = ['def test():', '    old_line1', '    old_line2', '    old_line3', 'end']
    remove_block = ['    old_line1', '    old_line2', '    old_line3']
    add_block = ['    new_line1', '    new_line2']
    match_pos = 1
    file_lines[match_pos:match_pos + len(remove_block)] = add_block
    expected = ['def test:', '    new_line1', '    new_line2', 'end']
    assert len(file_lines) == len(expected), f'Line count mismatch: {len(file_lines)} vs {len(expected)}'

def test_indentation_context_basic():
    """Test basic indentation preservation."""
    original = textwrap.dedent('\n        def test():\n            x = 1\n            y = 2\n    ').strip()
    match_indent = '        '
    ctx = IndentationContext.from_diff_lines(original.splitlines(), match_indent)
    result = ctx.adjust_lines(textwrap.dedent('\n        def test():\n            a = 3\n            b = 4\n    ').strip().splitlines())
    expected = ['        def test():', '            a = 3', '            b = 4']
    assert result == expected, f'Basic indentation failed:\nExpected:\n{expected}\nGot:\n{result}'

def test_indentation_context_nested():
    """Test preservation of nested indentation structure."""
    original = textwrap.dedent('\n        if True:\n            if nested:\n                deep = True\n    ').strip()
    match_indent = '        '
    ctx = IndentationContext.from_diff_lines(original.splitlines(), match_indent)
    result = ctx.adjust_lines(original.splitlines())
    expected = ['        if True:', '            if nested:', '                deep = True']
    assert result == expected, f'Nested indentation failed:\nExpected:\n{expected}\nGot:\n{result}'

def test_indentation_context_mixed():
    """Test handling of mixed indentation levels."""
    original = textwrap.dedent('\n        def test():\n                extra_indent = True\n            normal_indent = True\n                    very_deep = True\n    ').strip()
    match_indent = '        '
    ctx = IndentationContext.from_diff_lines(original.splitlines(), match_indent)
    result = ctx.adjust_lines(original.splitlines())
    expected = ['        def test():', '                extra_indent = True', '            normal_indent = True', '                    very_deep = True']
    assert result == expected, f'Mixed indentation failed:\nExpected:\n{expected}\nGot:\n{result}'

def test_indentation_context_empty_lines():
    """Test handling of empty lines in indentation."""
    original = textwrap.dedent('\n        def test():\n            x = 1\n\n            y = 2\n    ').strip()
    match_indent = '        '
    ctx = IndentationContext.from_diff_lines(original.splitlines(), match_indent)
    result = ctx.adjust_lines(original.splitlines())
    expected = ['        def test():', '            x = 1', '', '            y = 2']
    assert result == expected, f'Empty line handling failed:\nExpected:\n{expected}\nGot:\n{result}'

def test_indentation_context_relative_preservation():
    """Test that relative indentation relationships are preserved."""
    original = textwrap.dedent('\n        if True:\n            print("hello")\n            print("world")\n    ').strip()
    match_indent = '        '
    ctx = IndentationContext.from_diff_lines(original.splitlines(), match_indent)
    new_block = textwrap.dedent('\n        if False:\n            print("goodbye")\n            if True:\n                print("nested")\n    ').strip().splitlines()
    result = ctx.adjust_lines(new_block)
    expected = ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")']
    assert result == expected, f'Relative indentation preservation failed:\nExpected:\n{expected}\nGot:\n{result}'

def test_diff_block_extraction():
    """Test extraction of remove/add blocks from diff spec."""
    diff = textwrap.dedent('\n        -    if True:\n        -        print("hello")\n        -        print("world")\n        +        if False:\n        +            print("goodbye")\n        +            if True:\n        +                print("nested")\n    ').strip()
    progress = DiffProgress()
    for line in diff.splitlines():
        next_state = _determine_next_state(line, progress.state)
        if next_state != progress.state:
            if progress.current_block:
                if progress.state == DiffState.REMOVE:
                    remove_block = progress.current_block.copy()
                    assert remove_block == ['    if True:', '        print("hello")', '        print("world")'], f'Remove block incorrect: {remove_block}'
            progress.state = next_state
            progress.current_block = []
        processed_line = _process_line(line, progress)
        if next_state != DiffState.HEADER:
            progress.current_block.append(processed_line)
    assert progress.current_block == ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")'], f'Add block incorrect: {progress.current_block}'

def test_find_matching_location():
    """Test finding the correct location in file content."""
    file_content = textwrap.dedent('\n        class TestClass:\n            def test_method():\n                if True:\n                    print("hello")\n                    print("world")\n    ').strip().splitlines()
    progress = DiffProgress()
    progress.pending_remove = ['    if True:', '        print("hello")', '        print("world")']
    match_pos, ctx = _find_matching_block(file_content, progress)
    assert match_pos == 2, f'Wrong match position: {match_pos}'
    assert len(ctx.match_indent) == 8, f'Wrong indentation length: {len(ctx.match_indent)}'

def test_match_to_add_conversion():
    """Test conversion from match location to add block indentation."""
    match_indent = ' ' * 8
    add_block = ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")']
    ctx = IndentationContext.from_diff_lines(add_block, match_indent)
    result = ctx.adjust_lines(add_block)
    expected = ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")']
    assert result == expected, f'Wrong indentation adjustment:\nExpected: {expected}\nGot: {result}'

def test_complete_indentation_pipeline():
    """Test the complete indentation pipeline in a controlled way.

    The key rules are:
    1. Match blocks by content, ignoring indentation
    2. Use the indentation from where we found the match as our base
    3. Preserve relative indentation structure from there
    """
    file_lines = ['class TestClass:', '    def test_method():', '        if True:', '            print("hello")', '            print("world")']
    diff = textwrap.dedent('\n        -    if True:\n        -        print("hello")\n        -        print("world")\n        +        if False:\n        +            print("goodbye")\n        +            if True:\n        +                print("nested")\n    ').strip()
    progress = DiffProgress()
    remove_block = []
    add_block = []
    current_block = []
    for line in diff.splitlines():
        next_state = _determine_next_state(line, progress.state)
        if next_state != progress.state:
            if current_block:
                if progress.state == DiffState.REMOVE:
                    remove_block = current_block.copy()
                elif progress.state == DiffState.ADD:
                    add_block = current_block.copy()
            current_block = []
        progress.state = next_state
        if next_state != DiffState.HEADER:
            current_block.append(_process_line(line, progress))
    if current_block:
        add_block = current_block.copy()
    assert remove_block == ['    if True:', '        print("hello")', '        print("world")'], f'Remove block incorrect: {remove_block}'
    assert add_block == ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")'], f'Add block incorrect: {add_block}'
    progress.pending_remove = remove_block
    match_pos, ctx = _find_matching_block(file_lines, progress)
    assert match_pos == 2, f'Wrong match position: {match_pos}'
    match_line = file_lines[match_pos]
    match_indent = _get_indentation(match_line)
    assert len(match_indent) == 8, f'Match indent wrong length: {len(match_indent)}'
    adjusted_lines = ctx.adjust_lines(add_block)
    assert len(_get_indentation(adjusted_lines[0])) == 8, f'First line wrong indent: {len(_get_indentation(adjusted_lines[0]))}'
    assert len(_get_indentation(adjusted_lines[1])) == 12, f'Second line wrong indent: {len(_get_indentation(adjusted_lines[1]))}'
    file_lines[match_pos:match_pos + len(remove_block)] = adjusted_lines
    expected = ['class TestClass:', '    def test_method():', '        if False:', '            print("goodbye")', '            if True:', '                print("nested")']
    assert file_lines == expected, f'Pipeline result incorrect:\nExpected:\n{expected}\nGot:\n{file_lines}'

def test_indentation_level_determination():
    """Test how we determine the base indentation level for replacements.

    When replacing a block inside a method:
    - The block might have its own indentation in the diff spec
    - But we need to place it at the method's indentation level
    - Plus any additional relative indentation
    """
    file_lines = ['class TestClass:', '    def test_method():', '        if True:', '            print("hello")', '            print("world")']
    match_line = '        if True:'
    base_indent = _get_indentation(match_line)
    assert len(base_indent) == 8, f'Base indent should be 8 spaces, got {len(base_indent)}'
    new_block = ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")']
    ctx = IndentationContext.from_diff_lines(new_block, base_indent)
    result = ctx.adjust_lines(new_block)
    expected = ['        if False:', '            print("goodbye")', '            if True:', '                print("nested")']
    for i, (result_line, expected_line) in enumerate(zip(result, expected)):
        result_indent = len(_get_indentation(result_line))
        expected_indent = len(_get_indentation(expected_line))
        assert result_indent == expected_indent, f'Line {i} has wrong indentation: expected {expected_indent}, got {result_indent}'

def test_context_matching_first_block():
    """Test that we can explicitly match the first occurrence of a block.

    This test verifies that when we have identical blocks and want the first one,
    we can match it correctly using preceding context.
    """
    file_content = ['def setup():', '    # Initialize', '    x = 1', '    y = 2', '', 'def first():', '    # Block A', '    x = 1', '    y = 2', '', 'def second():', '    # Block A', '    x = 1', '    y = 2']
    context_lines = ['def first():', '    # Block A', '    x = 1']
    progress = DiffProgress()
    progress.context_lines = context_lines
    progress.pending_remove = ['    y = 2']
    match_pos, ctx = _find_matching_block(file_content, progress)
    assert match_pos == 8, f'Matched wrong position: {match_pos} (should be 8 for first block)'

def test_context_matching_second_block():
    """Test that we can explicitly match the second occurrence of a block.

    This test verifies that when we have identical blocks and want the second one,
    we can match it correctly using preceding context.
    """
    file_content = ['def setup():', '    # Initialize', '    x = 1', '    y = 2', '', 'def first():', '    # Block A', '    x = 1', '    y = 2', '', 'def second():', '    # Block A', '    x = 1', '    y = 2']
    context_lines = ['def second():', '    # Block A', '    x = 1']
    progress = DiffProgress()
    progress.context_lines = context_lines
    progress.pending_remove = ['    y = 2']
    match_pos, ctx = _find_matching_block(file_content, progress)
    assert match_pos == 13, f'Matched wrong position: {match_pos} (should be 13 for second block)'

def test_ambiguous_match_error(temp_file: str) -> None:
    """Test that ambiguous matches result in a clear error message.

    Verifies that when multiple identical blocks are found:
    - No changes are made to the file
    - An error message lists all match locations
    - The error message is clear and actionable
    """
    initial = textwrap.dedent('\n        def first_block():\n            # Common block\n            x = 1\n            y = 2\n            z = 3\n\n        def second_block():\n            # Common block\n            x = 1\n            y = 2\n            z = 3\n\n        def third_block():\n            # Different block\n            x = 1\n            y = 2\n            z = 4\n    ').strip()
    diff = textwrap.dedent('\n        -    x = 1\n        -    y = 2\n        -    z = 3\n        +    x = 10\n        +    y = 20\n        +    z = 30\n    ').strip()
    result = write_and_edit(temp_file, initial, diff)
    file_content = read_file(temp_file)
    assert file_content == initial, 'File was modified despite ambiguous match'
    assert 'more than one match found' in result.lower(), 'Error message should indicate multiple matches'
    assert 'first_block' in result, 'Error should mention first match location'
    assert 'second_block' in result, 'Error should mention second match location'
    assert 'third_block' not in result, 'Error should not mention non-matching block'

def test_find_matching_block_basic():
    """Test basic block matching with different whitespace"""
    file_content = ['def test():', '    x = 1', '    y = 2']
    progress = DiffProgress()
    progress.context_lines = ['x = 1']
    progress.pending_remove = ['    y = 2']
    match_pos, ctx = _find_matching_block(file_content, progress)
    assert match_pos == 2, f'Basic match failed. Expected pos 2, got {match_pos}'

def test_find_matching_block_multiple_context():
    """Test matching with multiple context lines and varying whitespace"""

    def normalize_line(line: str) -> str:
        """Strip whitespace for content comparison"""
        return line.strip()
    file_content = ['def first():', '    # Comment', '    x = 1', '    y = 2', '', 'def second():', '    # Comment', '    x = 1', '    y = 2']
    progress = DiffProgress()
    progress.context_lines = ['# Comment', 'x = 1']
    progress.pending_remove = ['    y = 2']
    print('\nDebug context matching:')
    for i in range(len(file_content)):
        if i < len(file_content) - 1:
            test_lines = file_content[i:i + 2]
            print(f'Testing at pos {i}:')
            print(f'  File lines: {test_lines}')
            print(f'  Context lines: {progress.context_lines}')
            print(f'  Normalized file: {[l.strip() for l in test_lines]}')
            print(f'  Normalized context: {[l.strip() for l in progress.context_lines]}')
            if i <= len(file_content) - 2:
                matches = all((normalize_line(a) == normalize_line(b) for a, b in zip(file_content[i:i + 2], progress.context_lines)))
                print(f'  Would match: {matches}')
    print('\nDebug remove block matching:')
    remove_pos = 3
    remove_block = file_content[remove_pos:remove_pos + 1]
    print(f'Looking for remove block at pos {remove_pos}:')
    print(f'  File block: {remove_block}')
    print(f'  Remove lines: {progress.pending_remove}')
    print(f'  Normalized file: {[l.strip() for l in remove_block]}')
    print(f'  Normalized remove: {[l.strip() for l in progress.pending_remove]}')
    match_pos, ctx = _find_matching_block(file_content, progress)
    print(f'\nMatch result: {match_pos}')
    print(f'Progress state:')
    print(f'  error_type: {progress.error_type}')
    print(f'  last_match_position: {progress.last_match_position}')
    print(f"  context_match_position: {getattr(progress, 'context_match_position', 'not set')}")
    print(f'  error_context: {progress.error_context}')
    assert match_pos == 3, f'First match position wrong. Expected 3, got {match_pos}'

def test_find_matching_block_whitespace_variants():
    """Test matching with various whitespace patterns"""
    file_content = ['def test():', '    x = 1', '        y = 2', '            z = 3']
    progress = DiffProgress()
    test_cases = [('x = 1', 2), ('    x = 1', 2), ('\tx = 1', 2), ('        x = 1', 2)]
    for context, expected_pos in test_cases:
        progress.context_lines = [context]
        progress.pending_remove = ['        y = 2']
        match_pos, ctx = _find_matching_block(file_content, progress)
        assert match_pos == expected_pos, f'Failed for context "{context}". Expected {expected_pos}, got {match_pos}'
        assert progress.context_match_position == 1, f'Context position wrong for "{context}". Expected 1, got {progress.context_match_position}'

def test_determine_next_state():
    """Test state transitions in diff parsing.
    Verifies that _determine_next_state correctly identifies:
    - Headers (@@)
    - Removals (-)
    - Additions (+)
    - Context lines
    """
    from bots.tools.code_tools import _determine_next_state, DiffState
    assert _determine_next_state('@@ -1,3 +1,3 @@', DiffState.CONTEXT) == DiffState.HEADER
    assert _determine_next_state('-    print("hello")', DiffState.CONTEXT) == DiffState.REMOVE
    assert _determine_next_state('-print("hello")', DiffState.HEADER) == DiffState.REMOVE
    assert _determine_next_state('+    print("goodbye")', DiffState.REMOVE) == DiffState.ADD
    assert _determine_next_state('+print("goodbye")', DiffState.CONTEXT) == DiffState.ADD
    assert _determine_next_state('    print("unchanged")', DiffState.ADD) == DiffState.CONTEXT
    assert _determine_next_state('print("unchanged")', DiffState.REMOVE) == DiffState.CONTEXT
    assert _determine_next_state('', DiffState.ADD) == DiffState.CONTEXT

def test_process_line():
    """Test line processing in diff parsing.
    Verifies that _process_line correctly:
    - Strips diff markers (+ and -)
    - Preserves indentation
    - Updates progress state
    - Handles empty lines
    """
    from bots.tools.code_tools import _process_line, DiffProgress, DiffState
    progress = DiffProgress()
    assert _process_line('-    print("hello")', progress) == '    print("hello")'
    assert _process_line('-print("hello")', progress) == 'print("hello")'
    assert _process_line('+    print("goodbye")', progress) == '    print("goodbye")'
    assert _process_line('+print("goodbye")', progress) == 'print("goodbye")'
    assert _process_line('    print("unchanged")', progress) == '    print("unchanged")'
    assert _process_line('print("unchanged")', progress) == 'print("unchanged")'
    assert _process_line('', progress) == ''
    assert _process_line('    ', progress) == '    '

def test_find_matching_block_disambiguation():
    """Test that _find_matching_block correctly uses context to disambiguate between multiple matches.

    The test file contains two identical blocks, but the context lines should help identify
    the correct one based on the surrounding code structure.
    """
    from bots.tools.code_tools import _find_matching_block, DiffProgress, DiffErrorType
    file_content = ['def first():', '    # Comment', '    x = 1', '    y = 2', '', 'def second():', '    # Comment', '    x = 1', '    y = 2']
    progress1 = DiffProgress()
    progress1.context_lines = ['x = 1']
    progress1.pending_remove = ['    y = 2']
    match_pos1, ctx1 = _find_matching_block(file_content, progress1)
    print(f'\nTest Case 1 - Minimal Context')
    print(f'Context lines: {progress1.context_lines}')
    print(f'Looking to remove: {progress1.pending_remove}')
    print(f'Match position: {match_pos1}')
    print(f'Error type: {progress1.error_type}')
    print(f'Error context: {progress1.error_context}')
    assert match_pos1 == -1, 'Should return -1 for ambiguous match'
    assert progress1.error_type == DiffErrorType.AMBIGUOUS_MATCH, 'Should detect ambiguous match with minimal context'
    progress2 = DiffProgress()
    progress2.context_lines = ['def first():', '    # Comment', '    x = 1']
    progress2.pending_remove = ['    y = 2']
    match_pos2, ctx2 = _find_matching_block(file_content, progress2)
    print(f'\nTest Case 2 - Full Context')
    print(f'Context lines: {progress2.context_lines}')
    print(f'Looking to remove: {progress2.pending_remove}')
    print(f'Match position: {match_pos2}')
    print(f'Error type: {progress2.error_type}')
    assert match_pos2 == 3, f'Should find correct match at position 3, got {match_pos2}'
    assert progress2.error_type == DiffErrorType.NONE, 'Should not have any errors with sufficient context'

def test_indentation_matching_simple():
    """Test that IndentationContext correctly matches target indentation level."""
    from bots.tools.code_tools import IndentationContext
    ctx = IndentationContext.from_diff_lines(['print("hello")'], '    ')
    result = ctx.adjust_lines(['print("hello")'])
    assert result == ['    print("hello")']

def test_indentation_relative_single():
    """Test that relative indentation is preserved within a single line."""
    from bots.tools.code_tools import IndentationContext
    ctx = IndentationContext.from_diff_lines(['    print("hello")'], '        ')
    result = ctx.adjust_lines(['    print("hello")'])
    assert result == ['        print("hello")']

def test_indentation_relative_multiple():
    """Test that relative indentation is preserved between multiple lines."""
    from bots.tools.code_tools import IndentationContext
    input_lines = ['if True:', '    print("hello")']
    ctx = IndentationContext.from_diff_lines(input_lines, '    ')
    result = ctx.adjust_lines(input_lines)
    assert result == ['    if True:', '        print("hello")']

def test_indentation_nested_block():
    """Test that nested block structure is preserved."""
    from bots.tools.code_tools import IndentationContext
    input_lines = ['if True:', '    if False:', '        print("nested")']
    ctx = IndentationContext.from_diff_lines(input_lines, '    ')
    result = ctx.adjust_lines(input_lines)
    assert result == ['    if True:', '        if False:', '            print("nested")']

def test_process_state_indentation():
    """Test that _process_state_transition maintains indentation through state changes."""
    from bots.tools.code_tools import DiffProgress, DiffState
    progress = DiffProgress()
    file_lines = ['def test():', '    if True:', '        print("hello")', '    print("world")']
    progress.state = DiffState.REMOVE
    progress.current_block = ['    if True:', '        print("hello")']
    error = _process_state_transition(progress, file_lines)
    assert error is None
    progress.state = DiffState.ADD
    progress.current_block = ['    if False:', '        print("goodbye")']
    error = _process_state_transition(progress, file_lines)
    assert error is None
    assert file_lines == ['def test():', '    if False:', '        print("goodbye")', '    print("world")']

def test_sequential_additions_indentation():
    """Test that sequential additions maintain correct relative indentation.
    This test mimics the specific case from test_inexact_indentation_multiline
    but breaks it down into explicit steps.
    """
    from bots.tools.code_tools import DiffProgress, DiffState, _process_state_transition
    file_lines = ['def test():', '    if True:', '        print("hello")']
    progress = DiffProgress()
    progress.state = DiffState.REMOVE
    progress.current_block = ['    if True:', '        print("hello")']
    error = _process_state_transition(progress, file_lines)
    assert error is None
    progress.state = DiffState.ADD
    additions = ['    if False:', '        print("goodbye")', '        if True:', '            print("nested")']
    progress.current_block = additions
    error = _process_state_transition(progress, file_lines)
    assert error is None
    print('\nFinal result:')
    print('\n'.join(file_lines))
    expected = ['def test():', '    if False:', '        print("goodbye")', '        if True:', '            print("nested")']
    assert file_lines == expected, f'Expected:\n{expected}\n\nGot:\n{file_lines}'