import ast
import astor
import os
import re
import inspect
import traceback
import datetime as DT
import subprocess


def rewrite(file_path, content):
    """
    Completely rewrites the content of a file with new content.

    Use when you want to replace the entire contents of a file or write a new file.

    Parameters:
    - file_path (str): The path to the file that will be rewritten.
    - content (str): The new content that will be written to the file.

    Returns 'success' or an error message string.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f'Rewrote {file_path} successfully'
    except Exception as error:
        return _process_error(error)

def replace_string(file_path, old_string, new_string):
    """
    Replaces all occurrences of a specified string with a new string in a file.

    Use when you need to find and replace a specific string throughout an entire file.

    Parameters:
    - file_path (str): The path to the file where the replacements will be made.
    - old_string (str): The string to be replaced.
    - new_string (str): The string that will replace the old string.

    Returns a confirmation message or an error message.
    """
    if not os.path.exists(file_path):
        return _process_error(FileNotFoundError(
            f"File '{file_path}' not found."))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        updated_content = re.sub(re.escape(old_string), new_string, content)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return (
        f"Replaced all instances of '{old_string}' with '{new_string}' in '{file_path}'."
        )

def replace_class(file_path, new_class_def, old_class_name=None):
    """
    Replaces a class definition in a file with a new class definition.

    Use when you need to update or modify an entire class definition within a Python file.

    Parameters:
    - file_path (str): The path to the file containing the class to be replaced.
    - new_class_def (str): The new class definition as a string. Note this function uses ast parsing, so it is not necessary to mimic indentation level.
    - old_class_name (str, optional): The name of the class to be replaced.

    Returns a confirmation message or an error message.
    """

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_class_node = ast.parse(_clean(new_class_def)).body[0
            ]
        if not isinstance(new_class_node, ast.ClassDef):
            return _process_error(ValueError(
                'Provided definition is not a class'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new class definition: {str(e)}'))
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

def replace_function(file_path, new_function_def):
    """
    Replaces a function definition in a file with a new function definition.

    Use when you need to update or modify an entire function within a Python file.

    Parameters:
    - file_path (str): The path to the file containing the function to be replaced.
    - new_function_def (str): The new function definition as a string. Note this function uses ast parsing, so it is not necessary to mimic indentation level.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_func_node = ast.parse(_clean(new_function_def)
            ).body[0]
        if not isinstance(new_func_node, ast.FunctionDef):
            return _process_error(ValueError(
                'Provided definition is not a function'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new function definition: {str(e)}'))
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

def add_function_to_class(file_path, class_name, new_method_def):
    """
    Adds a new method (function) to an existing class in a Python file.

    Use when you need to extend a class by adding a new method without modifying existing methods.

    Parameters:
    - file_path (str): The path to the file containing the class to be modified.
    - class_name (str): The name of the class to which the new method will be added.
    - new_method_def (str): The new method definition as a string. Note this function uses ast parsing, so it is not necessary to mimic indentation level.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_method_node = ast.parse(_clean(new_method_def)
            ).body[0]
        if not isinstance(new_method_node, ast.FunctionDef):
            return _process_error(ValueError(
                'Provided definition is not a function'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new method definition: {str(e)}'))
    try:
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))


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
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return (
        f"Method '{new_method_node.name}' has been added to class '{class_name}' in '{file_path}'."
        )

def add_function_to_file(file_path: str, new_function_def: str) -> str:
    """
    Adds a new function definition to an existing Python file.

    Use when you want to add a completely new function to a Python file without modifying existing content.

    Parameters:
    - file_path (str): The path to the file where the new function will be added.
    - new_function_def (str): The new function definition as a string. Note this function uses ast parsing, so it is not necessary to mimic indentation level.

    Returns a confirmation message or an error message.
    """

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_func_node = ast.parse(_clean(new_function_def)
            ).body[0]
        if not isinstance(new_func_node, ast.FunctionDef):
            return _process_error(ValueError(
                'Provided definition is not a function'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new function definition: {str(e)}'))
    try:
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))
    tree.body.append(new_func_node)
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return f"Function '{new_func_node.name}' has been added to '{file_path}'."

def add_class_to_file(file_path, class_def):
    """
    Adds a new class definition to an existing Python file.

    Use when you want to add a completely new class to a Python file without modifying existing content.

    Parameters:
    - file_path (str): The path to the file where the new class will be added.
    - class_def (str): The new class definition as a string. Note this function uses ast parsing, so it is not necessary to mimic indentation level.

    Returns a confirmation message or an error message.
    """

    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        new_class_node = ast.parse(_clean(class_def)).body[0]
        if not isinstance(new_class_node, ast.ClassDef):
            return _process_error(ValueError(
                'Provided definition is not a class'))
    except Exception as e:
        return _process_error(ValueError(
            f'Error in new class definition: {str(e)}'))
    try:
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(ValueError(
            f'Error parsing the file {file_path}: {str(e)}'))
    tree.body.append(new_class_node)
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return f"Class '{new_class_node.name}' has been added to '{file_path}'."

def append(file_path, content_to_append):
    """
    Appends content to the end of a file.

    Use when you want to add new content to a file without modifying its existing content.

    Parameters:
    - file_path (str): The path to the file where content will be appended.
    - content_to_append (str): The content to be added to the end of the file.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(content_to_append)
    except Exception as e:
        return _process_error(e)
    return f"Content appended to the file '{file_path}'."

def prepend(file_path, content_to_prepend):
    """
    Prepends content to the beginning of a file.

    Use when you need to add new content to the start of a file, before any existing content.

    Parameters:
    - file_path (str): The path to the file where content will be prepended.
    - content_to_prepend (str): The content to be added to the beginning of the file.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.read()
            file.seek(0, 0)
            file.write(content_to_prepend + content)
    except Exception as e:
        return _process_error(e)
    return f"Content prepended to the file '{file_path}'."

def delete_match(file_path, pattern):
    """
    Deletes all lines in a file that contain a specified pattern (case-insensitive).

    Use to remove specific content from a file based on a search pattern.

    Parameters:
    - file_path (str): The path to the file from which lines will be deleted.
    - pattern (str): The pattern to search for in each line.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in lines:
                if pattern.lower() not in line.lower():
                    file.write(line)
            return (
                f"Lines containing '{pattern}' (case-insensitive) have been deleted from '{file_path}'."
                )
    except Exception as e:
        return _process_error(e)

def read_file(file_path):
    """
    Reads and returns the entire content of a file as a string.

    Use when you need to retrieve the complete content of a file for further processing or analysis.

    Parameters:
    - file_path (str): The path to the file to be read.

    Returns the file content as a string or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return _process_error(e)

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
    except Exception as error_error:
        print(f"An error occurred: {str(error_error)}", file=sys.stderr)
        print("Local variables at the time of the error:", file=sys.stderr)
        tb = sys.exc_info()[2]
        while tb:
            frame = tb.tb_frame
            tb = tb.tb_next
            print(f"Frame {frame.f_code.co_name} in {frame.f_code.co_filename}:{frame.f_lineno}", file=sys.stderr)
            local_vars = dict(frame.f_locals)
            for key, value in local_vars.items():
                if not key.startswith('__') and key not in ['sys', 'traceback', 'error_error', 'main', 'tb', 'frame']:
                    print(f"    {key} = {value}", file=sys.stderr)
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
    
    # Get the directory of the current file (which should be in your package)
    package_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    # Define the scripts directory
    scripts_dir = os.path.join(package_root, 'scripts')

    # Create the scripts directory if it doesn't exist
    if not os.path.exists(scripts_dir):
        os.makedirs(scripts_dir)

    # Use package_root instead of cwd
    temp_file_name = os.path.join(scripts_dir, 'temp_script.py')
    temp_file_copy = os.path.join(scripts_dir, f'last_temp_script@{formatted_datetime}.py')

    with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
        temp_file.write(final_code)
        temp_file.flush()

    with open(temp_file_copy, 'w', encoding='utf-8') as temp_file:
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
            return _process_error(f'Error: Code execution timed out after {300} seconds.')
    except Exception as e:
        return _process_error(e)
    finally:
        if os.path.exists(temp_file_name):
            os.remove(temp_file_name)

def execute_powershell(code):
    """
    Executes PowerShell code in a stateless environment

    Use when you need to run PowerShell commands and capture their output.

    Parameters:
    - code (str): PowerShell code to execute.

    Returns command output or an error message.
    """
    output = ''
    try:
        result = subprocess.run(['powershell', '-Command', code],
            capture_output=True, text=True, timeout=300)
        output += result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output += 'Error: Command execution timed out after 30 seconds.'
    except Exception as e:
        output += _process_error(e)
    return output

def get_py_interface(file_path: str) -> str:
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


