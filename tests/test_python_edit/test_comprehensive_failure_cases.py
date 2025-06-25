import os
import tempfile
from textwrap import dedent
from bots.tools.python_edit import python_edit
import pytest

def setup_test_file(content):
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(dedent(content))
        return f.name

def test_comprehensive_failure_cases():
    """Test all the major failure cases discovered during testing"""
    # Test 1: File-level insert_after bug
    print("=== Testing file-level insert_after bug ===")
    content1 = """
        def func_a():
            return "a"
        def func_b():
            return "b"
    """
    test_file1 = setup_test_file(content1)
    try:
        result = python_edit(test_file1, 'def func_new():\n    return "new"', insert_after="func_a")
        with open(test_file1, "r") as f:
            final_content = f.read()
        print(f"Result: {result}")
        print(f"Content: {final_content}")
        # This will likely fail - file gets replaced instead of inserting
        if "func_a" not in final_content or "func_b" not in final_content:
            print("BUG: File-level insert_after replaced entire file!")
        else:
            print("File-level insert_after working correctly")
    finally:
        if os.path.exists(test_file1):
            os.unlink(test_file1)
if __name__ == "__main__":
    test_comprehensive_failure_cases()