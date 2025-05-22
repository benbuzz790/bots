import ast
import os
import textwrap
from bots.utils.helpers import _process_error, _clean, _py_ast_to_source

def python_edit(target_scope: str, code: str, *, insert_after: str=None) -> str:
    """
    Edit Python code using pytest-style scope syntax.

    Parameters:
    ----------
    target_scope : str
        Location to edit in pytest-style scope syntax:
        - "file.py" (whole file)
        - "file.py::MyClass" (class)
        - "file.py::my_function" (function)
        - "file.py::MyClass::method" (method)
        - "file.py::Outer::Inner::method" (nested)
        - "file.py::utils::helper_func" (nested function)

    code : str
        Python code to insert/replace. Will be cleaned/dedented.
        Import statements will be automatically extracted and handled.

    insert_after : str, optional
        Where to insert the code. Can be either:
        - "__FILE_START__" (special token for file beginning)
        - A scope ("MyClass::method")
        - An exact line match
        If not specified, replaces the node at target_scope.

    Returns:
    --------
    str
        Description of what was modified or error message
    """
    try:
        file_path, *path_elements = target_scope.split('::')
        if not file_path.endswith('.py'):
            return _process_error(ValueError(f'File path must end with .py: {file_path}'))
        for element in path_elements:
            if not element.isidentifier():
                return _process_error(ValueError(f'Invalid identifier in path: {element}'))
        abs_path = _make_file(file_path)
        try:
            new_tree = ast.parse(_clean(code))
            import_nodes = []
            code_nodes = []
            for node in new_tree.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    import_nodes.append(node)
                else:
                    code_nodes.append(node)
        except Exception as e:
            return _process_error(ValueError(f'Error parsing new code: {str(e)}'))
        try:
            with open(abs_path, 'r', encoding='utf-8') as file:
                content = file.read()
            file_lines = content.split('\n')
            tree = ast.parse(content) if content.strip() else ast.Module(body=[], type_ignores=[])
        except Exception as e:
            return _process_error(ValueError(f'Error reading/parsing file {abs_path}: {str(e)}'))
        existing_imports = []
        non_imports = []
        for node in tree.body:
            if isinstance(node, (ast.Import, ast.ImportFrom)):
                existing_imports.append(node)
            else:
                non_imports.append(node)
        if insert_after == '__FILE_START__':
            tree.body = import_nodes + code_nodes + existing_imports + non_imports
            try:
                updated_content = _py_ast_to_source(tree)
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                return f"Code inserted at start of '{abs_path}'."
            except Exception as e:
                return _process_error(e)
        if not path_elements:
            tree.body = existing_imports + import_nodes + non_imports + code_nodes
            try:
                updated_content = _py_ast_to_source(tree)
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(updated_content)
                return f"Code added at file level in '{abs_path}'."
            except Exception as e:
                return _process_error(e)
        tree.body = existing_imports + import_nodes + non_imports
        transformer = ScopeTransformer(path_elements, code_nodes, insert_after, file_lines)
        modified_tree = transformer.visit(tree)
        if not transformer.success:
            if insert_after:
                return _process_error(ValueError(f'Insert point not found: {insert_after}'))
            else:
                return _process_error(ValueError(f'Target scope not found: {target_scope}'))
        try:
            updated_content = _py_ast_to_source(modified_tree)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(updated_content)
        except Exception as e:
            return _process_error(e)
        action = 'inserted after' if insert_after else 'replaced at'
        scope_str = '::'.join(path_elements) if path_elements else 'file level'
        return f"Code {action} {scope_str} in '{abs_path}'."
    except Exception as e:
        return _process_error(e)

def _make_file(file_path: str) -> str:
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
            raise ValueError(f'Error creating directories {dir_path}: {str(e)}')
    if not os.path.exists(abs_path):
        try:
            with open(abs_path, 'w', encoding='utf-8') as f:
                f.write('')
        except Exception as e:
            raise ValueError(f'Error creating file {abs_path}: {str(e)}')
    return abs_path

class ScopeTransformer(ast.NodeTransformer):
    """AST transformer that handles scope-based Python code modifications."""

    def __init__(self, path_elements, new_nodes, insert_after=None, file_lines=None):
        self.original_path = path_elements
        self.new_nodes = new_nodes
        self.insert_after = insert_after
        self.file_lines = file_lines
        self.current_path = []
        self.success = False
        self.line_match_count = 0

    def visit_ClassDef(self, node):
        """Visit a class definition node."""
        if not self.original_path or node.name != self.original_path[0]:
            return self.generic_visit(node)
        self.current_path.append(node.name)
        remaining_path = self.original_path[1:]
        if not remaining_path:
            if self.insert_after:
                node = self._handle_insertion(node)
            else:
                self.success = True
                if len(self.new_nodes) == 1:
                    return self.new_nodes[0]
                else:
                    node.body = self.new_nodes
                    return node
        else:
            saved_path = self.original_path
            self.original_path = remaining_path
            node.body = [self.visit(child) for child in node.body]
            self.original_path = saved_path
        self.current_path.pop()
        return node

    def visit_FunctionDef(self, node):
        """Visit a function definition node."""
        return self._handle_function_node(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit an async function definition node."""
        return self._handle_function_node(node)

    def _handle_function_node(self, node):
        """Common handling for both regular and async functions."""
        if not self.original_path or node.name != self.original_path[0]:
            return self.generic_visit(node)
        self.current_path.append(node.name)
        remaining_path = self.original_path[1:]
        if not remaining_path:
            if self.insert_after:
                node = self._handle_insertion(node)
            else:
                self.success = True
                if len(self.new_nodes) == 1:
                    return self.new_nodes[0]
                else:
                    node.body = self.new_nodes
                    return node
        else:
            saved_path = self.original_path
            self.original_path = remaining_path
            node.body = [self.visit(child) for child in node.body]
            self.original_path = saved_path
        self.current_path.pop()
        return node

    def _handle_one_line_function(self, node, line):
        """Special handling for one-line function definitions"""
        if ': pass' in line or ':pass' in line:
            base_indent = len(line) - len(line.lstrip())
            def_line = line.rstrip()
            if self.insert_after == 'pass':
                def_line = def_line.replace(': pass', ':').replace(':pass', ':')
                body_indent = base_indent + 4
                body_lines = []
                body_lines.append(' ' * body_indent + 'pass')
                for new_node in self.new_nodes:
                    node_lines = _py_ast_to_source(new_node).split('\n')
                    for nl in node_lines:
                        if nl.strip():
                            body_lines.append(' ' * body_indent + nl.lstrip())
                new_source = def_line + '\n' + '\n'.join(body_lines)
                try:
                    new_node = ast.parse(new_source).body[0]
                    self.success = True
                    return new_node
                except Exception:
                    normalized = textwrap.dedent(new_source)
                    try:
                        new_node = ast.parse(normalized).body[0]
                        self.success = True
                        return new_node
                    except Exception:
                        pass
        return node

    def _handle_insertion(self, node):
        """Handle inserting nodes after a specific point."""
        if isinstance(self.insert_after, str) and '::' not in self.insert_after:
            if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                if node.lineno == node.end_lineno:
                    line = self.file_lines[node.lineno - 1]
                    return self._handle_one_line_function(node, line)
                orig_source = self._preserve_node_source(node)
                lines = orig_source.split('\n')
                def_line = lines[0]
                body_lines = lines[1:]
                base_indent = len(def_line) - len(def_line.lstrip())
                body_indent = base_indent + 4
                target = self.insert_after.strip()
                for i, line in enumerate(body_lines):
                    line = line.rstrip()
                    if line.strip() == target:
                        self.line_match_count += 1
                        if self.line_match_count == 1:
                            insertion = []
                            for new_node in self.new_nodes:
                                node_lines = _py_ast_to_source(new_node).split('\n')
                                for nl in node_lines:
                                    if nl.strip():
                                        insertion.append(' ' * body_indent + nl.lstrip())
                                    else:
                                        insertion.append('')
                            body_lines[i:i + 1] = [body_lines[i]] + insertion
                            self.success = True
                            break
                if self.line_match_count == 0:
                    return node
                elif self.line_match_count > 1:
                    raise ValueError(f'Ambiguous insert_after - found {self.line_match_count} matches for: {self.insert_after}')
                new_source = def_line + '\n' + '\n'.join((l for l in body_lines if l is not None))
                try:
                    new_node = ast.parse(new_source).body[0]
                    for attr in ['lineno', 'col_offset', 'end_lineno', 'end_col_offset']:
                        if hasattr(node, attr):
                            setattr(new_node, attr, getattr(node, attr))
                    new_node._source = orig_source
                    return new_node
                except Exception:
                    return node
            return node
        else:
            if self.insert_after:
                target_path = self.insert_after.split('::')
                current_path = self.current_path
                if len(current_path) == len(target_path) and all((c == t for c, t in zip(current_path, target_path))):
                    self.success = True
                    if isinstance(node, ast.ClassDef):
                        node.body.extend(self.new_nodes)
                    else:
                        for new_node in self.new_nodes:
                            node.body.append(new_node)
            return node

    def _preserve_node_source(self, node):
        """Get the original source of a node, preserving comments and formatting"""
        if hasattr(node, 'lineno') and hasattr(node, 'end_lineno'):
            lines = self.file_lines[node.lineno - 1:node.end_lineno]
            return '\n'.join(lines)
        return _py_ast_to_source(node)
