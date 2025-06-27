import ast
import os
import tempfile
from textwrap import dedent

import pytest

from bots.tools.python_edit import _detokenize_source, _tokenize_source, python_edit

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
    assert "insert point not found" in result.lower() or "not found" in result.lower()

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

def test_minimal_tokenize():
    """Test tokenization of minimal valid Python"""
    source = "x = 1"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    print(f"DEBUG - Token map: {token_map}")
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

def test_minimal_tokenize_with_comment():
    """Test tokenization with just a comment"""
    source = "# A comment"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    print(f"DEBUG - Token map: {token_map}")
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

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

def test_tokenize_basic():
    """Test basic tokenization of comments and strings"""
    source = '\n    # Header comment\n    x = "string literal"  # Inline comment\n    y = 1\n    '
    tokenized, token_map = _tokenize_source(source)
    assert "# Header comment" not in tokenized
    assert '"string literal"' not in tokenized
    assert "# Inline comment" not in tokenized
    assert "TOKEN_" in tokenized
    restored = _detokenize_source(tokenized, token_map)
    assert "# Header comment" in restored and '"string literal"' in restored and ("# Inline comment" in restored)

def test_tokenize_multiline():
    """Test tokenization of multiline strings and nested structures"""
    source = '\n    def func():\n        """\n        Multiline\n        docstring\n        """\n        # Comment\n        if True:\n            # Nested comment\n            x = 1\n    '
    tokenized, token_map = _tokenize_source(source)
    assert '"""' not in tokenized
    assert "# Comment" not in tokenized
    assert "# Nested comment" not in tokenized
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_tokenize_contains_tokens():
    """Ensure tokenization produces token markers"""
    source = '\n    x = 1; y = 2  # Multiple statements\n    # Comment with ; semicolon\n    s = "String # with hash"\n    q = \'String ; with semicolon\'\n    """\n    Multiline string\n    # with comment\n    ; with semicolon\n    """\n    '
    tokenized, _ = _tokenize_source(source)
    assert "TOKEN_" in tokenized

def test_tokenize_preserves_comments():
    """Ensure comments are preserved in restored source"""
    source = '\n    x = 1; y = 2  # Multiple statements\n    # Comment with ; semicolon\n    s = "String # with hash"\n    q = \'String ; with semicolon\'\n    """\n    Multiline string\n    # with comment\n    ; with semicolon\n    """\n    '
    tokenized, token_map = _tokenize_source(source)
    restored = _detokenize_source(tokenized, token_map)
    assert "Multiple statements" in restored
    assert "Comment with ; semicolon" in restored

def test_tokenize_preserves_string_literals():
    """Ensure string literals are unchanged after round trip"""
    source = "\n    s = \"String # with hash\"\n    q = 'String ; with semicolon'\n    "
    tokenized, token_map = _tokenize_source(source)
    restored = _detokenize_source(tokenized, token_map)
    assert "String # with hash" in restored
    assert "String ; with semicolon" in restored

def test_tokenize_preserves_multiline_strings():
    """Ensure multiline strings are preserved intact"""
    source = '\n    """\n    Multiline string\n    # with comment\n    ; with semicolon\n    """\n    '
    tokenized, token_map = _tokenize_source(source)
    restored = _detokenize_source(tokenized, token_map)
    assert "Multiline string" in restored
    assert "# with comment" in restored
    assert "; with semicolon" in restored

def test_minimal_tokenize():
    """Test tokenization of minimal valid Python"""
    source = "x = 1"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    print(f"DEBUG - Token map: {token_map}")
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

def test_minimal_tokenize_with_comment():
    """Test tokenization with just a comment"""
    source = "# A comment"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    print(f"DEBUG - Token map: {token_map}")
    ast.parse(tokenized)
    assert _detokenize_source(tokenized, token_map) == source

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

def test_minimal_multiline():
    """Test tokenization of multiline content"""
    source = 'def test():\n        """\n        Docstring\n        with lines\n        """\n        pass'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized:\n{tokenized}")
    print(f"DEBUG - Token map:\n{token_map}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    print(f"DEBUG - Restored:\n{restored}")
    assert restored == source

def test_minimal_nested_multiline():
    """Test tokenization of nested multiline content"""
    source = 'def outer():\n        """Outer docstring"""\n        def inner():\n            """\n            Inner\n            docstring\n            """\n            pass'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized:\n{tokenized}")
    print(f"DEBUG - Token map:\n{token_map}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    print(f"DEBUG - Restored:\n{restored}")
    assert restored == source

def test_minimal_complex_indent():
    """Test tokenization with complex indentation patterns"""
    source = 'def test():\n        # Comment at level 1\n        if True:\n            # Comment at level 2\n            if True:\n                """\n                Docstring at\n                level 3\n                """\n                # Comment at level 3\n                pass'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized:\n{tokenized}")
    print(f"DEBUG - Token map:\n{token_map}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    print(f"DEBUG - Restored:\n{restored}")
    assert restored == source

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

def test_fstring_basic():
    """Test basic f-string tokenization and preservation"""
    source = 'name = "Alice"\ngreeting = f"Hello, {name}!"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    print(f"DEBUG - Token map: {token_map}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_nested_quotes():
    """Test f-strings with nested quotes"""
    source = 'user = {"name": "Alice", "age": 30}\nmessage = f"User {user[\'name\']} is {user[\'age\']} years old"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_complex_expressions():
    """Test f-strings with complex expressions"""
    source = "def format_data(items):\n    return f\"Total: {sum(item['value'] for item in items if item['active'])}\""
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_escaped_braces():
    """Test f-strings with escaped braces"""
    source = 'template = f"{{item}} costs ${price:.2f}"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_with_format_specs():
    """Test f-strings with format specifications"""
    source = 'price = 19.99\nformatted = f"Price: ${price:.2f} ({price:>10.2f})"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_multiline():
    """Test multiline f-strings"""
    source = 'name = "Alice"\nage = 30\nbio = f"""\nName: {name}\nAge: {age}\nStatus: {\'Active\' if age < 65 else \'Retired\'}\n"""'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_fstring_prefixes():
    """Test various f-string prefixes (rf, fr, etc.)"""
    source = 'pattern = rf"Hello {name}\n"\nraw_fstring = fr"Path: {path}\\"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

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

def test_mixed_quote_types():
    """Test mixing single and double quotes"""
    source = (
        'message = "He said \'Hello\'"\nother = \'She replied "Hi there"\'\nfstring = f"Mixed: {\'single\'} and {"double"}"'
    )
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_string_concatenation():
    """Test string concatenation edge cases"""
    source = 'long_string = ("This is a very long string "\n               "that spans multiple lines "\n               f"with an f-string {variable}")'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_regex_strings():
    """Test regex strings that might confuse tokenization"""
    source = 'import re\npattern = r"(\\d+)-(\\d+)-(\\d+)"\nfstring_pattern = rf"User-{user_id}-\\d+"\ncomplex_regex = r"(?P<name>[a-zA-Z]+):\\s*(?P<value>[\'\\"].*?[\'\\"])"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_comments_with_quotes():
    """Test comments containing quote characters"""
    source = 'x = 1  # This comment has "quotes" and \'apostrophes\'\ny = 2  # Even f-string-like {syntax} in comments\n# Standalone comment with "mixed" quotes and {braces}'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert '"quotes"' in restored
    assert "'apostrophes'" in restored
    assert "{syntax}" in restored

def test_docstring_edge_cases():
    """Test various docstring formats"""
    source = 'def func():\n    """Single line docstring with \'quotes\' and {braces}."""\n    pass\n\nclass MyClass:\n    """\n    Multi-line docstring with:\n    - "Double quotes"\n    - \'Single quotes\'  \n    - f-string-like {syntax}\n    - Even some "nested \'quotes\'"\n    """\n    pass'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_unterminated_fstring():
    """Test handling of malformed f-strings that might cause errors"""
    source = 'x = f"Hello {name'
    try:
        tokenized, token_map = _tokenize_source(source)
        print(f"DEBUG - Tokenized malformed: {tokenized}")
        ast.parse(tokenized)
        assert False, "Should have caught malformed f-string"
    except SyntaxError:
        pass

def test_nested_fstring_depth():
    """Test deeply nested f-string expressions"""
    source = 'data = {"users": [{"name": "Alice", "prefs": {"theme": "dark"}}]}\nmessage = f"User {data[\'users\'][0][\'name\']} likes {data[\'users\'][0][\'prefs\'][\'theme\']} theme"'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_data_processing_code():
    """Test tokenizing realistic data processing code with f-strings"""
    source = 'import json\nfrom typing import Dict, List\n\ndef process_users(users: List[Dict]) -> str:\n    """Process user data and return formatted summary."""\n    active_users = [u for u in users if u.get(\'active\', False)]\n    \n    summary = f"""\n    User Summary:\n    - Total users: {len(users)}\n    - Active users: {len(active_users)}\n    - Percentage active: {len(active_users)/len(users)*100:.1f}%\n    """\n    \n    details = []\n    for user in active_users[:5]:  # Top 5\n        name = user[\'name\']\n        email = user.get(\'email\', \'No email\')\n        last_login = user.get(\'last_login\', \'Never\')\n        details.append(f"- {name} ({email}) - Last: {last_login}")\n    \n    if details:\n        summary += f"\\n\\nTop Active Users:\\n" + "\\n".join(details)\n    \n    return summary.strip()'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized length: {len(tokenized)}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

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

def test_large_fstring_file():
    """Test handling a file with many f-strings"""
    lines = ["import math"]
    for i in range(50):
        lines.append(f'result_{i} = f"Item {{i}}: {{math.sqrt({i})}}"')
    source = "\n".join(lines)
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Token count: {len(token_map)}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_mixed_content_stress():
    """Test file with mixed strings, f-strings, comments, and code"""
    source = '#!/usr/bin/env python3\n"""\nModule for data processing with f-strings.\nContains "quotes" and {braces} in docstring.\n"""\n\nimport os  # Standard library\nfrom typing import Dict, List  # Type hints\n\n# Configuration with f-string\nCONFIG_PATH = f"{os.path.expanduser(\'~\')}/.config/app.json"\n\nclass DataProcessor:\n    """Process data with various string formats."""\n    \n    def __init__(self, config_path: str = CONFIG_PATH):\n        self.config_path = config_path  # Store path\n        self.data = {}  # Initialize empty\n    \n    def load_config(self) -> Dict:\n        """Load configuration from file."""\n        if not os.path.exists(self.config_path):\n            raise FileNotFoundError(f"Config not found: {self.config_path}")\n        \n        # Read and parse config\n        with open(self.config_path, \'r\') as f:\n            content = f.read()  # Regular string method\n        \n        return json.loads(content)  # Parse JSON\n    \n    def format_output(self, data: List[Dict]) -> str:\n        """Format data for output."""\n        lines = [f"Processing {len(data)} items..."]  # F-string with len()\n        \n        for i, item in enumerate(data):\n            name = item.get(\'name\', \'Unknown\')\n            value = item.get(\'value\', 0)\n            # Complex f-string with formatting\n            line = f"  {i+1:2d}. {name:<20} = {value:>8.2f} ({value/100:.1%})"\n            lines.append(line)\n        \n        summary = f"\\nSummary: {len(data)} items processed"\n        return "\\n".join(lines) + summary'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Token count: {len(token_map)}")
    print(f"DEBUG - Tokenized length: {len(tokenized)}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored.replace(" ", "").replace("\n", "") == source.replace(" ", "").replace("\n", "")

def test_single_quote_preservation():
    """Test that single quotes are preserved in string concatenation"""
    source = "message = ('Hello world' \n               'with single quotes')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert "'Hello world'" in restored
    assert "'with single quotes'" in restored

def test_double_quote_preservation():
    """Test that double quotes are preserved in string concatenation"""
    source = 'message = ("Hello world" \n               "with double quotes")'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '"Hello world"' in restored
    assert '"with double quotes"' in restored

def test_mixed_quotes_preservation():
    """Test mixed quote styles in same concatenation"""
    source = (
        'message = ("Double quoted string "\n               \'Single quoted string \'\n               "Back to double quotes")'
    )
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '"Double quoted string "' in restored
    assert "'Single quoted string '" in restored
    assert '"Back to double quotes"' in restored

def test_fstring_quote_preservation():
    """Test f-string quote preservation in concatenation"""
    source = "message = (f\"F-string with {variable}\"\n               'Regular single quote'\n               f'F-string with single quotes {other_var}')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert 'f"F-string with {variable}"' in restored
    assert "'Regular single quote'" in restored
    assert "f'F-string with single quotes {other_var}'" in restored

def test_nested_quotes_preservation():
    """Test strings containing opposite quote types"""
    source = "message = (\"String with 'nested single quotes'\"\n               'String with \"nested double quotes\"')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert "\"String with 'nested single quotes'\"" in restored
    assert "'String with \"nested double quotes\"'" in restored

def test_triple_quote_preservation():
    """Test that triple quotes are handled correctly (should not be affected by concatenation logic)"""
    source = 'docstring = """This is a\nmultiline string\nwith triple quotes"""'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '"""This is a' in restored

def test_non_concatenated_quote_preservation():
    """Test that non-concatenated strings preserve quotes"""
    source = "single = 'Single quoted'\ndouble = \"Double quoted\"\nf_single = f'F-string single {var}'\nf_double = f\"F-string double {var}\""
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert "single = 'Single quoted'" in restored
    assert 'double = "Double quoted"' in restored
    assert "f_single = f'F-string single {var}'" in restored
    assert 'f_double = f"F-string double {var}"' in restored

def test_complex_mixed_concatenation():
    """Test complex real-world concatenation with mixed quotes and f-strings"""
    source = "sql_query = (\"SELECT * FROM users \"\n               'WHERE name = \"John\" '\n               f\"AND age > {min_age} \"\n               'AND status = \\'active\\' '\n               f'ORDER BY {sort_column}')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    lines = restored.split("\n")
    assert '"SELECT * FROM users "' in lines[0]
    assert "'WHERE name = \"John\" '" in lines[1]
    assert f'"AND age > {{min_age}} "' in lines[2]
    assert "'AND status = \\'active\\' '" in lines[3]
    assert f"'ORDER BY {{sort_column}}')" in lines[4]

def test_edge_case_empty_strings():
    """Test concatenation with empty strings"""
    source = 'result = ("" \n               \'\' \n               f"")'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '""' in restored
    assert "''" in restored
    assert 'f""' in restored

def test_single_quote_preservation():
    """Test that single quotes are preserved in string concatenation"""
    source = "message = ('Hello world' \n               'with single quotes')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert "'Hello world'" in restored
    assert "'with single quotes'" in restored

def test_double_quote_preservation():
    """Test that double quotes are preserved in string concatenation"""
    source = 'message = ("Hello world" \n               "with double quotes")'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '"Hello world"' in restored
    assert '"with double quotes"' in restored

def test_mixed_quotes_preservation():
    """Test mixed quote styles in same concatenation"""
    source = (
        'message = ("Double quoted string "\n               \'Single quoted string \'\n               "Back to double quotes")'
    )
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '"Double quoted string "' in restored
    assert "'Single quoted string '" in restored
    assert '"Back to double quotes"' in restored

def test_fstring_quote_preservation():
    """Test f-string quote preservation in concatenation"""
    source = "message = (f\"F-string with {variable}\"\n               'Regular single quote'\n               f'F-string with single quotes {other_var}')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert 'f"F-string with {variable}"' in restored
    assert "'Regular single quote'" in restored
    assert "f'F-string with single quotes {other_var}'" in restored

def test_nested_quotes_preservation():
    """Test strings containing opposite quote types"""
    source = "message = (\"String with 'nested single quotes'\"\n               'String with \"nested double quotes\"')"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert "\"String with 'nested single quotes'\"" in restored
    assert "'String with \"nested double quotes\"'" in restored

def test_triple_quote_preservation():
    """Test that triple quotes are handled correctly (should not be affected by concatenation logic)"""
    source = 'docstring = """This is a\nmultiline string\nwith triple quotes"""'
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert '"""This is a' in restored

def test_non_concatenated_quote_preservation():
    """Test that non-concatenated strings preserve quotes"""
    source = "single = 'Single quoted'\ndouble = \"Double quoted\"\nf_single = f'F-string single {var}'\nf_double = f\"F-string double {var}\""
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    ast.parse(tokenized)
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source
    assert "single = 'Single quoted'" in restored
    assert 'double = "Double quoted"' in restored
    assert "f_single = f'F-string single {var}'" in restored
    assert 'f_double = f"F-string double {var}"' in restored

def test_quote_metadata_storage():
    """Test that quote character metadata is correctly stored"""
    source = "concat = (\"double\" 'single' f\"f-double\" f'f-single')"
    tokenized, token_map = _tokenize_source(source)
    quote_chars_found = []
    for token_name, token_data in token_map.items():
        metadata = token_data["metadata"]
        if metadata.get("in_parens", False) and "quote_char" in metadata:
            quote_chars_found.append(metadata["quote_char"])
    assert '"' in quote_chars_found
    assert "'" in quote_chars_found
    restored = _detokenize_source(tokenized, token_map)
    assert restored == source

def test_escaped_quotes_debugging():
    """Debug the specific escaped quotes issue"""
    source = "'AND status = \\'active\\' '"
    print(f"Testing source: {repr(source)}")
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Tokenized: {tokenized}")
    test_assignment = f"x = {tokenized}"
    print(f"Testing assignment: {test_assignment}")
    try:
        ast.parse(test_assignment)
        print("âœ“ AST parsing successful")
    except Exception as e:
        print(f"âœ— AST parsing failed: {e}")
    restored = _detokenize_source(tokenized, token_map)
    print(f"Restored: {repr(restored)}")
    assert restored == source

def test_complex_mixed_concatenation_simple():
    """Simplified version of the failing test"""
    source = "'AND status = \\'active\\' '"
    tokenized, token_map = _tokenize_source(source)
    print(f"DEBUG - Single string tokenized: {tokenized}")
    concat_source = f'("SELECT * FROM users " {source})'
    print(f"Testing concatenation: {concat_source}")
    tokenized_concat, token_map_concat = _tokenize_source(concat_source)
    print(f"DEBUG - Concatenation tokenized: {tokenized_concat}")
    try:
        ast.parse(f"x = {tokenized_concat}")
        print("âœ“ Concatenation AST parsing successful")
    except Exception as e:
        print(f"âœ— Concatenation AST parsing failed: {e}")
    restored = _detokenize_source(tokenized_concat, token_map_concat)
    print(f"Restored: {repr(restored)}")
    assert restored == concat_source

def test_problematic_string():
    """Test the specific case that was failing."""
    test_line = "'AND status = \\'active\\' '"
    print("Testing problematic string:")
    locations = debug_string_locations(test_line)
    assert len(locations) == 1, f"Expected 1 string, found {len(locations)}"
    assert locations[0]["start"] == 0, f"Expected start at 0, got {locations[0]['start']}"
    assert locations[0]["end"] == len(test_line) - 1, f"Expected end at {len(test_line) - 1}, got {locations[0]['end']}"
    print("âœ“ Problematic string correctly identified as single unit")

def test_multiple_strings():
    """Test multiple strings on one line."""
    test_line = 'result = "string1" + "string2" + f"string3 {var}"'
    print("\nTesting multiple strings:")
    locations = debug_string_locations(test_line)
    assert len(locations) == 3, f"Expected 3 strings, found {len(locations)}"
    print("âœ“ Multiple strings correctly identified")

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

def test_tokenization_edge_cases():
    """
    Test edge cases in the tokenization process that were problematic.
    """
    edge_cases = [
        'def test():\n    data = {"key": "value\'s here"}  # This isn\'t a problem\n    return data',
        'def test():\n    result = f"Hello {name}"  # User\'s name is dynamic\n    return result',
        "def test():\n    single = 'text'\n    double = \"text\"  # Don't mix these\n    f_string = f\"value: {x}\"  # It's an f-string\n    return single, double, f_string",
        'def test():\n    message = "He said \\"Hello\\""  # User\'s quote is escaped\n    return message',
    ]
    for i, test_code in enumerate(edge_cases):
        with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
            f.write(test_code)
            test_file = f.name
        try:
            from bots.tools.python_edit import _detokenize_source, _tokenize_source

            tokenized, token_map = _tokenize_source(test_code)
            for token_name, token_data in token_map.items():
                content = token_data["content"]
                assert len(content) < 200, f"Mega-token detected in edge case {i}: {token_name} = {repr(content)}"
            ast.parse(tokenized)
            detokenized = _detokenize_source(tokenized, token_map)
            ast.parse(detokenized)
            result = python_edit(f"{test_file}::test", "    # Added comment", insert_after="return '''")
            assert "Error" not in result, f"python_edit failed on edge case {i}: {result}"
        finally:
            if os.path.exists(test_file):
                os.unlink(test_file)

def debug_string_locations(line):
    """Debug helper to see what strings are found in a line."""
    from bots.tools.python_edit import _find_all_string_locations

    print(f"Analyzing line: {repr(line)}")
    locations = _find_all_string_locations(line)
    for i, loc in enumerate(locations):
        print(f"  String {i + 1}: {repr(loc['content'])} at positions {loc['start']}-{loc['end']}")
        print(f"    - F-string: {loc['is_fstring']}")
        print(f"    - In parens: {loc['paren_depth'] > 0}")
        print(f"    - Quote char: {repr(loc['quote_char'])}")
    return locations

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



