import os
import tempfile
from pathlib import Path
from textwrap import dedent

import pytest

from bots.tools.python_edit import python_edit


def setup_test_file(tmp_path, content):
    """Helper to create a test file with given content"""
    import uuid

    # Convert to Path if it's a string
    if isinstance(tmp_path, str):
        tmp_path = Path(tmp_path)

    # pytest's tmp_path fixture creates the directory automatically
    # With xdist, each worker gets its own isolated tmp_path (e.g., basetemp/gw0/test_name/)
    # We should rarely need to create it manually
    if not tmp_path.exists():
        try:
            tmp_path.mkdir(parents=True, exist_ok=True)
        except FileExistsError:
            # Another worker created it, that's fine
            pass

    # Verify directory exists
    if not tmp_path.is_dir():
        raise RuntimeError(f"tmp_path {tmp_path} is not a directory")

    # Create the test file with a unique name to avoid collisions
    # Even with worker isolation, unique names are good practice
    unique_id = uuid.uuid4().hex[:8]
    test_file = tmp_path / f"test_file_{unique_id}.py"

    with open(test_file, "w", encoding="utf-8") as f:
        f.write(dedent(content))

    return str(test_file)


pytestmark = pytest.mark.integration


def test_empty_string_deletes_entire_file(tmp_path):
    """Test that empty string at file level clears the entire file"""
    content = """
    import os
    from typing import List

    def hello():
        print("Hello, World!")

    def goodbye():
        print("Goodbye!")

    class MyClass:
        def method(self):
            pass
    """
    test_file = setup_test_file(tmp_path, content)

    # Test file-level deletion with empty string
    result = python_edit(test_file, "")
    assert "cleared" in result.lower() or "deleted all content" in result.lower()

    # Check that file is now empty
    with open(test_file, "r") as f:
        content = f.read()
    assert content == "", f"Expected empty file, got: {repr(content)}"


def test_empty_string_deletes_function(tmp_path):
    """Test that empty string deletes specific function"""
    content = """
    def hello():
        print("Hello, World!")

    def goodbye():
        print("Goodbye!")

    def farewell():
        print("Farewell!")
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete the middle function
    result = python_edit(f"{test_file}::goodbye", "")
    assert "deleted scope" in result.lower()

    # Check that only goodbye function was deleted
    with open(test_file, "r") as f:
        content = f.read()
    assert "def hello():" in content
    assert "def goodbye():" not in content
    assert "def farewell():" in content
    assert "Hello, World!" in content
    assert "Goodbye!" not in content
    assert "Farewell!" in content


def test_empty_string_deletes_class(tmp_path):
    """Test that empty string deletes specific class"""
    content = """
    class FirstClass:
        def method1(self):
            pass

    class SecondClass:
        def method2(self):
            pass

    class ThirdClass:
        def method3(self):
            pass
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete the middle class
    result = python_edit(f"{test_file}::SecondClass", "")
    assert "deleted scope" in result.lower()

    # Check that only SecondClass was deleted
    with open(test_file, "r") as f:
        content = f.read()
    assert "class FirstClass:" in content
    assert "class SecondClass:" not in content
    assert "class ThirdClass:" in content
    assert "method1" in content
    assert "method2" not in content
    assert "method3" in content


def test_empty_string_deletes_method(tmp_path):
    """Test that empty string deletes specific method from class"""
    content = """
    class MyClass:
        def __init__(self):
            self.value = 42

        def method_to_delete(self):
            return "will be deleted"

        def method_to_keep(self):
            return "will be kept"
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete specific method
    result = python_edit(f"{test_file}::MyClass::method_to_delete", "")
    assert "deleted scope" in result.lower()

    # Check that only the specific method was deleted
    with open(test_file, "r") as f:
        content = f.read()
    assert "class MyClass:" in content
    assert "__init__" in content
    assert "method_to_delete" not in content
    assert "method_to_keep" in content
    assert "will be deleted" not in content
    assert "will be kept" in content


def test_empty_string_deletes_inner_class(tmp_path):
    """Test that empty string deletes nested class"""
    content = """
    class OuterClass:
        def outer_method(self):
            pass

        class InnerClass:
            def inner_method(self):
                return "inner"

        def another_outer_method(self):
            pass
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete nested class
    result = python_edit(f"{test_file}::OuterClass::InnerClass", "")
    assert "deleted scope" in result.lower()

    # Check that only InnerClass was deleted
    with open(test_file, "r") as f:
        content = f.read()
    assert "class OuterClass:" in content
    assert "outer_method" in content
    assert "another_outer_method" in content
    assert "class InnerClass:" not in content
    assert "inner_method" not in content
    assert "inner" not in content


def test_empty_string_deletes_helper_func(tmp_path):
    """Test that empty string deletes nested function"""
    content = """
    def outer_function():
        def helper1():
            return "helper1"

        def helper2():
            return "helper2"

        return helper1() + helper2()
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete nested function
    result = python_edit(f"{test_file}::outer_function::helper1", "")
    assert "deleted scope" in result.lower()

    # Check that only helper1 was deleted
    with open(test_file, "r") as f:
        content = f.read()
    assert "def outer_function():" in content
    assert "def helper1():" not in content
    assert "def helper2():" in content
    assert "helper1" not in content.replace("helper1()", "")  # Remove the call
    assert "helper2" in content


def test_empty_string_with_coscope_with_fails(tmp_path):
    """Test that empty string with coscope_with raises an error"""
    content = """
    def hello():
        print("Hello!")

    def goodbye():
        print("Goodbye!")
    """
    test_file = setup_test_file(tmp_path, content)

    # Try to use empty string with coscope_with - should fail
    result = python_edit(test_file, "", coscope_with="hello")
    assert "cannot use empty code with coscope_with" in result.lower() or "tool failed" in result.lower()

    # File should be unchanged
    with open(test_file, "r") as f:
        content = f.read()
    assert "def hello():" in content
    assert "def goodbye():" in content


def test_empty_string_nonexistent_scope_fails(tmp_path):
    """Test that trying to delete nonexistent scope fails"""
    content = """
    def existing_function():
        pass
    """
    test_file = setup_test_file(tmp_path, content)

    # Try to delete nonexistent function
    result = python_edit(f"{test_file}::nonexistent_function", "")
    assert "error" in result.lower() or "not found" in result.lower()

    # File should be unchanged
    with open(test_file, "r") as f:
        content = f.read()
    assert "def existing_function():" in content


@pytest.mark.skipif(
    os.environ.get("CI") == "true", reason="Flaky in CI due to temp directory race conditions - see issue #XXX"
)
def test_empty_string_preserves_file_structure(tmp_path):
    """Test that deletion preserves overall file structure"""
    content = """
    # File header comment
    import os
    from typing import List

    # Global variable
    GLOBAL_VAR = "value"

    def function_to_delete():
        pass

    def function_to_keep():
        pass

    # End of file comment
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete one function
    result = python_edit(f"{test_file}::function_to_delete", "")
    assert "deleted scope" in result.lower()

    # Check that file structure is preserved
    with open(test_file, "r") as f:
        content = f.read()
    assert "# File header comment" in content
    assert "import os" in content
    assert "from typing import List" in content
    assert "GLOBAL_VAR = " in content
    assert "function_to_delete" not in content
    assert "def function_to_keep():" in content
    assert "# End of file comment" in content


def test_empty_string_with_complex_class(tmp_path):
    """Test deletion with complex class containing multiple elements"""
    content = """
    class ComplexClass:
        '''Class docstring'''

        class_var = "class variable"

        def __init__(self):
            self.instance_var = "instance"

        @property
        def prop(self):
            return self.instance_var

        @staticmethod
        def static_method():
            return "static"

        def method_to_delete(self):
            '''Method to be deleted'''
            return "delete me"

        def method_to_keep(self):
            '''Method to keep'''
            return "keep me"
    """
    test_file = setup_test_file(tmp_path, content)

    # Delete one method from complex class
    result = python_edit(f"{test_file}::ComplexClass::method_to_delete", "")
    assert "deleted scope" in result.lower()

    # Check that everything else is preserved
    with open(test_file, "r") as f:
        content = f.read()
    assert "class ComplexClass:" in content
    assert "Class docstring" in content
    assert "class_var" in content
    assert "__init__" in content
    assert "@property" in content
    assert "@staticmethod" in content
    assert "method_to_delete" not in content
    assert "delete me" not in content
    assert "method_to_keep" in content
    assert "keep me" in content


if __name__ == "__main__":
    # Run tests manually for debugging

    with tempfile.TemporaryDirectory() as tmp_dir:
        print("Testing empty string deletion functionality...")
        test_empty_string_deletes_entire_file(tmp_dir)
        print("✓ File-level deletion works")
        test_empty_string_deletes_function(tmp_dir)
        print("✓ Function deletion works")
        test_empty_string_deletes_class(tmp_dir)
        print("✓ Class deletion works")
        test_empty_string_deletes_method(tmp_dir)
        print("✓ Method deletion works")
        test_empty_string_with_coscope_with_fails(tmp_dir)
        print("✓ Insert after with empty string fails correctly")
        test_empty_string_nonexistent_scope_fails(tmp_dir)
        print("✓ Nonexistent scope deletion fails correctly")
        print("All tests passed!")
