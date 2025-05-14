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
    1. dedent the entire block to normalize its internal structure
    2. indent the whole block to match target location
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
        """Adjust indentation of a block of lines.
        Preserves relative indentation while aligning to match location.
        """
        if not lines:
            return lines
        block = '\n'.join(lines)
        dedented = textwrap.dedent(block)
        indented = textwrap.indent(dedented, self.match_indent)
        return indented.splitlines()

def _determine_next_state(line: str, current_state: DiffState) -> DiffState:
    """Determine the next state based on the current line and state."""
    print(f'\nDEBUG _determine_next_state:')
    print(f"Line: '{line}'")
    print(f'Current state: {current_state}')
    if line.startswith('@@'):
        print('Found header')
        return DiffState.HEADER
    elif line.startswith('-'):
        print('Found removal')
        return DiffState.REMOVE
    elif line.startswith('+'):
        print('Found addition')
        return DiffState.ADD
    else:
        print('Found context')
        return DiffState.CONTEXT

def _process_line(line: str, progress: DiffProgress) -> str:
    """Process a single line from the diff spec and update state."""
    if line.startswith(('-', '+')):
        return line[1:]
    return line

def _find_matching_block(file_lines: List[str], progress: DiffProgress) -> tuple[int, IndentationContext]:
    """Find the position where a block matches in the file content."""
    print('\nDEBUG _find_matching_block:')
    print(f'File lines: {file_lines}')
    print(f'Context lines: {progress.context_lines}')
    print(f'Pending remove: {progress.pending_remove}')
    if not progress.pending_remove:
        print('No pending remove lines')
        ctx = IndentationContext()
        if file_lines:
            ctx.match_indent = _get_indentation(file_lines[-1])
        return (len(file_lines), ctx)

    def normalize_line(line: str) -> str:
        """Strip whitespace for content comparison"""
        return line.strip()

    def get_surrounding_context(lines: List[str], pos: int, context_lines: int=3) -> str:
        """Get lines before and after position for context"""
        start = max(0, pos - context_lines)
        end = min(len(lines), pos + context_lines + 1)
        return '\n'.join(lines[start:end])
    all_matches = []
    if progress.context_lines:
        print('\nChecking with context lines:')
        context_len = len(progress.context_lines)
        remove_len = len(progress.pending_remove)
        context_positions = []
        for i in range(len(file_lines) - context_len + 1):
            test_lines = file_lines[i:i + context_len]
            print(f'\nTesting context at pos {i}:')
            print(f'  File slice: {test_lines}')
            print(f'  Context lines: {progress.context_lines}')
            if all((normalize_line(a) == normalize_line(b) for a, b in zip(test_lines, progress.context_lines))):
                print('  Context match found!')
                context_positions.append(i)
        print(f'\nFound context positions: {context_positions}')
        for pos in context_positions:
            remove_pos = pos + context_len
            if remove_pos + remove_len <= len(file_lines):
                test_lines = file_lines[remove_pos:remove_pos + remove_len]
                print(f'\nTesting remove at pos {remove_pos}:')
                print(f'  File slice: {test_lines}')
                print(f'  Remove lines: {progress.pending_remove}')
                if all((normalize_line(a) == normalize_line(b) for a, b in zip(test_lines, progress.pending_remove))):
                    print('  Remove match found!')
                    match_indent = _get_indentation(file_lines[remove_pos])
                    broader_context = get_surrounding_context(file_lines, remove_pos)
                    match_info = {'position': pos, 'remove_position': remove_pos, 'indent': match_indent, 'context': broader_context}
                    all_matches.append(match_info)
    else:
        print('\nChecking without context lines:')
        for i in range(len(file_lines) - len(progress.pending_remove) + 1):
            test_lines = file_lines[i:i + len(progress.pending_remove)]
            print(f'\nTesting at pos {i}:')
            print(f'  File slice: {test_lines}')
            print(f'  Remove lines: {progress.pending_remove}')
            if all((normalize_line(a) == normalize_line(b) for a, b in zip(test_lines, progress.pending_remove))):
                print('  Match found!')
                match_indent = _get_indentation(file_lines[i])
                broader_context = get_surrounding_context(file_lines, i)
                match_info = {'position': i, 'remove_position': i, 'indent': match_indent, 'context': broader_context}
                all_matches.append(match_info)
    print(f'\nTotal matches found: {len(all_matches)}')
    if len(all_matches) == 0:
        print('No matches found')
        progress.last_match_score = 0
        progress.error_context = []
        progress.error_type = DiffErrorType.NO_MATCH
        return (-1, IndentationContext())
    elif len(all_matches) == 1:
        print('Single match found')
        match = all_matches[0]
        ctx = IndentationContext.from_diff_lines(progress.pending_add, match['indent'])
        progress.error_type = DiffErrorType.NONE
        progress.last_match_position = match['remove_position']
        progress.context_match_position = match['position']
        return (match['remove_position'], ctx)
    else:
        print('Multiple matches found')
        match_details = []
        for i, m in enumerate(all_matches):
            context_lines = m['context'].split('\n')
            match_details.append(f"Match {i + 1} in:\n{m['context']}")
        progress.error_context = ['More than one match found:', 'Please provide more context to disambiguate between:', *match_details]
        progress.error_type = DiffErrorType.AMBIGUOUS_MATCH
        progress.last_match_score = 1.0
        return (-1, IndentationContext())

def _process_state_transition(progress: DiffProgress, file_lines: List[str]) -> Optional[str]:
    """Handle state transitions and return error message if any.
    Preserves indentation structure from the diff spec, adjusted to match
    the nesting level where we found the block in the original file.
    """
    print('\nDEBUG _process_state_transition:')
    print(f'Current state: {progress.state}')
    print(f'Current block: {progress.current_block}')
    print(f'Context lines: {progress.context_lines}')
    print(f'Pending remove: {progress.pending_remove}')
    print(f'Pending add: {progress.pending_add}')
    print(f'Last match position: {progress.last_match_position}')
    if not progress.current_block:
        print('No current block')
        return None
    if progress.state == DiffState.CONTEXT:
        print('Processing CONTEXT state')
        progress.context_lines = [line for line in progress.current_block if line.strip()]
        progress.context_line_numbers = list(range(progress.block_start_line, progress.block_start_line + len(progress.current_block)))
    elif progress.state == DiffState.REMOVE:
        print('Processing REMOVE state')
        if progress.pending_remove is None:
            progress.pending_remove = []
        progress.pending_remove.extend(progress.current_block)
        print(f'Accumulated remove lines: {progress.pending_remove}')
    elif progress.state == DiffState.ADD:
        print('Processing ADD state')
        if progress.pending_add is None:
            progress.pending_add = []
        progress.pending_add.extend(progress.current_block)
        print(f'Accumulated add lines: {progress.pending_add}')
        if progress.pending_remove:
            print('Processing block replacement')
            match_pos, ctx = _find_matching_block(file_lines, progress)
            if match_pos < 0:
                return progress.format_error_message()
            progress.last_match_position = match_pos
            progress.last_match_context = ctx
            adjusted_lines = ctx.adjust_lines(progress.pending_add)
            file_lines[match_pos:match_pos + len(progress.pending_remove)] = adjusted_lines
            progress.pending_remove = None
            progress.pending_add = None
        elif progress.pending_add and hasattr(progress, 'last_match_position'):
            print('Processing block insertion')
            adjusted_lines = progress.last_match_context.adjust_lines(progress.pending_add)
            insert_pos = progress.last_match_position + 1
            file_lines[insert_pos:insert_pos] = adjusted_lines
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

def diff_edit(file_path: str, diff_spec: str) -> str:
    """Apply a diff specification to a file.
    Args:
        file_path: Path to the file to modify
        diff_spec: Diff specification in unified diff format
    Returns:
        A message describing what changes were made
    """
    try:
        used_encoding = 'utf-8'
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            used_encoding = 'utf-8-sig'
            with open(file_path, 'r', encoding='utf-8-sig') as f:
                content = f.read()
        file_lines = content.split('\n')
        original_content = '\n'.join(file_lines)
        changes_applied = 0
        changes_failed = 0
        error_messages = []
        diff_blocks = split_diff_blocks(diff_spec)
        for block in diff_blocks:
            progress = DiffProgress()
            current_state = DiffState.CONTEXT
            print('\nProcessing diff block:')
            print(block)
            for line in block.split('\n'):
                next_state = _determine_next_state(line, current_state)
                if next_state != DiffState.HEADER:
                    progress.state = next_state
                    progress.current_block.append(_process_line(line, progress))
                    error = _process_state_transition(progress, file_lines)
                    if error:
                        error_messages.append(error)
                        changes_failed += 1
                        break
                current_state = next_state
                progress.line_number += 1
            if progress.current_block:
                error = _process_state_transition(progress, file_lines)
                if error:
                    error_messages.append(error)
                    changes_failed += 1
        new_content = '\n'.join(file_lines)
        if new_content != original_content:
            changes_applied += 1
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
        if changes_failed > 0:
            return 'Failed to apply some changes:\n' + '\n'.join(error_messages)
        elif changes_applied > 0:
            return f'Successfully applied {changes_applied} changes'
        else:
            return 'No changes were applied'
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

def get_block_context(file_lines: List[str], pos: int, context_lines: int=3) -> str:
    """Get broader context around a position, including function/class definitions.

    Args:
        file_lines: List of lines from the file
        pos: Position to get context around
        context_lines: Number of lines of context to include before and after

    Returns:
        String containing the context, including any relevant function/class definitions
    """
    start = max(0, pos - context_lines)
    end = min(len(file_lines), pos + context_lines + 1)
    context = []
    for i in range(pos - 1, max(-1, pos - 10), -1):
        if i < 0:
            break
        line = file_lines[i].strip()
        if line.startswith('def ') or line.startswith('class '):
            context.append(file_lines[i])
            break
    context.extend(file_lines[start:end])
    return '\n'.join(context)

def split_diff_blocks(diff: str) -> List[str]:
    """Split a multi-block diff into individual change blocks.

    A block is a sequence of removals (-) and additions (+) that belong together.
    Blocks are separated by:
    - Context lines (lines without - or +)
    - Blank lines
    - Or when we see a new removal (-) after seeing additions (+)

    Args:
        diff: The complete diff string

    Returns:
        List of individual diff blocks
    """
    blocks = []
    current_block = []
    saw_addition = False
    for line in diff.split('\n'):
        line = line.rstrip()
        if not line:
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
                saw_addition = False
            continue
        if not line.startswith(('-', '+')):
            if current_block:
                blocks.append('\n'.join(current_block))
                current_block = []
                saw_addition = False
            continue
        if line.startswith('-') and saw_addition and current_block:
            blocks.append('\n'.join(current_block))
            current_block = []
            saw_addition = False
        current_block.append(line)
        if line.startswith('+'):
            saw_addition = True
    if current_block:
        blocks.append('\n'.join(current_block))
    return blocks