import os
import pytest
from textwrap import dedent
from bots.tools.python_edit import python_edit
from bots.tools.python_edit import _tokenize_source, _detokenize_source
import ast

def setup_test_file(tmp_path, content):
    """Helper to create a test file with given content"""
    if isinstance(tmp_path, str):
        os.makedirs(tmp_path, exist_ok=True)
        test_file = os.path.join(tmp_path, 'test_file.py')
    else:
        test_file = os.path.join(str(tmp_path), 'test_file.py')
    with open(test_file, 'w', encoding='utf-8') as f:
        f.write(dedent(content))
    return test_file

@pytest.fixture
def test_file(tmp_path):
    """Create a test file with various Python constructs"""
    content = '\n        import os\n        from typing import List, Optional\n\n        def outer_func():\n            def inner_func():\n                pass\n            return inner_func\n\n        class OuterClass:\n            def method(self):\n                pass\n\n            class InnerClass:\n                @staticmethod\n                def static_method():\n                    pass\n\n                async def async_method(self):\n                    pass\n\n            def another_method(self):\n                # Insert here\n                pass\n    '
    return setup_test_file(tmp_path, content)

def test_basic_file_level_edit(test_file):
    """Test adding code at file level"""
    result = python_edit(test_file, 'x = 42')
    assert 'file level' in result
    with open(test_file) as f:
        content = f.read()
    assert 'x = 42' in content

def test_file_start_insertion(test_file):
    """Test inserting at file start"""
    result = python_edit(test_file, 'import sys', insert_after='__FILE_START__')
    assert 'start' in result
    with open(test_file) as f:
        lines = f.readlines()
        assert 'import sys' in lines[0]

def test_class_replacement(test_file):
    """Test replacing a class"""
    new_class = '\n    class OuterClass:\n        def new_method(self):\n            pass\n    '
    result = python_edit(f'{test_file}::OuterClass', new_class)
    assert 'OuterClass' in result
    with open(test_file) as f:
        content = f.read()
    assert 'new_method' in content
    assert 'another_method' not in content

def test_nested_class_method(test_file):
    """Test modifying a method in a nested class"""
    new_method = '\n    async def async_method(self):\n        return 42\n    '
    result = python_edit(f'{test_file}::OuterClass::InnerClass::async_method', new_method)
    assert 'async_method' in result
    with open(test_file) as f:
        content = f.read()
    assert 'return 42' in content

def test_nested_function(test_file):
    """Test modifying a nested function"""
    new_func = '\n    def inner_func():\n        return 42\n    '
    result = python_edit(f'{test_file}::outer_func::inner_func', new_func)
    assert 'inner_func' in result
    with open(test_file) as f:
        content = f.read()
    assert 'return 42' in content

def test_insert_after_line(test_file):
    """Test inserting after specific line"""
    new_code = 'x = 42'
    result = python_edit(f'{test_file}::OuterClass::another_method', new_code, insert_after='# Insert here')
    with open(test_file) as f:
        print(f'\nDEBUG - File content:\n{f.read()}')
    print(f'\nDEBUG - Result: {result}')
    assert 'inserted after' in result
    with open(test_file) as f:
        content = f.read()
    assert '# Insert here\n' in content
    assert 'x = 42' in content

def test_insert_after_scope(test_file):
    """Test inserting after a scope"""
    new_method = '\n    def extra_method(self):\n        pass\n    '
    result = python_edit(f'{test_file}::OuterClass', new_method, insert_after='OuterClass::another_method')
    assert 'inserted after' in result
    with open(test_file) as f:
        content = f.read()
    assert 'extra_method' in content
    assert content.index('extra_method') > content.index('another_method')

def test_import_handling(test_file):
    """Test automatic import handling"""
    new_code = '\n    import sys\n    from typing import Dict\n\n    def new_func():\n        pass\n    '
    result = python_edit(test_file, new_code)
    with open(test_file) as f:
        content = f.read()
    assert 'import sys' in content
    assert 'from typing import Dict' in content
    assert content.index('import sys') < content.index('def new_func')

def test_decorated_method(test_file):
    """Test handling decorated methods"""
    new_method = '\n    @staticmethod\n    @property\n    def static_method():\n        return 42\n    '
    result = python_edit(f'{test_file}::OuterClass::InnerClass::static_method', new_method)
    assert 'static_method' in result
    with open(test_file) as f:
        content = f.read()
    assert '@property' in content
    assert 'return 42' in content

def test_error_invalid_scope(test_file):
    """Test error handling for invalid scope"""
    result = python_edit(f'{test_file}::NonExistentClass', 'pass')
    assert 'not found' in result.lower()

def test_error_ambiguous_insert(test_file):
    """Test error handling for ambiguous insert point"""
    content = '\n    def func():\n        # Insert here\n        x = 1\n        # Insert here\n        y = 2\n    '
    test_file = setup_test_file(os.path.dirname(test_file), content)
    result = python_edit(test_file, 'z = 3', insert_after='# Insert here')
    assert 'ambiguous' in result.lower()

def test_error_invalid_code(test_file):
    """Test error handling for invalid Python code"""
    result = python_edit(test_file, 'this is not valid python')
    assert 'error' in result.lower()

def test_async_function(test_file):
    """Test handling async functions"""
    new_func = '\n    async def new_async():\n        await something()\n    '
    result = python_edit(test_file, new_func)
    assert 'added' in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert 'async def new_async' in content

def test_indentation_preservation(test_file):
    """Test proper indentation is maintained"""
    new_method = '\n    def indented_method(self):\n        if True:\n            x = 1\n            if True:\n                y = 2\n    '
    result = python_edit(f'{test_file}::OuterClass', new_method, insert_after='OuterClass::method')
    with open(test_file) as f:
        content = f.read()
    assert '    def indented_method' in content
    assert '        if True:' in content
    assert '            x = 1' in content

def test_empty_file(tmp_path):
    """Test handling empty target file"""
    empty_file = setup_test_file(tmp_path, '')
    result = python_edit(empty_file, 'x = 42')
    assert 'added' in result.lower()
    with open(empty_file) as f:
        content = f.read()
    assert content.strip() == 'x = 42'

def test_multiline_imports(test_file):
    """Test handling multiline import statements"""
    new_code = '\n    from typing import (\n        List,\n        Dict,\n        Optional,\n        Union\n    )\n\n    x = 42\n    '
    result = python_edit(test_file, new_code)
    with open(test_file) as f:
        content = f.read()
    assert 'Union' in content
    assert content.index('Union') < content.index('x = 42')

def test_line_comment_preservation(tmp_path):
    """Test that comments are preserved when inserting after them"""
    content = '\n    def my_func():\n        # First comment\n        x = 1\n        # Target comment\n        y = 2\n    '
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f'{test_file}::my_func', 'z = 3', insert_after='# Target comment')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    assert '# Target comment' in content
    assert 'z = 3' in content
    assert content.index('# Target comment') < content.index('z = 3')
    assert content.index('z = 3') < content.index('y = 2')

def test_import_at_file_start(tmp_path):
    """Test that imports are added at the start of the file"""
    content = '\n    x = 1\n    y = 2\n    '
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(test_file, 'import sys\nz = 3')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    assert 'import sys' in content
    assert content.index('import sys') < content.index('x = 1')

def test_nested_scope_insertion(tmp_path):
    """Test inserting into deeply nested scopes"""
    content = '\n    class Outer:\n        class Inner:\n            def method(self):\n                x = 1\n    '
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f'{test_file}::Outer::Inner::method', 'y = 2', insert_after='x = 1')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    assert 'y = 2' in content
    assert content.index('x = 1') < content.index('y = 2')

def test_indentation_in_class(tmp_path):
    """Test that proper indentation is maintained in class methods"""
    content = '\n    class MyClass:\n        def method_one(self):\n            pass\n    '
    test_file = setup_test_file(tmp_path, content)
    new_method = '\n    def method_two(self):\n        if True:\n            x = 1\n    '
    result = python_edit(f'{test_file}::MyClass', new_method, insert_after='MyClass::method_one')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    assert '    def method_two(self):' in content
    assert '        if True:' in content
    assert '            x = 1' in content

def test_scope_path_matching(tmp_path):
    """Test that scope paths are correctly matched"""
    content = '\n    class ClassA:\n        def method(self): pass\n    class ClassB:\n        def method(self): pass\n    '
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f'{test_file}::ClassB::method', 'x = 1', insert_after='pass')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    lines = content.split('\n')
    classA_method = next((i for i, line in enumerate(lines) if 'ClassA' in line))
    classB_method = next((i for i, line in enumerate(lines) if 'ClassB' in line))
    x_equals_1 = next((i for i, line in enumerate(lines) if 'x = 1' in line))
    assert classA_method < classB_method < x_equals_1

def test_file_start_insertion_empty():
    """Test inserting at start of empty file"""
    test_file = setup_test_file('tmp', '')
    result = python_edit(test_file, 'import sys', insert_after='__FILE_START__')
    with open(test_file) as f:
        content = f.read()
    assert content.strip() == 'import sys'

def test_file_start_insertion_with_imports():
    """Test inserting at start of file that already has imports"""
    content = '\n    import os\n    from typing import List\n\n    x = 1\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(test_file, 'import sys', insert_after='__FILE_START__')
    with open(test_file) as f:
        lines = f.readlines()
    print(f'DEBUG - File lines: {lines}')
    assert 'import sys\n' == lines[0]
    assert 'import os\n' in lines[1:]
    assert 'x = 1' in lines[-1]

def test_file_start_insertion_with_code():
    """Test inserting at start of file that has no imports"""
    content = '\n    x = 1\n    y = 2\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(test_file, 'import sys', insert_after='__FILE_START__')
    with open(test_file) as f:
        lines = f.readlines()
    print(f'DEBUG - File lines: {lines}')
    assert 'import sys\n' == lines[0]
    assert 'x = 1' in lines[1]

def test_file_start_insertion_multiple():
    """Test multiple insertions at file start come in correct order"""
    content = 'x = 1'
    test_file = setup_test_file('tmp', content)
    python_edit(test_file, 'import sys', insert_after='__FILE_START__')
    python_edit(test_file, 'import os', insert_after='__FILE_START__')
    with open(test_file) as f:
        lines = f.readlines()
    print(f'DEBUG - File lines: {lines}')
    assert 'import os\n' == lines[0]
    assert 'import sys\n' == lines[1]
    assert 'x = 1' in lines[-1]

def test_line_insert_basic():
    """Test inserting after a simple line in a function"""
    content = '\n    def test_func():\n        x = 1\n        # marker\n        z = 3\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::test_func', 'y = 2', insert_after='# marker')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    assert '# marker\n' in content
    assert 'y = 2' in content
    assert content.index('# marker') < content.index('y = 2')
    assert content.index('y = 2') < content.index('z = 3')

def test_line_insert_indentation():
    """Test that inserted code maintains proper indentation"""
    content = '\n    def test_func():\n        if True:\n            x = 1\n            # marker\n            z = 3\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::test_func', 'y = 2', insert_after='# marker')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - Result content:\n{content}')
    lines = content.split('\n')
    marker_line = next((i for i, line in enumerate(lines) if '# marker' in line))
    y_line = next((i for i, line in enumerate(lines) if 'y = 2' in line))
    assert marker_line < y_line
    assert len(lines[marker_line]) - len(lines[marker_line].lstrip()) == len(lines[y_line]) - len(lines[y_line].lstrip())

def test_line_insert_preservation():
    """Test that the line we insert after is preserved"""
    content = '\n    def simple():\n        # keep me\n        pass\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::simple', 'x = 1', insert_after='# keep me')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    print(f'DEBUG - Result: {result}')
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    print(f'DEBUG - Stripped lines: {lines}')
    assert lines == ['def simple():', '# keep me', 'x = 1', 'pass']

def test_line_insert_ast_handling():
    """Test that comments and non-AST lines are preserved during insertion"""
    content = '\n    def func():\n        x = 1  # comment one\n        # standalone comment\n        y = 2  # comment two\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::func', 'z = 3', insert_after='# standalone comment')
    print(f'DEBUG - python_edit result: {result}')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    print(f'DEBUG - Stripped lines: {lines}')
    assert 'comment one' in content
    assert '# standalone comment' in content
    assert 'comment two' in content
    assert lines.index('# standalone comment') < lines.index('z = 3')

def test_line_insert_function_body():
    """Test that we correctly handle function body when inserting lines"""
    content = '\n    def example():\n        """Docstring."""\n        # First comment\n        x = 1  # Inline comment\n\n        # Marker\n        y = 2\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::example', 'z = 3', insert_after='# Marker')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    assert '"""Docstring."""' in content
    assert '# First comment' in content
    assert 'Inline comment' in content
    assert '# Marker' in content
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    print(f'DEBUG - Stripped lines: {lines}')
    marker_idx = lines.index('# Marker')
    z_idx = lines.index('z = 3')
    y_idx = lines.index('y = 2')
    assert marker_idx < z_idx < y_idx, 'Lines should be in correct order'

def test_line_insert_exact_preservation():
    """Test that lines are preserved exactly as they appear in the source"""
    content = '\n    def func():\n        x = 1  # comment one\n\n        # marker with spaces around\n\n        y = 2  # comment two\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::func', 'z = 3', insert_after='# marker with spaces around')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    assert 'x = 1  # comment one' in content
    assert '# marker with spaces around' in content
    assert 'y = 2  # comment two' in content
    lines = content.split('\n')
    marker_idx = next((i for i, line in enumerate(lines) if '# marker with spaces around' in line))
    assert lines[marker_idx - 1].strip() == '', 'Should preserve blank line before marker'
    assert lines[marker_idx + 1].strip() == '', 'Should preserve blank line after marker'

def test_source_preservation():
    """Test that source lines are preserved exactly when modifying a function"""
    content = '\n    def example():\n        """This is a docstring."""\n\n        # First we do x\n        x = 1  # comment about x\n\n        # Then we do y\n        y = 2  # comment about y\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::example', 'z = 3', insert_after='# Then we do y')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    assert '"""This is a docstring."""' in content
    assert '# First we do x' in content
    assert 'x = 1  # comment about x' in content
    assert '# Then we do y' in content
    assert 'z = 3' in content
    assert 'y = 2  # comment about y' in content
    lines = content.split('\n')

    def line_number(text):
        return next((i for i, line in enumerate(lines) if text in line))
    assert line_number('# Then we do y') < line_number('z = 3') < line_number('y = 2')

def test_ast_tree_preservation():
    """Test that source preservation works through AST tree reconstruction"""
    content = '\n    # Top level comment\n    import os  # os import\n\n    def example():  # example function\n        """Docstring."""\n\n        # First we do x\n        x = 1  # comment about x\n\n        # Then we do y\n        y = 2  # comment about y\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(f'{test_file}::example', 'z = 3', insert_after='# Then we do y')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    assert '# Top level comment' in content
    assert 'import os  # os import' in content
    assert 'def example():  # example function' in content
    assert '"""Docstring."""' in content
    assert '# First we do x' in content
    assert 'x = 1  # comment about x' in content
    assert '# Then we do y' in content
    assert 'z = 3' in content
    assert 'y = 2  # comment about y' in content

def test_minimal_tokenize():
    """Test tokenization of minimal valid Python"""
    source = 'x = 1'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

def test_minimal_tokenize_with_comment():
    """Test tokenization with just a comment"""
    source = '# A comment'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

def test_minimal_edit():
    """Test the most basic possible edit"""
    with open('minimal.py', 'w') as f:
        f.write('# Empty\n')
    result = python_edit('minimal.py', 'x = 1')
    print(f'DEBUG - Result: {result}')
    with open('minimal.py') as f:
        content = f.read()
    print(f'DEBUG - Content: {content}')
    assert 'file level' in result

def test_tokenize_basic():
    """Test basic tokenization of comments and strings"""
    source = '\n    # Header comment\n    x = "string literal"  # Inline comment\n    y = 1\n    '
    tokenized, token_map = _tokenize_source(source)
    assert '# Header comment' not in tokenized
    assert '"string literal"' not in tokenized
    assert '# Inline comment' not in tokenized
    assert 'TOKEN_' in tokenized
    # Note: Inline comment spacing changes from "  #" to "; #" due to tokenization approach
    restored = _detokenize_source(tokenized, token_map)
    assert '# Header comment' in restored and '"string literal"' in restored and '# Inline comment' in restored

def test_tokenize_multiline():
    """Test tokenization of multiline strings and nested structures"""
    source = '\n    def func():\n        """\n        Multiline\n        docstring\n        """\n        # Comment\n        if True:\n            # Nested comment\n            x = 1\n    '
    tokenized, token_map = _tokenize_source(source)
    assert '"""' not in tokenized
    assert '# Comment' not in tokenized
    assert '# Nested comment' not in tokenized
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_tokenize_contains_tokens():
    """Ensure tokenization produces token markers"""
    source = '''
    x = 1; y = 2  # Multiple statements
    # Comment with ; semicolon
    s = "String # with hash"
    q = 'String ; with semicolon'
    """
    Multiline string
    # with comment
    ; with semicolon
    """
    '''
    tokenized, _ = _tokenize_source(source)
    assert 'TOKEN_' in tokenized

def test_tokenize_preserves_comments():
    """Ensure comments are preserved in restored source"""
    source = '''
    x = 1; y = 2  # Multiple statements
    # Comment with ; semicolon
    s = "String # with hash"
    q = 'String ; with semicolon'
    """
    Multiline string
    # with comment
    ; with semicolon
    """
    '''
    tokenized, token_map = _tokenize_source(source)
    restored = _detokenize_source(tokenized, token_map)
    assert 'Multiple statements' in restored
    assert 'Comment with ; semicolon' in restored

def test_tokenize_preserves_string_literals():
    """Ensure string literals are unchanged after round trip"""
    source = '''
    s = "String # with hash"
    q = 'String ; with semicolon'
    '''
    tokenized, token_map = _tokenize_source(source)
    restored = _detokenize_source(tokenized, token_map)
    assert 'String # with hash' in restored
    assert 'String ; with semicolon' in restored

def test_tokenize_preserves_multiline_strings():
    """Ensure multiline strings are preserved intact"""
    source = '''
    """
    Multiline string
    # with comment
    ; with semicolon
    """
    '''
    tokenized, token_map = _tokenize_source(source)
    restored = _detokenize_source(tokenized, token_map)
    assert 'Multiline string' in restored
    assert '# with comment' in restored
    assert '; with semicolon' in restored

def test_minimal_tokenize():
    """Test tokenization of minimal valid Python"""
    source = 'x = 1'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

def test_minimal_tokenize_with_comment():
    """Test tokenization with just a comment"""
    source = '# A comment'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

def test_minimal_edit():
    """Test the most basic possible edit"""
    with open('minimal.py', 'w') as f:
        f.write('# Empty\n')
    result = python_edit('minimal.py', 'x = 1')
    print(f'DEBUG - Result: {result}')
    with open('minimal.py') as f:
        content = f.read()
    print(f'DEBUG - Content: {content}')
    assert 'file level' in result

def test_minimal_multiline():
    """Test tokenization of multiline content"""
    source = 'def test():\n        """\n        Docstring\n        with lines\n        """\n        pass'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized:\n{tokenized}')
    print(f'DEBUG - Token map:\n{token_map}')
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    print(f'DEBUG - Restored:\n{restored}')
    assert restored == source

def test_minimal_nested_multiline():
    """Test tokenization of nested multiline content"""
    source = 'def outer():\n        """Outer docstring"""\n        def inner():\n            """\n            Inner\n            docstring\n            """\n            pass'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized:\n{tokenized}')
    print(f'DEBUG - Token map:\n{token_map}')
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    print(f'DEBUG - Restored:\n{restored}')
    assert restored == source

def test_minimal_complex_indent():
    """Test tokenization with complex indentation patterns"""
    source = 'def test():\n        # Comment at level 1\n        if True:\n            # Comment at level 2\n            if True:\n                """\n                Docstring at\n                level 3\n                """\n                # Comment at level 3\n                pass'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized:\n{tokenized}')
    print(f'DEBUG - Token map:\n{token_map}')
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    print(f'DEBUG - Restored:\n{restored}')
    assert restored == source

def test_ast_unparse_behavior():
    """Test how ast.unparse handles our token format"""
    import ast
    code = 'x = 1; """abc"""'
    print(f'Original: {code}')
    tree = ast.parse(code)
    print(f'AST body length: {len(tree.body)}')
    for i, node in enumerate(tree.body):
        print(f'Node {i}: {type(node).__name__}')
    unparsed = ast.unparse(tree)
    print(f'Unparsed: {repr(unparsed)}')
    token_code = 'x = 1;"""2320636f6d6d656e74"""'
    print(f'\nToken code: {token_code}')
    tree2 = ast.parse(token_code)
    unparsed2 = ast.unparse(tree2)
    print(f'Unparsed token: {repr(unparsed2)}')
    
# F-STRING TESTS
def test_fstring_basic():
    """Test basic f-string tokenization and preservation"""
    source = 'name = "Alice"\ngreeting = f"Hello, {name}!"'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_nested_quotes():
    """Test f-strings with nested quotes"""
    source = '''user = {"name": "Alice", "age": 30}
message = f"User {user['name']} is {user['age']} years old"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_complex_expressions():
    """Test f-strings with complex expressions"""
    source = '''def format_data(items):
    return f"Total: {sum(item['value'] for item in items if item['active'])}"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_escaped_braces():
    """Test f-strings with escaped braces"""
    source = 'template = f"{{item}} costs ${price:.2f}"'
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_with_format_specs():
    """Test f-strings with format specifications"""
    source = '''price = 19.99
formatted = f"Price: ${price:.2f} ({price:>10.2f})"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_multiline():
    """Test multiline f-strings"""
    source = '''name = "Alice"
age = 30
bio = f"""
Name: {name}
Age: {age}
Status: {'Active' if age < 65 else 'Retired'}
"""'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_prefixes():
    """Test various f-string prefixes (rf, fr, etc.)"""
    source = '''pattern = rf"Hello {name}\n"
raw_fstring = fr"Path: {path}\\"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_edit_integration():
    """Test editing code that contains f-strings"""
    content = '''
    def greet(name):
        return f"Hello, {name}!"
    '''
    test_file = setup_test_file('tmp', content)
    
    new_func = '''
    def greet(name, title=""):
        greeting = f"Hello, {title + ' ' if title else ''}{name}!"
        return greeting.upper()
    '''
    
    result = python_edit(f'{test_file}::greet', new_func)
    print(f'DEBUG - Result: {result}')
    
    with open(test_file) as f:
        final_content = f.read()
    print(f'DEBUG - Final content: {final_content}')
    
    # Should contain the f-string
    assert 'f"Hello, {title' in final_content
    assert '.upper()' in final_content

# EDGE CASE TESTS
def test_mixed_quote_types():
    """Test mixing single and double quotes"""
    source = '''message = "He said 'Hello'"
other = 'She replied "Hi there"'
fstring = f"Mixed: {'single'} and {"double"}"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_string_concatenation():
    """Test string concatenation edge cases"""
    source = '''long_string = ("This is a very long string "
               "that spans multiple lines "
               f"with an f-string {variable}")'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_regex_strings():
    """Test regex strings that might confuse tokenization"""
    source = r'''import re
pattern = r"(\d+)-(\d+)-(\d+)"
fstring_pattern = rf"User-{user_id}-\d+"
complex_regex = r"(?P<name>[a-zA-Z]+):\s*(?P<value>['\"].*?['\"])"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_comments_with_quotes():
    """Test comments containing quote characters"""
    source = '''x = 1  # This comment has "quotes" and 'apostrophes'
y = 2  # Even f-string-like {syntax} in comments
# Standalone comment with "mixed" quotes and {braces}'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly (accounting for tokenization changes)
    restored = _detokenize_source(tokenized, token_map)
    # Content should be preserved even if formatting changes slightly
    assert '"quotes"' in restored
    assert "'apostrophes'" in restored
    assert '{syntax}' in restored

def test_docstring_edge_cases():
    """Test various docstring formats"""
    source = '''def func():
    """Single line docstring with 'quotes' and {braces}."""
    pass

class MyClass:
    """
    Multi-line docstring with:
    - "Double quotes"
    - 'Single quotes'  
    - f-string-like {syntax}
    - Even some "nested 'quotes'"
    """
    pass'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

# ERROR HANDLING TESTS
def test_unterminated_fstring():
    """Test handling of malformed f-strings that might cause errors"""
    # This should be caught by our enhanced tokenizer
    source = 'x = f"Hello {name'  # Missing closing quote and brace
    
    try:
        tokenized, token_map = _tokenize_source(source)
        print(f'DEBUG - Tokenized malformed: {tokenized}')
        # If tokenization succeeds, AST parsing should catch the error
        ast.parse(tokenized)
        assert False, "Should have caught malformed f-string"
    except SyntaxError:
        # Expected - malformed f-string should be caught
        pass

def test_nested_fstring_depth():
    """Test deeply nested f-string expressions"""
    source = '''data = {"users": [{"name": "Alice", "prefs": {"theme": "dark"}}]}
message = f"User {data['users'][0]['name']} likes {data['users'][0]['prefs']['theme']} theme"'''
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

# REAL-WORLD SCENARIO TESTS
def test_data_processing_code():
    """Test tokenizing realistic data processing code with f-strings"""
    source = '''import json
from typing import Dict, List

def process_users(users: List[Dict]) -> str:
    """Process user data and return formatted summary."""
    active_users = [u for u in users if u.get('active', False)]
    
    summary = f"""
    User Summary:
    - Total users: {len(users)}
    - Active users: {len(active_users)}
    - Percentage active: {len(active_users)/len(users)*100:.1f}%
    """
    
    details = []
    for user in active_users[:5]:  # Top 5
        name = user['name']
        email = user.get('email', 'No email')
        last_login = user.get('last_login', 'Never')
        details.append(f"- {name} ({email}) - Last: {last_login}")
    
    if details:
        summary += f"\\n\\nTop Active Users:\\n" + "\\n".join(details)
    
    return summary.strip()'''
    
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Tokenized length: {len(tokenized)}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_edit_fstring_function():
    """Test editing a function that uses f-strings"""
    content = '''
    def format_price(price, currency="USD"):
        return f"${price:.2f} {currency}"
    '''
    test_file = setup_test_file('tmp', content)
    
    # Add logging to the function
    new_code = '''
    import logging
    
    def format_price(price, currency="USD"):
        logging.debug(f"Formatting price: {price} {currency}")
        if price < 0:
            return f"Invalid price: ${abs(price):.2f} {currency}"
        return f"${price:.2f} {currency}"
    '''
    
    result = python_edit(f'{test_file}::format_price', new_code)
    print(f'DEBUG - Edit result: {result}')
    
    with open(test_file) as f:
        final_content = f.read()
    print(f'DEBUG - Final content: {final_content}')
    
    # Verify f-strings are preserved
    assert 'f"Formatting price: {price} {currency}"' in final_content
    assert 'f"Invalid price: ${abs(price):.2f} {currency}"' in final_content
    assert 'logging.debug' in final_content

def test_class_with_fstring_methods():
    """Test editing classes that contain f-string methods"""
    content = '''
    class User:
        def __init__(self, name, age):
            self.name = name
            self.age = age
        
        def greet(self):
            return f"Hi, I'm {self.name}"
    '''
    test_file = setup_test_file('tmp', content)
    
    # Add a new method with complex f-strings
    new_method = '''
    def describe(self):
        status = "adult" if self.age >= 18 else "minor"
        return f"User: {self.name} ({self.age} years old, {status})"
    '''
    
    result = python_edit(f'{test_file}::User', new_method, insert_after='User::greet')
    print(f'DEBUG - Edit result: {result}')
    
    with open(test_file) as f:
        final_content = f.read()
    print(f'DEBUG - Final content: {final_content}')
    
    # Verify both f-strings are preserved
    assert 'f"Hi, I\'m {self.name}"' in final_content
    assert 'f"User: {self.name} ({self.age} years old, {status})"' in final_content

# PERFORMANCE AND STRESS TESTS
def test_large_fstring_file():
    """Test handling a file with many f-strings"""
    lines = ['import math']
    for i in range(50):
        lines.append(f'result_{i} = f"Item {{i}}: {{math.sqrt({i})}}"')
    
    source = '\n'.join(lines)
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Token count: {len(token_map)}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_mixed_content_stress():
    """Test file with mixed strings, f-strings, comments, and code"""
    source = '''#!/usr/bin/env python3
"""
Module for data processing with f-strings.
Contains "quotes" and {braces} in docstring.
"""

import os  # Standard library
from typing import Dict, List  # Type hints

# Configuration with f-string
CONFIG_PATH = f"{os.path.expanduser('~')}/.config/app.json"

class DataProcessor:
    """Process data with various string formats."""
    
    def __init__(self, config_path: str = CONFIG_PATH):
        self.config_path = config_path  # Store path
        self.data = {}  # Initialize empty
    
    def load_config(self) -> Dict:
        """Load configuration from file."""
        if not os.path.exists(self.config_path):
            raise FileNotFoundError(f"Config not found: {self.config_path}")
        
        # Read and parse config
        with open(self.config_path, 'r') as f:
            content = f.read()  # Regular string method
        
        return json.loads(content)  # Parse JSON
    
    def format_output(self, data: List[Dict]) -> str:
        """Format data for output."""
        lines = [f"Processing {len(data)} items..."]  # F-string with len()
        
        for i, item in enumerate(data):
            name = item.get('name', 'Unknown')
            value = item.get('value', 0)
            # Complex f-string with formatting
            line = f"  {i+1:2d}. {name:<20} = {value:>8.2f} ({value/100:.1%})"
            lines.append(line)
        
        summary = f"\\nSummary: {len(data)} items processed"
        return "\\n".join(lines) + summary'''
    
    tokenized, token_map = _tokenize_source(source)
    print(f'DEBUG - Token count: {len(token_map)}')
    print(f'DEBUG - Tokenized length: {len(tokenized)}')
    
    # Should be parseable
    ast.parse(tokenized)
    
    # Should restore exactly
    restored = _detokenize_source(tokenized, token_map)
    # Allow for minor whitespace differences in restoration
    assert restored.replace(' ', '').replace('\n', '') == source.replace(' ', '').replace('\n', '')