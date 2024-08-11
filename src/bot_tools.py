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

    This function should be used when you want to replace the entire contents of a file with new content.
    It will overwrite any existing content in the file.

    Parameters:
    - file_path (str): The path to the file that will be rewritten.
    - content (str): The new content that will be written to the file.

    The function will return either 'success' or an error message string.
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

    Use this function when you need to find and replace a specific string throughout an entire file.
    It performs a case-sensitive search and replacement.

    Parameters:
    - file_path (str): The path to the file where the replacements will be made.
    - old_string (str): The string to be replaced.
    - new_string (str): The string that will replace the old string.

    The function will return a FileNotFoundError if the specified file does not exist.
    It uses regular expressions for the replacement, so special characters in the old_string will be escaped.
    Returns a confirmation message or an error message
    """
    if not os.path.exists(file_path):
        return _process_error(FileNotFoundError(f"File '{file_path}' not found."))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        updated_content = re.sub(re.escape(old_string), new_string, content)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)

    return f"Replaced all instances of '{old_string}' with '{new_string}' in '{file_path}'."

def replace_class(file_path, new_class_def, old_class_name=None):
    """
    Replaces a class definition in a file with a new class definition.

    This function is useful when you need to update or modify an entire class definition within a Python file.
    It can either replace a class with a matching name or a specified old class name.

    Parameters:
    - file_path (str): The path to the file containing the class to be replaced.
    - new_class_def (str): The new class definition as a string.
    - old_class_name (str, optional): The name of the class to be replaced. If not provided, the function will
      replace the class that matches the name in the new class definition.

    The function parses the file and the new class definition using the ast module.
    After replacing the class, it rewrites the file and returns a confirmation message.
    The function will return either the confirmation message or an error message.

    Note: This function modifies the abstract syntax tree of the file, which may affect formatting.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    new_class_node = ast.parse(_remove_common_indent(new_class_def)).body[0]
    if not isinstance(new_class_node, ast.ClassDef):
        return _process_error(ValueError('Provided definition is not a class'))
    
    try:
        tree = ast.parse(content)
    except Exception as e:
        return _process_error(e)

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
    replaced_class_name = (old_class_name if old_class_name else new_class_node.name)
    return f"Class '{replaced_class_name}' has been replaced with '{new_class_node.name}' in '{file_path}'."

def replace_function(file_path, new_function_def):
    """
    Replaces a function definition in a file with a new function definition.

    This function is used when you need to update or modify an entire function within a Python file.
    It replaces the function that matches the name of the new function definition.

    Parameters:
    - file_path (str): The path to the file containing the function to be replaced.
    - new_function_def (str): The new function definition as a string.

    The function parses the file and the new function definition using the ast module.
    It will raise a ValueError if the provided new_function_def is not a valid function definition or if the function to be replaced is not found in the file.
    After replacing the function, it rewrites the file and prints a confirmation message.

    Note: This function modifies the abstract syntax tree of the file, which may affect formatting.
    It only replaces the first occurrence of a function with the matching name.
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    new_func_node: ast.FunctionDef = ast.parse(_remove_common_indent(new_function_def)).body[0]
    if not isinstance(new_func_node, ast.FunctionDef):
        return _process_error(ValueError('Provided definition is not a function'))
    tree = ast.parse(content)


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
            f"Function'{new_func_node.name}' not found in the file:\n\n{content}\n\n."))
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return f"Function '{new_func_node.name}' has been replaced in '{file_path}'."

def add_function_to_class(file_path, class_name, new_method_def):
    """
    Adds a new method (function) to an existing class in a Python file.

    This function is useful when you need to extend a class by adding a new method without modifying the existing methods.
    It locates the specified class and appends the new method to its body.

    Parameters:
    - file_path (str): The path to the file containing the class to be modified.
    - class_name (str): The name of the class to which the new method will be added.
    - new_method_def (str): The new method definition as a string.

    The function will return a FileNotFoundError if the specified file does not exist.
    It will return a ValueError if the provided new_method_def is not a valid function definition or if the specified class is not found in the file.
    After adding the method, it rewrites the file and returns a confirmation message.

    Note: This function modifies the abstract syntax tree of the file, which may affect formatting.
    It adds the new method at the end of the class body.
    """
    if not os.path.exists(file_path):
        return _process_error(FileNotFoundError(f"File '{file_path}' not found."))
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    new_method_node = ast.parse(_remove_common_indent(new_method_def)).body[0]
    if not isinstance(new_method_node, ast.FunctionDef):
        return _process_error(ValueError('Provided definition is not a function'))
    tree = ast.parse(content)

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
            f"Class '{class_name}' not found in the file:\n\n{content}\n\n."))
    try:
        updated_content = astor.to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return f"Method '{new_method_node.name}' has been added to class '{class_name}' in '{file_path}'."

def add_function_to_file(file_path: str, new_function_def: str) -> str:
    """
    Adds a new function definition to an existing Python file.

    This function is used when you want to add a completely new function to a Python file 
    without modifying existing content. It appends the new function definition to the end 
    of the file.

    Parameters:
    - file_path (str): The path to the file where the new function will be added.
    - new_function_def (str): The new function definition as a string.

    Returns:
    - str: A confirmation message or an error message.

    The function will return a FileNotFoundError if the specified file does not exist.
    It will return a ValueError if the provided new_function_def is not a valid function 
    definition. After adding the function, it rewrites the file and returns a confirmation 
    message.

    Note: This function modifies the abstract syntax tree of the file, which may affect 
    formatting. The new function is added at the end of the file, which may not be ideal if 
    specific import orders or file structures are required.
    """
    if not os.path.exists(file_path):
        return _process_error(FileNotFoundError(f"File '{file_path}' not found."))

    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()

    new_func_node = ast.parse(_remove_common_indent(new_function_def)).body[0]
    if not isinstance(new_func_node, ast.FunctionDef):
        return _process_error(ValueError('Provided definition is not a function'))

    tree = ast.parse(content)
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

    This function is used when you want to add a completely new class to a Python file without modifying existing content.
    It appends the new class definition to the end of the file.

    Parameters:
    - file_path (str): The path to the file where the new class will be added.
    - class_def (str): The new class definition as a string.

    The function will return a FileNotFoundError if the specified file does not exist.
    It will return a ValueError if the provided class_def is not a valid class definition.
    After adding the class, it rewrites the file and returns a confirmation message.

    Note: This function modifies the abstract syntax tree of the file, which may affect formatting.
    The new class is added at the end of the file, which may not be ideal if specific import orders or file structures are required.
    """
    if not os.path.exists(file_path):
        return _process_error(FileNotFoundError(f"File '{file_path}' not found."))
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    new_class_node = ast.parse(_remove_common_indent(class_def)).body[0]
    if not isinstance(new_class_node, ast.ClassDef):
        return _process_error(ValueError('Provided definition is not a class'))
    tree = ast.parse(content)
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

    This function is useful when you want to add new content to a file without modifying its existing content.
    The new content is added at the very end of the file.

    Parameters:
    - file_path (str): The path to the file where content will be appended.
    - content_to_append (str): The content to be added to the end of the file.

    The function opens the file in append mode, which automatically positions the file pointer at the end of the file.
    After appending the content, it returns a confirmation message or an error message.

    Note: This function does not add any newline characters automatically. If you want the appended content to start on a new line,
    make sure to include a newline character at the beginning of content_to_append if necessary.
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

    This function is used when you need to add new content to the start of a file, before any existing content.
    It reads the entire file, then rewrites it with the new content at the beginning.

    Parameters:
    - file_path (str): The path to the file where content will be prepended.
    - content_to_prepend (str): The content to be added to the beginning of the file.

    The function opens the file in read and write mode ('r+'), reads all existing content, 
    moves the file pointer to the beginning, and then writes the new content followed by the existing content.
    After prepending the content, it returns either a confirmation message or an error message.

    Note: This function does not add any newline characters automatically. If you want the original content to start on a new line after the prepended content, make sure to include a newline character at the end of content_to_prepend if necessary.
    This operation rewrites the entire files.
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

    This function is useful for removing specific content from a file based on a search pattern.
    It performs a case-insensitive search and removes entire lines that contain the pattern.
    You should use this to delete file content line by line.

    Parameters:
    - file_path (str): The path to the file from which lines will be deleted.
    - pattern (str): The pattern to search for in each line. Lines containing this pattern will be removed.

    The function reads the file line by line, keeping only the lines that do not contain the pattern (case-insensitive).
    After processing, it rewrites the file with the remaining lines and returns a confirmation message.

    If the file is not found, it returns an error message.

    Note: This function removes entire lines that contain the pattern, not just the pattern itself.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in lines:
                if pattern.lower() not in line.lower():
                    file.write(line)
            return f"Lines containing '{pattern}' (case-insensitive) have been deleted from '{file_path}'."
    except Exception as e:
        return _process_error(e)

def read_file(file_path):
    """
    Reads and returns the entire content of a file as a string.

    This function is used when you need to retrieve the complete content of a file for further processing or analysis.

    Parameters:
    - file_path (str): The path to the file to be read.

    Returns:
    - str: The entire content of the file as a string.

    The function opens the file in read mode with UTF-8 encoding, reads all the content, and returns it as a string.
    It uses a context manager ('with' statement) to ensure the file is properly closed after reading.

    It assumes the file is text-based and uses UTF-8 encoding. If the file uses a different encoding, you may need to modify the function.
    If the file doesn't exist or can't be read, this function will raise an exception (like FileNotFoundError).
    """
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()

def execute_python_code(code, timeout=300):
    """
    Executes python code in a safe environment.

    Parameters:
    - code (str): Syntactically correcy python code.

    Returns:
    - stdout (str): Standard output from running the code
    - error (str): A description of the error if the code ran incorrectly
    """
    
    # Parse the input code into an AST    
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
        main_func = next(node for node in wrapper_ast.body if isinstance(node, ast.FunctionDef) and node.name == 'main')
        main_func.body = code_ast.body
        return wrapper_ast
    
    code_ast = ast.parse(code)
    wrapper_ast = create_wrapper_ast()
    combined_ast = insert_code_into_wrapper(wrapper_ast, code_ast)
    final_code = astor.to_source(combined_ast)
    now = DT.datetime.now()
    formatted_datetime = now.strftime("%Y.%m.%d-%H.%M.%S")
    temp_file_name = os.path.join(os.getcwd(), 'scripts/temp_script.py')
    temp_file_copy = os.path.join(os.getcwd(), f'scripts/last_temp_script@{formatted_datetime}.py')
    
    with open(temp_file_name, 'w', encoding='utf-8') as temp_file:
        temp_file.write(final_code)
        temp_file.flush()
    
    with open(temp_file_copy, 'w', encoding='utf-8') as temp_file:
        temp_file.write(final_code)
        temp_file.flush()

    try:
        process = subprocess.Popen(['python', temp_file_name], stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, encoding='utf-8')
        try:
            stdout, stderr = process.communicate(timeout=300)
            return stdout + stderr
        except subprocess.TimeoutExpired:
            process.terminate()
            return f"Error: Code execution timed out after {300} seconds."
    except Exception as e:
        return _process_error(e)
    finally:
        if os.path.exists(temp_file_name):
            os.remove(temp_file_name)
        return stdout


def execute_powershell(code):
    output = ''
    try:
        result = subprocess.run(["powershell", "-Command", code], capture_output=True, text=True, timeout=300)
        output += result.stdout + result.stderr
    except subprocess.TimeoutExpired:
        output += "Error: Command execution timed out after 30 seconds."
    except Exception as e:
        output += _process_error(e)
    return output

def _remove_common_indent(code):
    return code
    return inspect.cleandoc(code)

def _process_error(error):
    error_message = f"tool failed: {str(error)}\n"
    error_message += f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}"
    return error_message

def get_py_interface(file_path: str) -> str:
    """
    Outputs a string showing all of the class and function definitions including docstrings,
    but does not output the code.

    Parameters:
    - file_path (str): The path to the Python file to analyze.

    Returns:
    - str: A string containing all class and function definitions with their docstrings.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        
        tree = ast.parse(content)
        interface = []

        for node in ast.walk(tree):
            if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                definition = f"{'class' if isinstance(node, ast.ClassDef) else 'def'} {node.name}"
                if isinstance(node, ast.FunctionDef):
                    args = [arg.arg for arg in node.args.args]
                    definition += f"({', '.join(args)})"
                interface.append(definition)
                
                docstring = ast.get_docstring(node)
                if docstring:
                    interface.append(f"    \"\"\"{docstring}\"\"\"")
                interface.append("")  # Add a blank line for readability

        return "\n".join(interface)
    except Exception as e:
        return _process_error(e)

def dispatch(prompt: str, bot=None) -> bool:
    """
    Dispatches an optionally input bot with the tools defined in src/bot_tools.py with the input prompt.

    Parameters:
    - prompt (str): The input prompt to be processed by the bot.
    - bot (optional): The bot instance to use. If None, a new bot will be created.

    Returns:
    - bool: True if the dispatch was successful, False otherwise.
    """
    try:
        from src.base import Bot, Engines
        from src.openai_bots import GPTBot

        if bot is None:
            bot = GPTBot(api_key=os.environ.get('OPENAI_API_KEY'),
                         model_engine=Engines.GPT4,
                         max_tokens=1000,
                         temperature=0.7,
                         name="DispatchBot",
                         role="assistant",
                         role_description="A helpful AI assistant.")

        # Add tools from src/bot_tools.py
        bot.add_tools('src/bot_tools.py')

        # Process the prompt
        response = bot.respond(prompt)
        print(f"Bot response: {response}")
        return True
    except Exception as e:
        print(_process_error(e))
        return False