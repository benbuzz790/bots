import ast
import os
import textwrap
from bots.utils.helpers import _process_error, _clean, _py_ast_to_source
import hashlib
import re
from typing import Dict, Tuple
from typing import Dict, Tuple, Union
from enum import Enum

class TokenType(Enum):
    """Types of tokens for metadata-driven processing"""
    STANDALONE_COMMENT = 'standalone_comment'
    INLINE_COMMENT = 'inline_comment'
    IMPORT_COMMENT = 'import_comment'
    COMPOUND_COMMENT = 'compound_comment'
    STRING_LITERAL = 'string_literal'
    MULTILINE_STRING = 'multiline_string'

def python_edit(target_scope: str, code: str, *, insert_after: str=None) -> str:
    """
    Edit Python code using pytest-style scope syntax.
    Default behavior: Replace entire target scope.

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
        - An exact line match (like a context line in git patches)
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
        tokenized_code, new_code_tokens = _tokenize_source(cleaned_code)
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
                original_content = file.read()
            tokenized_content, file_tokens = _tokenize_source(original_content) if original_content.strip() else ('', {})
            file_lines = tokenized_content.split('\n')
            tree = ast.parse(tokenized_content) if original_content.strip() else ast.Module(body=[], type_ignores=[])
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
                final_content = _detokenize_source(updated_content, all_tokens)
                final_content = _preserve_blank_lines(final_content, original_content)
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
                final_content = _detokenize_source(updated_content, all_tokens)
                final_content = _preserve_blank_lines(final_content, original_content)
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
            final_content = _detokenize_source(updated_content, all_tokens)
            final_content = _preserve_blank_lines(final_content, original_content)
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
                detokenized_line = _detokenize_source(line, self.all_tokens)
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

def _create_token(content: str, index: int, current_hash: str, token_type: TokenType=None, extra_metadata: dict=None) -> Tuple[str, Dict]:
    """Create a token with our specific pattern and metadata"""
    token_name = f'TOKEN_{current_hash}_{index}'
    metadata = extra_metadata or {}
    if token_type:
        metadata['type'] = token_type.value
    token_data = {'content': content, 'metadata': metadata}
    return (token_name, token_data)

def _get_file_hash(content: str) -> str:
    """Create a short hash of file content"""
    return hashlib.sha256(content.encode()).hexdigest()[:8]


def _contains_token(s: str) -> bool:
    return 'TOKEN_' in s


def _find_complete_triple_quote(text, start_pos=0):
    """Find complete triple-quoted strings manually"""
    for quote_type in ['"""', "'''"]:
        open_pos = text.find(quote_type, start_pos)
        if open_pos == -1:
            continue
        close_pos = text.find(quote_type, open_pos + 3)
        if close_pos == -1:
            continue
        complete_string = text[open_pos:close_pos + 3]
        if not _contains_token(complete_string):
            return (open_pos, close_pos + 3, complete_string)
    return (None, None, None)


def _find_string_end(line, start_pos, quote_char):
    """Find the end position of a quoted string, handling escape sequences."""
    pos = start_pos + 1
    while pos < len(line):
        if line[pos] == quote_char:
            return pos
        elif line[pos] == '\\' and pos + 1 < len(line):
            pos += 2  # Skip escaped character
        else:
            pos += 1
    return -1  # No closing quote found

def _tokenize_source(source: str) -> Tuple[str, Dict[str, Dict]]:
    """
    Tokenize source code, preserving exact formatting.

    Returns:
    - tokenized_source: Source with tokens inserted
    - token_map: Mapping of tokens to {'content': str, 'metadata': dict}
    """
    token_map = {}
    current_hash = _get_file_hash(source)
    token_counter = 0
    
    # First pass: handle multi-line strings
    tokenized = _process_multiline_strings(source, token_map, token_counter, current_hash)
    token_counter = len(token_map)
    
    # Second pass: process each line
    lines = tokenized.split('\n')
    processed_lines = []
    
    for line in lines:
        processed_line, token_counter = _process_single_line(
            line, token_map, token_counter, current_hash
        )
        processed_lines.append(processed_line)
    
    return '\n'.join(processed_lines), token_map


def _process_multiline_strings(source: str, token_map: dict, token_counter: int, current_hash: str) -> str:
    """Process all triple-quoted strings in the source."""
    tokenized = source
    processed_positions = set()
    
    for _ in range(10):  # Safety limit
        old_tokenized = tokenized
        
        start_pos, end_pos, string_content = _find_complete_triple_quote(tokenized)
        if start_pos is None:
            break
            
        if start_pos in processed_positions or len(string_content) > 1000:
            break
            
        processed_positions.add(start_pos)
        
        token_name, token_data = _create_token(
            string_content, token_counter, current_hash, TokenType.MULTILINE_STRING
        )
        token_map[token_name] = token_data
        tokenized = tokenized[:start_pos] + token_name + tokenized[end_pos:]
        token_counter += 1
        
        if tokenized == old_tokenized:
            break
    
    return tokenized

def _process_single_line(line: str, token_map: dict, token_counter: int, current_hash: str) -> Tuple[str, int]:
    """Process a single line of code, handling indentation and various token types."""
    if not line.strip():
        return line, token_counter
    
    indent = len(line) - len(line.lstrip())
    indentation = ' ' * indent
    content = line[indent:]
    
    if _contains_token(content):
        return line, token_counter
    
    # Handle standalone comments
    if content.strip().startswith('#'):
        token_name, token_data = _create_token(
            content.strip(), token_counter, current_hash, TokenType.STANDALONE_COMMENT
        )
        token_map[token_name] = token_data
        return f"{indentation}{token_name}", token_counter + 1
    
    # Process string literals
    processed_content, token_counter = _process_string_literals(
        content, token_map, token_counter, current_hash
    )
    
    # Handle inline comments
    if '#' in processed_content:
        processed_content, token_counter = _process_inline_comment(
            processed_content, token_map, token_counter, current_hash
        )
    
    return indentation + processed_content, token_counter

def _process_string_literals(processed_line, token_map, token_counter, current_hash):
    """Extract and tokenize string literals from a line of code."""
    if _contains_token(processed_line):
        return processed_line, token_counter
    
    for quote_char in ['"', "'"]:
        start = processed_line.find(quote_char)
        if start == -1:
            continue
            
        end = _find_string_end(processed_line, start, quote_char)
        if end == -1:
            continue
            
        string_content = processed_line[start:end + 1]
        token_name, token_data = _create_token(
            string_content, token_counter, current_hash, TokenType.STRING_LITERAL
        )
        token_map[token_name] = token_data
        processed_line = processed_line[:start] + token_name + processed_line[end + 1:]
        token_counter += 1
        break
    
    return processed_line, token_counter

def _process_inline_comment(line: str, token_map: dict, token_counter: int, current_hash: str) -> Tuple[str, int]:
    """Process inline comments, determining their type based on the preceding code."""
    comment_start = line.index('#')
    code = line[:comment_start]
    code_end = len(code.rstrip())
    spacing_and_comment = line[code_end:]
    code_stripped = code.rstrip()
    
    # Determine comment type and metadata
    token_type, extra_metadata = _determine_comment_type(code_stripped)
    
    token_name, token_data = _create_token(
        spacing_and_comment, token_counter, current_hash, token_type, extra_metadata
    )
    token_map[token_name] = token_data
    
    # For compound comments, put token on separate line with proper indentation
    if token_type == TokenType.COMPOUND_COMMENT:
        # Get the base indentation of the current line
        base_indent = len(line) - len(line.lstrip())
        # Add 4 spaces for the expected function/class body indentation
        token_indent = ' ' * (base_indent + 4)
        processed_line = f"{code.rstrip()}\n{token_indent}{token_name}"
    else:
        processed_line = f"{code.rstrip()}; {token_name}"
    
    return processed_line, token_counter + 1

def _determine_comment_type(code_stripped: str) -> Tuple[TokenType, dict]:
    """Determine the type of comment based on the preceding code."""
    if code_stripped.startswith(('import ', 'from ')):
        return TokenType.IMPORT_COMMENT, {'import_statement': code_stripped}
    
    compound_patterns = [
        'def ', 'class ', 'if ', 'elif ', 'for ', 'while ', 'with ', 'async def '
    ]
    standalone_statements = ['else:', 'try:', 'finally:']
    
    is_compound_with_colon = (
        any(code_stripped.startswith(pattern) for pattern in compound_patterns) 
        and code_stripped.endswith(':')
    )
    is_standalone_colon = code_stripped in standalone_statements
    
    if is_compound_with_colon or is_standalone_colon:
        return TokenType.COMPOUND_COMMENT, {'statement': code_stripped}
    
    return TokenType.INLINE_COMMENT, {}

def _detokenize_source(tokenized_source: str, token_map: Dict[str, Dict]) -> str:
    """
    Restore original source from tokenized version using metadata-driven processing.
    """
    result = tokenized_source
    for token_name, token_data in token_map.items():
        content = token_data['content']
        metadata = token_data['metadata']
        token_type = metadata.get('type')
        while token_name in result:
            start = result.find(token_name)
            if start == -1:
                break
            if token_type == TokenType.COMPOUND_COMMENT.value:
                result = _handle_compound_comment(result, token_name, content, start)
            elif token_type == TokenType.IMPORT_COMMENT.value:
                result = _handle_import_comment(result, token_name, content, start, metadata)
            elif token_type == TokenType.INLINE_COMMENT.value:
                result = _handle_inline_comment(result, token_name, content, start)
            elif token_type == TokenType.STANDALONE_COMMENT.value:
                result = _handle_standalone_comment(result, token_name, content, start)
            elif token_type == TokenType.MULTILINE_STRING.value:
                result = _handle_multiline_string(result, token_name, content, start)
            elif token_type == TokenType.STRING_LITERAL.value:
                result = _handle_string_literal(result, token_name, content, start)
            else:
                result = _handle_default_token(result, token_name, content, start)
    return result

def _get_indentation_at_position(source: str, pos: int) -> str:
    """Get the indentation level at a given position in source"""
    line_start = source.rfind('\n', 0, pos) + 1
    return source[line_start:pos].replace(source[line_start:pos].lstrip(), '')

def _indent_multiline_content(content: str, indent: str) -> str:
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

def _preserve_blank_lines(result: str, original_source: str) -> str:
    """
    Restore blank lines around comments that had them in the original source.
    """
    original_lines = original_source.split('\n')
    result_lines = result.split('\n')
    comments_with_blanks = {}
    for i, line in enumerate(original_lines):
        if line.strip().startswith('#') and 'marker' in line.lower():
            blank_before = i > 0 and (not original_lines[i - 1].strip())
            blank_after = i < len(original_lines) - 1 and (not original_lines[i + 1].strip())
            if blank_before or blank_after:
                comments_with_blanks[line.strip()] = {'blank_before': blank_before, 'blank_after': blank_after}
    if not comments_with_blanks:
        return result
    new_result_lines = []
    i = 0
    while i < len(result_lines):
        line = result_lines[i]
        line_stripped = line.strip()
        if line_stripped in comments_with_blanks:
            info = comments_with_blanks[line_stripped]
            if info['blank_before']:
                if i > 0 and new_result_lines[-1].strip():
                    new_result_lines.append('')
            new_result_lines.append(line)
            if info['blank_after']:
                if i < len(result_lines) - 1 and result_lines[i + 1].strip():
                    new_result_lines.append('')
        else:
            new_result_lines.append(line)
        i += 1
    return '\n'.join(new_result_lines)

def _handle_compound_comment(result: str, token_name: str, content: str, start: int) -> str:
    """Handle compound statement comments (def, class, if, etc.) with smart reunification"""
    line_start = result.rfind('\n', 0, start) + 1
    line_end = result.find('\n', start)
    if line_end == -1:
        line_end = len(result)
    line = result[line_start:line_end]
    line_stripped = line.strip()
    if line_stripped.startswith('# ') and line_stripped[2:] == token_name:
        prev_line_start = result.rfind('\n', 0, line_start - 1) + 1
        prev_line = result[prev_line_start:line_start - 1]
        if prev_line.strip():
            reunited = prev_line + content
            return result[:prev_line_start] + reunited + result[line_end:]
    elif line_stripped == token_name:
        search_start = line_start - 1
        while search_start > 0:
            prev_line_start = result.rfind('\n', 0, search_start) + 1
            prev_line = result[prev_line_start:search_start]
            if prev_line.strip():
                if prev_line.strip().endswith(':'):
                    reunited = prev_line.rstrip() + content
                    return result[:prev_line_start] + reunited + result[line_end:]
                break
            search_start = prev_line_start - 1
    return result[:start] + content + result[start + len(token_name):]

def _handle_import_comment(result: str, token_name: str, content: str, start: int, metadata: dict) -> str:
    """Handle import statement comments with metadata-driven reunification"""
    import_statement = metadata.get('import_statement')
    if not import_statement:
        return result[:start] + content + result[start + len(token_name):]
    lines = result.split('\n')
    token_line_idx = None
    for i, line in enumerate(lines):
        if token_name in line:
            token_line_idx = i
            break
    if token_line_idx is None:
        return result[:start] + content + result[start + len(token_name):]
    search_range = range(max(0, token_line_idx - 3), min(len(lines), token_line_idx + 3))
    for i in search_range:
        if i != token_line_idx and lines[i].strip() == import_statement:
            lines[i] = lines[i].rstrip() + content
            lines[token_line_idx] = '__REMOVE_THIS_LINE__'
            new_lines = [line for line in lines if line != '__REMOVE_THIS_LINE__']
            return '\n'.join(new_lines)
    return result[:start] + content + result[start + len(token_name):]

def _handle_inline_comment(result: str, token_name: str, content: str, start: int) -> str:
    """Handle inline comments (non-import, non-compound) with smart reunification"""
    line_start = result.rfind('\n', 0, start) + 1
    line_end = result.find('\n', start)
    if line_end == -1:
        line_end = len(result)
    line = result[line_start:line_end]
    line_stripped = line.strip()
    if line_stripped == token_name:
        search_start = line_start - 1
        while search_start > 0:
            prev_line_start = result.rfind('\n', 0, search_start) + 1
            prev_line = result[prev_line_start:search_start]
            if prev_line.strip():
                reunited = prev_line.rstrip() + content
                return result[:prev_line_start] + reunited + result[line_end:]
            search_start = prev_line_start - 1
    return result[:start] + content + result[start + len(token_name):]

def _handle_standalone_comment(result: str, token_name: str, content: str, start: int) -> str:
    """Handle standalone comment lines"""
    line_start = result.rfind('\n', 0, start) + 1
    line_end = result.find('\n', start)
    if line_end == -1:
        line_end = len(result)
    line = result[line_start:line_end]
    indent = line[:len(line) - len(line.lstrip())]
    replacement = indent + content
    return result[:line_start] + replacement + result[line_end:]

def _handle_multiline_string(result: str, token_name: str, content: str, start: int) -> str:
    """Handle multiline strings with proper indentation"""
    if '\n' in content:
        indent = _get_indentation_at_position(result, start)
        indented = _indent_multiline_content(content, indent)
        return result[:start] + indented + result[start + len(token_name):]
    else:
        return result[:start] + content + result[start + len(token_name):]

def _handle_string_literal(result: str, token_name: str, content: str, start: int) -> str:
    """Handle simple string literals"""
    return result[:start] + content + result[start + len(token_name):]

def _handle_default_token(result: str, token_name: str, content: str, start: int) -> str:
    """Handle tokens without specific type metadata"""
    return result[:start] + content + result[start + len(token_name):]