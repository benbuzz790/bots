import inspect
import traceback
import datetime as DT
import subprocess
import ast
import astor
import os


def add_import(file_path: str, import_stmt: str) ->str:
    """
    Adds a new import statement to a Python file.
    Creates the file if it doesn't exist.
    Avoids adding duplicate imports.

    Parameters:
    - file_path (str): The path to the file where the import will be added
    - import_stmt (str): The import statement to add (e.g., "import os" or "from typing import List")
        Must be a valid Python import statement.

    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        try:
            new_import_node = ast.parse(import_stmt).body[0]
            if not isinstance(new_import_node, (ast.Import, ast.ImportFrom)):
                return _process_error(ValueError(
                    'Provided statement is not a valid import'))
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing import statement: {str(e)}'))
        try:
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            return _process_error(ValueError(
                f'Error reading file {abs_path}: {str(e)}'))
        if not content.strip():
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(import_stmt + '\n')
            return (
                f"Import '{import_stmt}' has been added to new file '{abs_path}'."
                )
        try:
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing the file {abs_path}: {str(e)}'))
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                if astor.to_source(node).strip() == import_stmt:
                    return (
                        f"Import '{import_stmt}' already exists in '{abs_path}'."
                        )
        last_import_idx = -1
        for i, node in enumerate(tree.body):
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                last_import_idx = i
        tree.body.insert(last_import_idx + 1, new_import_node)
        try:
            updated_content = astor.to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return f"Import '{import_stmt}' has been added to '{abs_path}'."
    except Exception as e:
        return _process_error(e)


def remove_import(file_path: str, import_to_remove: str) ->str:
    """
    Removes an import statement from a Python file.
    
    Parameters:
    - file_path (str): The path to the file to modify
    - import_to_remove (str): The import statement to remove (e.g., "import os" or "from typing import List")
        Must match the existing import statement exactly.

    Returns a confirmation message or an error message.
    """
    if not os.path.exists(file_path):
        return _process_error(ValueError(f'File {file_path} does not exist'))
    try:
        remove_node = ast.parse(import_to_remove).body[0]
        if not isinstance(remove_node, (ast.Import, ast.ImportFrom)):
            return _process_error(ValueError(
                'Provided statement is not a valid import'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing import statement: {str(e)}'))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))
    original_length = len(tree.body)
    new_body = []
    found = False
    for node in tree.body:
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            node_str = astor.to_source(node).strip()
            if node_str == import_to_remove:
                found = True
                continue
        new_body.append(node)
    if not found:
        return f"Import '{import_to_remove}' not found in '{file_path}'."
    tree.body = new_body
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return f"Import '{import_to_remove}' has been removed from '{file_path}'."


def replace_import(file_path: str, old_import: str, new_import: str) ->str:
    """
    Replaces an existing import statement in a Python file.
    
    Parameters:
    - file_path (str): The path to the file to modify
    - old_import (str): The existing import statement to replace (e.g., "import os" or "from typing import List")
        Must match the existing import statement exactly.
    - new_import (str): The new import statement (e.g., "from os import path" or "from typing import List, Dict")
        Must be a valid Python import statement.

    Returns a confirmation message or an error message.
    """
    if not os.path.exists(file_path):
        return _process_error(ValueError(f'File {file_path} does not exist'))
    try:
        old_node = ast.parse(old_import).body[0]
        new_node = ast.parse(new_import).body[0]
        if not isinstance(old_node, (ast.Import, ast.ImportFrom)
            ) or not isinstance(new_node, (ast.Import, ast.ImportFrom)):
            return _process_error(ValueError(
                'Both statements must be valid imports'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing import statements: {str(e)}'))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))
    found = False
    for i, node in enumerate(tree.body):
        if isinstance(node, (ast.Import, ast.ImportFrom)):
            node_str = astor.to_source(node).strip()
            if node_str == old_import:
                tree.body[i] = new_node
                found = True
                break
    if not found:
        return f"Import '{old_import}' not found in '{file_path}'."
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return (
        f"Import '{old_import}' has been updated to '{new_import}' in '{file_path}'."
        )


def add_class(file_path, class_def):
    """
    Adds a new class definition to an existing Python file.
    Creates the file if it doesn't exist.

    Use when you want to add a completely new class to a Python file without modifying existing content.

    Parameters:
    - file_path (str): The path to the file where the new class will be added.
    - class_def (str): The new pure class definition as a string.
        Note this function uses ast parsing, so it is not necessary to mimic indentation level.
        Note that adding import statements outside the class will cause an error,
        as new_class_def would not be a pure class definition

    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            new_class_node = ast.parse(_clean(class_def)).body[0]
            if not isinstance(new_class_node, ast.ClassDef):
                return _process_error(ValueError(
                    'Provided definition is not a class'))
        except Exception as e:
            return _process_error(ValueError(
                f'Error in new class definition: {str(e)}'))
        if not content.strip():
            try:
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(astor.to_source(new_class_node))
                return (
                    f"Class '{new_class_node.name}' has been added to new file '{abs_path}'."
                    )
            except Exception as e:
                return _process_error(e)
        try:
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing the file {abs_path}: {str(e)}'))
        tree.body.append(new_class_node)
        try:
            updated_content = astor.to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return f"Class '{new_class_node.name}' has been added to '{abs_path}'."
    except Exception as e:
        return _process_error(e)


def replace_class(file_path, new_class_def, old_class_name=None):
    """
    Replaces a class definition in a file with a new class definition.
    Creates the file if it doesn't exist.

    Use when you need to update or modify an entire class definition within a Python file.

    Parameters:
    - file_path (str): The path to the file containing the class to be replaced.
    - new_class_def (str): The new class definition as a string. Note this function uses ast parsing, so it is not necessary to mimic indentation level.
    - old_class_name (str, optional): The name of the class to be replaced.

    Returns a confirmation message or an error message.
    """
    if not os.path.exists(file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            return _process_error(ValueError(
                f'Error creating new file {file_path}: {str(e)}'))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_class_node = ast.parse(_clean(new_class_def)).body[0]
        if not isinstance(new_class_node, ast.ClassDef):
            return _process_error(ValueError(
                'Provided definition is not a class'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new class definition: {str(e)}'))
    if not content.strip():
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(astor.to_source(new_class_node))
            return (
                f"Class '{new_class_node.name}' has been added to new file '{file_path}'."
                )
        except Exception as e:
            return _process_error(e)
    try:
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))


    class ClassReplacer(ast.NodeTransformer):

        def visit_ClassDef(self, node):
            if old_class_name:
                if node.name == old_class_name:
                    return new_class_node
            elif node.name == new_class_node.name:
                return new_class_node
            return node
    tree = ClassReplacer().visit(tree)
    updated_content = astor.to_source(tree)
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    replaced_class_name = (old_class_name if old_class_name else
        new_class_node.name)
    return (
        f"Class '{replaced_class_name}' has been replaced with '{new_class_node.name}' in '{file_path}'."
        )


def add_function_to_class(file_path, class_name, new_method_def):
    """
    Adds a new method (function) to an existing class in a Python file.
    Creates the file and class if they don't exist.

    Use when you need to extend a class by adding a new method without modifying existing methods.

    Parameters:
    - file_path (str): The path to the file containing the class to be modified.
    - class_name (str): The name of the class to which the new method will be added.
    - new_method_def (str): The new method definition as a string.
        Note this function uses ast parsing, so do not mimic indentation.
        Note that adding import statements outside the function will cause an error,
        as new_method_def would not be a pure method definition

    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            new_method_node = ast.parse(_clean(new_method_def)).body[0]
            if not isinstance(new_method_node, ast.FunctionDef):
                return _process_error(ValueError(
                    'Provided definition is not a function'))
        except Exception as e:
            return _process_error(ValueError(
                f'Error in new method definition: {str(e)}'))
        if not content.strip():
            try:
                class_template = f'class {class_name}:\n    pass\n'
                with open(abs_path, 'w', encoding='utf-8') as f:
                    f.write(class_template)
                content = class_template
            except Exception as e:
                return _process_error(e)
        try:
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing the file {abs_path}: {str(e)}'))


        class MethodAdder(ast.NodeTransformer):

            def __init__(self):
                self.success = False

            def visit_ClassDef(self, node):
                if node.name == class_name:
                    self.success = True
                    node.body.append(new_method_node)
                    return node
                return node
        transformer = MethodAdder()
        tree = transformer.visit(tree)
        if not transformer.success:
            return _process_error(ValueError(
                f"Class '{class_name}' not found in the file."))
        try:
            updated_content = astor.to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return (
            f"Method '{new_method_node.name}' has been added to class '{class_name}' in '{abs_path}'."
            )
    except Exception as e:
        return _process_error(e)


def add_function_to_file(file_path: str, new_function_def: str) ->str:
    """
    Adds a new function definition to an existing Python file.
    Creates the file if it doesn't exist.

    Use when you want to add a completely new function to a Python file without modifying existing content.

    Parameters:
    - file_path (str): The path to the file where the new function will be added.
    - new_function_def (str): The new pure function definition as a string
        Note this function uses ast parsing, so do not mimic indentation.
        Note that adding import statements outside the function will cause an error,
        as new_function_def would not be a pure function definition
    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        try:
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            new_func_node = ast.parse(_clean(new_function_def)).body[0]
            if not isinstance(new_func_node, ast.FunctionDef):
                return _process_error(ValueError(
                    'Provided definition is not a function'))
        except Exception as e:
            return _process_error(ValueError(
                f'Error in new function definition: {str(e)}'))
        if not content.strip():
            try:
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(astor.to_source(new_func_node))
                return (
                    f"Function '{new_func_node.name}' has been added to new file '{abs_path}'."
                    )
            except Exception as e:
                return _process_error(e)
        try:
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing the file {abs_path}: {str(e)}'))
        tree.body.append(new_func_node)
        try:
            updated_content = astor.to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return (
            f"Function '{new_func_node.name}' has been added to '{abs_path}'.")
    except Exception as e:
        return _process_error(e)


def replace_function(file_path, new_function_def):
    """
    Replaces a function definition in a file with a new function definition.
    Creates the file if it doesn't exist.

    Use when you need to update or modify an entire function within a Python file.

    Parameters:
    - file_path (str): The path to the file containing the function to be replaced.
    - new_function_def (str): The new, pure function definition as a string.
        Note this function uses ast parsing, so do not mimic indentation.
        Note that adding import statements outside the function will cause an error,
        as new_function_def would not be a pure function definition

    Returns a confirmation message or an error message.
    """
    if not os.path.exists(file_path):
        try:
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            return _process_error(ValueError(
                f'Error creating new file {file_path}: {str(e)}'))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_func_node = ast.parse(_clean(new_function_def)).body[0]
        if not isinstance(new_func_node, ast.FunctionDef):
            return _process_error(ValueError(
                'Provided definition is not a function'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new function definition: {str(e)}'))
    if not content.strip():
        try:
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(astor.to_source(new_func_node))
            return (
                f"Function '{new_func_node.name}' has been added to new file '{file_path}'."
                )
        except Exception as e:
            return _process_error(e)
    try:
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))


    class FunctionReplacer(ast.NodeTransformer):

        def __init__(self):
            self.success = False

        def visit_FunctionDef(self, node):
            if node.name == new_func_node.name:
                self.success = True
                return new_func_node
            return node
    transformer = FunctionReplacer()
    tree = transformer.visit(tree)
    if not transformer.success:
        return _process_error(ValueError(
            f"Function '{new_func_node.name}' not found in the file."))
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return (
        f"Function '{new_func_node.name}' has been replaced in '{file_path}'.")


def execute_python_code(code, timeout=300):
    """
    Executes python code in a stateless environment.

    Use when you need to run Python code dynamically and capture its output.

    Parameters:
    - code (str): Syntactically correct python code.
    - timeout (int): Maximum execution time in seconds.

    Returns stdout or an error message.
    """

    def create_wrapper_ast():
        wrapper_code = """
import os
import sys
import traceback
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

def main():
    pass  # Placeholder for user code

if __name__ == '__main__':
    try:
        main()
    except Exception as error:
        print(f"An error occurred: {str(error)}", file=sys.stderr)
        traceback.print_exc(file=sys.stderr)
    """
        return ast.parse(wrapper_code)

    def insert_code_into_wrapper(wrapper_ast, code_ast):
        main_func = next(node for node in wrapper_ast.body if isinstance(
            node, ast.FunctionDef) and node.name == 'main')
        main_func.body = code_ast.body
        return wrapper_ast
    try:
        code_ast = ast.parse(code)
        wrapper_ast = create_wrapper_ast()
        combined_ast = insert_code_into_wrapper(wrapper_ast, code_ast)
        final_code = astor.to_source(combined_ast)
    except Exception as e:
        return _process_error(e)
    now = DT.datetime.now()
    formatted_datetime = now.strftime('%Y.%m.%d-%H.%M.%S')
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
    scripts_dir = os.path.join(package_root, 'scripts')
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)
    temp_file_name = os.path.join(scripts_dir, 'temp_script.py')
    with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
        temp_file.write(final_code)
        temp_file.flush()
    try:
        process = subprocess.Popen(['python', temp_file_name], stdout=
            subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding=
            'utf-8')
        try:
            stdout, stderr = process.communicate(timeout=300)
            return stdout + stderr
        except subprocess.TimeoutExpired:
            process.terminate()
            return _process_error(
                f'Error: Code execution timed out after {300} seconds.')
    except Exception as e:
        return _process_error(e)
    finally:
        if os.path.exists(temp_file_name):
            os.remove(temp_file_name)


def get_py_interface(file_path: str) ->str:
    """
    Outputs a string showing all class and function definitions including docstrings.

    Use when you need to analyze the structure of a Python file without seeing the implementation details.

    Parameters:
    - file_path (str): The path to the Python file to analyze.

    Returns a string containing all class and function definitions with their docstrings.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        tree = ast.parse(content)
        interface = []
        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                definition = (
                    f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {node.name}"
                    )
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    definition += f"({', '.join(args)})"
                interface.append(definition)
                docstring = ast.get_docstring(node)
                if docstring:
                    interface.append(f'    """{docstring}"""')
                interface.append('')
        return '\n'.join(interface)
    except Exception as e:
        return _process_error(e)


def _clean(code):
    return code
    return inspect.cleandoc(code)


def _process_error(error):
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message


def _make_file(file_path: str) ->str:
    """
    Creates a file and its parent directories if they don't exist.
    Converts relative paths to absolute paths.
    
    Parameters:
    - file_path (str): The path to the file to be created
    
    Returns:
    - str: The absolute path to the file
    
    Raises:
    - ValueError: If there's an error creating the file or directories,
                 or if the file_path is empty
    """
    if not file_path:
        raise ValueError('File path cannot be empty')
    abs_path = os.path.abspath(file_path)
    dir_path = os.path.dirname(abs_path)
    if dir_path:
        try:
            os.makedirs(dir_path, exist_ok=True)
        except Exception as e:
            raise ValueError(f'Error creating directories {dir_path}: {str(e)}'
                )
    if not os.path.exists(abs_path):
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            raise ValueError(f'Error creating file {abs_path}: {str(e)}')
    return abs_path
