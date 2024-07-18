import os
import sys
import inspect
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src import bot_tools
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
        bot_tools.rewrite(self.test_file, new_content)
        self.assertFileContentEqual(self.test_file, new_content, 'Rewrite failed')

    def test_replace_string(self):
        initial_content = "old_string = 'value'"
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.replace_string(self.test_file, 'old_string', 'new_string')
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
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.replace_class(self.test_file, new_class)
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
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.replace_function(self.test_file, new_function)
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
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.add_function_to_class(self.test_file, 'TestClass', new_method)
        self.assertFileContentEqual(self.test_file, expected_content, 'Add function to class failed')

    def test_add_class_to_file(self):
        initial_content = "# Existing content\n"
        new_class = """
class NewClass:
    def method(self):
        pass
"""
        expected_content = initial_content + new_class
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.add_class_to_file(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, 'Add class to file failed')

    def test_append(self):
        initial_content = "# Initial content\n"
        append_content = "# Appended content\n"
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.append(self.test_file, append_content)
        self.assertFileContentEqual(self.test_file, initial_content + append_content, 'Append failed')

    def test_prepend(self):
        initial_content = "# Initial content\n"
        prepend_content = "# Prepended content\n"
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.prepend(self.test_file, prepend_content)
        self.assertFileContentEqual(self.test_file, prepend_content + initial_content, 'Prepend failed')

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
        bot_tools.rewrite(self.test_file, initial_content)
        bot_tools.delete_match(self.test_file, 'Delete this line')
        self.assertFileContentEqual(self.test_file, expected_content, 'Delete match failed')
if __name__ == '__main__':
    unittest.main()
