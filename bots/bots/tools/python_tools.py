import inspect
import traceback
import datetime as DT
import subprocess
import ast
import astor
import os
import textwrap


def _clean_code(code: str) ->str:
    """Clean and normalize code before processing.
    
    Handles:
    - Consistent indentation via textwrap.dedent
    - Trailing whitespace
    - Ensures trailing newline
    - Converts to unix line endings
    """
    code = textwrap.dedent(code)
    code = code.strip()
    code = code.replace('\r\n', '\n')
    return code + '\n'


def _process_error(error: Exception) ->str:
    """Format an error with traceback for tool output."""
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message


def _make_file(file_path: str) ->str:
    """Creates a file and its parent directories if they don't exist.
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


class NodeTransformerWithAsyncSupport(ast.NodeTransformer):
    """Base class for AST transformers that need to handle both sync and async functions."""

    def __init__(self):
        self.success = False
        self.last_modified_idx = None

    def visit_FunctionDef(self, node):
        return self._handle_function(node)

    def visit_AsyncFunctionDef(self, node):
        return self._handle_function(node)

    def _handle_function(self, node):
        """Override this method in subclasses to implement specific transformation logic"""
        raise NotImplementedError

    def _get_node_block(self, node_list, start_idx):
        """Get all nodes that belong to the same logical block."""
        block = []
        for node in node_list[start_idx:]:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef, ast.ClassDef)):
                break
            block.append(node)
        return block

class MethodAdder(NodeTransformerWithAsyncSupport):
    def __init__(self, class_name, new_method_node, trailing_nodes=None):
        super().__init__()
        self.class_name = class_name
        self.new_method_node = new_method_node
        self.trailing_nodes = trailing_nodes or []

    def visit_ClassDef(self, node):
        if node.name == self.class_name:
            self.success = True
            # Find index after last method
            last_method_idx = -1
            for i, n in enumerate(node.body):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    last_method_idx = i
            # Insert new method after last method, or at end if no methods
            insert_idx = last_method_idx + 1 if last_method_idx >= 0 else len(node.body)
            node.body.insert(insert_idx, self.new_method_node)
            # Add any trailing nodes after the method
            for trailing_node in self.trailing_nodes:
                insert_idx += 1
                node.body.insert(insert_idx, trailing_node)
            return node
        return node

    def _handle_function(self, node):
        return node

    def __init__(self, class_name, new_method_node, trailing_nodes=None):
        super().__init__()
        self.class_name = class_name
        self.new_method_node = new_method_node
        self.trailing_nodes = trailing_nodes or []

    def visit_ClassDef(self, node):
        if node.name == self.class_name:
            self.success = True
            last_method_idx = -1
            for i, n in enumerate(node.body):
                if isinstance(n, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    last_method_idx = i
            insert_idx = last_method_idx + 1 if last_method_idx >= 0 else len(
                node.body)
            node.body.insert(insert_idx, self.new_method_node)
            for trailing_node in self.trailing_nodes:
                insert_idx += 1
                node.body.insert(insert_idx, trailing_node)
            return node
        return node

    def _handle_function(self, node):
        return node


def add_imports(file_path: str, code: str) ->str:
    """Adds multiple import statements to a Python file.
    Creates the file if it doesn't exist.
    Avoids adding duplicate imports.

    Parameters:
    - file_path (str): The path to the file where the imports will be added
    - code (str): Newline-separated import statements
        Each statement must be a valid Python import statement.
        Example:
        '''
        import os
        from typing import List
        import sys
        '''

    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        import_list = [stmt.strip() for stmt in code.strip().split('\n') if
            stmt.strip()]
        new_import_nodes = []
        for stmt in import_list:
            try:
                node = ast.parse(stmt).body[0]
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    return _process_error(ValueError(
                        f'Invalid import statement: {stmt}'))
                new_import_nodes.append(node)
            except Exception as e:
                return _process_error(ValueError(
                    f'Error parsing import statement "{stmt}": {str(e)}'))
        try:
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
        except Exception as e:
            return _process_error(ValueError(
                f'Error reading file {abs_path}: {str(e)}'))
        if not content.strip():
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write('\n'.join(import_list) + '\n')
            return (
                f"{len(import_list)} imports have been added to new file '{abs_path}'."
                )
        try:
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing the file {abs_path}: {str(e)}'))
        added_imports = []
        existing_imports = []
        for new_node in new_import_nodes:
            new_stmt = astor.to_source(new_node).strip()
            is_duplicate = False
            for existing_node in tree.body:
                if isinstance(existing_node, (ast.Import, ast.ImportFrom)):
                    if astor.to_source(existing_node).strip() == new_stmt:
                        existing_imports.append(new_stmt)
                        is_duplicate = True
                        break
            if not is_duplicate:
                added_imports.append(new_stmt)
        if added_imports:
            last_import_idx = -1
            for i, node in enumerate(tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_idx = i
            for node in reversed(new_import_nodes):
                if astor.to_source(node).strip() in added_imports:
                    tree.body.insert(last_import_idx + 1, node)
            try:
                updated_content = astor.to_source(tree)
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
            except Exception as e:
                return _process_error(e)
        result_parts = []
        if added_imports:
            result_parts.append(
                f"Added {len(added_imports)} new imports to '{abs_path}'")
        if existing_imports:
            result_parts.append(
                f'Found {len(existing_imports)} existing imports')
        if not result_parts:
            raise ValueError('No valid import statements found')
        return '. '.join(result_parts) + '.'
    except Exception as e:
        return _process_error(e)


def remove_import(file_path: str, import_to_remove: str) ->str:
    """Removes an import statement from a Python file.

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
    """Replaces an existing import statement in a Python file.

    Parameters:
    - file_path (str): The path to the file to modify
    - old_import (str): The existing import statement to replace
    - new_import (str): The new import statement

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


def add_class(file_path: str, class_def: str) ->str:
    """Adds a new class definition to an existing Python file.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file where the new class will be added
    - class_def (str): The new class definition as a string

    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean_code(class_def))
            new_class_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, astor.to_source(node).strip())
                elif isinstance(node, ast.ClassDef):
                    new_class_node = node
            if new_class_node is None:
                return _process_error(ValueError(
                    'No class definition found in provided code'))
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error processing code: {str(e)}'))
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


def replace_class(file_path: str, new_class_def: str, old_class_name: str=None
    ) ->str:
    """Replaces a class definition in a file with a new class definition.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - new_class_def (str): The new class definition
    - old_class_name (str, optional): The name of the class to replace

    Returns a confirmation message or an error message.
    """
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean_code(new_class_def))
            new_class_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, astor.to_source(node).strip())
                elif isinstance(node, ast.ClassDef):
                    new_class_node = node
                    if old_class_name is None:
                        old_class_name = node.name
            if new_class_node is None:
                return _process_error(ValueError(
                    'No class definition found in provided code'))
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error processing code: {str(e)}'))
        trailing_nodes = []
        found_class = False
        for node in new_tree.body:
            if isinstance(node, ast.ClassDef):
                found_class = True
            elif found_class:
                trailing_nodes.append(node)


        class ClassReplacer(NodeTransformerWithAsyncSupport):

            def __init__(self, old_class_name, new_class_node,
                trailing_nodes=None):
                super().__init__()
                self.old_class_name = old_class_name
                self.new_class_node = new_class_node
                self.trailing_nodes = trailing_nodes or []

            def visit_ClassDef(self, node):
                if node.name == self.old_class_name:
                    self.success = True
                    new_node = self.new_class_node
                    for trailing_node in self.trailing_nodes:
                        new_node.body.append(trailing_node)
                    return new_node
                return node

            def _handle_function(self, node):
                return node
        transformer = ClassReplacer(old_class_name, new_class_node,
            trailing_nodes)
        tree = transformer.visit(tree)
        if not transformer.success:
            tree.body.append(new_class_node)
        try:
            updated_content = astor.to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        action = 'replaced in' if transformer.success else 'added to'
        return f"Class '{new_class_node.name}' has been {action} '{abs_path}'."
    except Exception as e:
        return _process_error(e)


def add_function_to_class(file_path: str, class_name: str, new_method_def: str
    ) ->str:
    """Adds one or more methods to an existing class in a Python file.
    Creates the file and class if they don't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - class_name (str): The name of the class to modify
    - new_method_def (str): One or more method definitions as a string

    Returns a confirmation message or an error message.
    """
    try:
        tree = ast.parse(_clean_code(new_method_def))
        messages = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                add_imports(file_path, astor.to_source(node).strip())
        found_method = False
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_method = True
                method_source = astor.to_source(node)
                result = _add_single_function_to_class(file_path,
                    class_name, method_source)
                messages.append(result)
        if not found_method:
            return _process_error(ValueError(
                'No method definitions found in provided code'))
        return '\n'.join(messages)
    except Exception as e:
        return _process_error(e)


def add_function_to_file(file_path: str, new_function_def: str, class_name:
    str=None) ->str:
    """Adds one or more function definitions to an existing Python file.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - new_function_def (str): One or more function definitions as a string
    - class_name (str, optional): If provided, add functions to this class

    Returns a confirmation message or an error message.
    """
    try:
        tree = ast.parse(_clean_code(new_function_def))
        messages = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                add_imports(file_path, astor.to_source(node).strip())
        found_function = False
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_function = True
                function_source = astor.to_source(node)
                if class_name:
                    result = add_function_to_class(file_path, class_name,
                        function_source)
                else:
                    result = _add_single_function_to_file(file_path,
                        function_source)
                messages.append(result)
        if not found_function:
            return _process_error(ValueError(
                'No function definitions found in provided code'))
        return '\n'.join(messages)
    except Exception as e:
        return _process_error(e)


def replace_function(file_path: str, new_function_def: str, class_name: str
    =None) ->str:
    """Replaces one or more function definitions in a file with new function definitions.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - new_function_def (str): One or more function definitions as a string
    - class_name (str, optional): If provided, only replace functions within this class

    Returns a confirmation message or an error message.
    """
    try:
        tree = ast.parse(_clean_code(new_function_def))
        messages = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                add_imports(file_path, astor.to_source(node).strip())
        found_function = False
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_function = True
                function_source = astor.to_source(node)
                result = _replace_single_function(file_path,
                    function_source, class_name)
                messages.append(result)
        if not found_function:
            return _process_error(ValueError(
                'No function definitions found in provided code'))
        return '\n'.join(messages)
    except Exception as e:
        return _process_error(e)


def _add_single_function_to_class(file_path: str, class_name: str,
    new_method_def: str) ->str:
    """Adds a single method to a class."""
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean_code(new_method_def))
            new_method_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, astor.to_source(node).strip())
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    new_method_node = node
            if new_method_node is None:
                return _process_error(ValueError(
                    'No method definition found in provided code'))
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            if not content.strip():
                content = f'class {class_name}:\n    pass\n'
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error processing code: {str(e)}'))
        transformer = MethodAdder(class_name, new_method_node)
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


def _add_single_function_to_file(file_path: str, new_function_def: str) ->str:
    """Adds a single function to a file."""
    try:
        abs_path = _make_file(file_path)
        try:
            new_func_node = ast.parse(_clean_code(new_function_def)).body[0]
            if not isinstance(new_func_node, (ast.FunctionDef, ast.
                AsyncFunctionDef)):
                return _process_error(ValueError(
                    'Provided definition is not a function'))
        except Exception as e:
            return _process_error(ValueError(
                f'Error in new function definition: {str(e)}'))
        with open(abs_path, 'r', encoding='utf-8') as file:
            content = file.read()
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


def _replace_single_function(file_path: str, new_function_def: str,
    class_name: str=None) ->str:
    """Replaces a single function in a file, optionally within a specific class.

    Args:
        file_path: Path to the file to modify
        new_function_def: The new function definition
        class_name: If provided, only replace within this class
    """
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean_code(new_function_def))
            new_func_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, astor.to_source(node).strip())
                elif isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                    new_func_node = node
            if new_func_node is None:
                return _process_error(ValueError(
                    'No function definition found in provided code'))
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error processing code: {str(e)}'))
        trailing_nodes = []
        found_func = False
        for node in new_tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if not found_func:
                    found_func = True
                else:
                    trailing_nodes.append(node)
            elif found_func:
                trailing_nodes.append(node)


        class ClassScopedFunctionReplacer(ast.NodeTransformer):

            def __init__(self, new_func_node, target_class=None,
                trailing_nodes=None):
                self.new_func_node = new_func_node
                self.target_class = target_class
                self.trailing_nodes = trailing_nodes or []
                self.success = False
                self.in_target_class = False

            def visit_ClassDef(self, node):
                if self.target_class is None or node.name == self.target_class:
                    old_in_target_class = self.in_target_class
                    self.in_target_class = True
                    node = self.generic_visit(node)
                    self.in_target_class = old_in_target_class
                return node

            def visit_FunctionDef(self, node):
                if node.name == self.new_func_node.name:
                    if self.target_class is None or self.in_target_class:
                        self.success = True
                        new_node = self.new_func_node
                        if self.target_class is None:
                            for trailing_node in self.trailing_nodes:
                                new_node.body.extend([trailing_node])
                        return new_node
                return node

            def visit_AsyncFunctionDef(self, node):
                return self.visit_FunctionDef(node)
        transformer = ClassScopedFunctionReplacer(new_func_node, class_name,
            trailing_nodes)
        tree = transformer.visit(tree)
        if not transformer.success:
            if class_name:
                return _process_error(ValueError(
                    f"Function '{new_func_node.name}' not found in class '{class_name}'"
                    ))
            tree.body.append(new_func_node)
        try:
            updated_content = astor.to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        context = f"in class '{class_name}'" if class_name else 'in file'
        action = 'replaced' if transformer.success else 'added'
        return (
            f"Function '{new_func_node.name}' has been {action} {context} '{abs_path}'."
            )
    except Exception as e:
        return _process_error(e)
