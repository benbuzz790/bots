import os
import traceback
import textwrap
from dataclasses import dataclass
from enum import Enum, auto
from typing import Optional, List, Dict, Tuple

class DiffState(Enum):
    HEADER = auto()
    CONTEXT = auto()
    REMOVE = auto()
    ADD = auto()

class DiffErrorType(Enum):
    """Types of errors that can occur during diff application"""
    NONE = auto()
    CONTEXT_NOT_FOUND = auto()
    NO_MATCH = auto()
    AMBIGUOUS_MATCH = auto()

@dataclass
class DiffProgress:
    state: DiffState = DiffState.CONTEXT
    line_number: int = 0
    context_lines: List[str] = None
    context_line_numbers: List[int] = None
    current_block: List[str] = None
    block_start_line: int = 0
    pending_remove: Optional[List[str]] = None
    pending_add: Optional[List[str]] = None
    last_match_position: int = 0
    last_match_score: float = 0.0
    error_type: DiffErrorType = DiffErrorType.NONE
    error_context: List[str] = None

    def __post_init__(self):
        self.context_lines = []
        self.context_line_numbers = []
        self.current_block = []
        self.error_context = []

    def format_error_message(self) -> str:
        """Generate detailed error message based on current state"""
        if self.error_type == DiffErrorType.CONTEXT_NOT_FOUND:
            return 'Required pre-context not found'
        elif self.error_type == DiffErrorType.NO_MATCH:
            return f'Could not find lines to remove at line {self.line_number}'
        elif self.error_type == DiffErrorType.AMBIGUOUS_MATCH:
            return '\n'.join(self.error_context)
        return f'Failed to apply changes at line {self.line_number}'
    error_type: DiffErrorType = DiffErrorType.NONE
    error_context: List[str] = None

    def __post_init__(self):
        self.context_lines = []
        self.context_line_numbers = []
        self.current_block = []
        self.error_context = []

    def format_error_message(self) -> str:
        """Generate detailed error message based on current state"""
        if self.error_type == DiffErrorType.CONTEXT_NOT_FOUND:
            return 'Required pre-context not found'
        elif self.error_type == DiffErrorType.NO_MATCH:
            return f'Could not find lines to remove at line {self.line_number}'
        elif self.error_type == DiffErrorType.AMBIGUOUS_MATCH:
            return '\n'.join(self.error_context)
        return f'Failed to apply changes at line {self.line_number}'

@dataclass
class IndentationContext:
    """Handles indentation for diff blocks using textwrap.

    Process:
    1. textwrap.dedent the add block to normalize structure
    2. determine target indentation from match location
    3. textwrap.indent to match the target level
    """
    match_indent: str = ''

    @staticmethod
    def from_diff_lines(lines: List[str], match_location_indent: str='') -> 'IndentationContext':
        """Create indentation context from diff spec lines.

        Args:
            lines: The lines from the diff spec (+ or - stripped)
            match_location_indent: Where the block was found in original file
        """
        ctx = IndentationContext()
        ctx.match_indent = match_location_indent
        return ctx

    def adjust_lines(self, lines: List[str]) -> List[str]:
        """Adjust indentation of lines to match target location.

        1. Dedents the block to normalize structure
        2. Indents entire block to match target location
        """
        if not lines:
            return lines
        dedented = textwrap.dedent('\n'.join(lines)).splitlines()
        indented = [self.match_indent + line if line.strip() else line for line in dedented]
        return indented

def _determine_next_state(line: str, current_state: DiffState) -> DiffState:
    """Determine the next state based on the current line and state."""
    if line.startswith('@@'):
        return DiffState.HEADER
    elif line.startswith('-'):
        return DiffState.REMOVE
    elif line.startswith('+'):
        return DiffState.ADD
    else:
        return DiffState.CONTEXT

def _process_line(line: str, progress: DiffProgress) -> str:
    """Process a single line from the diff spec and update state."""
    if line.startswith(('-', '+')):
        return line[1:]
    return line

def _find_matching_block(file_lines: List[str], progress: DiffProgress) -> tuple[int, IndentationContext]:
    """Find the position where a block matches in the file content."""
    if not progress.pending_remove:
        ctx = IndentationContext()
        if file_lines:
            ctx.match_indent = _get_indentation(file_lines[-1])
        return (len(file_lines), ctx)

    def normalize_line(line: str) -> str:
        """Strip whitespace for content comparison"""
        return line.strip()
    all_matches = []
    if progress.context_lines:
        context_len = len(progress.context_lines)
        remove_len = len(progress.pending_remove)
        context_matches = []
        for i in range(len(file_lines) - context_len + 1):
            if all((normalize_line(a) == normalize_line(b) for a, b in zip(file_lines[i:i + context_len], progress.context_lines))):
                context_matches.append(i)
        for context_pos in context_matches:
            max_search = len(file_lines) - remove_len + 1
            for remove_start in range(context_pos + context_len, max_search):
                remove_block = file_lines[remove_start:remove_start + remove_len]
                if all((normalize_line(a) == normalize_line(b) for a, b in zip(remove_block, progress.pending_remove))):
                    match_indent = _get_indentation(file_lines[remove_start])
                    context_start = max(0, context_pos - 1)
                    context_end = min(len(file_lines), remove_start + remove_len + 1)
                    match_info = {'position': context_pos, 'remove_position': remove_start, 'indent': match_indent, 'context': '\n'.join(file_lines[context_start:context_end])}
                    all_matches.append(match_info)
                    break
        if not all_matches and context_matches:
            best_pos = context_matches[-1]
            progress.last_match_score = 1.0
            progress.last_match_position = best_pos
            progress.context_match_position = best_pos
            progress.error_context = file_lines[best_pos:best_pos + context_len + 2]
            progress.error_type = DiffErrorType.CONTEXT_NOT_FOUND
            return (-1, IndentationContext())
        elif not all_matches:
            best_score = 0
            best_pos = 0
            for i in range(len(file_lines) - context_len + 1):
                score = sum((1 for a, b in zip(file_lines[i:i + context_len], progress.context_lines) if normalize_line(a) == normalize_line(b))) / context_len
                if score > best_score:
                    best_score = score
                    best_pos = i
            progress.last_match_score = best_score
            progress.last_match_position = best_pos
            progress.context_match_position = best_pos
            progress.error_context = file_lines[best_pos:best_pos + context_len + 2]
            progress.error_type = DiffErrorType.CONTEXT_NOT_FOUND
            return (-1, IndentationContext())
    else:
        for i in range(len(file_lines) - len(progress.pending_remove) + 1):
            block = file_lines[i:i + len(progress.pending_remove)]
            if all((normalize_line(a) == normalize_line(b) for a, b in zip(block, progress.pending_remove))):
                match_indent = _get_indentation(file_lines[i])
                context_start = max(0, i - 1)
                context_end = min(len(file_lines), i + len(progress.pending_remove) + 1)
                match_info = {'position': i, 'remove_position': i, 'indent': match_indent, 'context': '\n'.join(file_lines[context_start:context_end])}
                all_matches.append(match_info)
    if len(all_matches) == 0:
        progress.last_match_score = 0
        progress.error_context = []
        progress.error_type = DiffErrorType.NO_MATCH
        return (-1, IndentationContext())
    elif len(all_matches) == 1:
        match = all_matches[0]
        ctx = IndentationContext.from_diff_lines(progress.pending_add, match['indent'])
        progress.error_type = DiffErrorType.NONE
        progress.last_match_position = match['remove_position']
        progress.context_match_position = match['position']
        return (match['remove_position'], ctx)
    else:
        unique_contexts = {m['context'] for m in all_matches}
        if len(unique_contexts) == 1:
            match_details = [f"Match {i + 1}:\n{m['context']}" for i, m in enumerate(all_matches)]
            progress.error_context = ['More than one match found:', 'Please provide more context to disambiguate between:', *match_details]
            progress.error_type = DiffErrorType.AMBIGUOUS_MATCH
            progress.last_match_score = 1.0
            return (-1, IndentationContext())
        else:
            match = all_matches[0]
            ctx = IndentationContext.from_diff_lines(progress.pending_add, match['indent'])
            progress.error_type = DiffErrorType.NONE
            progress.last_match_position = match['remove_position']
            progress.context_match_position = match['position']
            return (match['remove_position'], ctx)

def _process_state_transition(progress: DiffProgress, file_lines: List[str]) -> Optional[str]:
    """Handle state transitions and return error message if any.

    Preserves indentation structure from the diff spec, adjusted to match
    the nesting level where we found the block in the original file.
    """
    if not progress.current_block:
        return None
    if progress.state == DiffState.CONTEXT:
        progress.context_lines = [line for line in progress.current_block if line.strip()]
        progress.context_line_numbers = list(range(progress.block_start_line, progress.block_start_line + len(progress.current_block)))
    elif progress.state == DiffState.REMOVE:
        progress.pending_remove = progress.current_block.copy()
        progress.pending_add = None
    elif progress.state == DiffState.ADD:
        progress.pending_add = progress.current_block.copy()
        if progress.pending_remove:
            match_pos, ctx = _find_matching_block(file_lines, progress)
            if match_pos < 0:
                return progress.format_error_message()
            adjusted_lines = ctx.adjust_lines(progress.pending_add)
            file_lines[match_pos:match_pos + len(progress.pending_remove)] = adjusted_lines
            progress.pending_remove = None
            progress.pending_add = None
    progress.current_block = []
    return None

def view(file_path: str, max_lines: str=2500):
    """
    Display the contents of a file with line numbers.

    Parameters:
    - file_path (str): The path to the file to be viewed.
    - max_lines (int, optional): Maximum number of lines to display. Defaults to 2500.

    Returns:
    A string containing the file contents with line numbers.

    cost: varies
    """
    max_lines = int(max_lines)
    encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252', 'iso-8859-1']
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = file.readlines()
                if len(lines) > max_lines:
                    return f'Error: File has {len(lines)} lines, which exceeds the maximum of {max_lines} lines.'
                numbered_lines = [f'{i + 1}:{line.rstrip()}' for i, line in enumerate(lines)]
                return '\n'.join(numbered_lines)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f'Error: {str(e)}'
    return f"Error: Unable to read file with any of the attempted encodings: {', '.join(encodings)}"

def view_dir(start_path: str='.', output_file=None, target_extensions: str="['py', 'txt', 'md']"):
    """Creates a summary of the directory structure starting from the given path.

    Use when you need to:
    - Get an overview of a directory's structure
    - Filter files by extension
    - Handle venv directories specially

    Parameters:
    - start_path (str): The root directory to start scanning from.
    - output_file (str): The name of the file to optionally write the directory structure to.
    - target_extensions (str): String representation of a list of file extensions or patterns.
        Supports:
        - Specific extensions: "['py', 'txt']"
        - Wildcard for all files: "['*']"
        - Extension patterns: "['*.py']"

    Returns:
    str: A formatted string containing the directory structure, with each directory and file properly indented.

    Example output:
    my_project/
        venv/
        module1/
            script.py
            README.md
        module2/
            utils.py

    cost: low
    """
    import fnmatch
    extensions_list = [ext.strip().strip('\'"') for ext in target_extensions.strip('[]').split(',')]
    show_all = '*' in extensions_list
    extensions_list = ['.' + ext if not ext.startswith('.') and (not ext.startswith('*.')) else ext for ext in extensions_list]

    def matches_pattern(filename, patterns):
        """Check if filename matches any of the patterns"""
        if show_all:
            return True
        for pattern in patterns:
            if pattern.startswith('*.'):
                if fnmatch.fnmatch(filename, pattern):
                    return True
            elif filename.endswith(pattern):
                return True
        return False
    output_text = []
    start_path = os.path.abspath(start_path)
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = '    ' * level
        basename = os.path.basename(root) or os.path.basename(start_path)
        is_venv = basename in ['venv', 'env', '.env'] or 'pyvenv.cfg' in files
        if is_venv:
            line = f'{indent}{basename}/'
            output_text.append(line)
            dirs[:] = []
            continue
        has_relevant_files = False
        if show_all:
            has_relevant_files = bool(files)
        else:
            for _, _, fs in os.walk(root):
                if any((matches_pattern(f, extensions_list) for f in fs)):
                    has_relevant_files = True
                    break
        if has_relevant_files:
            if root != start_path:
                line = f'{indent}{basename}/'
                output_text.append(line)
            subindent = '    ' * (level + 1)
            for file in sorted(files):
                if matches_pattern(file, extensions_list):
                    line = f'{subindent}{file}'
                    output_text.append(line)
    if output_file is not None:
        with open(output_file, 'w') as file:
            file.write('\n'.join(output_text))
    return '\n'.join(output_text)

def diff_edit(file_path: str, diff_spec: str):
    """Diff spec editing with flexible matching and git-style diff support.

    Use when you need to make precision changes in text files. Accepts both strict +/- format
    and git-style diffs with context lines and @@ headers.

    Parameters:
    - file_path (str): Path to the file to modify
    - diff_spec (str): Diff-style specification of changes.
        Supports:
        - Lines beginning with '-' for removal
        - Lines beginning with '+' for addition
        - Git-style context lines (used for location matching)
        - @@ headers (ignored)
        Whitespace must match exactly in the content after +/-.

    Returns:
    str: Description of changes made/to be made or error message with context

    Examples:
    1. Simple change:
        -import numpy
        +import scipy

    2. Git-style diff with context:
        @@ -1,3 +1,3 @@
         import os
        -import numpy
        +import scipy
         import pandas

    3. Function replacement:
        -    def old_function():
        +    def new_function():
        +        # New implementation
        +        return True

    cost: low
    """
    try:
        progress = DiffProgress()
        encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252', 'iso-8859-1']
        content = None
        used_encoding = 'utf-8'
        if not os.path.exists(file_path):
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write('')
            content = ''
        else:
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as file:
                        content = file.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
        if content is None:
            return f"Error: Unable to read file with any of the attempted encodings: {', '.join(encodings)}"
        if not diff_spec.strip():
            return 'Error: No changes specified'
        file_lines = content.splitlines()
        changes_applied = 0
        changes_failed = 0
        error_messages = []
        diff_spec = textwrap.dedent(diff_spec)
        for line in diff_spec.splitlines():
            if not line.strip():
                continue
            next_state = _determine_next_state(line, progress.state)
            if next_state != progress.state:
                error = _process_state_transition(progress, file_lines)
                if error:
                    error_messages.append(error)
                    changes_failed += 1
                elif progress.state == DiffState.ADD:
                    changes_applied += 1
                progress.state = next_state
                progress.block_start_line = progress.line_number
            processed_line = _process_line(line, progress)
            if next_state != DiffState.HEADER:
                progress.current_block.append(processed_line)
            progress.line_number += 1
        if progress.current_block:
            error = _process_state_transition(progress, file_lines)
            if error:
                error_messages.append(error)
                changes_failed += 1
            elif progress.state == DiffState.ADD:
                changes_applied += 1
        if changes_applied > 0:
            new_content = '\n'.join(file_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
        report = ['Changes made:']
        if changes_applied > 0:
            report.append(f'\nSuccessfully applied {changes_applied} changes')
        if changes_failed > 0:
            report.append(f'\nFailed to apply {changes_failed} changes:')
            report.extend(error_messages)
        return '\n'.join(report) if len(report) > 1 else 'No changes were applied'
    except Exception as e:
        return f'Error: {str(e)}\n{traceback.format_exc()}'

def _get_indentation(line):
    """Extract the leading whitespace from a line."""
    return line[:len(line) - len(line.lstrip())]

def _get_context(lines, center_idx, context_size):
    """Get context lines around an index with line numbers."""
    start = max(0, center_idx - context_size)
    end = min(len(lines), center_idx + context_size + 1)
    return [f'{i + 1}: {line}' for i, line in enumerate(lines[start:end], start)]

def _has_line_number_prefix(line: str) -> bool:
    """Check if a string starts with a line number format (e.g., '123:' or '  123:')
    Args:
        line (str): The line to check
    Returns:
        bool: True if the line starts with a number followed by a colon
    """
    stripped = line.lstrip()
    if ':' not in stripped:
        return False
    prefix = stripped.split(':', 1)[0]
    try:
        int(prefix)
        return True
    except ValueError:
        return False

def _strip_line_number(line: str) -> str:
    """Remove line number prefix if present (e.g., '123:content' or '  123:content' becomes 'content')
    Preserves any leading whitespace before the line number.
    Args:
        line (str): The line to process
    Returns:
        str: The line with any line number prefix removed
    """
    if not _has_line_number_prefix(line):
        return line
    whitespace = line[:len(line) - len(line.lstrip())]
    stripped = line.lstrip()
    content = stripped.split(':', 1)[1]
    return whitespace + content

def _document_indentation_rules():
    """Indentation Rules for diff_edit

    The diff_edit function follows these rules for indentation:

    1. Block Matching:
       - Blocks are matched ignoring indentation differences
       - e.g., "    if True:" matches "if True:" in the diff spec

    2. Indentation Preservation:
       - The absolute indentation level of the matched block sets the base level
       - e.g., if we match a block at 8 spaces, the replacement starts at 8 spaces

    3. Relative Indentation:
       - Lines within the new block maintain their relative indentation
       - e.g., if new content has a 4-space indent from its base, it becomes base+4

    Examples:

    Original:
        class MyClass:
            def method():
                if True:
                    print("hello")
                    print("world")

    Diff spec:
        -    if True:
        -        print("hello")
        -        print("world")
        +    if False:
        +        print("goodbye")
        +        if True:
        +            print("nested")

    Result:
        class MyClass:
            def method():
                if False:           # Maintains original 8-space level
                    print("goodbye")  # 12 spaces (base + 4)
                    if True:         # 12 spaces
                        print("nested") # 16 spaces (base + 8)

    Key Points:
    1. The indentation in the diff spec is used only for relative relationships
    2. The absolute indentation level is determined by the matched block
    3. All new lines are adjusted relative to the base indentation
    4. Empty lines and comments maintain their position in the structure
    """
    pass

class DiffErrorType(Enum):
    """Types of errors that can occur during diff application"""
    NONE = auto()
    CONTEXT_NOT_FOUND = auto()
    NO_MATCH = auto()
    AMBIGUOUS_MATCH = auto()