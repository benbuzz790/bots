import unittest
import os
import ast
import astor


def add_function_to_file(file_path: str, new_function_def: str, class_name:
    str=None) ->str:
    """
    Adds code containing function definitions to an existing Python file.
    Creates the file if it doesn't exist.
    Preserves all code blocks including imports, functions, and other code.

    Parameters:
    - file_path (str): The path to the file to modify
    - new_function_def (str): Code containing function definitions and other code
    - class_name (str, optional): If provided, add functions to this class

    Returns a confirmation message or an error message.
    """
    try:
        tree = ast.parse(new_function_def)
        if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) for node in tree.body):
            return _process_error(ValueError(
                'No function definitions found in provided code'))
        if class_name:
            messages = []
            for node in tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, astor.to_source(node).strip())
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    result = add_function_to_class(file_path, class_name,
                        astor.to_source(node))
                    messages.append(result)
            return '\n'.join(messages)
        else:
            return _add_single_function_to_file(file_path, new_function_def)
    except Exception as e:
        return _process_error(e)


def _add_single_function_to_file(file_path: str, new_function_def: str) ->str:
    """Adds a single function and preserves all other code blocks."""
    try:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')
        try:
            new_tree = ast.parse(new_function_def)
            new_func_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    new_func_node = node
                    break
            if not new_func_node:
                return _process_error(ValueError(
                    'No function definition found in provided code'))
        except Exception as e:
            return _process_error(ValueError(f'Error in code: {str(e)}'))
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if not content.strip():
            try:
                with open(file_path, 'w', encoding='utf-8') as file:
                    file.write(new_function_def)
                return (
                    f"Code with function '{new_func_node.name}' has been added to new file '{file_path}'."
                    )
            except Exception as e:
                return _process_error(e)
        try:
            existing_tree = ast.parse(content)
            combined_body = []
            for node in (existing_tree.body + new_tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    combined_body.append(node)
            for node in (existing_tree.body + new_tree.body):
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    combined_body.append(node)
            for node in (existing_tree.body + new_tree.body):
                if not isinstance(node, (ast.Import, ast.ImportFrom, ast.
                    FunctionDef, ast.AsyncFunctionDef)):
                    combined_body.append(node)
            combined_tree = ast.Module(body=combined_body, type_ignores=[])
            updated_content = astor.to_source(combined_tree)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return (
            f"Code with function '{new_func_node.name}' has been added to '{file_path}'."
            )
    except Exception as e:
        return _process_error(e)


def add_function_to_class(file_path: str, class_name: str, new_method_def: str
    ) ->str:
    """
    Adds code to an existing class in a Python file.
    Creates the file and class if they don't exist.
    Preserves all code blocks including class-level code.

    Parameters:
    - file_path (str): The path to the file to modify
    - class_name (str): The name of the class to modify
    - new_method_def (str): Code containing method definitions and class-level code

    Returns a confirmation message or an error message.
    """
    try:
        new_tree = ast.parse(new_method_def)
        if not any(isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)
            ) for node in new_tree.body):
            return _process_error(ValueError(
                'No method definitions found in provided code'))
        return _add_single_function_to_class(file_path, class_name,
            new_method_def)
    except Exception as e:
        return _process_error(e)


def _add_single_function_to_class(file_path: str, class_name: str,
    new_method_def: str) ->str:
    """Adds code to a class, preserving all code blocks."""
    try:
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(f'class {class_name}:\n    pass\n')
        new_tree = ast.parse(new_method_def)
        has_method = False
        for node in new_tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                has_method = True
                break
        if not has_method:
            return _process_error(ValueError(
                'No method definitions found in provided code'))
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        try:
            file_tree = ast.parse(content)


            class ClassCodeCombiner(ast.NodeTransformer):

                def __init__(self, new_nodes):
                    self.new_nodes = new_nodes
                    self.success = False

                def visit_ClassDef(self, node):
                    if node.name == class_name:
                        self.success = True
                        node.body.extend(new_tree.body)
                        return node
                    return node
            transformer = ClassCodeCombiner(new_tree.body)
            file_tree = transformer.visit(file_tree)
            if not transformer.success:
                class_node = ast.ClassDef(name=class_name, bases=[],
                    keywords=[], body=new_tree.body, decorator_list=[])
                file_tree.body.append(class_node)
            updated_content = astor.to_source(file_tree)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            return (
                f"Code has been added to class '{class_name}' in '{file_path}'."
                )
        except Exception as e:
            return _process_error(ValueError(
                f'Error processing code: {str(e)}'))
    except Exception as e:
        return _process_error(e)


def _process_error(error: Exception) ->str:
    return f'Tool Failed: {str(error)}'


class TestNewTools(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.join('test_workspace')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_file = os.path.join(self.test_dir, 'test_file.py')
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def test_preserve_non_function_code(self):
        """Test that add_function_to_file preserves non-function code blocks."""
        code_with_multiple_blocks = """
import sys
from typing import List

def test_function():
    print("Hello")

if __name__ == '__main__':
    test_function()
    print("Done")
"""
        result = add_function_to_file(self.test_file, code_with_multiple_blocks
            )
        print(f'Tool result: {result}')
        with open(self.test_file, 'r') as f:
            result_content = f.read()
        print(f'Resulting file content:\n{result_content}')
        expected_elements = ['import sys', 'from typing import List',
            'def test_function():', 'print("Hello")',
            "if __name__ == '__main__':", 'test_function()', 'print("Done")']
        for element in expected_elements:
            self.assertIn(element, result_content,
                f'Missing code block: {element}')

    def test_preserve_class_level_code(self):
        """Test that add_function_to_class preserves class-level code."""
        initial_class = """
class TestClass:
    x = 1
    print("Class initialization")
    
    if x > 0:
        y = 2
    
    def existing_method(self):
        pass
"""
        with open(self.test_file, 'w') as f:
            f.write(initial_class)
        new_method = """
def new_method(self):
    print("New method")

x = 1  # This should be ignored as it exists
print("More class code")  # This should be preserved
"""
        result = add_function_to_class(self.test_file, 'TestClass', new_method)
        print(f'Tool result: {result}')
        with open(self.test_file, 'r') as f:
            result_content = f.read()
        print(f'Resulting file content:\n{result_content}')
        expected_elements = ['x = 1', 'print("Class initialization")',
            'if x > 0:', 'y = 2', 'def existing_method(self):',
            'print("More class code")', 'def new_method(self):']
        for element in expected_elements:
            self.assertIn(element, result_content,
                f'Missing code block: {element}')


class TestNewTools(unittest.TestCase):

    def setUp(self):
        self.test_dir = os.path.join('test_workspace')
        os.makedirs(self.test_dir, exist_ok=True)
        self.test_file = os.path.join(self.test_dir, 'test_file.py')
        if os.path.exists(self.test_file):
            os.remove(self.test_file)

    def tearDown(self):
        if os.path.exists(self.test_file):
            os.remove(self.test_file)
        if os.path.exists(self.test_dir):
            os.rmdir(self.test_dir)

    def normalize_text(self, text: str) ->str:
        """Normalize text for comparison, handling quotes and whitespace."""
        text = str(text).lower()
        text = text.replace('"', '').replace("'", '')
        text = text.replace('\\n', '\n')
        return text.strip()

    def test_preserve_non_function_code(self):
        """Test that add_function_to_file preserves non-function code blocks."""
        code_with_multiple_blocks = """
import sys
from typing import List

def test_function():
    print("Hello")

if __name__ == '__main__':
    test_function()
    print("Done")
"""
        result = add_function_to_file(self.test_file, code_with_multiple_blocks
            )
        print(f'Tool result: {result}')
        with open(self.test_file, 'r') as f:
            result_content = f.read()
        print(f'Resulting file content:\n{result_content}')
        expected_elements = ['import sys', 'from typing import List',
            'def test_function():', 'print("Hello")',
            "if __name__ == '__main__':", 'test_function()', 'print("Done")']
        for element in expected_elements:
            self.assertIn(self.normalize_text(element), self.normalize_text
                (result_content), f'Missing code block: {element}')

    def test_preserve_class_level_code(self):
        """Test that add_function_to_class preserves class-level code."""
        initial_class = """
class TestClass:
    x = 1
    print("Class initialization")
    
    if x > 0:
        y = 2
    
    def existing_method(self):
        pass
"""
        with open(self.test_file, 'w') as f:
            f.write(initial_class)
        new_method = """
def new_method(self):
    print("New method")

x = 1  # This should be ignored as it exists
print("More class code")  # This should be preserved
"""
        result = add_function_to_class(self.test_file, 'TestClass', new_method)
        print(f'Tool result: {result}')
        with open(self.test_file, 'r') as f:
            result_content = f.read()
        print(f'Resulting file content:\n{result_content}')
        expected_elements = ['x = 1', 'print("Class initialization")',
            'if x > 0:', 'y = 2', 'def existing_method(self):',
            'print("More class code")', 'def new_method(self):']
        for element in expected_elements:
            self.assertIn(self.normalize_text(element), self.normalize_text
                (result_content), f'Missing code block: {element}')
