import ast
import hashlib
import os
import textwrap
from enum import Enum
from typing import Dict, List, Tuple
from bots.dev.decorators import handle_errors
from bots.utils.helpers import _clean, _process_error, _py_ast_to_source
from bots.utils.unicode_utils import clean_unicode_string
import libcst as cst
from typing import Optional, Union, List, Tuple
from bots.utils.helpers import _process_error

def _read_file_bom_safe(file_path: str) -> str:
    """Read a file with BOM protection."""
    with open(file_path, 'r', encoding='utf-8') as file:
        content = file.read()
    return clean_unicode_string(content)

def _write_file_bom_safe(file_path: str, content: str) -> None:
    """Write a file with BOM protection."""
    clean_content = clean_unicode_string(content)
    with open(file_path, 'w', encoding='utf-8') as file:
        file.write(clean_content)

class ScopeViewer(ast.NodeVisitor):
    """AST visitor that finds and extracts specific scopes from Python code."""

    def __init__(self, path_elements):
        self.target_path = path_elements
        self.current_path = []
        self.target_node = None
        self.found = False

    def find_target(self, tree):
        """Find the target node in the AST tree."""
        self.visit(tree)
        return self.target_node

    def visit_ClassDef(self, node):
        """Visit a class definition node."""
        return self._visit_named_node(node)

    def visit_FunctionDef(self, node):
        """Visit a function definition node."""
        return self._visit_named_node(node)

    def visit_AsyncFunctionDef(self, node):
        """Visit an async function definition node."""
        return self._visit_named_node(node)

    def _visit_named_node(self, node):
        """Common handling for named nodes (classes, functions)."""
        if self.found:
            return
        if len(self.current_path) < len(self.target_path) and node.name == self.target_path[len(self.current_path)]:
            self.current_path.append(node.name)
            if len(self.current_path) == len(self.target_path):
                self.target_node = node
                self.found = True
                return
            for child in node.body:
                self.visit(child)
            self.current_path.pop()
        elif len(self.current_path) == 0:
            pass
        else:
            return

class TokenType(Enum):
    """Types of tokens for metadata-driven processing"""
    STANDALONE_COMMENT = 'standalone_comment'
    INLINE_COMMENT = 'inline_comment'
    IMPORT_COMMENT = 'import_comment'
    COMPOUND_COMMENT = 'compound_comment'
    STRING_LITERAL = 'string_literal'
    FSTRING_LITERAL = 'fstring_literal'
    MULTILINE_STRING = 'multiline_string'

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
        self.ambiguity_error = None
        self._is_comment_only_insertion = False
        self._insert_after_line = None

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
        """Handle inserting nodes after a specific scope point."""
        if not self.insert_after:
            return node
        if self.insert_after == '__FILE_START__':
            return node
        if self._is_quoted_expression(self.insert_after):
            return self._handle_expression_insertion(node)
        if '::' in self.insert_after:
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
        else:
            target_name = self.insert_after
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

    def _is_quoted_expression(self, text):
        """Check if text is a quoted expression."""
        text = text.strip()
        double_quote = '"'
        single_quote = "'"
        double_quoted = text.startswith(double_quote) and text.endswith(double_quote) and (len(text) >= 2)
        single_quoted = text.startswith(single_quote) and text.endswith(single_quote) and (len(text) >= 2)
        return double_quoted or single_quoted

    def _extract_expression_pattern(self, quoted_text):
        """Extract pattern from quoted text."""
        quoted_text = quoted_text.strip()
        double_quote = chr(34)
        single_quote = chr(39)
        if quoted_text.startswith(double_quote) and quoted_text.endswith(double_quote):
            return quoted_text[1:-1]
        elif quoted_text.startswith(single_quote) and quoted_text.endswith(single_quote):
            return quoted_text[1:-1]
        return quoted_text

    def _matches_expression_pattern(self, source, pattern):
        """Check if source matches the expression pattern according to our rules."""
        source_lines = source.split('\n')
        pattern_lines = pattern.split('\n')
        if len(pattern_lines) == 1:
            pattern_line = pattern_lines[0].strip()
            for source_line in source_lines:
                if source_line.strip().startswith(pattern_line):
                    return True
            return False
        else:
            source_normalized = '\n'.join((line.rstrip() for line in source_lines))
            pattern_normalized = '\n'.join((line.rstrip() for line in pattern_lines))
            return source_normalized.strip() == pattern_normalized.strip()

    def _handle_expression_insertion(abs_path: str, tree: cst.Module, new_module: cst.Module, pattern: str) -> str:
        """Handle insertion after a quoted expression pattern."""
        inserter = ExpressionInserter(pattern, new_module.body)
        modified_tree = tree.visit(inserter)
        if not inserter.modified:
            return _process_error(ValueError(f'Insert point not found: "{pattern}"'))
        _write_file_bom_safe(abs_path, modified_tree.code)
        return f"Code inserted after '{pattern}' in '{abs_path}'."

@handle_errors
def python_view(target_scope: str) -> str:
    """
    View Python code using pytest-style scope syntax.

    Parameters:
    -----------
    target_scope : str
        Location to view in pytest-style scope syntax:
        - "file.py" (whole file)
        - "file.py::MyClass" (class)
        - "file.py::my_function" (function)
        - "file.py::MyClass::method" (method)

    Returns:
    --------
    str
        The source code at the specified scope, or error message
    """
    try:
        file_path, *path_elements = target_scope.split('::')
        if not file_path.endswith('.py'):
            return _process_error(ValueError(f'File path must end with .py: {file_path}'))
        for element in path_elements:
            if not element.isidentifier():
                return _process_error(ValueError(f'Invalid identifier in path: {element}'))
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return _process_error(FileNotFoundError(f'File not found: {abs_path}'))
        try:
            source_code = _read_file_bom_safe(abs_path)
            if not source_code.strip():
                return f"File '{abs_path}' is empty."
        except Exception as e:
            return _process_error(ValueError(f'Error reading file {abs_path}: {str(e)}'))
        if not path_elements:
            return source_code
        try:
            wrapper = cst.MetadataWrapper(cst.parse_module(source_code))
        except Exception as e:
            return _process_error(ValueError(f'Error parsing file {abs_path}: {str(e)}'))
        finder = ScopeFinder(path_elements)
        wrapper.visit(finder)
        if not finder.target_node:
            return _process_error(ValueError(f'Target scope not found: {target_scope}'))
        return wrapper.module.code_for_node(finder.target_node)
    except Exception as e:
        return _process_error(e)

@handle_errors
def python_edit(target_scope: str, code: str, *, insert_after: str=None) -> str:
    """
    Edit Python code using pytest-style scope syntax.

    Parameters:
    -----------
    target_scope : str
        Location to edit in pytest-style scope syntax:
        - "file.py" (whole file)
        - "file.py::MyClass" (class)
        - "file.py::my_function" (function)
        - "file.py::MyClass::method" (method)

    code : str
        Python code to insert/replace. Will be dedented automatically.

    insert_after : str, optional
        Scope to insert the code after, using the same syntax as target_scope:
        - "__FILE_START__" (special token for file beginning)
        - "MyClass::method" (insert after this method within the target scope)
        - '"expression"' (insert after a line matching this expression)

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
            original_content = _read_file_bom_safe(abs_path)
            was_originally_empty = not original_content.strip()
        except Exception as e:
            return _process_error(ValueError(f'Error reading file {abs_path}: {str(e)}'))
        try:
            import textwrap
            cleaned_code = textwrap.dedent(code).strip()
            if not cleaned_code:
                return _process_error(ValueError('Code to insert/replace is empty'))
            if was_originally_empty and (not path_elements):
                _write_file_bom_safe(abs_path, cleaned_code)
                return f"Code added to '{abs_path}'."
            try:
                new_module = cst.parse_module(cleaned_code)
            except Exception as e:
                return _process_error(ValueError(f'Error parsing new code: {str(e)}'))
        except Exception as e:
            return _process_error(ValueError(f'Error processing new code: {str(e)}'))
        try:
            if original_content.strip():
                tree = cst.parse_module(original_content)
            else:
                tree = cst.parse_module('')
        except Exception as e:
            return _process_error(ValueError(f'Error parsing file {abs_path}: {str(e)}'))
        if insert_after == '__FILE_START__':
            return _handle_file_start_insertion(abs_path, tree, new_module)
        elif not path_elements:
            if insert_after:
                return _handle_file_level_insertion(abs_path, tree, new_module, insert_after)
            else:
                _write_file_bom_safe(abs_path, cleaned_code)
                return f"Code replaced at file level in '{abs_path}'."
        else:
            replacer = ScopeReplacer(path_elements, new_module, insert_after, tree)
            modified_tree = tree.visit(replacer)
            if not replacer.modified:
                if insert_after:
                    return _process_error(ValueError(f'Insert point not found: {insert_after}'))
                else:
                    return _process_error(ValueError(f'Target scope not found: {target_scope}'))
            _write_file_bom_safe(abs_path, modified_tree.code)
            if insert_after:
                return f"Code inserted after '{insert_after}' in '{abs_path}'."
            else:
                return f"Code replaced at '{target_scope}'."
    except Exception as e:
        return _process_error(e)

def _make_file(file_path: str) -> str:
    """
    Create a file and its parent directories if they don't exist.

    Parameters:
    -----------
    file_path : str
        Path to the file to create

    Returns:
    --------
    str
        Absolute path to the created/existing file

    Raises:
    -------
    ValueError
        If there's an error creating the file or directories
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

def prep_input(code: str) -> tuple[str, str | None]:
    """
    Prepare and validate input code with informative error messages.

    Parameters:
    -----------
    code : str
        The input code to validate and prepare

    Returns:
    --------
    tuple[str, str | None]
        (cleaned_code, error_message) where error_message is None if successful
    """
    try:
        cleaned_code = _clean(code)
        if not cleaned_code.strip():
            return ('', 'Input code is empty or contains only whitespace')
        try:
            ast.parse(cleaned_code)
            return (cleaned_code, None)
        except SyntaxError as e:
            error_lines = []
            error_lines.append(f'Syntax error in input code: {e.msg}')
            if hasattr(e, 'lineno') and e.lineno:
                error_lines.append(f"Line {e.lineno}: {(e.text.strip() if e.text else '(unknown)')}")
                if hasattr(e, 'offset') and e.offset:
                    pointer = ' ' * (e.offset - 1) + '^'
                    error_lines.append(pointer)
            if e.lineno and cleaned_code:
                lines = cleaned_code.split('\n')
                start = max(0, e.lineno - 3)
                end = min(len(lines), e.lineno + 2)
                error_lines.append('\nContext:')
                for i in range(start, end):
                    if i < len(lines):
                        line_num = i + 1
                        line_content = lines[i]
                        marker = '>>> ' if i == e.lineno else '    '
                        error_lines.append(f'{marker}{line_num:3d}: {line_content}')
            return (cleaned_code, '\n'.join(error_lines))
        except Exception as e:
            return (cleaned_code, f'Failed to parse input code: {type(e).__name__}: {str(e)}')
    except Exception as e:
        return (code, f'Failed to process input code: {type(e).__name__}: {str(e)}')

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

def _is_fstring_start(line, pos):
    """Check if position starts an f-string (f", f', rf", etc.)"""
    if pos >= len(line) or line[pos] not in ['"', "'"]:
        return (False, False)
    prefixes = {'f': (True, False), 'F': (True, False), 'rf': (True, True), 'Rf': (True, True), 'rF': (True, True), 'RF': (True, True), 'fr': (True, True), 'Fr': (True, True), 'fR': (True, True), 'FR': (True, True)}
    for prefix, (is_f, is_raw) in prefixes.items():
        prefix_start = pos - len(prefix)
        if prefix_start >= 0 and line[prefix_start:pos] == prefix and (prefix_start == 0 or not line[prefix_start - 1].isalnum()):
            return (is_f, is_raw)
    return (False, False)

def _find_fstring_end(line, start_pos, quote_char, is_raw=False):
    """Find the end of an f-string, handling nested braces and expressions."""
    pos = start_pos + 1
    brace_depth = 0
    while pos < len(line):
        char = line[pos]
        if char == '{':
            if pos + 1 < len(line) and line[pos + 1] == '{':
                pos += 2
                continue
            else:
                brace_depth += 1
                pos += 1
                continue
        elif char == '}':
            if pos + 1 < len(line) and line[pos + 1] == '}':
                pos += 2
                continue
            else:
                brace_depth -= 1
                pos += 1
                continue
        elif char == quote_char and brace_depth == 0:
            return pos
        elif char == '\\' and (not is_raw) and (pos + 1 < len(line)):
            pos += 2
            continue
        elif char in ['"', "'"] and brace_depth > 0:
            nested_end = _find_string_end(line, pos, char)
            if nested_end == -1:
                return -1
            pos = nested_end + 1
            continue
        pos += 1
    return -1

def _determine_comment_type(code_stripped: str) -> Tuple[TokenType, dict]:
    """Determine the type of comment based on the preceding code."""
    code_no_indent = code_stripped.lstrip()
    if code_no_indent.startswith(('import ', 'from ')):
        return (TokenType.IMPORT_COMMENT, {'import_statement': code_stripped})
    compound_patterns = ['def ', 'class ', 'if ', 'elif ', 'for ', 'while ', 'with ', 'async def ', 'try:', 'except ', 'finally:', 'else:']
    is_compound = any((code_no_indent.startswith(pattern) for pattern in compound_patterns)) and code_stripped.endswith(':') or code_stripped.strip() in ['else:', 'try:', 'finally:']
    if is_compound:
        return (TokenType.COMPOUND_COMMENT, {'statement': code_stripped})
    return (TokenType.INLINE_COMMENT, {})

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

def _find_string_end(line, start_pos, quote_char):
    """
    Find the end position of a quoted string, handling escape sequences properly.
    Enhanced with better validation.
    """
    if start_pos >= len(line):
        return -1
    pos = start_pos + 1
    while pos < len(line):
        if line[pos] == '\\' and pos + 1 < len(line):
            pos += 2
        elif line[pos] == quote_char:
            return pos
        elif line[pos] == '\n' and quote_char in ['"', "'"]:
            return -1
        else:
            pos += 1
    return -1

def _find_string_end_in_source(source, start_pos, quote_char):
    if start_pos >= len(source):
        return -1
    pos = start_pos + 1
    while pos < len(source):
        if source[pos] == chr(92) and pos + 1 < len(source):
            pos += 2
        elif source[pos] == quote_char:
            return pos
        else:
            pos += 1
    return -1

def _find_fstring_end_in_source(source, start_pos, quote_char, is_raw=False):
    pos = start_pos + 1
    brace_depth = 0
    while pos < len(source):
        char = source[pos]
        if char == chr(123):
            if pos + 1 < len(source) and source[pos + 1] == chr(123):
                pos += 2
                continue
            else:
                brace_depth += 1
                pos += 1
                continue
        elif char == chr(125):
            if pos + 1 < len(source) and source[pos + 1] == chr(125):
                pos += 2
                continue
            else:
                brace_depth -= 1
                pos += 1
                continue
        elif char == quote_char and brace_depth == 0:
            return pos
        elif char == chr(92) and (not is_raw) and (pos + 1 < len(source)):
            pos += 2
            continue
        elif char in [chr(34), chr(39)] and brace_depth > 0:
            nested_end = _find_string_end_in_source(source, pos, char)
            if nested_end == -1:
                return -1
            pos = nested_end + 1
            continue
        pos += 1
    return -1

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
    tokenized = _process_multiline_strings(source, token_map, token_counter, current_hash)
    token_counter = len(token_map)
    tokenized, token_counter = _process_all_string_literals(tokenized, token_map, token_counter, current_hash)
    lines = tokenized.split('\n')
    processed_lines = []
    for line in lines:
        processed_line, token_counter = _process_line_comments(line, token_map, token_counter, current_hash)
        processed_lines.append(processed_line)
    return ('\n'.join(processed_lines), token_map)

def _extract_top_level_comments(source: str) -> Tuple[str, List[str]]:
    """
    Extract top-level standalone comments that appear before any code.

    Returns:
        (source_without_top_comments, list_of_top_comment_lines)
    """
    lines = source.split('\n')
    top_comments = []
    first_code_line_idx = 0
    for i, line in enumerate(lines):
        stripped = line.strip()
        if not stripped:
            continue
        elif stripped.startswith('#'):
            top_comments.append(line)
        else:
            first_code_line_idx = i
            break
    else:
        first_code_line_idx = len(lines)
    if top_comments:
        remaining_lines = lines[first_code_line_idx:]
        source_without_comments = '\n'.join(remaining_lines)
        return (source_without_comments, top_comments)
    return (source, [])

def _process_line_comments(line: str, token_map: dict, token_counter: int, current_hash: str) -> Tuple[str, int]:
    """Process comments on a single line, after string processing."""
    if not line.strip():
        return (line, token_counter)
    indent = len(line) - len(line.lstrip())
    indentation = ' ' * indent
    content = line[indent:]
    if content.strip().startswith('#'):
        token_name, token_data = _create_token(content.strip(), token_counter, current_hash, TokenType.STANDALONE_COMMENT)
        token_map[token_name] = token_data
        return (f'{indentation}# {token_name}', token_counter + 1)
    if '#' in content:
        hash_positions = [i for i, c in enumerate(content) if c == '#']
        for hash_pos in hash_positions:
            is_inside_token = False
            for token_name in token_map:
                if token_name in content:
                    token_start = content.find(token_name)
                    token_end = token_start + len(token_name)
                    if token_start <= hash_pos < token_end:
                        is_inside_token = True
                        break
            if not is_inside_token:
                processed_line, new_counter = _process_inline_comment(line, token_map, token_counter, current_hash)
                return (processed_line, new_counter)
    return (line, token_counter)

def _process_multiline_strings(source: str, token_map: dict, token_counter: int, current_hash: str) -> str:
    """Process all triple-quoted strings in the source, including f-strings."""
    tokenized = source
    processed_positions = set()
    patterns = [('"""', '"""'), ("'''", "'''"), ('f"""', '"""'), ("f'''", "'''"), ('F"""', '"""'), ("F'''", "'''"), ('rf"""', '"""'), ("rf'''", "'''"), ('fr"""', '"""'), ("fr'''", "'''"), ('Rf"""', '"""'), ("Rf'''", "'''"), ('rF"""', '"""'), ("rF'''", "'''"), ('RF"""', '"""'), ("RF'''", "'''"), ('Fr"""', '"""'), ("Fr'''", "'''"), ('fR"""', '"""'), ("fR'''", "'''"), ('FR"""', '"""'), ("FR'''", "'''")]
    for start_pattern, end_pattern in patterns:
        pos = 0
        iteration_count = 0
        while True:
            start_pos = tokenized.find(start_pattern, pos)
            iteration_count += 1
            if iteration_count > 1000:
                print(f'Warning: Breaking infinite loop for pattern {start_pattern}')
                break
            if start_pos == -1:
                break
            if start_pos in processed_positions:
                pos = start_pos + 1
                continue
            end_pos = tokenized.find(end_pattern, start_pos + len(start_pattern))
            if end_pos == -1:
                pos = start_pos + 1
                continue
            end_pos += len(end_pattern)
            string_content = tokenized[start_pos:end_pos]
            if _contains_token(string_content) or False:
                pos = start_pos + 1
                continue
            processed_positions.add(start_pos)
            is_fstring = any((string_content.startswith(p) for p in ['f', 'F', 'rf', 'Rf', 'rF', 'RF', 'fr', 'Fr', 'fR', 'FR']))
            token_name, token_data = _create_token(string_content, token_counter, current_hash, TokenType.MULTILINE_STRING, {'is_fstring': is_fstring} if is_fstring else None)
            token_map[token_name] = token_data
            tokenized = tokenized[:start_pos] + token_name + tokenized[end_pos:]
            pos = start_pos + len(token_name)
            token_counter += 1
    return tokenized

def _process_all_string_literals(source, token_map, token_counter, current_hash):
    """Process all string literals in the entire source at once, preserving escape sequences."""
    if _contains_token(source):
        lines = source.split('\n')
        processed_lines = []
        for line in lines:
            processed_line, token_counter = _process_string_literals(line, token_map, token_counter, current_hash)
            processed_lines.append(processed_line)
        return ('\n'.join(processed_lines), token_counter)
    string_locations = _find_all_string_locations_in_source(source)
    if not string_locations:
        return (source, token_counter)
    string_locations.sort(key=lambda x: x['start'], reverse=True)
    result = source
    for string_info in string_locations:
        start = string_info['start']
        end = string_info['end']
        string_content = string_info['content']
        is_fstring = string_info['is_fstring']
        is_raw = string_info['is_raw']
        paren_depth = string_info['paren_depth']
        quote_char = string_info['quote_char']
        metadata = {'is_fstring': is_fstring, 'is_raw': is_raw, 'in_parens': paren_depth > 0}
        if paren_depth > 0:
            metadata['quote_char'] = quote_char
        token_name, token_data = _create_token(string_content, token_counter, current_hash, TokenType.STRING_LITERAL, metadata)
        token_map[token_name] = token_data
        if paren_depth > 0 or is_fstring:
            replacement = f'{quote_char}{token_name}{quote_char}'
        else:
            replacement = token_name
        token_counter += 1
        result = result[:start] + replacement + result[end + 1:]
    return (result, token_counter)

def _is_position_in_comment(source, pos):
    line_start = source.rfind(chr(10), 0, pos) + 1
    line_content = source[line_start:pos + 1]
    hash_pos = line_content.find(chr(35))
    return hash_pos != -1

def _find_all_string_locations_in_source(source):
    """Find all string literal locations in the entire source, preserving escape sequences."""
    locations = []
    paren_depth = 0
    pos = 0
    while pos < len(source):
        char = source[pos]
        if char == '(':
            paren_depth += 1
            pos += 1
            continue
        elif char == ')':
            paren_depth -= 1
            pos += 1
            continue
        if char in [chr(34), chr(39)]:
            string_info = _analyze_string_at_position_in_source(source, pos, paren_depth)
            if string_info:
                locations.append(string_info)
                pos = string_info['end'] + 1
            else:
                pos += 1
        else:
            pos += 1
    return locations

def _analyze_string_at_position_in_source(source, pos, paren_depth):
    """Analyze a potential string starting at the given position in the full source."""
    char = source[pos]
    is_fstring, is_raw = _is_fstring_start(source, pos)
    if is_fstring:
        string_start = pos
        for prefix in ['rf', 'Rf', 'rF', 'RF', 'fr', 'Fr', 'fR', 'FR', 'f', 'F']:
            prefix_start = pos - len(prefix)
            if prefix_start >= 0 and source[prefix_start:pos] == prefix and (prefix_start == 0 or not source[prefix_start - 1].isalnum()):
                string_start = prefix_start
                break
        end_pos = _find_fstring_end_in_source(source, pos, char, is_raw)
    else:
        string_start = pos
        for prefix in ['r', 'R']:
            prefix_start = pos - len(prefix)
            if prefix_start >= 0 and source[prefix_start:pos] == prefix and (prefix_start == 0 or not source[prefix_start - 1].isalnum()):
                string_start = prefix_start
                is_raw = True
                break
        end_pos = _find_string_end_in_source(source, pos, char)
    if end_pos == -1:
        return None
    string_content = source[string_start:end_pos + 1]
    if len(string_content) < 2:
        return None
    return {'start': string_start, 'end': end_pos, 'content': string_content, 'is_fstring': is_fstring, 'is_raw': is_raw, 'paren_depth': paren_depth, 'quote_char': char}

def _process_string_literals(processed_line, token_map, token_counter, current_hash):
    """Process all strings in a line at once - fallback for when source already has tokens."""
    if _contains_token(processed_line):
        return (processed_line, token_counter)
    string_locations = _find_all_string_locations(processed_line)
    if not string_locations:
        return (processed_line, token_counter)
    string_locations.sort(key=lambda x: x['start'], reverse=True)
    result = processed_line
    for string_info in string_locations:
        start = string_info['start']
        end = string_info['end']
        string_content = string_info['content']
        is_fstring = string_info['is_fstring']
        is_raw = string_info['is_raw']
        paren_depth = string_info['paren_depth']
        quote_char = string_info['quote_char']
        metadata = {'is_fstring': is_fstring, 'is_raw': is_raw, 'in_parens': paren_depth > 0}
        if paren_depth > 0:
            metadata['quote_char'] = quote_char
        token_name, token_data = _create_token(string_content, token_counter, current_hash, TokenType.STRING_LITERAL, metadata)
        token_map[token_name] = token_data
        if paren_depth > 0 or is_fstring:
            replacement = f'{quote_char}{token_name}{quote_char}'
        else:
            replacement = token_name
        token_counter += 1
        result = result[:start] + replacement + result[end + 1:]
    return (result, token_counter)

def _find_all_string_locations(line):
    """Find all string literal locations in a line without tokenizing."""
    locations = []
    paren_depth = 0
    pos = 0
    while pos < len(line):
        char = line[pos]
        if char == '(':
            paren_depth += 1
            pos += 1
            continue
        elif char == ')':
            paren_depth -= 1
            pos += 1
            continue
        if char in ['"', "'"]:
            string_info = _analyze_string_at_position(line, pos, paren_depth)
            if string_info:
                locations.append(string_info)
                pos = string_info['end'] + 1
            else:
                pos += 1
        else:
            pos += 1
    return locations

def _analyze_string_at_position(line, pos, paren_depth):
    """Analyze a potential string starting at the given position."""
    char = line[pos]
    is_fstring, is_raw = _is_fstring_start(line, pos)
    if is_fstring:
        string_start = pos
        for prefix in ['rf', 'Rf', 'rF', 'RF', 'fr', 'Fr', 'fR', 'FR', 'f', 'F']:
            prefix_start = pos - len(prefix)
            if prefix_start >= 0 and line[prefix_start:pos] == prefix and (prefix_start == 0 or not line[prefix_start - 1].isalnum()):
                string_start = prefix_start
                break
        end_pos = _find_fstring_end(line, pos, char, is_raw)
    else:
        string_start = pos
        for prefix in ['r', 'R']:
            prefix_start = pos - len(prefix)
            if prefix_start >= 0 and line[prefix_start:pos] == prefix and (prefix_start == 0 or not line[prefix_start - 1].isalnum()):
                string_start = prefix_start
                is_raw = True
                break
        end_pos = _find_string_end(line, pos, char)
    if end_pos == -1:
        return None
    string_content = line[string_start:end_pos + 1]
    if len(string_content) < 2:
        return None
    return {'start': string_start, 'end': end_pos, 'content': string_content, 'is_fstring': is_fstring, 'is_raw': is_raw, 'paren_depth': paren_depth, 'quote_char': char}

def _process_inline_comment(line: str, token_map: dict, token_counter: int, current_hash: str) -> Tuple[str, int]:
    """Process inline comments, determining their type based on the preceding code."""
    hash_positions = [i for i, c in enumerate(line) if c == '#']
    for hash_pos in hash_positions:
        is_inside_token = False
        for token_name in token_map:
            if token_name in line:
                token_start = line.find(token_name)
                token_end = token_start + len(token_name)
                if token_start <= hash_pos < token_end:
                    is_inside_token = True
                    break
        if not is_inside_token:
            comment_start = hash_pos
            code = line[:comment_start]
            code_end = len(code.rstrip())
            spacing_and_comment = line[code_end:]
            code_stripped = code.rstrip()
            token_type, extra_metadata = _determine_comment_type(code_stripped)
            token_name, token_data = _create_token(spacing_and_comment, token_counter, current_hash, token_type, extra_metadata)
            token_map[token_name] = token_data
            if token_type == TokenType.COMPOUND_COMMENT:
                base_indent = len(line) - len(line.lstrip())
                token_indent = ' ' * (base_indent + 4)
                processed_line = f'{code.rstrip()}\n{token_indent}{token_name}'
                return (processed_line, token_counter + 1)
            elif token_type == TokenType.IMPORT_COMMENT:
                base_indent = len(line) - len(line.lstrip())
                token_indent = ' ' * base_indent
                processed_line = f'{code.rstrip()}\n{token_indent}{token_name}'
                return (processed_line, token_counter + 1)
            else:
                code_trimmed = code.rstrip()
                no_semicolon_endings = [',', ':', '(', '[', '{', '\\']
                if any((code_trimmed.endswith(char) for char in no_semicolon_endings)):
                    if code_trimmed.endswith(','):
                        base_indent = len(line) - len(line.lstrip())
                        token_indent = ' ' * base_indent
                        spacing_before_comment = line[len(code_trimmed):comment_start]
                        processed_line = f'{code_trimmed}{spacing_before_comment}{token_name}'
                    else:
                        spacing_before_comment = line[len(code_trimmed):comment_start]
                        processed_line = f'{code_trimmed}{spacing_before_comment}{token_name}'
                else:
                    processed_line = f'{code.rstrip()}; {token_name}'
                return (processed_line, token_counter + 1)
    return (line, token_counter)

def _detokenize_source(tokenized_source: str, token_map: Dict[str, Dict]) -> str:
    """
    Restore original source from tokenized version using reverse tokenization order.
    This prevents issues with nested tokens and maintains proper reconstruction sequence.
    """
    result = tokenized_source
    comment_tokens = []
    string_tokens = []
    multiline_tokens = []
    other_tokens = []
    for token_name, token_data in token_map.items():
        metadata = token_data['metadata']
        token_type = metadata.get('type')
        if token_type in [TokenType.STANDALONE_COMMENT.value, TokenType.INLINE_COMMENT.value, TokenType.IMPORT_COMMENT.value, TokenType.COMPOUND_COMMENT.value]:
            comment_tokens.append((token_name, token_data))
        elif token_type == TokenType.STRING_LITERAL.value:
            string_tokens.append((token_name, token_data))
        elif token_type == TokenType.MULTILINE_STRING.value:
            multiline_tokens.append((token_name, token_data))
        else:
            other_tokens.append((token_name, token_data))
    comment_tokens.sort(key=lambda x: len(x[0]), reverse=True)
    string_tokens.sort(key=lambda x: len(x[0]), reverse=True)
    multiline_tokens.sort(key=lambda x: len(x[0]), reverse=True)
    other_tokens.sort(key=lambda x: len(x[0]), reverse=True)
    for token_name, token_data in comment_tokens:
        result = _process_single_token(result, token_name, token_data)
    for token_name, token_data in string_tokens:
        result = _process_single_token(result, token_name, token_data)
    for token_name, token_data in multiline_tokens:
        result = _process_single_token(result, token_name, token_data)
    for token_name, token_data in other_tokens:
        result = _process_single_token(result, token_name, token_data)
    return result

def _process_single_token(result: str, token_name: str, token_data: Dict) -> str:
    """Process a single token replacement with all its occurrences."""
    content = token_data['content']
    metadata = token_data['metadata']
    token_type = metadata.get('type')
    while token_name in result:
        if token_type == TokenType.STRING_LITERAL.value:
            if metadata.get('in_parens', False):
                quote_char = metadata.get('quote_char', '"')
                pattern = f'{quote_char}{token_name}{quote_char}'
                if pattern in result:
                    result = result.replace(pattern, content)
                    continue
            quote_patterns = [f'"{token_name}"', f"'{token_name}'"]
            found_pattern = False
            for pattern in quote_patterns:
                if pattern in result:
                    result = result.replace(pattern, content)
                    found_pattern = True
                    break
            if found_pattern:
                continue
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

def _handle_compound_comment(result: str, token_name: str, content: str, start: int) -> str:
    """Handle compound statement comments (def, class, if, etc.) with smart reunification"""
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
                if prev_line.strip().endswith(':'):
                    reunited = prev_line.rstrip() + content
                    return result[:prev_line_start] + reunited + result[line_end:]
                break
            search_start = prev_line_start - 1
    return result[:start] + content + result[start + len(token_name):]

def _handle_import_comment(result: str, token_name: str, content: str, start: int, metadata: dict) -> str:
    """Handle import statement comments with metadata-driven reunification"""
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
            import_statement = metadata.get('import_statement', '').strip()
            if prev_line.strip() == import_statement:
                reunited = prev_line.rstrip() + content
                return result[:prev_line_start] + reunited + result[line_end:]
            search_start = prev_line_start - 1
    return result[:start] + content + result[start + len(token_name):]

def _handle_inline_comment(result: str, token_name: str, content: str, start: int) -> str:
    """Handle inline comments (non-import, non-compound) with smart reunification"""
    line_start = result.rfind('\n', 0, start) + 1
    line_end = result.find('\n', start)
    if line_end == -1:
        line_end = len(result)
    line = result[line_start:line_end]
    if '; ' + token_name in line:
        new_line = line.replace('; ' + token_name, content)
        return result[:line_start] + new_line + result[line_end:]
    if token_name in line:
        token_pos_in_line = line.find(token_name)
        before_token = line[:token_pos_in_line].rstrip()
        no_semicolon_endings = [',', ':', '(', '[', '{', '\\']
        if any((before_token.endswith(char) for char in no_semicolon_endings)):
            new_line = line.replace(token_name, content)
            return result[:line_start] + new_line + result[line_end:]
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
    replacement = indent + '# ' + content if not content.startswith('#') else indent + content
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

def _restore_top_level_comments(final_content: str, top_comments: List[str]) -> str:
    """
    Restore top-level comments to the beginning of the file.

    Args:
        final_content: The processed file content
        top_comments: List of original top-level comment lines

    Returns:
        Content with top-level comments restored
    """
    if not top_comments:
        return final_content
    comment_section = '\n'.join(top_comments)
    if final_content.strip():
        return comment_section + '\n\n' + final_content
    else:
        return comment_section + '\n'

def _deduplicate_imports(existing_imports: List[ast.stmt], new_imports: List[ast.stmt]) -> List[ast.stmt]:
    """
    Deduplicate import statements, keeping new imports and non-duplicate existing ones.

    Parameters:
    - existing_imports: List of existing import AST nodes
    - new_imports: List of new import AST nodes to add

    Returns:
    - List of deduplicated import AST nodes
    """

    def import_signature(node):
        """Create a signature for an import node for comparison."""
        if isinstance(node, ast.Import):
            names = frozenset((alias.name for alias in node.names))
            return ('import', names)
        elif isinstance(node, ast.ImportFrom):
            module = node.module or ''
            names = frozenset((alias.name for alias in node.names))
            level = node.level
            return ('from', module, names, level)
        return None
    new_signatures = set()
    result_imports = []
    for imp in new_imports:
        sig = import_signature(imp)
        if sig:
            new_signatures.add(sig)
            result_imports.append(imp)
    for imp in existing_imports:
        sig = import_signature(imp)
        if sig and sig not in new_signatures:
            result_imports.append(imp)
    return result_imports

def _py_ast_to_source_with_comment_handling(node, token_map=None):
    """
    Convert AST to source, handling comment-only placeholder nodes specially.
    """
    if isinstance(node, ast.Module):
        parts = []
        for child in node.body:
            if hasattr(child, '_is_comment_placeholder') and child._is_comment_placeholder:
                if hasattr(child, '_original_comment_code'):
                    parts.append(child._original_comment_code.rstrip())
            else:
                parts.append(_py_ast_to_source(child))
        return '\n'.join(parts)
    elif isinstance(node, ast.AST) and hasattr(node, '_is_comment_placeholder') and node._is_comment_placeholder:
        if hasattr(node, '_original_comment_code'):
            return node._original_comment_code
        else:
            return ''
    else:
        return _py_ast_to_source(node)

def _insert_code_after_line(file_content: str, line_number: int, code_to_insert: str, indent_level: int=0) -> str:
    """
    Insert code after a specific line number in the file content.

    Parameters:
    -----------
    file_content : str
        The original file content
    line_number : int
        The line number after which to insert (1-based)
    code_to_insert : str
        The code to insert
    indent_level : int
        The indentation level to apply to the inserted code

    Returns:
    --------
    str
        The modified file content
    """
    lines = file_content.split('\n')
    if line_number < 1 or line_number > len(lines):
        raise ValueError(f'Line number {line_number} is out of range')
    indent = ' ' * indent_level
    inserted_lines = []
    for line in code_to_insert.split('\n'):
        if line.strip():
            inserted_lines.append(indent + line)
        else:
            inserted_lines.append(line)
    result_lines = lines[:line_number] + inserted_lines + lines[line_number:]
    return '\n'.join(result_lines)

def _handle_comment_only_insertion(abs_path: str, comment_code: str, insert_after: str, path_elements: list) -> str:
    """
    Special handler for inserting comment-only code after a quoted expression.
    This bypasses AST manipulation and works directly with the file content.
    """
    try:
        with open(abs_path, 'r', encoding='utf-8') as f:
            original_content = f.read()
        pattern = insert_after.strip()
        if pattern.startswith('"') and pattern.endswith('"'):
            pattern = pattern[1:-1]
        elif pattern.startswith("'") and pattern.endswith("'"):
            pattern = pattern[1:-1]
        lines = original_content.split('\n')
        pattern_lines = pattern.split('\n')
        is_multiline_pattern = len(pattern_lines) > 1
        insert_line = None
        if is_multiline_pattern:
            pattern_normalized = '\n'.join((line.strip() for line in pattern_lines))
            for i in range(len(lines) - len(pattern_lines) + 1):
                chunk = lines[i:i + len(pattern_lines)]
                chunk_normalized = '\n'.join((line.strip() for line in chunk))
                if chunk_normalized == pattern_normalized:
                    insert_line = i + len(pattern_lines) - 1
                    break
        else:
            pattern_stripped = pattern_lines[0].strip()
            for i, line in enumerate(lines):
                if line.strip().startswith(pattern_stripped):
                    insert_line = i
                    break
        if insert_line is None:
            return _process_error(ValueError(f'Insert point not found: {insert_after}'))
        indent_level = 0
        if insert_line < len(lines):
            matched_line = lines[insert_line]
            indent_level = len(matched_line) - len(matched_line.lstrip())
        if path_elements:
            tokenized_content, _ = _tokenize_source(original_content)
            tree = ast.parse(tokenized_content)
            viewer = ScopeViewer(path_elements)
            target_node = viewer.find_target(tree)
            if not target_node:
                return _process_error(ValueError(f'Target scope not found: ::'.join(path_elements)))
            if hasattr(target_node, 'lineno') and hasattr(target_node, 'end_lineno'):
                if not target_node.lineno <= insert_line + 1 <= target_node.end_lineno:
                    return _process_error(ValueError(f'Insert point is not within the target scope'))
        modified_content = _insert_code_after_line(original_content, insert_line + 1, comment_code, indent_level)
        with open(abs_path, 'w', encoding='utf-8') as f:
            f.write(modified_content)
        return f"Code inserted after '{insert_after}' in '{abs_path}'."
    except Exception as e:
        return _process_error(e)

class ScopeFinder(cst.CSTVisitor):
    """
    Visitor to find a specific scope in the CST based on a path.
    """

    def __init__(self, path_elements: List[str]):
        self.path_elements = path_elements
        self.current_path = []
        self.target_node = None
        self.parent_stack = []

    def visit_ClassDef(self, node: cst.ClassDef) -> Optional[bool]:
        """Visit a class definition."""
        return self._visit_scope_node(node)

    def leave_ClassDef(self, node: cst.ClassDef) -> None:
        """Leave a class definition."""
        if self.current_path and self.current_path[-1] == node.name.value:
            self.current_path.pop()
            self.parent_stack.pop()

    def visit_FunctionDef(self, node: cst.FunctionDef) -> Optional[bool]:
        """Visit a function definition."""
        return self._visit_scope_node(node)

    def leave_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Leave a function definition."""
        if self.current_path and self.current_path[-1] == node.name.value:
            self.current_path.pop()
            self.parent_stack.pop()

    def _visit_scope_node(self, node: Union[cst.ClassDef, cst.FunctionDef]) -> Optional[bool]:
        """Common logic for visiting scope nodes."""
        if len(self.current_path) < len(self.path_elements):
            expected_name = self.path_elements[len(self.current_path)]
            if node.name.value == expected_name:
                self.current_path.append(node.name.value)
                self.parent_stack.append(node)
                if len(self.current_path) == len(self.path_elements):
                    self.target_node = node
                    return False
                return True
        return False

class ScopeReplacer(cst.CSTTransformer):
    """
    Transformer to replace or modify a specific scope in the CST.
    """

    def __init__(self, path_elements: List[str], new_code: Optional[cst.CSTNode]=None, insert_after: Optional[str]=None, module: Optional[cst.Module]=None):
        self.path_elements = path_elements
        self.new_code = new_code
        self.insert_after = insert_after
        self.current_path = []
        self.modified = False
        self.module = module

    def visit_ClassDef(self, node: cst.ClassDef) -> None:
        """Track when entering a class."""
        self.current_path.append(node.name.value)

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Handle leaving a class definition."""
        result = self._handle_scope_node(original_node, updated_node)
        if self.current_path and self.current_path[-1] == original_node.name.value:
            self.current_path.pop()
        return result

    def visit_FunctionDef(self, node: cst.FunctionDef) -> None:
        """Track when entering a function."""
        self.current_path.append(node.name.value)

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Handle leaving a function definition."""
        result = self._handle_scope_node(original_node, updated_node)
        if self.current_path and self.current_path[-1] == original_node.name.value:
            self.current_path.pop()
        return result

    def _handle_scope_node(self, original_node: Union[cst.ClassDef, cst.FunctionDef], updated_node: Union[cst.ClassDef, cst.FunctionDef]) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Common logic for handling scope nodes."""
        if self.current_path == self.path_elements:
            if self.insert_after:
                result = self._handle_insertion(updated_node)
                return result
            elif self.new_code is not None:
                self.modified = True
                return self.new_code
        return updated_node

    def _handle_insertion(self, node: Union[cst.ClassDef, cst.FunctionDef]) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Handle inserting code after a specific element within a scope."""
        if self.insert_after.startswith('"') and self.insert_after.endswith('"'):
            pattern = self.insert_after[1:-1]
            return self._insert_after_expression(node, pattern)
        else:
            return self._insert_after_named_scope(node)

    def _insert_after_expression(self, node: Union[cst.ClassDef, cst.FunctionDef], pattern: str) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Insert code after a line matching the expression pattern within the scope."""
        if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
            body = node.body
            if isinstance(body, cst.IndentedBlock):
                new_body_nodes = []
                pattern_found = False
                for i, stmt in enumerate(body.body):
                    new_body_nodes.append(stmt)
                    if self.module:
                        try:
                            stmt_code = self.module.code_for_node(stmt).strip()
                        except:
                            temp_module = cst.Module(body=[stmt])
                            stmt_code = temp_module.code.strip()
                    else:
                        temp_module = cst.Module(body=[stmt])
                        stmt_code = temp_module.code.strip()
                    if pattern in stmt_code or stmt_code.startswith(pattern):
                        if self.new_code:
                            new_code_str = self.new_code.code.strip()
                            if new_code_str.startswith('#') or new_code_str.startswith('    #'):
                                comment_stmt = _create_statement_with_comment(new_code_str)
                                new_body_nodes.append(comment_stmt)
                            elif hasattr(self.new_code, 'body'):
                                for new_stmt in self.new_code.body:
                                    new_body_nodes.append(new_stmt)
                            else:
                                new_body_nodes.append(self.new_code)
                        pattern_found = True
                if pattern_found:
                    self.modified = True
                    new_body = body.with_changes(body=new_body_nodes)
                    return node.with_changes(body=new_body)
        return node

    def _insert_after_named_scope(self, node: Union[cst.ClassDef, cst.FunctionDef]) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Insert code after a named element within the scope."""
        target_parts = self.insert_after.split('::')
        if len(target_parts) > 1:
            scope_prefix = target_parts[:-1]
            if self.current_path != self.path_elements or scope_prefix != self.path_elements[-len(scope_prefix):]:
                return node
            target_name = target_parts[-1]
        else:
            target_name = target_parts[0]
        body = node.body
        if isinstance(body, cst.IndentedBlock):
            new_body_nodes = []
            inserted = False
            for stmt in body.body:
                new_body_nodes.append(stmt)
                if isinstance(stmt, (cst.FunctionDef, cst.ClassDef)):
                    if hasattr(stmt, 'name') and stmt.name.value == target_name:
                        if self.new_code and hasattr(self.new_code, 'body'):
                            new_body_nodes.extend(self.new_code.body)
                        inserted = True
                        self.modified = True
            if inserted:
                new_body = body.with_changes(body=new_body_nodes)
                return node.with_changes(body=new_body)
        return node

@handle_errors
def python_view(target_scope: str) -> str:
    """
    View Python code using pytest-style scope syntax.

    Parameters:
    -----------
    target_scope : str
        Location to view in pytest-style scope syntax:
        - "file.py" (whole file)
        - "file.py::MyClass" (class)
        - "file.py::my_function" (function)
        - "file.py::MyClass::method" (method)

    Returns:
    --------
    str
        The source code at the specified scope, or error message
    """
    try:
        file_path, *path_elements = target_scope.split('::')
        if not file_path.endswith('.py'):
            return _process_error(ValueError(f'File path must end with .py: {file_path}'))
        for element in path_elements:
            if not element.isidentifier():
                return _process_error(ValueError(f'Invalid identifier in path: {element}'))
        abs_path = os.path.abspath(file_path)
        if not os.path.exists(abs_path):
            return _process_error(FileNotFoundError(f'File not found: {abs_path}'))
        try:
            source_code = _read_file_bom_safe(abs_path)
            if not source_code.strip():
                return f"File '{abs_path}' is empty."
        except Exception as e:
            return _process_error(ValueError(f'Error reading file {abs_path}: {str(e)}'))
        if not path_elements:
            return source_code
        try:
            wrapper = cst.MetadataWrapper(cst.parse_module(source_code))
        except Exception as e:
            return _process_error(ValueError(f'Error parsing file {abs_path}: {str(e)}'))
        finder = ScopeFinder(path_elements)
        wrapper.visit(finder)
        if not finder.target_node:
            return _process_error(ValueError(f'Target scope not found: {target_scope}'))
        return wrapper.module.code_for_node(finder.target_node)
    except Exception as e:
        return _process_error(e)

@handle_errors
def python_edit(target_scope: str, code: str, *, insert_after: str=None) -> str:
    """
    Edit Python code using pytest-style scope syntax.

    Parameters:
    -----------
    target_scope : str
        Location to edit in pytest-style scope syntax:
        - "file.py" (whole file)
        - "file.py::MyClass" (class)
        - "file.py::my_function" (function)
        - "file.py::MyClass::method" (method)

    code : str
        Python code to insert/replace. Will be dedented automatically.

    insert_after : str, optional
        Scope to insert the code after, using the same syntax as target_scope:
        - "__FILE_START__" (special token for file beginning)
        - "MyClass::method" (insert after this method within the target scope)
        - '"expression"' (insert after a line matching this expression)

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
            original_content = _read_file_bom_safe(abs_path)
            was_originally_empty = not original_content.strip()
        except Exception as e:
            return _process_error(ValueError(f'Error reading file {abs_path}: {str(e)}'))
        try:
            import textwrap
            cleaned_code = textwrap.dedent(code).strip()
            if not cleaned_code:
                return _process_error(ValueError('Code to insert/replace is empty'))
            if was_originally_empty and (not path_elements):
                _write_file_bom_safe(abs_path, cleaned_code)
                return f"Code added to '{abs_path}'."
            try:
                new_module = cst.parse_module(cleaned_code)
            except Exception as e:
                return _process_error(ValueError(f'Error parsing new code: {str(e)}'))
        except Exception as e:
            return _process_error(ValueError(f'Error processing new code: {str(e)}'))
        try:
            if original_content.strip():
                tree = cst.parse_module(original_content)
            else:
                tree = cst.parse_module('')
        except Exception as e:
            return _process_error(ValueError(f'Error parsing file {abs_path}: {str(e)}'))
        if insert_after == '__FILE_START__':
            return _handle_file_start_insertion(abs_path, tree, new_module)
        elif not path_elements:
            if insert_after:
                return _handle_file_level_insertion(abs_path, tree, new_module, insert_after)
            else:
                _write_file_bom_safe(abs_path, cleaned_code)
                return f"Code replaced at file level in '{abs_path}'."
        else:
            replacer = ScopeReplacer(path_elements, new_module, insert_after, tree)
            modified_tree = tree.visit(replacer)
            if not replacer.modified:
                if insert_after:
                    return _process_error(ValueError(f'Insert point not found: {insert_after}'))
                else:
                    return _process_error(ValueError(f'Target scope not found: {target_scope}'))
            _write_file_bom_safe(abs_path, modified_tree.code)
            if insert_after:
                return f"Code inserted after '{insert_after}' in '{abs_path}'."
            else:
                return f"Code replaced at '{target_scope}'."
    except Exception as e:
        return _process_error(e)

def _handle_file_start_insertion(abs_path: str, tree: cst.Module, new_module: cst.Module) -> str:
    """Handle insertion at the beginning of a file."""
    new_body = list(new_module.body) + list(tree.body)
    modified_tree = tree.with_changes(body=new_body)
    _write_file_bom_safe(abs_path, modified_tree.code)
    return f"Code inserted at start of '{abs_path}'."

def _handle_file_level_insertion(abs_path: str, tree: cst.Module, new_module: cst.Module, insert_after: str) -> str:
    """Handle insertion at file level after a specific pattern."""
    if insert_after.strip().startswith('"') and insert_after.strip().endswith('"'):
        pattern = insert_after.strip()[1:-1]
        return _handle_expression_insertion(abs_path, tree, new_module, pattern)
    else:
        inserter = FileInserter(insert_after, new_module.body)
        modified_tree = tree.visit(inserter)
        if not inserter.modified:
            return _process_error(ValueError(f'Insert point not found at file level: {insert_after}'))
        _write_file_bom_safe(abs_path, modified_tree.code)
        return f"Code inserted after '{insert_after}' in '{abs_path}'."

def _handle_expression_insertion(abs_path: str, tree: cst.Module, new_module: cst.Module, pattern: str) -> str:
    """Handle insertion after a quoted expression pattern."""
    inserter = ExpressionInserter(pattern, new_module.body)
    modified_tree = tree.visit(inserter)
    if not inserter.modified:
        return _process_error(ValueError(f'Insert point not found: "{pattern}"'))
    _write_file_bom_safe(abs_path, modified_tree.code)
    return f"Code inserted after '{pattern}' in '{abs_path}'."

class FileInserter(cst.CSTTransformer):
    """
    Transformer to insert code after a specific top-level definition.
    """

    def __init__(self, target_name: str, new_nodes: List[cst.BaseSmallStatement]):
        self.target_name = target_name
        self.new_nodes = new_nodes
        self.modified = False
        self.insert_after_next = False

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Process the module to insert nodes."""
        new_body = []
        for i, node in enumerate(updated_node.body):
            new_body.append(node)
            if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
                if node.name.value == self.target_name:
                    new_body.extend(self.new_nodes)
                    self.modified = True
        if self.modified:
            return updated_node.with_changes(body=new_body)
        return updated_node

class ExpressionInserter(cst.CSTTransformer):
    """
    Transformer to insert code after a line matching a specific expression pattern.
    """

    def __init__(self, pattern: str, new_nodes: List[cst.BaseSmallStatement]):
        self.pattern = pattern
        self.new_nodes = new_nodes
        self.modified = False
        self.pattern_lines = pattern.split('\n')
        self.is_multiline = len(self.pattern_lines) > 1

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Process the module to find and insert after the pattern."""
        module_lines = updated_node.code.split('\n')
        insert_index = self._find_pattern(module_lines)
        if insert_index is None:
            return updated_node
        new_body = []
        current_line = 0
        for node in updated_node.body:
            new_body.append(node)
            node_code = updated_node.code_for_node(node)
            node_lines = node_code.count('\n') + 1
            node_end_line = current_line + node_lines
            if current_line <= insert_index < node_end_line:
                new_body.extend(self.new_nodes)
                self.modified = True
            current_line = node_end_line
        if self.modified:
            return updated_node.with_changes(body=new_body)
        return updated_node

    def _find_pattern(self, lines: List[str]) -> Optional[int]:
        """Find the line index where the pattern matches."""
        if self.is_multiline:
            pattern_normalized = '\n'.join((line.strip() for line in self.pattern_lines))
            for i in range(len(lines) - len(self.pattern_lines) + 1):
                chunk = lines[i:i + len(self.pattern_lines)]
                chunk_normalized = '\n'.join((line.strip() for line in chunk))
                if chunk_normalized == pattern_normalized:
                    return i + len(self.pattern_lines) - 1
        else:
            pattern_stripped = self.pattern_lines[0].strip()
            for i, line in enumerate(lines):
                if line.strip().startswith(pattern_stripped):
                    return i
        return None

def _create_statement_with_comment(comment_text: str, indent_level: int=0) -> cst.SimpleStatementLine:
    """
    Create a statement that contains just a comment.
    Since LibCST requires statements to have actual code, we create a pass statement
    with a trailing comment.
    """
    lines = comment_text.strip().split('\n')
    if len(lines) > 1:
        comment_text = lines[0]
    comment_text = comment_text.strip()
    if comment_text.startswith('#'):
        comment_text = comment_text[1:].strip()
    comment = cst.Comment(f'# {comment_text}')
    return cst.SimpleStatementLine(body=[cst.Pass()], trailing_whitespace=cst.TrailingWhitespace(whitespace=cst.SimpleWhitespace('  '), comment=comment))