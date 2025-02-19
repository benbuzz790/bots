import inspect
import traceback
import datetime as DT
import subprocess
import ast
import astor
import os
import textwrap
from bots.utils.helpers import _process_error, _clean, py_ast_to_source

class NodeTransformerWithAsyncSupport(ast.NodeTransformer):
    """Base class for AST transformers that need to handle both sync and async functions."""

    def __init__(self):
        self.success = False

    def visit_FunctionDef(self, node):
        return self._handle_function(node)

    def visit_AsyncFunctionDef(self, node):
        return self._handle_function(node)

    def _handle_function(self, node):
        """Override this method in subclasses to implement specific transformation logic"""
        raise NotImplementedError


class FunctionReplacer(NodeTransformerWithAsyncSupport):

    def __init__(self, new_func_node):
        super().__init__()
        self.new_func_node = new_func_node

    def _handle_function(self, node):
        if node.name == self.new_func_node.name:
            self.success = True
            return self.new_func_node
        return node


class MethodAdder(NodeTransformerWithAsyncSupport):

    def __init__(self, class_name, new_method_node):
        super().__init__()
        self.class_name = class_name
        self.new_method_node = new_method_node

    def visit_ClassDef(self, node):
        if node.name == self.class_name:
            self.success = True
            node.body.append(self.new_method_node)
            return node
        return node

    def _handle_function(self, node):
        return node


def add_imports(file_path: str, code: str) ->str:
    """
    Adds multiple import statements to a Python file.
    Creates the file if it doesn't exist.
    Avoids adding duplicate imports.

    Parameters:
    - file_path (str): The path to the file where the imports will be added
    - code (str): Import statements, which can include parenthesized multi-line imports

    Returns a confirmation message or an error message.

    cost: very low
    """
    try:
        abs_path = _make_file(file_path)
        lines = code.strip().split('\n')
        import_blocks = []
        current_block = []
        in_parentheses = False
        for line in lines:
            stripped = line.strip()
            if not stripped:
                continue
            if '(' in stripped and not stripped.endswith(')'):
                in_parentheses = True
                current_block.append(stripped)
            elif ')' in stripped and in_parentheses:
                in_parentheses = False
                current_block.append(stripped)
                import_blocks.append('\n'.join(current_block))
                current_block = []
            elif in_parentheses:
                current_block.append(stripped)
            elif current_block:
                current_block.append(stripped)
            else:
                import_blocks.append(stripped)
        if current_block:
            import_blocks.append('\n'.join(current_block))
        new_import_nodes = []
        for stmt in import_blocks:
            try:
                node = ast.parse(_clean(stmt)).body[0]
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
                file.write('\n'.join(import_blocks) + '\n')
            return (
                f"{len(import_blocks)} imports have been added to new file '{abs_path}'."
                )
        try:
            tree = ast.parse(content)
        except Exception as e:
            return _process_error(ValueError(
                f'Error parsing the file {abs_path}: {str(e)}'))
        added_imports = []
        existing_imports = []

        def normalize_import(node):
            """Helper to normalize import node to string for comparison"""
            return py_ast_to_source(node).strip().replace(' ', '')
        for new_node in new_import_nodes:
            new_stmt_normalized = normalize_import(new_node)
            is_duplicate = False
            for existing_node in tree.body:
                if isinstance(existing_node, (ast.Import, ast.ImportFrom)):
                    if normalize_import(existing_node) == new_stmt_normalized:
                        existing_imports.append(py_ast_to_source(new_node).strip())
                        is_duplicate = True
                        break
            if not is_duplicate:
                added_imports.append(py_ast_to_source(new_node).strip())
        if added_imports:
            last_import_idx = -1
            for i, node in enumerate(tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    last_import_idx = i
            for node in new_import_nodes:
                if py_ast_to_source(node).strip() in added_imports:
                    tree.body.insert(last_import_idx + 1, node)
                    last_import_idx += 1
            try:
                updated_content = py_ast_to_source(tree)
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
    """
    Removes an import statement from a Python file.
    
    Parameters:
    - file_path (str): The path to the file to modify
    - import_to_remove (str): The import statement to remove (e.g., "import os" or "from typing import List")
        Must match the existing import statement exactly.

    Returns a confirmation message or an error message.

    cost: very low
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
            node_str = py_ast_to_source(node).strip()
            if node_str == import_to_remove:
                found = True
                continue
        new_body.append(node)
    if not found:
        return f"Import '{import_to_remove}' not found in '{file_path}'."
    tree.body = new_body
    try:
        updated_content = py_ast_to_source(tree)
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
    - old_import (str): The existing import statement to replace
    - new_import (str): The new import statement

    Returns a confirmation message or an error message.

    cost: very low
    """
    if not os.path.exists(file_path):
        return _process_error(ValueError(f'File {file_path} does not exist'))
    try:
        old_node = ast.parse(_clean(old_import)).body[0]
        new_node = ast.parse(_clean(new_import)).body[0]
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
            node_str = py_ast_to_source(node).strip()
            if node_str == old_import:
                tree.body[i] = new_node
                found = True
                break
    if not found:
        return f"Import '{old_import}' not found in '{file_path}'."
    try:
        updated_content = py_ast_to_source(tree)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return (
        f"Import '{old_import}' has been updated to '{new_import}' in '{file_path}'."
        )


def add_class(file_path: str, class_def: str) ->str:
    """
    Adds a new class definition to an existing Python file.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file where the new class will be added
    - class_def (str): The new class definition as a string

    Returns a confirmation message or an error message.

    cost: low
    """
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean(class_def))
            new_class_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, py_ast_to_source(node).strip())
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
            updated_content = py_ast_to_source(tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return f"Class '{new_class_node.name}' has been added to '{abs_path}'."
    except Exception as e:
        return _process_error(e)


def replace_class(file_path: str, new_class_def: str, old_class_name: str=None
    ) ->str:
    """
    Replaces a class definition in a file with a new class definition.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - new_class_def (str): The new class definition
    - old_class_name (str, optional): The name of the class to replace

    Returns a confirmation message or an error message.

    cost: low
    """
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean(new_class_def))
            new_class_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, py_ast_to_source(node).strip())
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


        class ClassReplacer(NodeTransformerWithAsyncSupport):

            def visit_ClassDef(self, node):
                if node.name == old_class_name:
                    self.success = True
                    return new_class_node
                return node

            def _handle_function(self, node):
                return node
        transformer = ClassReplacer()
        tree = transformer.visit(tree)
        if not transformer.success:
            tree.body.append(new_class_node)
        try:
            updated_content = py_ast_to_source(tree)
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
    """
    Adds one or more methods to an existing class in a Python file.
    Creates the file and class if they don't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - class_name (str): The name of the class to modify
    - new_method_def (str): One or more method definitions as a string

    Returns a confirmation message or an error message.

    cost: very low
    """
    try:
        tree = ast.parse(_clean(new_method_def))
        messages = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                add_imports(file_path, py_ast_to_source(node).strip())
        found_method = False
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_method = True
                method_source = py_ast_to_source(node)
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
    """
    Adds one or more function definitions to an existing Python file.
    Creates the file if it doesn't exist.

    When adding complex code blocks:
    - Imports are moved to the top of the file
    - Functions are added in order of appearance
    - Non-function code (assignments, if blocks, etc.) is preserved but may be reordered
    - Comments are not preserved (limitation of AST)

    Parameters:
    - file_path (str): The path to the file to modify
    - new_function_def (str): One or more function definitions as a string
    - class_name (str, optional): If provided, add functions to this class

    Returns a confirmation message or an error message.

    cost: very low
    """
    try:
        tree = ast.parse(_clean(new_function_def))
        messages = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                add_imports(file_path, py_ast_to_source(node).strip())
        found_function = False
        remaining_nodes = []
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_function = True
                function_source = py_ast_to_source(node)
                if class_name:
                    result = add_function_to_class(file_path, class_name,
                        function_source)
                else:
                    result = _add_single_function_to_file(file_path,
                        function_source)
                messages.append(result)
            elif not isinstance(node, (ast.Import, ast.ImportFrom)):
                remaining_nodes.append(node)
        if not found_function:
            return _process_error(ValueError(
                'No function definitions found in provided code'))
        if remaining_nodes:
            with open(file_path, 'r', encoding='utf-8') as file:
                content = file.read()
            existing_tree = ast.parse(content)
            existing_tree.body.extend(remaining_nodes)
            updated_content = py_ast_to_source(existing_tree)
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
            messages.append(
                f'Added {len(remaining_nodes)} additional code blocks')
        return '\n'.join(messages)
    except Exception as e:
        return _process_error(e)


def replace_function(file_path: str, new_function_def: str, class_name: str
    =None) ->str:
    """
    Replaces one or more function definitions in a file with new function definitions.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): The path to the file to modify
    - new_function_def (str): One or more function definitions as a string
    - class_name (str, optional): If provided, only replace functions within this class

    Returns a confirmation message or an error message.

    cost: very low
    """
    try:
        tree = ast.parse(_clean(new_function_def))
        messages = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                add_imports(file_path, py_ast_to_source(node).strip())
        found_function = False
        for node in tree.body:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                found_function = True
                function_source = py_ast_to_source(node)
                result = _replace_single_function(file_path,
                    function_source, class_name)
                messages.append(result)
        if not found_function:
            return _process_error(ValueError(
                'No function definitions found in provided code'))
        return '\n'.join(messages)
    except Exception as e:
        return _process_error(e)


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


def _add_single_function_to_class(file_path: str, class_name: str,
    new_method_def: str) ->str:
    """Adds a single method to a class."""
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean(new_method_def))
            new_method_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, py_ast_to_source(node).strip())
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
            updated_content = py_ast_to_source(tree)
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
    """Adds a single function and preserves all code blocks, including any code following the function."""
    try:
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean(new_function_def))
            new_func_node = None
            found_func = False
            new_nodes = []
            for node in new_tree.body:
                if not found_func and isinstance(node, (ast.FunctionDef,
                    ast.AsyncFunctionDef)):
                    new_func_node = node
                    found_func = True
                elif found_func:
                    new_nodes.append(node)
            if not new_func_node:
                return _process_error(ValueError(
                    'No function definition found in provided code'))
        except Exception as e:
            return _process_error(ValueError(f'Error in code: {str(e)}'))
        with open(abs_path, 'r', encoding='utf-8') as file:
            content = file.read()
        if not content.strip():
            try:
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(py_ast_to_source(new_tree))
                return (
                    f"Code with function '{new_func_node.name}' has been added to new file '{abs_path}'."
                    )
            except Exception as e:
                return _process_error(e)
        try:
            existing_tree = ast.parse(content)
            combined_body = []
            imports = []
            for node in (existing_tree.body + new_tree.body):
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
            combined_body.extend(imports)
            for node in existing_tree.body:
                if not isinstance(node, (ast.Import, ast.ImportFrom)):
                    combined_body.append(node)
            combined_body.append(new_func_node)
            combined_body.extend(new_nodes)
            combined_tree = ast.Module(body=combined_body, type_ignores=[])
            updated_content = py_ast_to_source(combined_tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        return (
            f"Code with function '{new_func_node.name}' has been added to '{abs_path}'."
            )
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
            new_tree = ast.parse(_clean(new_function_def))
            new_func_node = None
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    add_imports(file_path, py_ast_to_source(node).strip())
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


        class ClassScopedFunctionReplacer(ast.NodeTransformer):

            def __init__(self, new_func_node, target_class=None):
                self.new_func_node = new_func_node
                self.target_class = target_class
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
                        return self.new_func_node
                return node

            def visit_AsyncFunctionDef(self, node):
                return self.visit_FunctionDef(node)
        transformer = ClassScopedFunctionReplacer(new_func_node, class_name)
        tree = transformer.visit(tree)
        if not transformer.success:
            if class_name:
                return _process_error(ValueError(
                    f"Function '{new_func_node.name}' not found in class '{class_name}'"
                    ))
            tree.body.append(new_func_node)
        try:
            updated_content = py_ast_to_source(tree)
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
