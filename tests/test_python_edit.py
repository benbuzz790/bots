import os
import pytest
from textwrap import dedent
from bots.tools.python_edit import python_edit

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