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
                error_message = f'\nAssertion Error: {str(e)}\n'
                error_message += '\nLocal variables:\n'
                for key, value in local_vars.items():
                    error_message += f'{key} = {repr(value)}\n'
                error_message += '\nTraceback:\n'
                error_message += ''.join(traceback.format_tb(exc_traceback))
                error_message += '\nDifference between expected and actual:\n'
                diff = difflib.unified_diff(normalized_second.splitlines(
                    keepends=True), normalized_first.splitlines(keepends=
                    True), fromfile='Expected', tofile='Actual', n=3)
                error_message += ''.join(diff)
                error_message += '\nTest function source:\n'
                test_func = frame.f_code
                source_lines, start_line = inspect.getsourcelines(test_func)
                error_message += ''.join(f'{i + start_line}: {line}' for i,
                    line in enumerate(source_lines))
            else:
                error_message = f'\nAssertion Error: {str(e)}\n'
                error_message += 'Unable to retrieve local variables.\n'
                error_message += '\nTraceback:\n'
                error_message += ''.join(traceback.format_tb(exc_traceback))
            raise AssertionError(error_message)

    def assertFileContentEqual(self, file_path, expected_content, msg=None):
        with open(file_path, 'r') as f:
            actual_content = f.read()
        self.assertEqualDetailed(actual_content, expected_content, msg)


class TestPythonTools(DetailedTestCase):

    def setUp(self):
        self.test_file = 'test_file.py'
        with open(self.test_file, 'w') as f:
            f.write('# Original content\n')

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def test_replace_class(self):
        initial_content = (
            '\nclass OldClass:\n    def method(self):\n        pass\n')
        new_class = (
            '\nclass OldClass:\n    def new_method(self):\n        print("New method")\n'
            )
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, new_class,
            'Replace class failed')

    def test_replace_function(self):
        initial_content = '\ndef old_function():\n    print("Old function")\n'
        new_function = '\ndef old_function():\n    print("New function")\n'
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.replace_function(self.test_file, new_function)
        self.assertFileContentEqual(self.test_file, new_function,
            'Replace function failed')

    def test_add_function_to_class(self):
        initial_content = (
            '\nclass TestClass:\n    def existing_method(self):\n        pass\n'
            )
        new_method = '\ndef new_method(self):\n    print("New method")\n'
        expected_content = """
class TestClass:
    def existing_method(self):
        pass

    def new_method(self):
        print("New method")
"""
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.add_function_to_class(self.test_file, 'TestClass',
            new_method)
        self.assertFileContentEqual(self.test_file, expected_content,
            'Add function to class failed')

    def test_add_class(self):
        initial_content = '# Existing content\n'
        new_class = '\nclass NewClass:\n    def method(self):\n        pass\n'
        expected_content = initial_content + new_class
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.add_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content,
            'Add class to file failed')

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
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content,
            'Replace class with comments failed')

    def test_replace_class_preserve_whitespace(self):
        initial_content = """

class OldClass:

    def method(self):
        pass


# Some space after
"""
        new_class = (
            '\nclass OldClass:\n    def new_method(self):\n        print("New method")\n'
            )
        expected_content = """

class OldClass:
    def new_method(self):
        print("New method")


# Some space after
"""
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content,
            'Replace class preserve whitespace failed')

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
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content,
            'Replace complex class failed')

    def test_add_import(self):
        initial_content = '\ndef some_function():\n    pass\n'
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.add_import(self.test_file, 'import os')
        expected_after_first = (
            '\nimport os\n\ndef some_function():\n    pass\n')
        self.assertFileContentEqual(self.test_file, expected_after_first,
            'Add simple import failed')
        python_tools.add_import(self.test_file, 'from typing import List, Dict'
            )
        expected_after_second = """
import os
from typing import List, Dict

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_second,
            'Add from-import failed')
        python_tools.add_import(self.test_file, 'import os')
        self.assertFileContentEqual(self.test_file, expected_after_second,
            'Duplicate import check failed')

    def test_remove_import(self):
        initial_content = """
import os
from typing import List, Dict
import sys
from pathlib import Path

def some_function():
    pass
"""
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.remove_import(self.test_file, 'import sys')
        expected_after_first = """
import os
from typing import List, Dict
from pathlib import Path

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_first,
            'Remove simple import failed')
        python_tools.remove_import(self.test_file,
            'from typing import List, Dict')
        expected_after_second = """
import os
from pathlib import Path

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_second,
            'Remove from-import failed')
        python_tools.remove_import(self.test_file, 'import non_existent')
        self.assertFileContentEqual(self.test_file, expected_after_second,
            'Non-existent import removal check failed')

    def test_replace_import(self):
        initial_content = """
import os
from typing import List, Dict
import sys as system
from pathlib import Path as p

def some_function():
    pass
"""
        with open(self.test_file, 'w') as f:
            f.write(initial_content)
        python_tools.replace_import(self.test_file, 'import os',
            'from os import path, getcwd')
        expected_after_first = """
from os import path, getcwd
from typing import List, Dict
import sys as system
from pathlib import Path as p

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_first,
            'Update simple import to from-import failed')
        python_tools.replace_import(self.test_file,
            'from typing import List, Dict',
            'from typing import List, Dict, Optional, Union')
        expected_after_second = """
from os import path, getcwd
from typing import List, Dict, Optional, Union
import sys as system
from pathlib import Path as p

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_second,
            'Update from-import to add imports failed')
        python_tools.replace_import(self.test_file, 'import sys as system',
            'from sys import path as syspath, version as py_version')
        expected_after_third = """
from os import path, getcwd
from typing import List, Dict, Optional, Union
from sys import path as syspath, version as py_version
from pathlib import Path as p

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_third,
            'Update aliased import failed')
        python_tools.replace_import(self.test_file, 'import non_existent',
            'from non_existent import something')
        self.assertFileContentEqual(self.test_file, expected_after_third,
            'Non-existent import update check failed')


if __name__ == '__main__':
    unittest.main()
