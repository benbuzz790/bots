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
# TokenType enum removed - tokenization system eliminated in favor of native CST handling
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
        self.replaced_at_top_level = False
        self.replacement_index = -1

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Handle module-level whitespace after replacements."""
        if self.replaced_at_top_level and self.replacement_index >= 0:
            # Ensure proper spacing after top-level function/class replacements
            new_body = list(updated_node.body)

            # If there's a statement after the replaced one, ensure it has proper leading lines
            if self.replacement_index + 1 < len(new_body):
                next_stmt = new_body[self.replacement_index + 1]

                # Add a blank line before the next statement if it's a class or function
                if isinstance(next_stmt, (cst.ClassDef, cst.FunctionDef)):
                    # Create a blank line
                    blank_line = cst.SimpleStatementLine(
                        body=[],
                        leading_lines=[cst.EmptyLine(indent="", whitespace=cst.SimpleWhitespace(""), comment=None, newline=cst.Newline())],
                        trailing_whitespace=cst.TrailingWhitespace(
                            whitespace=cst.SimpleWhitespace(""),
                            comment=None,
                            newline=cst.Newline()
                        )
                    )

                    # Actually, let's use leading_lines on the next statement instead
                    if not next_stmt.leading_lines:
                        # Add a blank line before this statement
                        blank_line_node = cst.EmptyLine(
                            indent="",
                            whitespace=cst.SimpleWhitespace(""),
                            comment=None,
                            newline=cst.Newline()
                        )
                        new_leading_lines = (blank_line_node,)
                        new_body[self.replacement_index + 1] = next_stmt.with_changes(leading_lines=new_leading_lines)

            return updated_node.with_changes(body=new_body)
        return updated_node

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

                # Track if this is a top-level replacement
                if len(self.path_elements) == 1:  # Top-level scope
                    self.replaced_at_top_level = True
                    # Find the index of this node in the module
                    if self.module:
                        for i, stmt in enumerate(self.module.body):
                            if stmt is original_node:
                                self.replacement_index = i
                                break

                # Extract the actual function/class definition from the module
                if hasattr(self.new_code, 'body') and len(self.new_code.body) > 0:
                    # Find the matching function/class definition, not just the first element
                    target_name = original_node.name.value
                    new_node = None

                    for stmt in self.new_code.body:
                        if isinstance(stmt, type(original_node)) and hasattr(stmt, 'name') and stmt.name.value == target_name:
                            new_node = stmt
                            break

                    # Fallback to first element if no matching name found
                    if new_node is None:
                        new_node = self.new_code.body[0]

                    # Preserve the original node's leading lines
                    if hasattr(original_node, 'leading_lines'):
                        new_node = new_node.with_changes(leading_lines=original_node.leading_lines)

                    return new_node
                else:
                    # Fallback to original behavior if no body
                    return self.new_code
        return updated_node

    def _handle_insertion(self, node: Union[cst.ClassDef, cst.FunctionDef]) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Handle inserting code after a specific element within a scope."""
        if (self.insert_after.startswith('"') and self.insert_after.endswith('"')) or (self.insert_after.startswith("'") and self.insert_after.endswith("'")):
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
                pattern_lines = pattern.split('\n')
                is_multiline = len(pattern_lines) > 1
                for i, stmt in enumerate(body.body):
                    new_body_nodes.append(stmt)
                    if self.module:
                        try:
                            stmt_code = self.module.code_for_node(stmt)
                        except:
                            temp_module = cst.Module(body=[stmt])
                            stmt_code = temp_module.code
                    else:
                        temp_module = cst.Module(body=[stmt])
                        stmt_code = temp_module.code
                    stmt_code = stmt_code.rstrip('\n')
                    if is_multiline:
                        stmt_lines = stmt_code.split('\n')
                        if len(stmt_lines) >= len(pattern_lines):

                            def get_structure_and_content(lines):
                                """Get relative indentation structure and content"""
                                result = []
                                indent_levels = []
                                for line in lines:
                                    if line.strip():
                                        indent = len(line) - len(line.lstrip())
                                        indent_levels.append(indent)
                                unique_levels = sorted(set(indent_levels)) if indent_levels else [0]
                                for line in lines:
                                    if line.strip():
                                        indent = len(line) - len(line.lstrip())
                                        level = unique_levels.index(indent)
                                        content = line.strip()
                                        result.append((level, content))
                                    else:
                                        result.append((0, ''))
                                return result
                            pattern_structure = get_structure_and_content(pattern_lines)
                            stmt_prefix_lines = stmt_lines[:len(pattern_lines)]
                            stmt_structure = get_structure_and_content(stmt_prefix_lines)
                            if pattern_structure == stmt_structure:
                                pattern_found = True
                    else:
                        pattern_stripped = pattern.strip()
                        stmt_code_stripped = stmt_code.strip()
                        if pattern_stripped in stmt_code_stripped or stmt_code_stripped.startswith(pattern_stripped):
                            pattern_found = True
                    if pattern_found:
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
                        pattern_found = False
                        self.modified = True
                if self.modified:
                    new_body = body.with_changes(body=new_body_nodes)
                    return node.with_changes(body=new_body)
        return node

    def _handle_insertion(self, node: Union[cst.ClassDef, cst.FunctionDef]) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Handle inserting code after a specific element within a scope."""
        if (self.insert_after.startswith('"') and self.insert_after.endswith('"')) or (self.insert_after.startswith("'") and self.insert_after.endswith("'")):
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
                pattern_lines = pattern.split('\n')
                is_multiline = len(pattern_lines) > 1
                for i, stmt in enumerate(body.body):
                    new_body_nodes.append(stmt)
                    if self.module:
                        try:
                            stmt_code = self.module.code_for_node(stmt)
                        except:
                            temp_module = cst.Module(body=[stmt])
                            stmt_code = temp_module.code
                    else:
                        temp_module = cst.Module(body=[stmt])
                        stmt_code = temp_module.code
                    stmt_code = stmt_code.rstrip('\n')
                    if is_multiline:
                        stmt_lines = stmt_code.split('\n')
                        if len(stmt_lines) >= len(pattern_lines):

                            def get_structure_and_content(lines):
                                """Get relative indentation structure and content"""
                                result = []
                                indent_levels = []
                                for line in lines:
                                    if line.strip():
                                        indent = len(line) - len(line.lstrip())
                                        indent_levels.append(indent)
                                unique_levels = sorted(set(indent_levels)) if indent_levels else [0]
                                for line in lines:
                                    if line.strip():
                                        indent = len(line) - len(line.lstrip())
                                        level = unique_levels.index(indent)
                                        content = line.strip()
                                        result.append((level, content))
                                    else:
                                        result.append((0, ''))
                                return result
                            pattern_structure = get_structure_and_content(pattern_lines)
                            stmt_prefix_lines = stmt_lines[:len(pattern_lines)]
                            stmt_structure = get_structure_and_content(stmt_prefix_lines)
                            if pattern_structure == stmt_structure:
                                pattern_found = True
                    else:
                        pattern_stripped = pattern.strip()
                        stmt_code_stripped = stmt_code.strip()
                        if pattern_stripped in stmt_code_stripped or stmt_code_stripped.startswith(pattern_stripped):
                            pattern_found = True
                    if pattern_found:
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
                        pattern_found = False
                        self.modified = True
                if self.modified:
                    new_body = body.with_changes(body=new_body_nodes)
                    return node.with_changes(body=new_body)
        return node    
    def _insert_after_expression(self, node: Union[cst.ClassDef, cst.FunctionDef], pattern: str) -> Union[cst.ClassDef, cst.FunctionDef]:
        """Insert code after a line matching the expression pattern within the scope."""
        if isinstance(node, (cst.FunctionDef, cst.ClassDef)):
            body = node.body
            if isinstance(body, cst.IndentedBlock):
                new_body_nodes = []
                pattern_found = False
                pattern_lines = pattern.split('\n')
                is_multiline = len(pattern_lines) > 1
                for i, stmt in enumerate(body.body):
                    new_body_nodes.append(stmt)
                    if self.module:
                        try:
                            stmt_code = self.module.code_for_node(stmt)
                        except:
                            temp_module = cst.Module(body=[stmt])
                            stmt_code = temp_module.code
                    else:
                        temp_module = cst.Module(body=[stmt])
                        stmt_code = temp_module.code
                    stmt_code = stmt_code.rstrip('\n')
                    if is_multiline:
                        stmt_lines = stmt_code.split('\n')
                        if len(stmt_lines) >= len(pattern_lines):

                            def get_structure_and_content(lines):
                                """Get relative indentation structure and content"""
                                result = []
                                indent_levels = []
                                for line in lines:
                                    if line.strip():
                                        indent = len(line) - len(line.lstrip())
                                        indent_levels.append(indent)
                                unique_levels = sorted(set(indent_levels)) if indent_levels else [0]
                                for line in lines:
                                    if line.strip():
                                        indent = len(line) - len(line.lstrip())
                                        level = unique_levels.index(indent)
                                        content = line.strip()
                                        result.append((level, content))
                                    else:
                                        result.append((0, ''))
                                return result
                            pattern_structure = get_structure_and_content(pattern_lines)
                            stmt_prefix_lines = stmt_lines[:len(pattern_lines)]
                            stmt_structure = get_structure_and_content(stmt_prefix_lines)
                            if pattern_structure == stmt_structure:
                                pattern_found = True
                    else:
                        pattern_stripped = pattern.strip()
                        stmt_code_stripped = stmt_code.strip()
                        if pattern_stripped in stmt_code_stripped or stmt_code_stripped.startswith(pattern_stripped):
                            pattern_found = True
                    if pattern_found:
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
                        pattern_found = False
                        self.modified = True
                if self.modified:
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
    Edit Python code using pytest-style scope syntax and optional expression matching.

    Parameters:
    -----------
    target_scope : str
        Location to edit in pytest-style scope syntax:
        - "file.py" (whole file)
        - "file.py::MyClass" (class)
        - "file.py::my_function" (function)
        - "file.py::MyClass::method" (method)

    code : str
        Python code to insert (default) or replace (if insert_after is specified). 
        Some automatic formatting happens including dedenting to match to scope.

    insert_after : str, optional
        If specified, code is inserted after, and in the same scope as, the specified code.
        example)
            
            Scope:
                - a
                - b
             
            - python edit called with insert_after = "a", code = "- c" - 

            Scope:
                - a
                - c
                - b

        Uses the same syntax as target_scope with optional expression at the end in quotes.
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
    # Remove quotes if present - GenericPatternInserter handles all patterns uniformly
    pattern = insert_after.strip()
    if (pattern.startswith('"') and pattern.endswith('"')) or (pattern.startswith("'") and pattern.endswith("'")):
        pattern = pattern[1:-1]

    inserter = GenericPatternInserter(pattern, new_module.body, tree)
    modified_tree = tree.visit(inserter)
    if not inserter.modified:
        return _process_error(ValueError(f'Insert point not found at file level: {insert_after}'))
    _write_file_bom_safe(abs_path, modified_tree.code)
    return f"Code inserted after '{insert_after}' in '{abs_path}'."

class GenericPatternInserter(cst.CSTTransformer):
    """
    Generic CST transformer that can insert code after any pattern,
    regardless of node type or nesting level.
    """

    def __init__(self, pattern: str, new_nodes: List[cst.CSTNode], module: cst.Module):
        self.pattern = pattern.strip()
        self.new_nodes = new_nodes
        self.module = module
        self.modified = False
        self.pattern_lines = self.pattern.split('\n')
        self.is_multiline = len(self.pattern_lines) > 1

    def leave_Module(self, original_node: cst.Module, updated_node: cst.Module) -> cst.Module:
        """Handle the module level."""
        new_body = self._process_statement_list(updated_node.body)
        if self.modified:
            return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_If(self, original_node: cst.If, updated_node: cst.If) -> cst.If:
        """Handle If statements."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_FunctionDef(self, original_node: cst.FunctionDef, updated_node: cst.FunctionDef) -> cst.FunctionDef:
        """Handle function definitions."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_ClassDef(self, original_node: cst.ClassDef, updated_node: cst.ClassDef) -> cst.ClassDef:
        """Handle class definitions."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_For(self, original_node: cst.For, updated_node: cst.For) -> cst.For:
        """Handle For loops."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_While(self, original_node: cst.While, updated_node: cst.While) -> cst.While:
        """Handle While loops."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_With(self, original_node: cst.With, updated_node: cst.With) -> cst.With:
        """Handle With statements."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node

    def leave_Try(self, original_node: cst.Try, updated_node: cst.Try) -> cst.Try:
        """Handle Try statements."""
        if hasattr(updated_node.body, 'body'):
            new_body_list = self._process_statement_list(updated_node.body.body)
            if self.modified:
                new_body = updated_node.body.with_changes(body=new_body_list)
                return updated_node.with_changes(body=new_body)
        return updated_node
    def _process_statement_list(self, statements: List[cst.CSTNode]) -> List[cst.CSTNode]:
        """Process a list of statements, inserting after pattern matches."""
        new_statements = []
        match_count = 0

        for stmt in statements:
            new_statements.append(stmt)

            # Get the source code for this statement
            try:
                stmt_code = self.module.code_for_node(stmt).strip()
            except Exception:
                continue

            # Check if this statement matches our pattern
            if self._matches_pattern(stmt_code):
                match_count += 1
                if match_count == 1:
                    new_statements.extend(self.new_nodes)
                    self.modified = True
                elif match_count == 2:
                    # Ambiguous match detected
                    raise ValueError(f"Ambiguous pattern '{self.pattern}' - multiple matches found")

        return new_statements
    def _matches_pattern(self, stmt_code: str) -> bool:
        """Check if statement code matches the pattern."""
        if self.is_multiline:
            # For multiline patterns, do structural comparison
            stmt_lines = stmt_code.split('\n')
            if len(stmt_lines) < len(self.pattern_lines):
                return False

            # Compare structure and content (simplified version)
            for i, pattern_line in enumerate(self.pattern_lines):
                if i >= len(stmt_lines):
                    return False
                if pattern_line.strip() not in stmt_lines[i]:
                    return False
            return True
        else:
            # Single line: exact match or starts-with
            pattern_stripped = self.pattern_lines[0].strip()
            stmt_stripped = stmt_code.strip()
            return (stmt_stripped == pattern_stripped or 
                    stmt_stripped.startswith(pattern_stripped))
# ExpressionInserter class removed - functionality merged into GenericPatternInserter
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
