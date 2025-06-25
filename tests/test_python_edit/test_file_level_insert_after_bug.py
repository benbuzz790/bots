import os
import tempfile
from textwrap import dedent

from bots.tools.python_edit import python_edit


def setup_test_file(content):
    """Helper to create a test file with given content"""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(dedent(content))
        return f.name


def test_file_level_insert_after_replaces_entire_file():
    """
    BUG: When using insert_after at file level, the tool replaces the entire file
    instead of inserting after the specified element.
    Expected: Insert new code after the specified function/class
    Actual: Replaces entire file with just imports + new code
    """
    content = '''
        import os
        import sys
        def hello_world():
            """A simple hello world function."""
            print("Hello, World!")
        class Calculator:
            """A simple calculator class."""
            def add(self, x, y):
                return x + y
        if __name__ == "__main__":
            hello_world()
    '''
    test_file = setup_test_file(content)
    try:
        # This should insert after hello_world, but it replaces the entire file
        result = python_edit(
            target_scope=test_file,
            code='''
                import json
                def goodbye_world():
                    """A simple goodbye function."""
                    print("Goodbye, World!")
            ''',
            insert_after="hello_world",
        )
        with open(test_file, "r") as f:
            final_content = f.read()
        print(f"Result: {result}")
        print(f"Final content:\n{final_content}")
        # BUG: The file gets replaced entirely instead of inserting after hello_world
        # These assertions will fail due to the bug:
        assert "def hello_world():" in final_content, "Original hello_world function should be preserved"
        assert "class Calculator:" in final_content, "Original Calculator class should be preserved"
        assert "if __name__" in final_content, "Original main block should be preserved"
        assert "def goodbye_world():" in final_content, "New function should be added"
        # The new function should come after hello_world
        hello_pos = final_content.find("def hello_world")
        goodbye_pos = final_content.find("def goodbye_world")
        assert hello_pos < goodbye_pos, "goodbye_world should come after hello_world"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


def test_file_level_insert_after_function_bug():
    """Test inserting after a function at file level - should preserve all content"""
    content = """
        def func_a():
            return "a"
        def func_b():
            return "b"
        def func_c():
            return "c"
    """
    test_file = setup_test_file(content)
    try:
        python_edit(target_scope=test_file, code='def func_new():\n    return "new"', insert_after="func_b")
        with open(test_file, "r") as f:
            final_content = f.read()
        # All original functions should be preserved
        assert "def func_a():" in final_content, "func_a should be preserved"
        assert "def func_b():" in final_content, "func_b should be preserved"
        assert "def func_c():" in final_content, "func_c should be preserved"
        assert "def func_new():" in final_content, "New function should be added"
        # Order should be: func_a, func_b, func_new, func_c
        lines = final_content.split("\n")
        func_positions = {}
        for i, line in enumerate(lines):
            if "def func_a():" in line:
                func_positions["a"] = i
            elif "def func_b():" in line:
                func_positions["b"] = i
            elif "def func_c():" in line:
                func_positions["c"] = i
            elif "def func_new():" in line:
                func_positions["new"] = i
        assert (
            func_positions["a"] < func_positions["b"] < func_positions["new"] < func_positions["c"]
        ), f"Functions in wrong order: {func_positions}"
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


if __name__ == "__main__":
    # Run the tests to demonstrate the bugs
    print("Testing file-level insert_after bugs...")
    try:
        test_file_level_insert_after_replaces_entire_file()
        print("✓ File-level insert_after test passed")
    except AssertionError as e:
        print(f"✗ File-level insert_after test failed: {e}")
    try:
        test_file_level_insert_after_function_bug()
        print("✓ Function insert_after test passed")
    except AssertionError as e:
        print(f"✗ Function insert_after test failed: {e}")
