import os
import sys
import inspect
from bots import python_tools
import unittest
import traceback
import difflib
import ast
import astor

def ast_normalize(code):
    try:
        tree = ast.parse(code)
        normalized_code = astor.to_source(tree)
        return normalized_code
    except SyntaxError:
        return code

class DetailedTestCase(unittest.TestCase):
    def assertEqualDetailed(self, first, second, msg=None):
        normalized_first = ast_normalize(first)
        normalized_second = ast_normalize(second)
        try:
            self.assertEqual(normalized_first, normalized_second, msg)
        except AssertionError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            frame = exc_traceback.tb_frame.f_back
            
            if frame:
                local_vars = frame.f_locals.copy()
                local_vars.pop('self', None)
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "\nLocal variables:\n"
                for key, value in local_vars.items():
                    error_message += f"{key} = {repr(value)}\n"
                error_message += "\nTraceback:\n"
                error_message += ''.join(traceback.format_tb(exc_traceback))
                
                error_message += "\nDifference between expected and actual:\n"
                diff = difflib.unified_diff(
                    normalized_second.splitlines(keepends=True),
                    normalized_first.splitlines(keepends=True),
                    fromfile='Expected',
                    tofile='Actual',
                    n=3
                )
                error_message += ''.join(diff)
                
                error_message += "\nTest function source:\n"
                test_func = frame.f_code
                source_lines, start_line = inspect.getsourcelines(test_func)
                error_message += ''.join(f"{i+start_line}: {line}" for i, line in enumerate(source_lines))
                
            else:
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "Unable to retrieve local variables.\n"
                error_message += "\nTraceback:\n"
                error_message += ''.join(traceback.format_tb(exc_traceback))
            
            raise AssertionError(error_message)

    def assertFileContentEqual(self, file_path, expected_content, msg=None):
        with open(file_path, 'r') as f:
            actual_content = f.read()
        self.assertEqualDetailed(actual_content, expected_content, msg)

class TestBotTools(DetailedTestCase):

    def setUp(self):
        self.test_file = 'test_file.py'
        with open(self.test_file, 'w') as f:
            f.write('# Original content\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_rewrite(self):
        new_content = '# New content'
        python_tools.rewrite(self.test_file, new_content)
        self.assertFileContentEqual(self.test_file, new_content, 'Rewrite failed')

    def test_replace_string(self):
        initial_content = "old_string = 'value'"
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.replace_string(self.test_file, 'old_string', 'new_string')
        self.assertFileContentEqual(self.test_file, "new_string = 'value'", 'Replace string failed')

    def test_replace_class(self):
        initial_content = """
class OldClass:
    def method(self):
        pass
"""
        new_class = """
class OldClass:
    def new_method(self):
        print("New method")
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, new_class, 'Replace class failed')

    def test_replace_function(self):
        initial_content = """
def old_function():
    print("Old function")
"""
        new_function = """
def old_function():
    print("New function")
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.replace_function(self.test_file, new_function)
        self.assertFileContentEqual(self.test_file, new_function, 'Replace function failed')

    def test_add_function_to_class(self):
        initial_content = """
class TestClass:
    def existing_method(self):
        pass
"""
        new_method = """
def new_method(self):
    print("New method")
"""
        expected_content = """
class TestClass:
    def existing_method(self):
        pass

    def new_method(self):
        print("New method")
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.add_function_to_class(self.test_file, 'TestClass', new_method)
        self.assertFileContentEqual(self.test_file, expected_content, 'Add function to class failed')

    def test_add_class_to_file(self):
        initial_content = "# Existing content\n"
        new_class = """
class NewClass:
    def method(self):
        pass
"""
        expected_content = initial_content + new_class
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.add_class_to_file(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, 'Add class to file failed')

    def test_append(self):
        initial_content = "# Initial content\n"
        append_content = "# Appended content\n"
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.append(self.test_file, append_content)
        self.assertFileContentEqual(self.test_file, initial_content + append_content, 'Append failed')

    def test_prepend(self):
        initial_content = "# Initial content\n"
        prepend_content = "# Prepended content\n"
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.prepend(self.test_file, prepend_content)
        self.assertFileContentEqual(self.test_file, prepend_content + initial_content, 'Prepend failed')

    def test_read_file(self):
        # Create a temporary file
        temp_file = 'temp_test_file.txt'
        with open(temp_file, 'w') as f:
            f.write("Test content")
        
        # Read the file using the new function
        content = python_tools.read_file(temp_file)
        
        # Check if the content is correct
        self.assertEqual(content, "Test content")
        
        # Clean up
        os.remove(temp_file)

    def test_delete_match(self):
        initial_content = """
# Keep this line
# Delete this line
# Keep this line too
"""
        expected_content = """
# Keep this line
# Keep this line too
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.delete_match(self.test_file, 'Delete this line')
        self.assertFileContentEqual(self.test_file, expected_content, 'Delete match failed')

    def test_replace_class_with_comments(self):
        initial_content = """
# This is a comment before the class
class OldClass:
    # This is a comment inside the class
    def method(self):
        # This is a comment inside a method
        pass
# This is a comment after the class
"""
        new_class = """
class OldClass:
    # This is a new comment
    def new_method(self):
        print("New method")
"""
        expected_content = """
# This is a comment before the class
class OldClass:
    # This is a new comment
    def new_method(self):
        print("New method")
# This is a comment after the class
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, 'Replace class with comments failed')

    def test_replace_class_preserve_whitespace(self):
        initial_content = """

class OldClass:

    def method(self):
        pass


# Some space after
"""
        new_class = """
class OldClass:
    def new_method(self):
        print("New method")
"""
        expected_content = """

class OldClass:
    def new_method(self):
        print("New method")


# Some space after
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, 'Replace class preserve whitespace failed')

    def test_replace_class_complex(self):
        initial_content = """
import some_module

@some_decorator
class ComplexClass(BaseClass1, BaseClass2):
    class_var = "some value"

    def __init__(self, arg1, arg2):
        super().__init__()
        self.arg1 = arg1
        self.arg2 = arg2

    @property
    def some_property(self):
        return self.arg1 + self.arg2

    @staticmethod
    def static_method():
        return "static result"

    class NestedClass:
        def nested_method(self):
            pass

def some_function():
    pass
"""
        new_class = """
@new_decorator
class ComplexClass(NewBase):
    new_class_var = "new value"

    def __init__(self, new_arg):
        super().__init__()
        self.new_arg = new_arg

    def new_method(self):
        return self.new_arg * 2
"""
        expected_content = """
import some_module

@new_decorator
class ComplexClass(NewBase):
    new_class_var = "new value"

    def __init__(self, new_arg):
        super().__init__()
        self.new_arg = new_arg

    def new_method(self):
        return self.new_arg * 2

def some_function():
    pass
"""
        python_tools.rewrite(self.test_file, initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, 'Replace complex class failed')

if __name__ == '__main__':
    unittest.main()

