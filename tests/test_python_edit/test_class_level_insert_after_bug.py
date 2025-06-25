import os
import tempfile
from textwrap import dedent
from bots.tools.python_edit import python_edit
import pytest

def setup_test_file(content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(dedent(content))
        return f.name

def test_class_level_insert_after_bug():
    """BUG: Class-level insert_after replaces entire file"""
    content = """
        class Calculator:
            def add(self, x, y):
                return x + y
            def multiply(self, x, y):
                return x * y
        def other_function():
            pass
    """
    test_file = setup_test_file(content)
    try:
        python_edit(target_scope=f"{test_file}::Calculator", code="def subtract(self, x, y):\n    return x - y", insert_after="add")
        with open(test_file, "r") as f:
            final_content = f.read()
        # These should pass but will fail due to the bug
        assert "class Calculator:" in final_content
        assert "def add(self, x, y):" in final_content
        assert "def multiply(self, x, y):" in final_content
        assert "def subtract(self, x, y):" in final_content
        assert "def other_function():" in final_content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)
if __name__ == "__main__":
    test_class_level_insert_after_bug()