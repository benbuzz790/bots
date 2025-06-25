import ast
import difflib
import inspect
import os
import shutil
import sys
import tempfile
import textwrap
import time
import traceback
import unittest

import psutil

from bots.tools import python_editing_tools, python_execution_tool
from tests.conftest import get_unique_filename


def ast_normalize(code):
    try:
        tree = ast.parse(code)
        normalized_code = ast.unparse(tree)
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
                local_vars.pop("self", None)
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "\nLocal variables:\n"
                for key, value in local_vars.items():
                    error_message += f"{key} = {repr(value)}\n"
                error_message += "\nTraceback:\n"
                error_message += "".join(traceback.format_tb(exc_traceback))
                error_message += "\nDifference between expected and actual:\n"
                diff = difflib.unified_diff(
                    normalized_second.splitlines(keepends=True),
                    normalized_first.splitlines(keepends=True),
                    fromfile="Expected",
                    tofile="Actual",
                    n=3,
                )
                error_message += "".join(diff)
                error_message += "\nTest function source:\n"
                test_func = frame.f_code
                source_lines, start_line = inspect.getsourcelines(test_func)
                error_message += "".join(f"{i + start_line}: {line}" for i, line in enumerate(source_lines))
            else:
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "Unable to retrieve local variables.\n"
                error_message += "\nTraceback:\n"
                error_message += "".join(traceback.format_tb(exc_traceback))
            raise AssertionError(error_message)

    def assertFileContentEqual(self, file_path, expected_content, msg=None):
        with open(file_path, "r") as f:
            actual_content = f.read()
        self.assertEqualDetailed(actual_content, expected_content, msg)


class TestPythonTools(DetailedTestCase):

    def test_class_scoped_functions(self):
        """Test function replacement and addition within specific classes"""
        test_dir = os.path.join(self.temp_dir, "test_class_scoped")
        os.makedirs(test_dir, exist_ok=True)
        test_file = os.path.join(test_dir, get_unique_filename("test_class_functions", "py"))
        try:
            initial_code = """
class TestClass:
    def test_method(self):
        return "old"

class OtherClass:
    def test_method(self):
        return "other\"
"""
            with open(test_file, "w") as f:
                f.write(textwrap.dedent(initial_code))
            new_method = '\ndef test_method(self):\n    return "new"\n'
            result = python_editing_tools.replace_function(test_file, new_method, class_name="TestClass")
            self.assertIn("replaced", result)
            with open(test_file, "r") as f:
                content = f.read()
            self.assertTrue('return "new"' in content or "return 'new'" in content)
            self.assertTrue('return "other"' in content or "return 'other'" in content)
            new_method = '\ndef new_method(self):\n    return "added"\n'
            result = python_editing_tools.add_function_to_file(test_file, new_method, class_name="TestClass")
            self.assertIn("added", result)
            with open(test_file, "r") as f:
                content = f.read()
            self.assertIn("def new_method", content)
            self.assertTrue('return "added"' in content or "return 'added'" in content)
        finally:
            if os.path.exists(test_dir):
                import shutil

                shutil.rmtree(test_dir)

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.test_file = os.path.join(self.temp_dir, get_unique_filename("test_file", "py"))
        with open(self.test_file, "w") as f:
            f.write("# Original content\n")

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.temp_dir}: {e}")

    def test_replace_class(self):
        initial_content = "\nclass OldClass:\n    def method(self):\n        pass\n"
        new_class = '\nclass OldClass:\n    def new_method(self):\n        print("New method")\n'
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, new_class, "Replace class failed")

    def test_replace_function(self):
        initial_content = '\ndef old_function():\n    print("Old function")\n'
        new_function = '\ndef old_function():\n    print("New function")\n'
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_function(self.test_file, new_function)
        self.assertFileContentEqual(self.test_file, new_function, "Replace function failed")

    def test_add_function_to_class(self):
        initial_content = "\nclass TestClass:\n    def existing_method(self):\n        pass\n"
        new_method = '\ndef new_method(self):\n    print("New method")\n'
        expected_content = """
class TestClass:
    def existing_method(self):
        pass

    def new_method(self):
        print("New method")
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_function_to_class(self.test_file, "TestClass", new_method)
        self.assertFileContentEqual(self.test_file, expected_content, "Add function to class failed")

    def test_add_class(self):
        initial_content = "# Existing content\n"
        new_class = "\nclass NewClass:\n    def method(self):\n        pass\n"
        expected_content = initial_content + new_class
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, "Add class to file failed")

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
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, "Replace class with comments failed")

    def test_replace_class_preserve_whitespace(self):
        initial_content = """

class OldClass:

    def method(self):
        pass


# Some space after
"""
        new_class = '\nclass OldClass:\n    def new_method(self):\n        print("New method")\n'
        expected_content = """

class OldClass:
    def new_method(self):
        print("New method")


# Some space after
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, "Replace class preserve whitespace failed")

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
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_class(self.test_file, new_class)
        self.assertFileContentEqual(self.test_file, expected_content, "Replace complex class failed")

    def test_add_imports(self):
        initial_content = "\ndef some_function():\n    pass\n"
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, "import os")
        expected_after_first = "\nimport os\n\ndef some_function():\n    pass\n"
        self.assertFileContentEqual(self.test_file, expected_after_first, "Add simple import failed")
        python_editing_tools.add_imports(self.test_file, "from typing import List, Dict")
        expected_after_second = """
import os
from typing import List, Dict

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_second, "Add from-import failed")
        python_editing_tools.add_imports(self.test_file, "import os")
        self.assertFileContentEqual(self.test_file, expected_after_second, "Duplicate import check failed")

    def test_remove_import(self):
        initial_content = """
import os
from typing import List, Dict
import sys
from pathlib import Path

def some_function():
    pass
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.remove_import(self.test_file, "import sys")
        expected_after_first = """
import os
from typing import List, Dict
from pathlib import Path

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_first, "Remove simple import failed")
        python_editing_tools.remove_import(self.test_file, "from typing import List, Dict")
        expected_after_second = """
import os
from pathlib import Path

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_second, "Remove from-import failed")
        python_editing_tools.remove_import(self.test_file, "import non_existent")
        self.assertFileContentEqual(self.test_file, expected_after_second, "Non-existent import removal check failed")

    def test_replace_import(self):
        initial_content = """
import os
from typing import List, Dict
import sys as system
from pathlib import Path as p

def some_function():
    pass
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_import(self.test_file, "import os", "from os import path, getcwd")
        expected_after_first = """
from os import path, getcwd
from typing import List, Dict
import sys as system
from pathlib import Path as p

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_first, "Update simple import to from-import failed")
        python_editing_tools.replace_import(
            self.test_file, "from typing import List, Dict", "from typing import List, Dict, Optional, Union"
        )
        expected_after_second = """
from os import path, getcwd
from typing import List, Dict, Optional, Union
import sys as system
from pathlib import Path as p

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_second, "Update from-import to add imports failed")
        python_editing_tools.replace_import(
            self.test_file, "import sys as system", "from sys import path as syspath, version as py_version"
        )
        expected_after_third = """
from os import path, getcwd
from typing import List, Dict, Optional, Union
from sys import path as syspath, version as py_version
from pathlib import Path as p

def some_function():
    pass
"""
        self.assertFileContentEqual(self.test_file, expected_after_third, "Update aliased import failed")
        python_editing_tools.replace_import(self.test_file, "import non_existent", "from non_existent import something")
        self.assertFileContentEqual(self.test_file, expected_after_third, "Non-existent import update check failed")

    def test_file_creation_scenarios(self):
        """Test file creation with different path scenarios"""
        import shutil
        import tempfile

        test_dir = tempfile.mkdtemp()
        try:
            simple_file = os.path.join(self.temp_dir, get_unique_filename("simple", "py"))
            python_editing_tools.add_imports(simple_file, "import os")
            self.assertTrue(os.path.exists(simple_file))
            os.remove(simple_file)
            rel_path = os.path.join(self.temp_dir, "test_subdir", get_unique_filename("relative", "py"))
            python_editing_tools.add_imports(rel_path, "import sys")
            self.assertTrue(os.path.exists(rel_path))
            shutil.rmtree(os.path.join(self.temp_dir, "test_subdir"))
            abs_path = os.path.join(test_dir, "subdir", get_unique_filename("absolute", "py"))
            python_editing_tools.add_imports(abs_path, "import datetime")
            self.assertTrue(os.path.exists(abs_path))
            class_file = os.path.join(test_dir, get_unique_filename("class_test", "py"))
            python_editing_tools.add_class(class_file, "class TestClass:\n    pass")
            self.assertTrue(os.path.exists(class_file))
            func_file = os.path.join(test_dir, get_unique_filename("func_test", "py"))
            python_editing_tools.add_function_to_file(func_file, "def test_func():\n    pass")
            self.assertTrue(os.path.exists(func_file))
            method_file = os.path.join(test_dir, get_unique_filename("method_test", "py"))
            python_editing_tools.add_function_to_class(
                method_file,
                "TestClass",
                """def test_method(self):
    pass""",
            )
            self.assertTrue(os.path.exists(method_file))
        finally:
            shutil.rmtree(test_dir)
            for f in [simple_file]:
                if os.path.exists(f):
                    os.remove(f)

    def test_make_file(self):
        """Test the private _make_file function directly for edge cases"""
        import shutil
        import tempfile

        test_dir = tempfile.mkdtemp()
        try:
            with self.assertRaises(ValueError):
                python_editing_tools._make_file("")
            simple_path = os.path.join(self.temp_dir, get_unique_filename("test_make_file", "py"))
            abs_path = python_editing_tools._make_file(simple_path)
            self.assertTrue(os.path.isabs(abs_path))
            self.assertTrue(os.path.exists(abs_path))
            os.remove(abs_path)
            rel_path = os.path.join(self.temp_dir, "test_subdir", "nested", get_unique_filename("test", "py"))
            abs_path = python_editing_tools._make_file(rel_path)
            self.assertTrue(os.path.isabs(abs_path))
            self.assertTrue(os.path.exists(abs_path))
            shutil.rmtree(os.path.join(self.temp_dir, "test_subdir"))
            abs_input_path = os.path.join(test_dir, get_unique_filename("absolute_test", "py"))
            returned_path = python_editing_tools._make_file(abs_input_path)
            self.assertEqual(os.path.abspath(abs_input_path), returned_path)
            self.assertTrue(os.path.exists(returned_path))
            existing_file = os.path.join(test_dir, get_unique_filename("existing", "py"))
            with open(existing_file, "w") as f:
                f.write("# existing content")
            abs_path = python_editing_tools._make_file(existing_file)
            self.assertTrue(os.path.exists(abs_path))
            with open(abs_path, "r") as f:
                content = f.read()
            self.assertEqual(content, "# existing content")
        finally:
            shutil.rmtree(test_dir)

    def test_definitions_with_imports(self):
        """Test that functions/classes with imports are handled correctly"""
        class_with_imports = """
from typing import List, Dict
import os.path

class TestClass:
    def method(self):
        path = os.path.join("a", "b")
        items: List[Dict] = []
        return items
"""
        python_editing_tools.replace_class(self.test_file, class_with_imports)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertIn("from typing import List, Dict", content)
        self.assertIn("import os.path", content)
        self.assertIn("class TestClass:", content)
        function_with_imports = """
from pathlib import Path
import json

def test_function():
    data = json.loads('{}')
    path = Path('test')
    return str(path)
"""
        python_editing_tools.replace_function(self.test_file, function_with_imports)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertIn("from pathlib import Path", content)
        self.assertIn("import json", content)
        self.assertIn("def test_function():", content)
        method_with_imports = """
from datetime import datetime
import calendar

def new_method(self):
    now = datetime.now()
    return calendar.month_name[now.month]
"""
        python_editing_tools.add_function_to_class(self.test_file, "TestClass", method_with_imports)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertIn("from datetime import datetime", content)
        self.assertIn("import calendar", content)
        self.assertIn("def new_method(self):", content)
        new_class_with_imports = """
from typing import Optional
import sys

class NewClass:
    def __init__(self):
        self.version: Optional[str] = sys.version
"""
        python_editing_tools.add_class(self.test_file, new_class_with_imports)
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertIn("from typing import Optional", content)
        self.assertIn("import sys", content)
        self.assertIn("class NewClass:", content)

    def test_add_multiple_methods_to_class(self):
        initial_content = "\nclass TestClass:\n    def existing_method(self):\n        pass\n"
        new_methods = """
def method1(self):
    print("Method 1")
def method2(self):
    print("Method 2")
"""
        expected_content = """
class TestClass:
    def existing_method(self):
        pass

    def method1(self):
        print("Method 1")

    def method2(self):
        print("Method 2")
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_function_to_class(self.test_file, "TestClass", new_methods)
        self.assertFileContentEqual(self.test_file, expected_content, "Add multiple methods to class failed")

    def test_add_multiple_functions_to_file(self):
        initial_content = "# Empty file\n"
        new_functions = """
def func1():
    print("Function 1")
def func2():
    print("Function 2")
"""
        expected_content = """# Empty file

def func1():
    print("Function 1")

def func2():
    print("Function 2")
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_function_to_file(self.test_file, new_functions)
        self.assertFileContentEqual(self.test_file, expected_content, "Add multiple functions to file failed")

    def test_replace_multiple_functions(self):
        initial_content = """
def func1():
    print("Old 1")
def func2():
    print("Old 2")
def func3():
    print("Keep me")
"""
        new_functions = '\ndef func1():\n    print("New 1")\ndef func2():\n    print("New 2")\n'
        expected_content = """
def func1():
    print("New 1")

def func2():
    print("New 2")

def func3():
    print("Keep me")
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_function(self.test_file, new_functions)
        self.assertFileContentEqual(self.test_file, expected_content, "Replace multiple functions failed")

    def test_replace_async_function(self):
        """Test replacing an async function with a new async function"""
        initial_content = '\nasync def old_async():\n    await some_call()\n    return "old"\n    '
        new_function = """
async def old_async():
    result = await other_call()
    return "new"
    """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_function(self.test_file, new_function)
        self.assertFileContentEqual(self.test_file, new_function, "Replace async function failed")

    def test_add_async_method_to_class(self):
        """Test adding an async method to an existing class"""
        initial_content = textwrap.dedent(
            """
            class AsyncClass:
                def normal_method(self):
                    pass
            """
        )
        new_method = textwrap.dedent(
            """
            async def async_method(self):
                result = await external_call()
                return result
            """
        )
        expected_content = textwrap.dedent(
            """
            class AsyncClass:
                def normal_method(self):
                    pass

                async def async_method(self):
                    result = await external_call()
                    return result
            """
        )
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_function_to_class(self.test_file, "AsyncClass", new_method)
        self.assertFileContentEqual(self.test_file, expected_content, "Add async method to class failed")

    def test_mixed_sync_async_functions(self):
        """Test handling a mix of sync and async functions in the same file"""
        initial_content = """
async def async_func():
    await some_call()

def sync_func():
    return "sync"
    """
        new_functions = """
async def async_func():
    return await new_call()

def sync_func():
    return "new sync"
    """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_function(self.test_file, new_functions)
        self.assertFileContentEqual(self.test_file, new_functions, "Replace mixed sync/async functions failed")

    def test_class_with_mixed_methods(self):
        """Test class containing both sync and async methods"""
        initial_content = "\nclass MixedClass:\n    def sync_method(self):\n        pass\n"
        new_methods = """
async def async_method(self):
    await something()

def another_sync(self):
    pass
"""
        expected_content = """
class MixedClass:
    def sync_method(self):
        pass

    async def async_method(self):
        await something()

    def another_sync(self):
        pass
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_function_to_class(self.test_file, "MixedClass", new_methods)
        self.assertFileContentEqual(self.test_file, expected_content, "Add mixed sync/async methods to class failed")

    def test_replace_sync_with_async(self):
        """Test replacing a sync function with an async version"""
        initial_content = '\ndef old_sync():\n    return "sync"\n'
        new_function = "\nasync def old_sync():\n    return await async_operation()\n"
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_function(self.test_file, new_function)
        self.assertFileContentEqual(self.test_file, new_function, "Replace sync with async function failed")

    def test_preserve_async_decorators(self):
        """Test preserving decorators when modifying async functions"""
        initial_content = """
@decorator1
@decorator2
async def decorated_async():
    return await something()
"""
        new_function = """
@decorator1
@decorator2
async def decorated_async():
    return await new_something()
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.replace_function(self.test_file, new_function)
        self.assertFileContentEqual(self.test_file, new_function, "Preserve async function decorators failed")

    def test_multiple_imports_basic(self):
        """Test basic addition of multiple imports to an empty file"""
        initial_content = "# Empty file\n"
        import_statements = "\nimport os\nfrom typing import List\nimport sys\n    "
        expected_content = "# Empty file\nimport os\nfrom typing import List\nimport sys\n    "
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertFileContentEqual(self.test_file, expected_content, "Basic multiple imports failed")

    def test_multiple_imports_with_existing(self):
        """Test adding multiple imports to a file with existing imports"""
        initial_content = """
import os
from datetime import datetime

def some_function():
    pass
    """
        import_statements = """
from typing import List, Dict
import sys
from pathlib import Path
    """
        expected_content = """
import os
from datetime import datetime
from typing import List, Dict
import sys
from pathlib import Path

def some_function():
    pass
    """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertFileContentEqual(self.test_file, expected_content, "Multiple imports with existing content failed")

    def test_multiple_imports_duplicates(self):
        """Test handling of duplicate imports in multiple import statements"""
        initial_content = """
import os
from typing import List

def some_function():
    pass
    """
        import_statements = """
import os
from typing import Dict
from typing import List
import sys
    """
        expected_content = """
import os
from typing import List
from typing import Dict
import sys

def some_function():
    pass
    """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertFileContentEqual(self.test_file, expected_content, "Multiple imports with duplicates failed")

    def test_multiple_imports_invalid_statement(self):
        """Test handling of invalid import statements within multiple imports"""
        initial_content = "# Empty file\n"
        import_statements = "\nimport os\nnot a valid import\nfrom typing import List\n    "
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        result = python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertIn("Tool Failed: invalid syntax", result, "Invalid import statement error not detected")
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, "# Empty file\n", "File was modified despite invalid import")

    def test_multiple_imports_whitespace_handling(self):
        """Test handling of various whitespace in multiple import statements"""
        initial_content = "# Empty file\n"
        import_statements = """

import os

from typing import List
import sys
from pathlib import Path  # with comment

    """
        expected_content = """# Empty file

import os
from typing import List
import sys
from pathlib import Path  # with comment
    """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertFileContentEqual(self.test_file, expected_content, "Multiple imports whitespace handling failed")

    def test_multiple_imports_complex_statements(self):
        """Test handling of complex import statements"""
        initial_content = "# Empty file\n"
        import_statements = """
import os.path as osp
from typing import List, Dict, Optional as Opt
import sys as system, json as jsn
from datetime import datetime as dt, timedelta
    """
        expected_content = """# Empty file
import os.path as osp
from typing import List, Dict, Optional as Opt
import sys as system, json as jsn
from datetime import datetime as dt, timedelta
    """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertFileContentEqual(self.test_file, expected_content, "Complex multiple imports failed")

    def test_multiple_imports_empty_input(self):
        """Test handling of empty or whitespace-only input"""
        initial_content = "# Empty file\n"
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        result = python_editing_tools.add_imports(self.test_file, "")
        self.assertIn("No valid import statements found", result, "Empty import string not handled properly")
        result = python_editing_tools.add_imports(self.test_file, "   \n  \t  \n   ")
        self.assertIn("No valid import statements found", result, "Whitespace-only import string not handled properly")
        with open(self.test_file, "r") as f:
            content = f.read()
        self.assertEqual(content, initial_content, "File was modified despite empty input")

    def test_indentation_handling(self):
        """Test that code tools handle various indentation patterns correctly"""
        initial_content = "class TestClass:\n    pass\n"
        indented_method = """
            def test_method(self):
                print("test")
                return True
        """
        very_indented_method = """
                    def another_method(self):
                        print("another test")
                        return False
        """
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_function_to_class(self.test_file, "TestClass", indented_method)
        python_editing_tools.add_function_to_class(self.test_file, "TestClass", very_indented_method)
        expected_tree = ast.parse(
            """
class TestClass:
    pass

    def test_method(self):
        print("test")
        return True

    def another_method(self):
        print("another test")
        return False
"""
        )
        expected_content = ast.unparse(expected_tree)
        self.assertFileContentEqual(self.test_file, expected_content, "Indentation handling failed")

    def test_multiple_imports_file_creation(self):
        """Test file creation when adding multiple imports to non-existent file"""
        import shutil
        import tempfile

        test_dir = tempfile.mkdtemp()
        try:
            test_file = os.path.join(test_dir, get_unique_filename("new_file", "py"))
            import_statements = "\nimport os\nfrom typing import List\nimport sys\n    "
            expected_content = "\nimport os\nfrom typing import List\nimport sys\n    "
            python_editing_tools.add_imports(test_file, import_statements)
            self.assertTrue(os.path.exists(test_file), "File was not created for multiple imports")
            with open(test_file, "r") as f:
                content = f.read()
            self.assertEqual(content.strip(), expected_content.strip(), "Created file content incorrect")
        finally:
            shutil.rmtree(test_dir)

    @unittest.skip("Using private implementation")
    def test_execute_python_code_basic(self):
        """Test basic code execution"""
        code = textwrap.dedent(
            """
            print("Hello, World!")
            x = 5 + 3
            print(f"Result: {x}")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Hello, World!", result)
        self.assertIn("Result: 8", result)

    def test_execute_python_code_timeout(self):
        """Test that the timeout mechanism works properly"""
        code = textwrap.dedent(
            """
            while True:
                pass
        """
        )
        result = python_execution_tool._execute_python_code(code, timeout=1)
        self.assertIn("timed out", result.lower())
        code = textwrap.dedent(
            """
            import time
            time.sleep(1)
            print("Completed")
        """
        )
        result = python_execution_tool._execute_python_code(code, timeout=2)
        self.assertIn("Completed", result)

    def test_execute_python_code_syntax_error(self):
        """Test handling of syntax errors in the code"""
        code = textwrap.dedent(
            """
            print("Start"
            while True
                print("Invalid syntax")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Tool Failed:", result)

    def test_execute_python_code_runtime_error(self):
        """Test handling of runtime errors in the code"""
        code = textwrap.dedent(
            """
            x = 1 / 0  # Division by zero
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("ZeroDivisionError", result)

    def test_execute_python_code_with_imports(self):
        """Test code execution with various imports"""
        code = textwrap.dedent(
            """
            import math
            import os
            from datetime import datetime

            print(f"Pi: {math.pi}")
            print(f"Current directory: {os.getcwd()}")
            print(f"Current hour: {datetime.now().hour}")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Pi: 3.14", result)
        self.assertIn("Current directory:", result)
        self.assertIn("Current hour:", result)

    def test_execute_python_code_with_multiline_output(self):
        """Test handling of code that produces multiline output"""
        code = textwrap.dedent(
            """
            for i in range(3):
                print(f"Line {i}")
            print("---")
            for j in range(2):
                print(f"More {j}")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        expected_lines = ["Line 0", "Line 1", "Line 2", "---", "More 0", "More 1"]
        for line in expected_lines:
            self.assertIn(line, result)

    def test_execute_python_code_with_stderr(self):
        """Test handling of code that writes to stderr"""
        code = textwrap.dedent(
            """
            import sys
            print("Standard output")
            print("Error output", file=sys.stderr)
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Standard output", result)
        self.assertIn("Error output", result)

    def test_execute_python_code_unicode(self):
        """Test handling of Unicode characters in the code and output"""
        code = textwrap.dedent(
            """
            print("Hello, 世界!")
            print("🌍 🌎 🌏")
            print("Café")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Hello, 世界!", result)
        self.assertIn("🌍 🌎 🌏", result)
        self.assertIn("Café", result)

    def test_execute_python_code_with_classes(self):
        """Test execution of code containing class definitions"""
        code = textwrap.dedent(
            """
            class TestClass:
                def __init__(self, value):
                    self.value = value

                def display(self):
                    print(f"Value is: {self.value}")

            obj = TestClass(42)
            obj.display()
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Value is: 42", result)

    def test_execute_python_code_long_output(self):
        """Test handling of code that produces a lot of output"""
        code = textwrap.dedent(
            """
            for i in range(1000):
                print(f"Line {i}")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Line 0", result)
        self.assertIn("Line 999", result)

    def test_execute_python_code_zero_timeout(self):
        """Test handling of invalid timeout values"""
        code = textwrap.dedent(
            """
            print('test')
        """
        )
        result = python_execution_tool._execute_python_code(code, timeout=0)
        self.assertIn("Tool Failed", result)
        self.assertIn("must be a positive integer", result.lower())

    def test_execute_python_code_negative_timeout(self):
        """Test handling of negative timeout values"""
        code = textwrap.dedent(
            """
            print('test')
        """
        )
        result = python_execution_tool._execute_python_code(code, timeout=-1)
        self.assertIn("Tool Failed", result)
        self.assertIn("must be a positive integer", result.lower())

    def test_execute_python_code_complex_computation(self):
        """Test execution of computationally intensive code"""
        code = textwrap.dedent(
            """
            def fibonacci(n):
                if n <= 1:
                    return n
                return fibonacci(n-1) + fibonacci(n-2)

            result = fibonacci(10)
            print(f"Fibonacci(10) = {result}")
        """
        )
        result = python_execution_tool._execute_python_code(code)
        self.assertIn("Fibonacci(10) = 55", result)

    def test_execute_python_code_process_cleanup(self):
        """Test that processes are properly cleaned up after execution"""

        initial_processes = set(psutil.Process().children(recursive=True))
        code = textwrap.dedent(
            """
            import time
            time.sleep(0.1)
        """
        )
        python_execution_tool._execute_python_code(code)
        time.sleep(0.2)
        final_processes = set(psutil.Process().children(recursive=True))
        new_processes = final_processes - initial_processes
        self.assertEqual(len(new_processes), 0, "Process cleanup failed")

    def test_parenthesized_imports(self):
        """Test handling of parenthesized multi-line import statements"""
        initial_content = "# Empty file\n"
        import_statements = """
    from typing import (
        List,
        Dict,
        Optional,
        Union
    )
    from collections import (
        defaultdict as dd,
        Counter,
        deque
    )
    import os
    """
        expected_content = """# Empty file
from typing import (
    List,
    Dict,
    Optional,
    Union
)
from collections import (
    defaultdict as dd,
    Counter,
    deque
)
import os
"""
        with open(self.test_file, "w") as f:
            f.write(initial_content)
        python_editing_tools.add_imports(self.test_file, import_statements)
        self.assertFileContentEqual(self.test_file, expected_content, "Parenthesized multi-line imports failed")


if __name__ == "__main__":
    unittest.main()
