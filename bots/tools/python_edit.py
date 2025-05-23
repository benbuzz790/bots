import ast
import os
import textwrap
TOKEN_START = ';;;'
TOKEN_END = ';;;'
from bots.utils.helpers import _process_error, _clean, _py_ast_to_source
import hashlib
import re
from typing import Dict, Tuple
from typing import Dict, Tuple, Union

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
        cleaned_code = _clean(code)
        tokenized_code, new_code_tokens = tokenize_source(cleaned_code)
        try:
            new_tree = ast.parse(tokenized_code)
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
            tokenized_content, file_tokens = tokenize_source(content) if content.strip() else ('', {})
            file_lines = tokenized_content.split('\n')
            tree = ast.parse(tokenized_content) if content.strip() else ast.Module(body=[], type_ignores=[])
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
                all_tokens = {**file_tokens, **new_code_tokens}
                final_content = detokenize_source(updated_content, all_tokens)
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(final_content)
                return f"Code inserted at start of '{abs_path}'."
            except Exception as e:
                return _process_error(e)
        if not path_elements:
            tree.body = existing_imports + import_nodes + non_imports + code_nodes
            try:
                updated_content = _py_ast_to_source(tree)
                all_tokens = {**file_tokens, **new_code_tokens}
                final_content = detokenize_source(updated_content, all_tokens)
                with open(abs_path, 'w', encoding='utf-8') as file:
                    file.write(final_content)
                return f"Code added at file level in '{abs_path}'."
            except Exception as e:
                return _process_error(e)
        tree.body = existing_imports + import_nodes + non_imports
        transformer = ScopeTransformer(path_elements, code_nodes, insert_after, file_lines, file_tokens, new_code_tokens)
        modified_tree = transformer.visit(tree)
        if not transformer.success:
            if insert_after:
                return _process_error(ValueError(f'Insert point not found: {insert_after}'))
            else:
                return _process_error(ValueError(f'Target scope not found: {target_scope}'))
        try:
            updated_content = _py_ast_to_source(modified_tree)
            all_tokens = {**file_tokens, **new_code_tokens}
            final_content = detokenize_source(updated_content, all_tokens)
            with open(abs_path, 'w', encoding='utf-8') as file:
                file.write(final_content)
            action = 'inserted after' if insert_after else 'replaced at'
            scope_str = '::'.join(path_elements) if path_elements else 'file level'
            return f"Code {action} {scope_str} in '{abs_path}'."
        except Exception as e:
            return _process_error(e)
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

    def __init__(self, path_elements, new_nodes, insert_after=None, file_lines=None, file_tokens=None, new_tokens=None):
        self.original_path = path_elements
        self.new_nodes = new_nodes
        self.insert_after = insert_after
        self.file_lines = file_lines
        self.file_tokens = file_tokens or {}
        self.new_tokens = new_tokens or {}
        self.current_path = []
        self.success = False
        self.line_match_count = 0
        self.all_tokens = {**self.file_tokens, **self.new_tokens}

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
            if not isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)):
                return node
            if node.lineno == node.end_lineno:
                return self._handle_one_line_function(node, self.file_lines[node.lineno - 1])
            func_lines = self.file_lines[node.lineno - 1:node.end_lineno]
            if not func_lines:
                return node
            target = self.insert_after.strip()
            target_line_idx = None
            for i, line in enumerate(func_lines):
                detokenized_line = detokenize_source(line, self.all_tokens)
                if detokenized_line.strip() == target:
                    self.line_match_count += 1
                    if self.line_match_count == 1:
                        target_line_idx = i
            if self.line_match_count == 0:
                return node
            elif self.line_match_count > 1:
                raise ValueError(f'Ambiguous insert_after - found {self.line_match_count} matches for: {self.insert_after}')
            target_absolute_line = node.lineno + target_line_idx
            containing_node = self._find_containing_node(node, target_absolute_line)
            if containing_node and containing_node is not node:
                self._insert_into_node(containing_node, target_absolute_line)
            else:
                insert_index = len(node.body)
                for idx, child in enumerate(node.body):
                    if hasattr(child, 'lineno') and child.lineno > target_absolute_line:
                        insert_index = idx
                        break
                if insert_index == len(node.body):
                    node.body.extend(self.new_nodes)
                else:
                    for i, new_node in enumerate(self.new_nodes):
                        node.body.insert(insert_index + i, new_node)
            self.success = True
            return node
        else:
            if self.insert_after:
                target_path = self.insert_after.split('::')
                current_path = self.current_path
                if len(target_path) > 1 and len(current_path) == len(target_path) - 1:
                    if all((c == t for c, t in zip(current_path, target_path[:len(current_path)]))):
                        target_name = target_path[-1]
                        insert_index = None
                        for idx, child in enumerate(node.body):
                            if hasattr(child, 'name') and child.name == target_name:
                                insert_index = idx + 1
                                break
                        if insert_index is not None:
                            for i, new_node in enumerate(self.new_nodes):
                                node.body.insert(insert_index + i, new_node)
                            self.success = True
                            return node
                if len(current_path) == len(target_path) and all((c == t for c, t in zip(current_path, target_path))):
                    self.success = True
                    if isinstance(node, ast.ClassDef):
                        node.body.extend(self.new_nodes)
                    else:
                        for new_node in self.new_nodes:
                            node.body.append(new_node)
            return node

    def _find_containing_node(self, node, target_line):
        """Find the deepest AST node with a body that contains the target line."""
        if not (hasattr(node, 'lineno') and hasattr(node, 'end_lineno')):
            return None
        if not node.lineno <= target_line <= node.end_lineno:
            return None
        deepest_with_body = node if hasattr(node, 'body') else None
        if hasattr(node, 'body'):
            for child in node.body:
                deeper_node = self._find_containing_node(child, target_line)
                if deeper_node:
                    return deeper_node
        if hasattr(node, 'orelse'):
            for child in node.orelse:
                deeper_node = self._find_containing_node(child, target_line)
                if deeper_node:
                    return deeper_node
        if deepest_with_body:
            return deepest_with_body
        return None

    def _insert_into_node(self, node, target_line):
        """Insert new nodes into the given node after the target line."""
        if not hasattr(node, 'body'):
            return
        insert_index = len(node.body)
        for idx, child in enumerate(node.body):
            if hasattr(child, 'lineno') and child.lineno > target_line:
                insert_index = idx
                break
        for i, new_node in enumerate(self.new_nodes):
            node.body.insert(insert_index + i, new_node)

def create_token(content: str, index: int, current_hash: str) -> str:
    """Create a token with our specific pattern"""
    hex_content = content.encode('utf-8').hex()
    token_name = f'TOKEN__{current_hash}_{index}'
    return (token_name, f';"""{hex_content}"""')

def get_file_hash(content: str) -> str:
    """Create a short hash of file content"""
    return hashlib.sha256(content.encode()).hexdigest()[:8]

def tokenize_source(source: str) -> Tuple[str, Dict[str, str]]:
    """
    Tokenize source code, preserving exact formatting.

    Returns:
    - tokenized_source: Source with tokens inserted
    - token_map: Mapping of tokens to original content
    """

    def contains_token(s: str) -> bool:
        return ';"""' in s and '"""' in s
    token_map = {}
    current_hash = get_file_hash(source)
    token_counter = 0
    tokenized = source
    triple_quote_patterns = ['"""[^"\\\\]*(?:(?:\\\\.|"(?!""))[^"\\\\]*)*"""', "'''[^'\\\\]*(?:(?:\\\\.|'(?!''))[^'\\\\]*)*'''"]
    for pattern in triple_quote_patterns:
        while True:
            match = re.search(pattern, tokenized)
            if not match:
                break
            string_content = match.group()
            if contains_token(string_content):
                continue
            token_name, hex_val = create_token(string_content, token_counter, current_hash)
            token_map[hex_val] = string_content
            tokenized = tokenized[:match.start()] + hex_val + tokenized[match.end():]
            token_counter += 1
    lines = tokenized.split('\n')
    processed_lines = []
    for line in lines:
        if not line.strip():
            processed_lines.append(line)
            continue
        indent = len(line) - len(line.lstrip())
        indentation = ' ' * indent
        content = line[indent:]
        if contains_token(content):
            processed_lines.append(line)
            continue
        if content.strip().startswith('#'):
            token_name, hex_val = create_token(content, token_counter, current_hash)
            token_map[hex_val] = content
            processed_lines.append(indentation + 'pass' + hex_val)
            token_counter += 1
            continue
        processed_line = content
        string_patterns = ['"[^"\\\\]*(?:\\\\.[^"\\\\]*)*"', "'[^'\\\\]*(?:\\\\.[^'\\\\]*)*'"]
        for pattern in string_patterns:
            while True:
                match = re.search(pattern, processed_line)
                if not match:
                    break
                string_content = match.group()
                if contains_token(string_content):
                    continue
                token_name, hex_val = create_token(string_content, token_counter, current_hash)
                token_map[hex_val] = string_content
                processed_line = processed_line[:match.start()] + hex_val + processed_line[match.end():]
                token_counter += 1
        if '#' in processed_line:
            comment_start = processed_line.index('#')
            code = processed_line[:comment_start].rstrip()
            comment = processed_line[comment_start:]
            token_name, hex_val = create_token(comment, token_counter, current_hash)
            token_map[hex_val] = comment
            processed_line = code + hex_val
            token_counter += 1
        processed_lines.append(indentation + processed_line)
    return ('\n'.join(processed_lines), token_map)

def detokenize_source(tokenized_source: str, token_map: Dict[str, str]) -> str:
    """
    Restore original source from tokenized version.

    Handles proper indentation of multiline content.
    """
    result = tokenized_source
    for token_name, original in token_map.items():
        if token_name.startswith(';"""') and token_name.endswith('"""'):
            hex_content = token_name[4:-3]
            patterns = [f"'{hex_content}'", f'"{hex_content}"']
            for pattern in patterns:
                while pattern in result:
                    lines = result.split('\n')
                    for i, line in enumerate(lines):
                        if line.strip() == pattern:
                            indent = len(line) - len(line.lstrip())
                            lines[i] = ' ' * indent + original
                            result = '\n'.join(lines)
                            break
                        elif pattern in line and line.strip() != pattern:
                            if 'pass' in line and line.index('pass') < line.index(pattern):
                                indent = len(line) - len(line.lstrip())
                                lines[i] = ' ' * indent + original
                            else:
                                lines[i] = line.replace(pattern, '  ' + original)
                            result = '\n'.join(lines)
                            break
                    else:
                        break
    for token_name, original in sorted(token_map.items(), key=lambda x: len(x[0]), reverse=True):
        while token_name in result:
            start = result.find(token_name)
            if start == -1:
                break
            if '\n' in original:
                indent = get_indentation_at_position(result, start)
                indented = indent_multiline_content(original, indent)
                result = result[:start] + indented + result[start + len(token_name):]
            else:
                result = result[:start] + original + result[start + len(token_name):]
    return result

def get_indentation_at_position(source: str, pos: int) -> str:
    """Get the indentation level at a given position in source"""
    line_start = source.rfind('\n', 0, pos) + 1
    return source[line_start:pos].replace(source[line_start:pos].lstrip(), '')

def indent_multiline_content(content: str, indent: str) -> str:
    """Indent multiline content while preserving internal formatting"""
    if not content.strip():
        return content
    lines = content.split('\n')
    if len(lines) == 1:
        return content
    if all((line.startswith(' ') for line in lines[1:] if line.strip())):
        return content
    result = [lines[0]]
    for line in lines[1:]:
        if line.strip():
            result.append(indent + line)
        else:
            result.append(line)
    return '\n'.join(result)