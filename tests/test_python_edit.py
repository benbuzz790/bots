import os
import pytest
from textwrap import dedent
from bots.tools.python_edit import python_edit
from bots.tools.python_edit import tokenize_source, detokenize_source
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
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    lines = [l.strip() for l in content.split('\n') if l.strip()]
    print(f'DEBUG - Stripped lines: {lines}')
    assert 'comment one' in content
    assert '# standalone comment' in content
    assert 'comment two' in content
    assert lines.index('# standalone comment') < lines.index('z = 3')
    assert lines.index('z = 3') < lines.index('y = 2  # comment two')

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

def test_file_level_preservation():
    """Test that file-level operations preserve formatting"""
    content = '\n    # Top level comment\n    import os  # os import\n\n    # Another comment\n    x = 1  # first assignment\n\n    # Final comment\n    y = 2  # second assignment\n    '
    test_file = setup_test_file('tmp', content)
    result = python_edit(test_file, 'z = 3', insert_after='__FILE_START__')
    with open(test_file) as f:
        content = f.read()
    print(f'DEBUG - File content:\n{content}')
    expected = '\n    # Top level comment\n    import os  # os import\n\n    z = 3\n\n    # Another comment\n    x = 1  # first assignment\n\n    # Final comment\n    y = 2  # second assignment\n    '.strip()
    print(f'DEBUG - Expected:\n{expected}')
    assert content.strip() == expected

    def test_minimal_tokenize():
        """Test tokenization of minimal valid Python"""
        source = 'x = 1'
        tokenized, token_map = tokenize_source(source)
        print(f'DEBUG - Tokenized: {tokenized}')
        print(f'DEBUG - Token map: {token_map}')
        ast.parse(tokenized)
        assert detokenize_source(tokenized, token_map) == source

    def test_minimal_tokenize_with_comment():
        """Test tokenization with just a comment"""
        source = '# A comment'
        tokenized, token_map = tokenize_source(source)
        print(f'DEBUG - Tokenized: {tokenized}')
        print(f'DEBUG - Token map: {token_map}')
        ast.parse(tokenized)
        assert detokenize_source(tokenized, token_map) == source

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
    tokenized, token_map = tokenize_source(source)
    assert '# Header comment' not in tokenized
    assert '"string literal"' not in tokenized
    assert '# Inline comment' not in tokenized
    assert '__TOKEN__' in tokenized
    assert detokenize_source(tokenized, token_map) == source
    restored = detokenize_source(tokenized, token_map)
    assert restored == source

def test_tokenize_multiline():
    """Test tokenization of multiline strings and nested structures"""
    source = '\n    def func():\n        """\n        Multiline\n        docstring\n        """\n        # Comment\n        if True:\n            # Nested comment\n            x = 1\n    '
    tokenized, token_map = tokenize_source(source)
    assert '"""' not in tokenized
    assert '# Comment' not in tokenized
    assert '# Nested comment' not in tokenized
    restored = detokenize_source(tokenized, token_map)
    assert restored == source

def test_tokenize_edge_cases():
    """Test tokenization of edge cases"""
    source = '\n    x = 1; y = 2  # Multiple statements\n    # Comment with ; semicolon\n    s = "String # with hash"\n    q = \'String ; with semicolon\'\n    """\n    Multiline string\n    # with comment\n    ; with semicolon\n    """\n    '
    tokenized, token_map = tokenize_source(source)
    assert '__TOKEN__' in tokenized
    assert detokenize_source(tokenized, token_map) == source
    restored = detokenize_source(tokenized, token_map)
    assert restored == source

def test_minimal_tokenize():
    """Test tokenization of minimal valid Python"""
    source = 'x = 1'
    tokenized, token_map = tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    ast.parse(tokenized)
    assert detokenize_source(tokenized, token_map) == source

def test_minimal_tokenize_with_comment():
    """Test tokenization with just a comment"""
    source = '# A comment'
    tokenized, token_map = tokenize_source(source)
    print(f'DEBUG - Tokenized: {tokenized}')
    print(f'DEBUG - Token map: {token_map}')
    ast.parse(tokenized)
    assert detokenize_source(tokenized, token_map) == source

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
    tokenized, token_map = tokenize_source(source)
    print(f'DEBUG - Tokenized:\n{tokenized}')
    print(f'DEBUG - Token map:\n{token_map}')
    ast.parse(tokenized)
    restored = detokenize_source(tokenized, token_map)
    print(f'DEBUG - Restored:\n{restored}')
    assert restored == source

def test_minimal_nested_multiline():
    """Test tokenization of nested multiline content"""
    source = 'def outer():\n        """Outer docstring"""\n        def inner():\n            """\n            Inner\n            docstring\n            """\n            pass'
    tokenized, token_map = tokenize_source(source)
    print(f'DEBUG - Tokenized:\n{tokenized}')
    print(f'DEBUG - Token map:\n{token_map}')
    ast.parse(tokenized)
    restored = detokenize_source(tokenized, token_map)
    print(f'DEBUG - Restored:\n{restored}')
    assert restored == source

def test_minimal_complex_indent():
    """Test tokenization with complex indentation patterns"""
    source = 'def test():\n        # Comment at level 1\n        if True:\n            # Comment at level 2\n            if True:\n                """\n                Docstring at\n                level 3\n                """\n                # Comment at level 3\n                pass'
    tokenized, token_map = tokenize_source(source)
    print(f'DEBUG - Tokenized:\n{tokenized}')
    print(f'DEBUG - Token map:\n{token_map}')
    ast.parse(tokenized)
    restored = detokenize_source(tokenized, token_map)
    print(f'DEBUG - Restored:\n{restored}')
    assert restored == source
