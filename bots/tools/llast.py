import ast
import os
import textwrap
from typing import List, Optional, Union, Any
from abc import ABC, abstractmethod

class LLASTNode(ABC):
    def __init__(self, label: str):
        self.label = label
        self.children: List[LLASTNode] = []
        self.parent: Optional[LLASTNode] = None

    def add_child(self, child: 'LLASTNode'):
        self.children.append(child)
        child.parent = self

    def count_display_lines(self) -> int:
        """Count the number of lines this node and all its children would display."""
        my_lines = len(self.node_description().splitlines())
        for child in self.children:
            my_lines += child.count_display_lines()
        return my_lines

    @abstractmethod
    def node_description(self, indent: int = 0) -> str:
        """Return a string description of this node with the given indentation."""
        pass

    def __str__(self) -> str:
        return f"{self.label:<10} {self.node_description()}"

    @abstractmethod
    def to_source(self) -> str:
        """Convert this node back to source code."""
        pass

    @classmethod
    def create_ast_node(cls, ast_node: ast.AST, label: str) -> Optional['LLASTNode']:
        try:
            if isinstance(ast_node, ast.Expr):
                if isinstance(ast_node.value, ast.Constant) and isinstance(ast_node.value.value, str):
                    return StringStatementNode(ast_node, label)
                else:
                    # Handle other expressions (like print statements) as regular statements
                    return StatementNode(ast_node, label)
            elif isinstance(ast_node, ast.FunctionDef):
                return FunctionNode(ast_node, label)
            elif isinstance(ast_node, ast.ClassDef):
                return ClassNode(ast_node, label)
            elif isinstance(ast_node, ast.If):
                return ControlFlowNode(ast_node, label)
            elif isinstance(ast_node, ast.Try):
                return ControlFlowNode(ast_node, label)
            elif isinstance(ast_node, (ast.For, ast.While)):
                return ControlFlowNode(ast_node, label)
            elif isinstance(ast_node, ast.With):
                return ControlFlowNode(ast_node, label)
            elif isinstance(ast_node, ast.Match):
                return MatchNode(ast_node, label)
            elif isinstance(ast_node, ast.AsyncFunctionDef):
                return AsyncFunctionNode(ast_node, label)
            elif isinstance(ast_node, (ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp)):
                return ComprehensionNode(ast_node, label)
            else:
                return StatementNode(ast_node, label)
        except Exception as e:
            print(f"Error creating node: {str(e)}")  # Debug print
            return ErrorNode(label, f"Node creation error: {str(e)}")

class DirectoryNode(LLASTNode):
    def __init__(self, path: str, label: str):
        super().__init__(label)
        self.path = path

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + os.path.abspath(self.path)

    def to_source(self) -> str:
        return ""  # Directories don't have source code

class ErrorNode(LLASTNode):
    def __init__(self, label: str, error_message: str):
        super().__init__(label)
        self.error_message = error_message

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + f"Error: {self.error_message}"

    def to_source(self) -> str:
        return f"# {self.error_message}"

class FileNode(LLASTNode):
    def __init__(self, path: str, label: str):
        super().__init__(label)
        self.path = path
        self.is_python = path.endswith('.py')
        self.content = ""
        self.modified = False  # Track if content has been modified
        if self.is_python:
            try:
                with open(path, 'r') as file:
                    self.content = file.read()
                self._build_tree()
            except Exception as e:
                error_node = ErrorNode(f"{label}.error", f"File read error: {str(e)}")
                self.add_child(error_node)

    def _build_tree(self):
        if not self.is_python:
            return
        try:
            tree = ast.parse(self.content)
            # Attach source code to nodes
            for node in ast.walk(tree):
                if hasattr(node, 'lineno'):
                    lines = self.content.splitlines()
                    if hasattr(node, 'end_lineno'):
                        # Multi-line node
                        source_lines = lines[node.lineno-1:node.end_lineno]
                        if hasattr(node, 'col_offset') and hasattr(node, 'end_col_offset'):
                            # Trim first and last line to column offsets
                            source_lines[0] = source_lines[0][node.col_offset:]
                            source_lines[-1] = source_lines[-1][:node.end_col_offset]
                        node.source = '\n'.join(source_lines)
                    else:
                        # Single-line node
                        if hasattr(node, 'col_offset'):
                            node.source = lines[node.lineno-1][node.col_offset:]
                        else:
                            node.source = lines[node.lineno-1]

            # Process nodes
            for i, node in enumerate(ast.iter_child_nodes(tree)):
                try:
                    child_node = LLASTNode.create_ast_node(node, f"{self.label}.{i}")
                    if child_node:
                        self.add_child(child_node)
                except Exception as e:
                    error_node = ErrorNode(f"{self.label}.{i}.error", f"Node creation error: {str(e)}")
                    self.add_child(error_node)
        except SyntaxError as e:
            error_node = ErrorNode(f"{self.label}.error", f"SyntaxError: {str(e)}")
            self.add_child(error_node)
        except Exception as e:
            error_node = ErrorNode(f"{self.label}.error", f"AST parse error: {str(e)}")
            self.add_child(error_node)

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + os.path.basename(self.path)

    def to_source(self) -> str:
        """Generate source code from the AST nodes."""
        if not self.is_python:
            return self.content
        
        parts = []
        for child in self.children:
            if not isinstance(child, ErrorNode):
                child_source = child.to_source()
                if child_source:  # Only add non-empty sources
                    parts.append(child_source)
        
        # Add a trailing newline if there's content
        if parts:
            parts.append("")  # This will create a trailing newline
        return "\n".join(parts)

    def write_to_file(self):
        """Write the file contents only if they've been modified."""
        if not self.modified:
            return  # Skip if not modified
            
        try:
            new_content = self.to_source()
            if new_content != self.content:  # Only write if content has changed
                with open(self.path, 'w') as file:
                    file.write(new_content)
                self.content = new_content  # Update stored content
                self.modified = False  # Reset modified flag
        except Exception as e:
            print(f"Error writing to {self.path}: {str(e)}")
            raise

    def mark_modified(self):
        """Mark this file as modified."""
        self.modified = True

class FunctionNode(LLASTNode):
    def __init__(self, ast_node: ast.FunctionDef, label: str):
        super().__init__(label)
        self.ast_node = ast_node
        print(f"Initial AST node body: {[type(n).__name__ for n in ast_node.body]}")  # Debug
        self._process_docstring()
        self._process_body()

    def _process_docstring(self):
        if (self.ast_node.body and 
            isinstance(self.ast_node.body[0], ast.Expr) and 
            isinstance(self.ast_node.body[0].value, ast.Constant) and
            isinstance(self.ast_node.body[0].value.value, str)):
            
            docstring_node = StringStatementNode(self.ast_node.body[0], f"{self.label}.0", is_docstring=True)
            self.add_child(docstring_node)
            self.ast_node.body = self.ast_node.body[1:]
            print(f"After docstring processing, body: {[type(n).__name__ for n in self.ast_node.body]}")  # Debug

    def _process_body(self):
        print(f"Processing body: {[type(n).__name__ for n in self.ast_node.body]}")  # Debug
        start_index = 1 if self.children else 0
        for i, node in enumerate(self.ast_node.body, start_index):
            print(f"Processing node {i}: {type(node).__name__}")  # Debug
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                print(f"Created child node {i}: {type(child_node).__name__}")  # Debug
                self.add_child(child_node)
            else:
                print(f"Failed to create child node for {type(node).__name__}")  # Debug


    def update_from_ast(self, new_ast_node: ast.FunctionDef):
        """Update this node from a new AST node while preserving the label."""
        print(f"Updating function {self.ast_node.name} with new AST node")  # Debug
        
        # Store current label and parent
        label = self.label
        parent = self.parent
        
        # Clear current state
        self.children.clear()
        
        # Update with new AST node
        self.ast_node = new_ast_node
        
        # Reprocess the node
        self._process_docstring()
        self._process_body()
        
        # Restore label and parent
        self.label = label
        self.parent = parent
        
        # Mark the file as modified
        current = self
        while current.parent:
            if isinstance(current.parent, FileNode):
                current.parent.modified = True
                break
            current = current.parent
            
        print(f"After update, function has {len(self.children)} children")  # Debug
        for child in self.children:
            print(f"  Child: {type(child).__name__}")  # Debug

    def to_source(self) -> str:
        parts = []
        if self.ast_node.decorator_list:
            for decorator in self.ast_node.decorator_list:
                parts.append(f"@{ast.unparse(decorator)}")
        
        args = ', '.join(arg.arg for arg in self.ast_node.args.args)
        parts.append(f"def {self.ast_node.name}({args}):")
        
        if self.children:
            print(f"to_source children: {[type(c).__name__ for c in self.children]}")  # Debug
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, '    '))
        else:
            parts.append("    pass")
        
        return "\n".join(parts)

    def node_description(self, indent: int = 0) -> str:
        args = ', '.join(arg.arg for arg in self.ast_node.args.args)
        decorators = ''
        if self.ast_node.decorator_list:
            decorator_lines = [f"@{ast.unparse(d)}" for d in self.ast_node.decorator_list]
            decorators = '\n'.join(' ' * indent + d for d in decorator_lines) + '\n'
        return decorators + " " * indent + f"def {self.ast_node.name}({args}):"

class StringStatementNode(LLASTNode):
    def __init__(self, ast_node: ast.Expr, label: str, is_docstring: bool = False):
        super().__init__(label)
        self.ast_node = ast_node
        self.is_docstring = is_docstring
        if isinstance(ast_node.value, ast.Constant) and isinstance(ast_node.value.value, str):
            self.string_value = ast_node.value.value
            # Get the original source form if available
            if hasattr(ast_node, 'source'):
                self.original_format = ast_node.source
            else:
                # Default to most appropriate quotes based on content
                if '\n' in self.string_value:
                    self.original_format = f'"""{self.string_value}"""'
                elif '"' in self.string_value and "'" not in self.string_value:
                    self.original_format = f"'{self.string_value}'"
                elif "'" in self.string_value and '"' not in self.string_value:
                    self.original_format = f'"{self.string_value}"'
                else:
                    # Default to single quotes if no preference
                    self.original_format = f"'{self.string_value}'"
        else:
            raise ValueError("Not a string expression")

    def _format_triple_quoted(self, indent: int) -> str:
        """Format a triple-quoted string with proper indentation."""
        lines = self.string_value.splitlines()
        
        # If it's just one line but using triple quotes, keep it on one line
        if len(lines) == 1:
            return " " * indent + f'"""{self.string_value}"""'
            
        result = []
        # First line gets base indentation
        result.append(" " * indent + '"""')
        
        # Handle empty strings
        if not lines:
            result.append(" " * (indent + 4) + '"""')
            return '\n'.join(result)
            
        # Middle lines get extra indentation
        for line in lines:
            if line.strip():  # Only indent non-empty lines
                result.append(" " * (indent + 8) + line.strip())
            else:
                result.append("")  # Empty lines get no indentation
                
        # Closing quotes get same indentation as content
        result.append(" " * (indent + 8) + '"""')
        return '\n'.join(result)

    def node_description(self, indent: int = 0) -> str:
        if '\n' in self.string_value or self.is_docstring:
            return self._format_triple_quoted(indent)
        else:
            # Single line strings - preserve original quote style
            if self.original_format.startswith("'"):
                escaped_value = self.string_value.replace("'", "\\'")
                return " " * indent + f"'{escaped_value}'"
            else:
                escaped_value = self.string_value.replace('"', '\\"')
                return " " * indent + f'"{escaped_value}"'

    def to_source(self) -> str:
        """
        Generate source code, preserving the original format where possible.
        Falls back to a safe default if original format isn't available.
        """
        if hasattr(self, 'original_format'):
            return self.original_format
            
        # Fallback formatting if original not available
        if '\n' in self.string_value or self.is_docstring:
            return f'"""{self.string_value}"""'
        else:
            # Use single quotes by default, escaping as needed
            escaped_value = self.string_value.replace("'", "\\'")
            return f"'{escaped_value}'"

class ClassNode(LLASTNode):
    def __init__(self, ast_node: ast.ClassDef, label: str):
        super().__init__(label)
        self.ast_node = ast_node
        self._process_docstring()
        self._process_body()

    def _process_docstring(self):
        # Check for docstring in the class body
        if (self.ast_node.body and 
            isinstance(self.ast_node.body[0], ast.Expr) and 
            isinstance(self.ast_node.body[0].value, ast.Constant) and
            isinstance(self.ast_node.body[0].value.value, str)):
            
            # Create StringStatementNode for docstring
            docstring_node = StringStatementNode(self.ast_node.body[0], f"{self.label}.0", is_docstring=True)
            self.add_child(docstring_node)
            # Remove docstring from body to avoid processing it twice
            self.ast_node.body = self.ast_node.body[1:]

    def _process_body(self):
        # Start numbering from after docstring if it exists
        start_index = 1 if self.children else 0
        for i, node in enumerate(self.ast_node.body, start_index):
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                self.add_child(child_node)

    def update_from_ast(self, new_ast_node: ast.ClassDef):
        """Update this node from a new AST node while preserving the label."""
        # Preserve the label and parent
        label = self.label
        parent = self.parent
        
        # Update the AST node
        self.ast_node = new_ast_node
        
        # Clear existing children
        self.children.clear()
        
        # Reprocess the node
        self._process_docstring()
        self._process_body()
        
        # Restore label and parent
        self.label = label
        self.parent = parent

        # Mark parent file as modified if there is one
        current = self
        while current.parent:
            current = current.parent
            if isinstance(current, FileNode):
                current.mark_modified()
                break

    def node_description(self, indent: int = 0) -> str:
        # Format any decorators
        parts = []
        if self.ast_node.decorator_list:
            for decorator in self.ast_node.decorator_list:
                parts.append(" " * indent + f"@{ast.unparse(decorator)}")
        
        # Format the class definition line
        bases = []
        for base in self.ast_node.bases:
            bases.append(ast.unparse(base))
        for kw in self.ast_node.keywords:
            if kw.arg == 'metaclass':
                bases.append(f"metaclass={ast.unparse(kw.value)}")
            else:
                bases.append(f"{kw.arg}={ast.unparse(kw.value)}")
                
        base_list = ", ".join(bases)
        class_def = f"class {self.ast_node.name}"
        if base_list:
            class_def += f"({base_list})"
        class_def += ":"
        
        parts.append(" " * indent + class_def)
        return "\n".join(parts)

    def to_source(self) -> str:
        parts = []
        
        # Add decorators
        for decorator in self.ast_node.decorator_list:
            parts.append(f"@{ast.unparse(decorator)}")
        
        # Add class definition
        bases = []
        for base in self.ast_node.bases:
            bases.append(ast.unparse(base))
        for kw in self.ast_node.keywords:
            if kw.arg == 'metaclass':
                bases.append(f"metaclass={ast.unparse(kw.value)}")
            else:
                bases.append(f"{kw.arg}={ast.unparse(kw.value)}")
                
        base_list = ", ".join(bases)
        class_def = f"class {self.ast_node.name}"
        if base_list:
            class_def += f"({base_list})"
        class_def += ":"
        parts.append(class_def)
        
        # Add class body
        if self.children:
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, '    '))
        else:
            # Empty class needs a pass statement
            parts.append("    pass")
        
        return "\n".join(parts)

class ControlFlowNode(LLASTNode):
    def __init__(self, ast_node: Union[ast.If, ast.For, ast.While, ast.With, ast.Try], label: str):
        super().__init__(label)
        self.ast_node = ast_node
        self._process_body()
        self._process_extras()  # Handle else, elif, finally clauses

    def _process_body(self):
        for i, node in enumerate(self.ast_node.body):
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                self.add_child(child_node)

    def _process_extras(self):
        """Process additional clauses like else, elif, except, finally."""
        if isinstance(self.ast_node, ast.Try):
            # Handle except handlers
            for i, handler in enumerate(self.ast_node.handlers):
                except_node = ExceptNode(handler, f"{self.label}.except{i}")
                self.add_child(except_node)

            # Handle else clause
            if self.ast_node.orelse:
                else_node = ElseNode(self.ast_node.orelse, f"{self.label}.else")
                self.add_child(else_node)

            # Handle finally clause
            if self.ast_node.finalbody:
                finally_node = FinallyNode(self.ast_node.finalbody, f"{self.label}.finally")
                self.add_child(finally_node)

        elif hasattr(self.ast_node, 'orelse') and self.ast_node.orelse:
            if isinstance(self.ast_node, ast.If) and len(self.ast_node.orelse) == 1 and isinstance(self.ast_node.orelse[0], ast.If):
                # This is an elif
                elif_node = self.create_ast_node(self.ast_node.orelse[0], f"{self.label}.elif")
                if elif_node:
                    self.add_child(elif_node)
            else:
                # Regular else clause
                else_node = ElseNode(self.ast_node.orelse, f"{self.label}.else")
                self.add_child(else_node)

    def node_description(self, indent: int = 0) -> str:
        if isinstance(self.ast_node, ast.Try):
            return " " * indent + "try:"
        elif isinstance(self.ast_node, ast.If):
            return " " * indent + f"if {ast.unparse(self.ast_node.test)}:"
        elif isinstance(self.ast_node, ast.For):
            return " " * indent + f"for {ast.unparse(self.ast_node.target)} in {ast.unparse(self.ast_node.iter)}:"
        elif isinstance(self.ast_node, ast.While):
            return " " * indent + f"while {ast.unparse(self.ast_node.test)}:"
        elif isinstance(self.ast_node, ast.With):
            items = ', '.join(ast.unparse(item) for item in self.ast_node.items)
            return " " * indent + f"with {items}:"
        else:
            return " " * indent + f"{ast.unparse(self.ast_node).split(':')[0]}:"

    def to_source(self) -> str:
        parts = [self.node_description().strip()]
        
        # Add main body
        if self.children:
            body_parts = []
            for child in self.children:
                if not isinstance(child, (ExceptNode, ElseNode, FinallyNode)):
                    body_parts.append(child.to_source())
            if body_parts:
                parts.append(textwrap.indent("\n".join(body_parts), "    "))
            
            # Add except/else/finally clauses
            for child in self.children:
                if isinstance(child, (ExceptNode, ElseNode, FinallyNode)):
                    parts.append(child.to_source())
        else:
            # Empty body needs a pass statement
            parts.append("    pass")
        
        return "\n".join(parts)

    def update_from_ast(self, new_ast_node: Union[ast.If, ast.For, ast.While, ast.With, ast.Try]):
        """Update this node from a new AST node while preserving the label."""
        label = self.label
        parent = self.parent
        
        self.ast_node = new_ast_node
        self.children.clear()
        
        self._process_body()
        self._process_extras()
        
        self.label = label
        self.parent = parent

        # Mark parent file as modified
        current = self
        while current.parent:
            current = current.parent
            if isinstance(current, FileNode):
                current.mark_modified()
                break

class ExceptNode(LLASTNode):
    def __init__(self, ast_node: ast.ExceptHandler, label: str):
        super().__init__(label)
        self.ast_node = ast_node
        self._process_body()

    def _process_body(self):
        for i, node in enumerate(self.ast_node.body):
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                self.add_child(child_node)

    def node_description(self, indent: int = 0) -> str:
        if self.ast_node.type:  # If there's an exception type
            if self.ast_node.name:  # If there's a name to bind the exception to
                return " " * indent + f"except {ast.unparse(self.ast_node.type)} as {self.ast_node.name}:"
            return " " * indent + f"except {ast.unparse(self.ast_node.type)}:"
        return " " * indent + "except:"  # Bare except

    def to_source(self) -> str:
        parts = [self.node_description().strip()]
        
        if self.children:
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, "    "))
        else:
            parts.append("    pass")
        
        return "\n".join(parts)

class ElseNode(LLASTNode):
    def __init__(self, body: List[ast.stmt], label: str):
        super().__init__(label)
        self.body = body
        self._process_body()

    def _process_body(self):
        for i, node in enumerate(self.body):
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                self.add_child(child_node)

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + "else:"

    def to_source(self) -> str:
        parts = ["else:"]
        
        if self.children:
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, "    "))
        else:
            parts.append("    pass")
        
        return "\n".join(parts)

class FinallyNode(LLASTNode):
    def __init__(self, body: List[ast.stmt], label: str):
        super().__init__(label)
        self.body = body
        self._process_body()

    def _process_body(self):
        for i, node in enumerate(self.body):
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                self.add_child(child_node)

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + "finally:"

    def to_source(self) -> str:
        parts = ["finally:"]
        
        if self.children:
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, "    "))
        else:
            parts.append("    pass")
        
        return "\n".join(parts)

class StatementNode(LLASTNode):
    def __init__(self, ast_node: ast.stmt, label: str):
        super().__init__(label)
        self.ast_node = ast_node

    def _handle_special_names(self, code: str) -> str:
        """
        Handle special Python dunder names.
        Ensures they are preserved correctly during unparsing.
        """
        # Handle special dunder names with specific logic for each
        replacements = {
            "**name**": "__name__",
            "**file**": "__file__",
            "**doc**": "__doc__",
            "**package**": "__package__",
            "**spec**": "__spec__",
            "**module**": "__module__",
            "**qualname**": "__qualname__",
            "**annotations**": "__annotations__",
            "**all__": "__all__"
        }
        
        for pattern, replacement in replacements.items():
            code = code.replace(pattern, replacement)
        return code

    def node_description(self, indent: int = 0) -> str:
        """Generate a description of this statement with proper indentation."""
        try:
            unparsed = ast.unparse(self.ast_node)
            fixed_code = self._handle_special_names(unparsed)
            return " " * indent + fixed_code
        except Exception as e:
            return " " * indent + f"<error unparsing statement: {str(e)}>"

    def to_source(self) -> str:
        """Convert the statement back to source code."""
        try:
            unparsed = ast.unparse(self.ast_node)
            return self._handle_special_names(unparsed)
        except Exception as e:
            # Include the error in a comment so it's valid Python
            return f"# Error generating source: {str(e)}"

    def update_from_ast(self, new_ast_node: ast.stmt):
        """Update this node from a new AST node while preserving the label."""
        label = self.label
        parent = self.parent
        
        self.ast_node = new_ast_node
        
        self.label = label
        self.parent = parent

        # Mark parent file as modified
        current = self
        while current.parent:
            current = current.parent
            if isinstance(current, FileNode):
                current.mark_modified()
                break

class MatchNode(LLASTNode):
    def __init__(self, ast_node: ast.Match, label: str):
        super().__init__(label)
        self.ast_node = ast_node
        self._process_cases()

    def _process_cases(self):
        for i, case in enumerate(self.ast_node.cases):
            case_node = CaseNode(case, f"{self.label}.{i}")
            if case_node:
                self.add_child(case_node)

    def update_from_ast(self, new_ast_node: ast.Match):
        """Update this node from a new AST node while preserving the label."""
        label = self.label
        parent = self.parent
        
        self.ast_node = new_ast_node
        self.children.clear()
        
        self._process_cases()
        
        self.label = label
        self.parent = parent

        # Mark parent file as modified
        current = self
        while current.parent:
            current = current.parent
            if isinstance(current, FileNode):
                current.mark_modified()
                break

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + f"match {ast.unparse(self.ast_node.subject)}:"

    def to_source(self) -> str:
        parts = [f"match {ast.unparse(self.ast_node.subject)}:"]
        
        if self.children:
            for child in self.children:
                parts.append(textwrap.indent(child.to_source(), "    "))
        else:
            # Empty match needs at least one case with pass
            parts.append("    case _:\n        pass")
        
        return "\n".join(parts)

class CaseNode(LLASTNode):
    def __init__(self, ast_node: ast.match_case, label: str):
        super().__init__(label)
        self.ast_node = ast_node
        self._process_body()

    def _process_body(self):
        for i, node in enumerate(self.ast_node.body):
            child_node = self.create_ast_node(node, f"{self.label}.{i}")
            if child_node:
                self.add_child(child_node)

    def _format_pattern(self) -> str:
        """Format the pattern part of the case statement."""
        pattern = ast.unparse(self.ast_node.pattern)
        
        # Handle guard clause if present
        if self.ast_node.guard:
            guard = ast.unparse(self.ast_node.guard)
            return f"case {pattern} if {guard}"
        
        return f"case {pattern}"

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + self._format_pattern() + ":"

    def to_source(self) -> str:
        parts = [self._format_pattern() + ":"]
        
        if self.children:
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, "    "))
        else:
            # Empty case needs a pass statement
            parts.append("    pass")
        
        return "\n".join(parts)

    def update_from_ast(self, new_ast_node: ast.match_case):
        """Update this node from a new AST node while preserving the label."""
        label = self.label
        parent = self.parent
        
        self.ast_node = new_ast_node
        self.children.clear()
        
        self._process_body()
        
        self.label = label
        self.parent = parent

        # Mark parent file as modified if we're part of one
        current = self
        while current.parent:
            current = current.parent
            if isinstance(current, FileNode):
                current.mark_modified()
                break

class AsyncFunctionNode(FunctionNode):
    """
    Handles async function definitions. Inherits most behavior from FunctionNode
    but overrides display and source generation to include 'async'.
    """
    def node_description(self, indent: int = 0) -> str:
        args = ', '.join(arg.arg for arg in self.ast_node.args.args)
        decorators = ''
        if self.ast_node.decorator_list:
            decorator_lines = [f"@{ast.unparse(d)}" for d in self.ast_node.decorator_list]
            decorators = '\n'.join(' ' * indent + d for d in decorator_lines) + '\n'
        return decorators + " " * indent + f"async def {self.ast_node.name}({args}):"

    def to_source(self) -> str:
        parts = []
        
        # Add decorators if any
        if self.ast_node.decorator_list:
            for decorator in self.ast_node.decorator_list:
                parts.append(f"@{ast.unparse(decorator)}")
        
        # Generate async function definition
        args = ', '.join(arg.arg for arg in self.ast_node.args.args)
        parts.append(f"async def {self.ast_node.name}({args}):")
        
        # Add body (including docstring)
        if self.children:
            body = "\n".join(child.to_source() for child in self.children)
            parts.append(textwrap.indent(body, '    '))
        else:
            # Empty async function needs a pass statement
            parts.append("    pass")
        
        return "\n".join(parts)

class ComprehensionNode(LLASTNode):
    """
    Handles list/set/dict comprehensions and generator expressions.
    """
    def __init__(self, ast_node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp], label: str):
        super().__init__(label)
        self.ast_node = ast_node
        self.comp_type = self._determine_comp_type()

    def _determine_comp_type(self) -> str:
        """Determine the type of comprehension."""
        if isinstance(self.ast_node, ast.ListComp):
            return 'list'
        elif isinstance(self.ast_node, ast.SetComp):
            return 'set'
        elif isinstance(self.ast_node, ast.DictComp):
            return 'dict'
        else:  # GeneratorExp
            return 'generator'

    def _format_comprehension(self) -> str:
        """Format the comprehension expression with appropriate brackets."""
        expr = ast.unparse(self.ast_node)
        
        # Generator expressions don't need extra parentheses when they're
        # the only argument in a function call, but we'll add them for consistency
        if self.comp_type == 'generator' and not expr.startswith('('):
            return f"({expr})"
        return expr

    def node_description(self, indent: int = 0) -> str:
        return " " * indent + self._format_comprehension()

    def to_source(self) -> str:
        return self._format_comprehension()

    def update_from_ast(self, new_ast_node: Union[ast.ListComp, ast.SetComp, ast.DictComp, ast.GeneratorExp]):
        """Update this node from a new AST node while preserving the label."""
        label = self.label
        parent = self.parent
        
        self.ast_node = new_ast_node
        self.comp_type = self._determine_comp_type()
        
        self.label = label
        self.parent = parent

        # Mark parent file as modified
        current = self
        while current.parent:
            current = current.parent
            if isinstance(current, FileNode):
                current.mark_modified()
                break

    def count_display_lines(self) -> int:
        """Comprehensions are always single line."""
        return 1

class LLASTProject:
    def __init__(self, path: str):
        self.path = os.path.abspath(path)
        self.root = self._build_tree(self.path, "0")

    def _build_tree(self, path: str, label: str) -> Optional[LLASTNode]:
        """Build tree from filesystem, returning None for skipped files/dirs."""
        if os.path.isfile(path):
            # Skip hidden files
            if os.path.basename(path).startswith('.'):
                return None
            return FileNode(path, label)
        elif os.path.isdir(path):
            dir_node = DirectoryNode(path, label)
            if os.path.basename(path).startswith('.'): # skip filling in hidden directories
                return dir_node

            try:
                entries = sorted(os.listdir(path))
                child_index = 0  # Use separate counter for valid children
                for item in entries:
                    # Skip hidden entries and __pycache__
                    if item.startswith(('.', '_')):
                        continue
                    
                    item_path = os.path.join(path, item)
                    child_label = f"{label}.{child_index}"
                    child_node = self._build_tree(item_path, child_label)
                    
                    if child_node is not None:  # Only add non-None nodes
                        dir_node.add_child(child_node)
                        child_index += 1  # Only increment for valid children
                
                return dir_node
            except PermissionError:
                return ErrorNode(label, f"Permission denied: {path}")
            except Exception as e:
                return ErrorNode(label, f"Error processing directory: {str(e)}")
        else:
            return ErrorNode(label, f"Unsupported path type: {path}")

    def view_project(self, node: Optional[LLASTNode] = None, indent: int = 0, 
                    expanded_labels: Optional[set] = None, depth: int = 0, 
                    show_path: bool = True) -> str:
        """
        Generate a string representation of the project tree.
        
        Args:
            node: The node to start from (defaults to root)
            indent: Current indentation level
            expanded_labels: Set of labels to show expanded
            depth: Current depth in tree
            show_path: Whether to show path from root to expanded node
        """
        if node is None:
            node = self.root
            
        if expanded_labels is None:
            expanded_labels = set()

        # If we're not showing path and this isn't the expanded node or its descendant, skip it
        if not show_path and expanded_labels and not any(node.label.startswith(l) for l in expanded_labels):
            return ""

        result = [f"{node.label:<10} {node.node_description(indent)}"]
        
        if node.children:
            # Calculate if we should show this node's children
            total_lines = node.count_display_lines()
            auto_expand = total_lines <= 25
            
            show_children = (
                node.label in expanded_labels or  # Node is specifically expanded
                depth < 2 or  # We're within the 2-level depth limit
                (auto_expand and any(l.startswith(node.label) for l in expanded_labels))  # Auto-expand small nodes
            )
            
            if show_children:
                for child in node.children:
                    child_indent = indent + 4
                    child_depth = depth + 1
                    child_view = self.view_project(
                        child, 
                        child_indent, 
                        expanded_labels, 
                        child_depth,
                        show_path
                    )
                    if child_view:  # Only add non-empty views
                        result.extend(child_view.splitlines())
            else:
                result[-1] += " ..."

        return '\n'.join(result)

    def expand(self, label: str) -> str:
        """Expand a specific node and its descendants if small enough."""
        node = self.get_node(label)
        if node is None:
            return f"Node with label {label} not found."

        # Start with just the target node expanded
        expanded_labels = {label}
        
        # If the total lines would be <= 25, add all descendant labels
        if node.count_display_lines() <= 25:
            def add_descendants(node):
                for child in node.children:
                    expanded_labels.add(child.label)
                    add_descendants(child)
            add_descendants(node)
        else:
            # Otherwise just expand one level
            for child in node.children:
                expanded_labels.add(child.label)
            
        # Start view from the target node
        result = self.view_project(
            node=node,
            expanded_labels=expanded_labels,
            show_path=False  # Don't show path from root to target
        )
        return result
    
    def view_full_tree(self, node: Optional[LLASTNode] = None, indent: int = 0) -> str:
        """
        Generate a complete string representation of the tree, showing all nodes.
        
        Args:
            node (Optional[LLASTNode]): The node to start from (defaults to root)
            indent (int): Current indentation level
        
        Returns:
            str: A string representation of the complete tree
        """
        if node is None:
            node = self.root

        result = [f"{node.label:<10} {node.node_description(indent)}"]

        for child in node.children:
            child_indent = indent + 4
            child_view = self.view_full_tree(child, child_indent)
            if child_view:  # Only add non-empty views
                result.extend(child_view.splitlines())

        return '\n'.join(result)

    def get_node(self, label: str) -> Optional[LLASTNode]:
        """Find and return a node by its label."""
        def _find_node(node: LLASTNode, target_label: str) -> Optional[LLASTNode]:
            if node.label == target_label:
                return node
            for child in node.children:
                result = _find_node(child, target_label)
                if result:
                    return result
            return None

        return _find_node(self.root, label)

    def write_changes(self):
        """Write changes only for modified files."""
        def _write_node(node: LLASTNode):
            if isinstance(node, FileNode):
                if hasattr(node, 'modified') and node.modified:
                    try:
                        node.write_to_file()
                    except Exception as e:
                        print(f"Error writing {node.path}: {str(e)}")
            for child in node.children:
                _write_node(child)

        _write_node(self.root)

    def update_node(self, label: str, new_code: str) -> str:
        """Update a node with new code."""
        node = self.get_node(label)
        if node is None:
            return f"Node with label {label} not found."

        try:
            # Parse the new code
            new_ast = ast.parse(new_code)
            print(f"Parsed new AST with {len(new_ast.body)} nodes of types: {[type(n).__name__ for n in new_ast.body]}")  # Debug
            
            if isinstance(node, FileNode):
                node.content = new_code
                node.children.clear()
                node.modified = True
                for i, ast_node in enumerate(new_ast.body):
                    child_node = LLASTNode.create_ast_node(ast_node, f"{label}.{i}")
                    if child_node:
                        node.add_child(child_node)
                return f"Updated file node {label}"

            elif isinstance(node, FunctionNode):
                if len(new_ast.body) == 1 and isinstance(new_ast.body[0], ast.FunctionDef):
                    node.update_from_ast(new_ast.body[0])
                    # Mark containing file as modified
                    current = node
                    while current.parent:
                        if isinstance(current.parent, FileNode):
                            current.parent.modified = True
                            break
                        current = current.parent
                    return f"Updated node {label}"
                else:
                    return "New code must be a single function definition"

            elif isinstance(node, (ClassNode, ControlFlowNode)):
                if len(new_ast.body) == 1 and (
                    (isinstance(node, ClassNode) and isinstance(new_ast.body[0], ast.ClassDef)) or
                    (isinstance(node, ControlFlowNode) and isinstance(new_ast.body[0], (ast.If, ast.For, ast.While, ast.With, ast.Try)))
                ):
                    node.update_from_ast(new_ast.body[0])
                    # Mark containing file as modified
                    current = node
                    while current.parent:
                        if isinstance(current.parent, FileNode):
                            current.parent.modified = True
                            break
                        current = current.parent
                    return f"Updated node {label}"
                else:
                    return f"New code must be a single {type(node).__name__.replace('Node', '').lower()} definition"

            elif isinstance(node, StatementNode):
                if len(new_ast.body) == 1:
                    new_node = LLASTNode.create_ast_node(new_ast.body[0], label)
                    if new_node:
                        if node.parent:
                            index = node.parent.children.index(node)
                            node.parent.children[index] = new_node
                            new_node.parent = node.parent
                            # Mark containing file as modified
                            current = new_node
                            while current.parent:
                                if isinstance(current.parent, FileNode):
                                    current.parent.modified = True
                                    break
                                current = current.parent
                        else:
                            self.root = new_node
                        return f"Updated node {label}"
                    else:
                        return "Failed to create new node"
                return "New code must be a single statement"

            elif isinstance(node, (StringStatementNode, AsyncFunctionNode, ComprehensionNode, 
                                MatchNode, CaseNode, ExceptNode, ElseNode, FinallyNode)):
                if len(new_ast.body) == 1:
                    # Create appropriate node type based on the new AST
                    new_node = LLASTNode.create_ast_node(new_ast.body[0], label)
                    if new_node and isinstance(new_node, type(node)):
                        if node.parent:
                            index = node.parent.children.index(node)
                            node.parent.children[index] = new_node
                            new_node.parent = node.parent
                            # Mark containing file as modified
                            current = new_node
                            while current.parent:
                                if isinstance(current.parent, FileNode):
                                    current.parent.modified = True
                                    break
                                current = current.parent
                        else:
                            self.root = new_node
                        return f"Updated node {label}"
                    else:
                        return f"New code must be a {type(node).__name__.replace('Node', '').lower()}"
                return "New code must be a single statement"

            else:
                return f"Cannot update node of type {type(node).__name__}"

        except SyntaxError as e:
            return f"Syntax error in provided code for node {label}: {str(e)}"
        except Exception as e:
            print(f"Exception during update: {str(e)}")  # Debug
            return f"Error updating node {label}: {str(e)}"

    def insert_child(self, label: str, code: str, filename: Optional[str] = None) -> str:
        """Insert new code as a child of the specified node."""
        parent_node = self.get_node(label)
        if parent_node is None:
            return f"Parent node with label {label} not found."

        if isinstance(parent_node, DirectoryNode) and filename is None:
            return "Filename is required when inserting into a directory."

        try:
            if filename:
                new_path = os.path.join(os.path.dirname(parent_node.path), filename)
                with open(new_path, 'w') as f:
                    f.write(code)
                new_node = FileNode(new_path, f"{label}.{len(parent_node.children)}")
                new_node.modified = True
            else:
                new_ast = ast.parse(code)
                new_node = LLASTNode.create_ast_node(new_ast.body[0], f"{label}.{len(parent_node.children)}")
                if not new_node:
                    return "Failed to create new node"

            parent_node.add_child(new_node)
            return f"Inserted new node with label {new_node.label}"

        except SyntaxError as e:
            return f"Syntax error in provided code: {str(e)}"
        except Exception as e:
            return f"Error inserting node: {str(e)}"

    def delete(self, label: str) -> str:
        """Delete a node and its corresponding file if applicable."""
        node = self.get_node(label)
        if node is None:
            return f"Node with label {label} not found."

        if node.parent is None:
            return "Cannot delete the root node."

        parent = node.parent
        parent.children.remove(node)
        
        if isinstance(node, FileNode):
            try:
                os.remove(node.path)
            except Exception as e:
                return f"Error deleting file {node.path}: {str(e)}"
        
        self._rebuild_labels(parent)
        return f"Deleted node with label {label}"

    def _rebuild_labels(self, node: LLASTNode):
        """Recursively rebuild labels after node deletion."""
        for i, child in enumerate(node.children):
            child.label = f"{node.label}.{i}"
            self._rebuild_labels(child)

import sys
import traceback
from functools import wraps
from typing import Any, Callable

def debug_on_error(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception:
            type, value, tb = sys.exc_info()
            traceback.print_exception(type, value, tb)
            print("\n--- Entering post-mortem debugging ---")
            import pdb
            pdb.post_mortem(tb)
    return wrapper

@debug_on_error
def main():
    """Test the LLAST implementation."""
    import tempfile

    with tempfile.TemporaryDirectory() as tmpdirname:
        # Create sample files
        with open(os.path.join(tmpdirname, "main.py"), "w") as f:
            f.write("""
def main():
    \"\"\"
    This is a multi-line docstring.
    It should be preserved exactly as it is.
    \"\"\"
    print("Hello, World!")

if __name__ == "__main__":
    main()
""")

        with open(os.path.join(tmpdirname, "utils.py"), "w") as f:
            f.write("""
def helper_function():
    return "I'm helping!"
""")

        # Create LLASTProject
        project = LLASTProject(tmpdirname)
        print("Initial project structure:")
        print(project.view_project())

        print("\nFull tree view:")
        print(project.view_full_tree())

        print("\nExpanded view of main.py:")
        print(project.expand("0.0"))

        print("\nInserting a new function into utils.py:")
        insert_result = project.insert_child("0.1", """
def new_function():
    \"\"\"This is a new function\"\"\"
    return "Hello from the new function!"
""")
        print(insert_result)
        print(project.expand("0.1"))

        print("\nUpdating the main function in main.py:")
        update_result = project.update_node("0.0.0", """
def main():
    \"\"\"
    This is an updated multi-line docstring.
    It should still be preserved exactly as it is.
    \"\"\"
    print("Hello, Updated World!")
""")
        print(update_result)
        print(project.expand("0.0.0"))

        print("\nDeleting the helper_function from utils.py:")
        delete_result = project.delete("0.1.0")
        print(delete_result)
        print(project.expand("0.1"))

        project.write_changes()
        print("\nChanges have been written to files.")

        print("\nFinal full tree structure:")
        print(project.view_full_tree())

if __name__ == "__main__":
    main()