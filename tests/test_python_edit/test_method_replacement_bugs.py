import os
import tempfile
from textwrap import dedent

from bots.tools.python_edit import python_edit


def setup_test_file(content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(dedent(content))
        return f.name


def test_method_replacement_with_imports_bug():
    """BUG: Method replacement with imports can replace entire file"""
    content = """
        import os
        import sys
        class StringUtils:
            def reverse_string(self, s):
                return s[::-1]
            def capitalize_words(self, s):
                return s.title()
        def other_function():
            return "preserved"
    """
    test_file = setup_test_file(content)
    try:
        python_edit(
            target_scope=f"{test_file}::StringUtils::reverse_string",
            code="""
                import re
                import datetime
                def reverse_string(self, s):
                    timestamp = datetime.datetime.now()
                    print(f"Reversing at {timestamp}")
                    return s[::-1]
            """,
        )
        with open(test_file, "r") as f:
            final_content = f.read()
        print(f"Final content: {final_content}")
        # These should pass but may fail due to the bug
        assert "class StringUtils:" in final_content
        assert "def capitalize_words(self, s):" in final_content
        assert "def other_function():" in final_content
        assert "import re" in final_content
        assert "import datetime" in final_content
        assert "datetime.datetime.now()" in final_content
    finally:
        if os.path.exists(test_file):
            os.unlink(test_file)


if __name__ == "__main__":
    test_method_replacement_with_imports_bug()
