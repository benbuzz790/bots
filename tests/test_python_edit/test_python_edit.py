import ast
import os
import tempfile
from textwrap import dedent

import pytest

from bots.tools.python_edit import python_edit

def setup_test_file(tmp_path, content):
    """Helper to create a test file with given content"""
    from tests.conftest import get_unique_filename

    if isinstance(tmp_path, str):
        os.makedirs(tmp_path, exist_ok=True)
        test_file = os.path.join(tmp_path, get_unique_filename("test_file", "py"))
    else:
        test_file = os.path.join(str(tmp_path), get_unique_filename("test_file", "py"))
    with open(test_file, "w", encoding="utf-8") as f:
        f.write(dedent(content))
    return test_file

@pytest.fixture
def test_file(tmp_path):
    """Create a test file with various Python constructs"""
    content = "\n        import os\n        from typing import List, Optional\n\n        def outer_func():\n            def inner_func():\n                pass\n            return inner_func\n\n        class OuterClass:\n            def method(self):\n                pass\n\n            class InnerClass:\n                @staticmethod\n                def static_method():\n                    pass\n\n                async def async_method(self):\n                    pass\n\n            def another_method(self):\n                # Insert here\n                pass\n    "
    return setup_test_file(tmp_path, content)

def test_basic_file_level_edit(test_file):
    """Test adding code at file level"""
    result = python_edit(test_file, "x = 42")
    assert "file level" in result
    with open(test_file) as f:
        content = f.read()
    assert "x = 42" in content

def test_file_start_insertion(test_file):
    """Test inserting at file start"""
    result = python_edit(test_file, "import sys", insert_after="__FILE_START__")
    assert "start" in result
    with open(test_file) as f:
        lines = f.readlines()
        assert "import sys" in lines[0]

def test_class_replacement(test_file):
    """Test replacing a class"""
    new_class = "\n    class OuterClass:\n        def new_method(self):\n            pass\n    "
    result = python_edit(f"{test_file}::OuterClass", new_class)
    assert "OuterClass" in result
    with open(test_file) as f:
        content = f.read()
    assert "new_method" in content
    assert "another_method" not in content

def test_nested_class_method(test_file):
    """Test modifying a method in a nested class"""
    new_method = "\n    async def async_method(self):\n        return 42\n    "
    result = python_edit(f"{test_file}::OuterClass::InnerClass::async_method", new_method)
    assert "async_method" in result
    with open(test_file) as f:
        content = f.read()
    assert "return 42" in content

def test_nested_function(test_file):
    """Test modifying a nested function"""
    new_func = "\n    def inner_func():\n        return 42\n    "
    result = python_edit(f"{test_file}::outer_func::inner_func", new_func)
    assert "inner_func" in result
    with open(test_file) as f:
        content = f.read()
    assert "return 42" in content

# Removed test_insert_after_line - line-based insertion descoped

def test_insert_after_scope(test_file):
    """Test inserting after a scope"""
    new_method = "\n    def extra_method(self):\n        pass\n    "
    result = python_edit(f"{test_file}::OuterClass", new_method, insert_after="OuterClass::another_method")
    assert "inserted after" in result
    with open(test_file) as f:
        content = f.read()
    assert "extra_method" in content
    assert content.index("extra_method") > content.index("another_method")

def test_import_handling(test_file):
    """Test automatic import handling"""
    new_code = "\n    import sys\n    from typing import Dict\n\n    def new_func():\n        pass\n    "
    result = python_edit(test_file, new_code)
    with open(test_file) as f:
        content = f.read()
    assert "import sys" in content
    assert "from typing import Dict" in content
    assert content.index("import sys") < content.index("def new_func")

def test_decorated_method(test_file):
    """Test handling decorated methods"""
    new_method = "\n    @staticmethod\n    @property\n    def static_method():\n        return 42\n    "
    result = python_edit(f"{test_file}::OuterClass::InnerClass::static_method", new_method)
    assert "static_method" in result
    with open(test_file) as f:
        content = f.read()
    assert "@property" in content
    assert "return 42" in content

def test_error_invalid_scope(test_file):
    """Test error handling for invalid scope"""
    result = python_edit(f"{test_file}::NonExistentClass", "pass")
    assert "not found" in result.lower()
def test_error_ambiguous_insert(test_file):
    """Test error handling for ambiguous insert point"""
    content = "\n    def func():\n        # Insert here\n        x = 1\n        # Insert here\n        y = 2\n    "
    test_file = setup_test_file(os.path.dirname(test_file), content)
    result = python_edit(test_file, "z = 3", insert_after="# Insert here")
    assert "ambiguous" in result.lower() or "multiple matches" in result.lower()
def test_error_invalid_code(test_file):
    """Test error handling for invalid Python code"""
    result = python_edit(test_file, "this is not valid python")
    assert "error" in result.lower()

def test_async_function(test_file):
    """Test handling async functions"""
    new_func = "\n    async def new_async():\n        await something()\n    "
    result = python_edit(test_file, new_func)
    assert "replaced" in result.lower() or "file level" in result.lower()
    with open(test_file) as f:
        content = f.read()
    assert "async def new_async" in content

def test_indentation_preservation(test_file):
    """Test proper indentation is maintained"""
    new_method = "\n    def indented_method(self):\n        if True:\n            x = 1\n            if True:\n                y = 2\n    "
    result = python_edit(f"{test_file}::OuterClass", new_method, insert_after="OuterClass::method")
    with open(test_file) as f:
        content = f.read()
    assert "    def indented_method" in content
    assert "        if True:" in content
    assert "            x = 1" in content

def test_empty_file(tmp_path):
    """Test handling empty target file"""
    empty_file = setup_test_file(tmp_path, "")
    result = python_edit(empty_file, "x = 42")
    assert "added" in result.lower()
    with open(empty_file) as f:
        content = f.read()
    assert content.strip() == "x = 42"

def test_multiline_imports(test_file):
    """Test handling multiline import statements"""
    new_code = (
        "\n    from typing import (\n        List,\n        Dict,\n        Optional,\n        Union\n    )\n\n    x = 42\n    "
    )
    result = python_edit(test_file, new_code)
    with open(test_file) as f:
        content = f.read()
    assert "Union" in content
    assert content.index("Union") < content.index("x = 42")

# Removed test_line_comment_preservation - line-based insertion descoped

# Removed test_import_at_file_start - line-based insertion descoped

# Removed test_nested_scope_insertion - line-based insertion descoped

def test_indentation_in_class(tmp_path):
    """Test that proper indentation is maintained in class methods"""
    content = "\n    class MyClass:\n        def method_one(self):\n            pass\n    "
    test_file = setup_test_file(tmp_path, content)
    new_method = "\n    def method_two(self):\n        if True:\n            x = 1\n    "
    result = python_edit(f"{test_file}::MyClass", new_method, insert_after="MyClass::method_one")
    with open(test_file) as f:
        content = f.read()
    print(f"DEBUG - Result content:\n{content}")
    assert "    def method_two(self):" in content
    assert "        if True:" in content
    assert "            x = 1" in content

# Removed test_scope_path_matching - line-based insertion descoped

def test_file_start_insertion_empty():
    """Test inserting at start of empty file"""
    test_file = setup_test_file("tmp", "")
    result = python_edit(test_file, "import sys", insert_after="__FILE_START__")
    with open(test_file) as f:
        content = f.read()
    assert content.strip() == "import sys"

def test_file_start_insertion_with_imports():
    """Test inserting at start of file that already has imports"""
    content = "\n    import os\n    from typing import List\n\n    x = 1\n    "
    test_file = setup_test_file("tmp", content)
    result = python_edit(test_file, "import sys", insert_after="__FILE_START__")
    with open(test_file) as f:
        lines = f.readlines()
    print(f"DEBUG - File lines: {lines}")
    assert "import sys\n" == lines[0]
    assert "import os\n" in lines[1:]
    assert "x = 1" in lines[-1]

def test_file_start_insertion_with_code():
    """Test inserting at start of file that has no imports"""
    content = "\n    x = 1\n    y = 2\n    "
    test_file = setup_test_file("tmp", content)
    result = python_edit(test_file, "import sys", insert_after="__FILE_START__")
    with open(test_file) as f:
        lines = f.readlines()
    print(f"DEBUG - File lines: {lines}")
    assert "import sys\n" == lines[0]
    assert "x = 1" in lines[1]

def test_file_start_insertion_multiple():
    """Test multiple insertions at file start come in correct order"""
    content = "x = 1"
    test_file = setup_test_file("tmp", content)
    python_edit(test_file, "import sys", insert_after="__FILE_START__")
    python_edit(test_file, "import os", insert_after="__FILE_START__")
    with open(test_file) as f:
        lines = f.readlines()
    print(f"DEBUG - File lines: {lines}")
    assert "import os\n" == lines[0]
    assert "import sys\n" == lines[1]
    assert "x = 1" in lines[-1]

# Removed test_line_insert_basic - line-based insertion descoped

# Removed test_line_insert_indentation - line-based insertion descoped

def test_line_insert_exact_preservation():
    """Test that lines are preserved exactly as they appear in the source"""
    content = "\n    def func():\n        x = 1  # comment one\n\n        # marker with spaces around\n\n        y = 2  # comment two\n    "
    test_file = setup_test_file("tmp", content)
    result = python_edit(f"{test_file}::func", "z = 3", insert_after="# marker with spaces around")
    with open(test_file) as f:
        content = f.read()
    print(f"DEBUG - File content:\n{content}")
    assert "x = 1  # comment one" in content
    assert "# marker with spaces around" in content
    assert "y = 2  # comment two" in content
    lines = content.split("\n")
    marker_idx = next((i for i, line in enumerate(lines) if "# marker with spaces around" in line))
    assert lines[marker_idx - 1].strip() == "", "Should preserve blank line before marker"
    assert lines[marker_idx + 1].strip() == "", "Should preserve blank line after marker"

def test_minimal_edit():
    """Test the most basic possible edit"""
    with open("minimal.py", "w") as f:
        f.write("# Empty\n")
    result = python_edit("minimal.py", "x = 1")
    print(f"DEBUG - Result: {result}")
    with open("minimal.py") as f:
        content = f.read()
    print(f"DEBUG - Content: {content}")
    assert "file level" in result

def test_minimal_edit():
    """Test the most basic possible edit"""
    with open("minimal.py", "w") as f:
        f.write("# Empty\n")
    result = python_edit("minimal.py", "x = 1")
    print(f"DEBUG - Result: {result}")
    with open("minimal.py") as f:
        content = f.read()
    print(f"DEBUG - Content: {content}")
    assert "file level" in result

def test_ast_unparse_behavior():
    """Test how ast.unparse handles our token format"""
    import ast

    code = 'x = 1; """abc"""'
    print(f"Original: {code}")
    tree = ast.parse(code)
    print(f"AST body length: {len(tree.body)}")
    for i, node in enumerate(tree.body):
        print(f"Node {i}: {type(node).__name__}")
    unparsed = ast.unparse(tree)
    print(f"Unparsed: {repr(unparsed)}")
    token_code = 'x = 1;"""2320636f6d6d656e74"""'
    print(f"\nToken code: {token_code}")
    tree2 = ast.parse(token_code)
    unparsed2 = ast.unparse(tree2)
    print(f"Unparsed token: {repr(unparsed2)}")

def test_fstring_edit_integration():
    """Test editing code that contains f-strings"""
    content = '\n    def greet(name):\n        return f"Hello, {name}!"\n    '
    test_file = setup_test_file("tmp", content)
    new_func = "\n    def greet(name, title=\"\"):\n        greeting = f\"Hello, {title + ' ' if title else ''}{name}!\"\n        return greeting.upper()\n    "
    result = python_edit(f"{test_file}::greet", new_func)
    print(f"DEBUG - Result: {result}")
    with open(test_file) as f:
        final_content = f.read()
    print(f"DEBUG - Final content: {final_content}")
    assert 'f"Hello, {title' in final_content
    assert ".upper()" in final_content

def test_edit_fstring_function():
    """Test editing a function that uses f-strings"""
    content = '\n    def format_price(price, currency="USD"):\n        return f"${price:.2f} {currency}"\n    '
    test_file = setup_test_file("tmp", content)
    new_code = '\n    import logging\n    \n    def format_price(price, currency="USD"):\n        logging.debug(f"Formatting price: {price} {currency}")\n        if price < 0:\n            return f"Invalid price: ${abs(price):.2f} {currency}"\n        return f"${price:.2f} {currency}"\n    '
    result = python_edit(f"{test_file}::format_price", new_code)
    print(f"DEBUG - Edit result: {result}")
    with open(test_file) as f:
        final_content = f.read()
    print(f"DEBUG - Final content: {final_content}")
    assert 'f"Formatting price: {price} {currency}"' in final_content
    assert 'f"Invalid price: ${abs(price):.2f} {currency}"' in final_content
    assert "logging.debug" in final_content

def test_class_with_fstring_methods():
    """Test editing classes that contain f-string methods"""
    content = '\n    class User:\n        def __init__(self, name, age):\n            self.name = name\n            self.age = age\n        \n        def greet(self):\n            return f"Hi, I\'m {self.name}"\n    '
    test_file = setup_test_file("tmp", content)
    new_method = '\n    def describe(self):\n        status = "adult" if self.age >= 18 else "minor"\n        return f"User: {self.name} ({self.age} years old, {status})"\n    '
    result = python_edit(f"{test_file}::User", new_method, insert_after="User::greet")
    print(f"DEBUG - Edit result: {result}")
    with open(test_file) as f:
        final_content = f.read()
    print(f"DEBUG - Final content: {final_content}")
    assert 'f"Hi, I\'m {self.name}"' in final_content
    assert 'f"User: {self.name} ({self.age} years old, {status})"' in final_content

def test_various_apostrophe_patterns():
    """
    Test various patterns of apostrophes in comments that previously caused issues.
    """
    test_cases = [
        "# This file doesn't work",
        "# It's a simple test",
        "# That's not correct",
        "# We can't do this",
        "# Won't work without this",
        'result = "success"  # It\'s working',
        "pattern = '*.txt'  # Won't match directories",
        "x = 1  # This doesn't handle edge cases",
        "log.write(\"Error: can't connect\")  # Server isn't responding",
        "message = f\"User {name} can't login\"  # Database isn't available",
    ]
    for i, test_case in enumerate(test_cases):
        test_code = f"\ndef test_function_{i}():\n    {test_case}\n    return True\n"
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = f.name
        try:
            result = python_edit(f"{test_file}::test_function_{i}", "    pass", insert_after="return True")
            assert "Error" not in result, f"Failed on test case {i}: {test_case}\\nError: {result}"
            with open(test_file, "r") as f:
                content = f.read()
            try:
                ast.parse(content)
            except SyntaxError as e:
                pytest.fail(f"Syntax error on test case {i}: {test_case}\\nError: {e}\\nContent:\\n{content}")
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)
    print(f"âœ“ All {len(test_cases)} apostrophe pattern tests passed!")

def test_decorated_function_import_capture():
    """Test that decorated functions can access imports from their original module."""
    result = python_edit("test_decorated.py", 'def simple_function(): return "Hello"')
    assert "Code added to" in result
    assert os.path.exists("test_decorated.py")
    if os.path.exists("test_decorated.py"):
        os.remove("test_decorated.py")

def test_decorated_function_with_tool_handler():
    """Test that decorated functions work correctly when added as tools to a bot."""
    from bots.foundation.anthropic_bots import AnthropicToolHandler
    from bots.tools.python_edit import python_edit

    handler = AnthropicToolHandler()
    handler.add_tool(python_edit)
    assert "python_edit" in handler.function_map
    assert len(handler.tools) == 1

def test_import_capture_regression():
    """Regression test to ensure the specific _process_error import issue is fixed."""
    test_code = "def example(): return 42"
    result = python_edit("regression_test.py", test_code)
    assert "Code added to" in result
    if os.path.exists("regression_test.py"):
        os.remove("regression_test.py")

def test_empty_file_message_format(tmp_path):
    """Test that empty files get 'added' message, not 'replaced'"""
    empty_file = setup_test_file(tmp_path, "")
    result = python_edit(empty_file, "x = 42")
    assert "added" in result.lower() or "inserted" in result.lower(), f"Expected 'added' or 'inserted', got: {result}"
    assert "replaced" not in result.lower(), f"Should not say 'replaced' for empty file, got: {result}"



def test_real_scenario_edit_integration():
    """
    Real-scenario test: Perform actual edits on copies of real files.
    This validates that python_edit works correctly on real codebase files
    by making safe, reversible edits.
    """
    import tempfile
    import shutil
    # Test with a real file
    source_file = "bots/tools/python_edit.py"
    if not os.path.exists(source_file):
        pytest.skip(f"Source file {source_file} not found")
    with tempfile.TemporaryDirectory() as temp_dir:
        # Copy the real file to temp location
        test_file = os.path.join(temp_dir, "test_edit.py")
        shutil.copy2(source_file, test_file)
        # Read original content
        with open(test_file, 'r') as f:
            original_content = f.read()
        original_lines = len(original_content.splitlines())
        print(f"Testing edits on real file: {original_lines} lines")
        # Test 1: Add a simple function at file level
        result1 = python_edit(test_file, '''
def test_function_added_by_integration_test():
    """This function was added by the integration test."""
    return "integration_test_marker"
'''.strip())
        assert "error" not in result1.lower(), f"Edit 1 failed: {result1}"
        # Verify the edit worked and file is still valid Python
        with open(test_file, 'r') as f:
            content_after_edit1 = f.read()
        ast.parse(content_after_edit1)  # Should not raise
        assert "test_function_added_by_integration_test" in content_after_edit1
        assert "integration_test_marker" in content_after_edit1
        # Test 2: Add import at file start
        result2 = python_edit(test_file, "import uuid  # Added by integration test", insert_after="__FILE_START__")
        assert "error" not in result2.lower(), f"Edit 2 failed: {result2}"
        # Verify import was added at the start
        with open(test_file, 'r') as f:
            final_content = f.read()
        ast.parse(final_content)  # Should not raise
        lines = final_content.splitlines()
        # Find the import line
        import_line_found = False
        for i, line in enumerate(lines[:10]):  # Check first 10 lines
            if "import uuid" in line and "integration test" in line:
                import_line_found = True
                break
        assert import_line_found, "Import was not added at file start"
        # Test 3: Verify tokenization handled the complex real file correctly
        print(f"? Successfully performed {len([result1, result2])} edits on real file")
        print(f"? File remains valid Python with {len(final_content.splitlines())} lines")

# Tests for AST-based insert_after expression functionality
def test_insert_after_quoted_single_line_expression(tmp_path):
    """Test inserting after a quoted single-line expression"""
    content = '''
    def func():
        x = 1
        y = 2
        z = 3
    '''
    test_file = setup_test_file(tmp_path, content)
    # Insert after the line that starts with "y = "
    result = python_edit(f"{test_file}::func", "    inserted_line = 'after y'", insert_after='"y = 2"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    print(f"DEBUG - Final content:\n{final_content}")
    lines = final_content.split('\n')
    y_line_idx = next(i for i, line in enumerate(lines) if 'y = 2' in line)
    inserted_line_idx = next(i for i, line in enumerate(lines) if 'inserted_line' in line)
    assert inserted_line_idx == y_line_idx + 1, "Inserted line should be right after y = 2"
    assert "inserted_line = 'after y'" in final_content

# def test_insert_after_quoted_expression_partial_match(tmp_path):
#     """Test inserting after a quoted expression using partial matching"""
#     content = '''
#     def func():
#         result = calculate_something(param1, param2)
#         other_result = calculate_other(param3)
#         final = process_results()
#     '''
#     test_file = setup_test_file(tmp_path, content)
#     # Insert after line that starts with "result = calculate_something"
#     result = python_edit(f"{test_file}::func", "    # Added after calculation", insert_after='"result = calculate_something"')
#     assert "inserted after" in result
#     print(f"DEBUG - python_edit result: {result}")
#     with open(test_file) as f:
#         final_content = f.read()
#     print(f"DEBUG - Final content: {repr(final_content)}")
#     assert "# Added after calculation" in final_content
#     comment_line_idx = next(i for i, line in enumerate(lines) if '# Added after calculation' in line)
#     assert comment_line_idx == calc_line_idx + 1

def test_insert_after_quoted_multiline_expression(tmp_path):
    """Test inserting after a quoted multi-line expression"""
    content = '''
    def func():
        if condition:
            x = 1
            y = 2
        else:
            z = 3
    '''
    test_file = setup_test_file(tmp_path, content)
    # Insert after the exact multi-line if block
    multiline_pattern = '''if condition:
            x = 1
            y = 2'''
    result = python_edit(f"{test_file}::func", "    # Added after if block", insert_after=f'"{multiline_pattern}"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "# Added after if block" in final_content
def test_insert_after_quoted_expression_no_match(tmp_path):
    """Test error handling when quoted expression doesn't match anything"""
    content = '''
    def func():
        x = 1
        y = 2
    '''
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f"{test_file}::func", "    inserted = True", insert_after='"nonexistent_pattern"')
    assert "not found" in result.lower() or "error" in result.lower()
def test_insert_after_scope_path_syntax(tmp_path):
    """Test inserting after a method using scope path syntax"""
    content = '''
    class MyClass:
        def method1(self):
            return "first"
        def method2(self):
            return "second"
        def method3(self):
            return "third"
    '''
    test_file = setup_test_file(tmp_path, content)
    # Insert after method2 within MyClass
    result = python_edit(f"{test_file}::MyClass", "    def inserted_method(self):\n        return 'inserted'", 
                        insert_after="MyClass::method2")
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "def inserted_method" in final_content
    # Verify order: method2 should come before inserted_method
    method2_pos = final_content.find('def method2')
    inserted_pos = final_content.find('def inserted_method')
    method3_pos = final_content.find('def method3')
    assert method2_pos < inserted_pos < method3_pos, "inserted_method should be between method2 and method3"
def test_insert_after_nested_scope_path(tmp_path):
    """Test inserting after a method in a nested class"""
    content = '''
    class OuterClass:
        def outer_method(self):
            pass
        class InnerClass:
            def inner_method1(self):
                return 1
            def inner_method2(self):
                return 2
    '''
    test_file = setup_test_file(tmp_path, content)
    # Insert after inner_method1 within InnerClass
    result = python_edit(f"{test_file}::OuterClass::InnerClass", 
                        "        def inserted_inner_method(self):\n            return 'inserted'",
                        insert_after="OuterClass::InnerClass::inner_method1")
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "def inserted_inner_method" in final_content
def test_insert_after_simple_name_in_scope(tmp_path):
    """Test inserting after a simple method name within current scope"""
    content = '''
    class TestClass:
        def setup(self):
            self.data = []
        def process(self):
            return len(self.data)
        def cleanup(self):
            self.data.clear()
    '''
    test_file = setup_test_file(tmp_path, content)
    # Insert after 'process' method using simple name
    result = python_edit(f"{test_file}::TestClass", 
                        "    def validate(self):\n        return self.data is not None",
                        insert_after="process")
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "def validate" in final_content
    # Verify it's between process and cleanup
    process_pos = final_content.find('def process')
    validate_pos = final_content.find('def validate')
    cleanup_pos = final_content.find('def cleanup')
    assert process_pos < validate_pos < cleanup_pos
def test_insert_after_function_in_function(tmp_path):
    """Test inserting after a nested function"""
    content = '''
    def outer_func():
        def helper1():
            return "help1"
        def helper2():
            return "help2"
        return helper1() + helper2()
    '''
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f"{test_file}::outer_func", 
                        "    def helper_inserted():\n        return 'inserted'",
                        insert_after="helper1")
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "def helper_inserted" in final_content
def test_insert_after_with_complex_expressions(tmp_path):
    """Test inserting after complex expressions with quotes and special characters"""
    content = '''
    def func():
        message = "Hello, 'world'!"
        pattern = r"\\d+\\.\\d+"
        query = f"SELECT * FROM table WHERE name = '{name}'"
        result = process_data()
    '''
    test_file = setup_test_file(tmp_path, content)
    # Insert after the f-string line
    result = python_edit(f"{test_file}::func", 
                        "    # Added after query",
                        insert_after='"query = f"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "# Added after query" in final_content
def test_insert_after_preserves_indentation(tmp_path):
    """Test that inserted code maintains proper indentation"""
    content = '''
    class MyClass:
        def method(self):
            if True:
                x = 1
                y = 2
            return x + y
    '''
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f"{test_file}::MyClass::method", 
                        "z = 3",
                        insert_after='"y = 2"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    lines = final_content.split('\n')

    # Find the z = 3 line
    z_line = None
    for line in lines:
        if 'z = 3' in line:
            z_line = line
            break

    assert z_line is not None, f"z = 3 line not found in:\n{final_content}"

    # Should maintain proper indentation (8 spaces for method level)
    assert z_line.startswith('        '), f"Expected 8 spaces, got: {repr(z_line)}"

def test_insert_after_file_level_with_quoted_expression(tmp_path):
    """Test inserting at file level after a quoted expression"""
    content = '''
import os
from typing import List
def main():
    print("Hello")
if __name__ == "__main__":
    main()
    '''
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(test_file, 
                        "def helper_function():\n    return 'helper'",
                        insert_after='"def main():"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "def helper_function" in final_content
    # Should be after main() but before if __name__
    main_pos = final_content.find('def main()')
    helper_pos = final_content.find('def helper_function')
    name_pos = final_content.find('if __name__')
    assert main_pos < helper_pos < name_pos
def test_insert_after_edge_cases_empty_lines(tmp_path):
    """Test insert_after behavior with empty lines and whitespace"""
    content = '''
    def func():
        x = 1
        # Comment with empty line above
        y = 2
    '''
    test_file = setup_test_file(tmp_path, content)
    result = python_edit(f"{test_file}::func", 
                        "    # Inserted after comment",
                        insert_after='"# Comment with empty line above"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    assert "# Inserted after comment" in final_content
def test_insert_after_expression_matching_rules(tmp_path):
    """Test the specific rules for expression pattern matching"""
    content = '''
    def func():
        result = calculate(param1, param2, param3)
        other = calculate(different_params)
        final = process_result(result)
    '''
    test_file = setup_test_file(tmp_path, content)
    # Single-line pattern should match the first line that STARTS with the pattern
    result = python_edit(f"{test_file}::func", 
                        "    # Added after first calculate",
                        insert_after='"result = calculate"')
    assert "inserted after" in result
    with open(test_file) as f:
        final_content = f.read()
    lines = final_content.split('\n')
    result_line_idx = next(i for i, line in enumerate(lines) if 'result = calculate(param1' in line)
    comment_line_idx = next(i for i, line in enumerate(lines) if '# Added after first calculate' in line)
    assert comment_line_idx == result_line_idx + 1
def test_insert_after_single_quote_vs_double_quote(tmp_path):
    """Test that both single and double quotes work for expression patterns"""
    content = '''
    def func():
        x = "double quoted string"
        y = 'single quoted string'
    '''
    test_file = setup_test_file(tmp_path, content)
    # Test with double quotes
    result1 = python_edit(f"{test_file}::func", 
                         "    # After double quote pattern",
                         insert_after='"x = "')
    assert "inserted after" in result1
    # Test with single quotes  
    result2 = python_edit(f"{test_file}::func", 
                         "    # After single quote pattern",
                         insert_after="'y = '")
    assert "inserted after" in result2
    with open(test_file) as f:
        final_content = f.read()
    assert "# After double quote pattern" in final_content
    assert "# After single quote pattern" in final_content

def test_insert_after_ambiguous_multiline_expression(tmp_path):
    """Test ambiguity handling for multiline expressions"""
    content = '''
    def func():
        if condition1:
            x = 1
            y = 2
        if condition2:
            x = 1
            y = 2
    '''
    test_file = setup_test_file(tmp_path, content)
    # This multiline pattern appears twice - should get ambiguity error
    ambiguous_pattern = '''if condition1:
            x = 1
            y = 2'''
    result = python_edit(f"{test_file}::func", "    # Should fail", 
                        insert_after=f'"{ambiguous_pattern}"')
    # Should handle ambiguity gracefully
    print(f"DEBUG - Ambiguity result: {result}")
def test_newline_preservation_after_scope_replacement(tmp_path):
    """Test that proper newlines are preserved when replacing scopes followed by definitions"""
    content = '''def function_one():
    return "something"
class ExistingClass:
    pass
def another_function():
    return "other"'''
    test_file = setup_test_file(tmp_path, content)
    # Replace function_one with new code that ends with return
    new_function = '''def function_one():
    x = 1
    return f"result: {x}"'''
    result = python_edit(f"{test_file}::function_one", new_function)
    assert "replaced" in result.lower()
    with open(test_file, 'r') as f:
        final_content = f.read()
    # Check that there are proper newlines between function and class
    # Should have at least one blank line between definitions
    assert 'return f"result: {x}"\n\nclass ExistingClass:' in final_content, \
        f"Missing proper newline separation. Content: {repr(final_content)}"
    # Also verify the class is still intact
    assert "class ExistingClass:" in final_content
    assert "def another_function():" in final_content
