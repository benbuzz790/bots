import os
import traceback
import textwrap


def view(file_path: str):
    """
    Display the contents of a file with line numbers.

    Parameters:
    - file_path (str): The path to the file to be viewed.

    Returns:
    A string containing the file contents with line numbers.
    """
    encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252', 'iso-8859-1'
        ]
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = file.readlines()
            numbered_lines = [f'{i + 1}:{line.rstrip()}' for i, line in
                enumerate(lines)]
            return '\n'.join(numbered_lines)
        except UnicodeDecodeError:
            continue
        except Exception as e:
            return f'Error: {str(e)}'
    return (
        f"Error: Unable to read file with any of the attempted encodings: {', '.join(encodings)}"
        )


def view_dir(start_path: str='.', output_file=None, target_extensions: str=
    "['py', 'txt', '.md']"):
    """
    Creates a summary of the directory structure starting from the given path, writing only files 
    with specified extensions. The output is written to a text file and returned as a string.

    Parameters:
    - start_path (str): The root directory to start scanning from.
    - output_file (str): The name of the file to optionally write the directory structure to.
    - target_extensions (str): String representation of a list of file extensions (e.g. "['py', 'txt']").

    Returns:
    str: A formatted string containing the directory structure, with each directory and file properly indented.

    Example output:
    my_project/
        module1/
            script.py
            README.md
        module2/
            utils.py
    """
    extensions_list = [ext.strip().strip('\'"') for ext in
        target_extensions.strip('[]').split(',')]
    extensions_list = [('.' + ext if not ext.startswith('.') else ext) for
        ext in extensions_list]
    output_text = []
    for root, dirs, files in os.walk(start_path):
        has_py = False
        for _, _, fs in os.walk(root):
            if any(f.endswith(tuple(extensions_list)) for f in fs):
                has_py = True
                break
        if has_py:
            level = root.replace(start_path, '').count(os.sep)
            indent = '    ' * level
            line = f'{indent}{os.path.basename(root)}/'
            output_text.append(line)
            subindent = '    ' * (level + 1)
            for file in files:
                if file.endswith(tuple(extensions_list)):
                    line = f'{subindent}{file}'
                    output_text.append(line)
    if output_file is not None:
        with open(output_file, 'w') as file:
            file.write(output_text)
    return '\n'.join(output_text)


def diff_edit(file_path: str, diff_spec: str):
    """Diff spec editing with flexible matching.

    Use when you need to make precision changes in text files.

    Parameters:
    - file_path (str): Path to the file to modify
    - diff_spec (str): Diff-style specification of changes

    Returns:
    str: Description of changes made/to be made or error message with context

    The diff spec uses a simplified format for precise text replacement:

    Key Rules:
    1. Format:
       - Lines to remove start with '-' (no space after, no tabs before)
       - Lines to add start with '+' (no space after, no tabs before)
       - TWO blank lines between separate changes
    2. Matching:
       - Whitespace-aware but flexible
       - Matches entire blocks exactly (all lines must match)
       - Best to include surrounding context for precision
    3. Order:
       - Changes applied sequentially
       - Each change: match -> remove -> add at same position
       - If no match found, provides context of nearest partial match

    Example 1: Simple import change
    ```
    -from typing import List
    +from typing import List, Optional
    ```

    Example 2: Class modification with context
    ```
    -class Calculator:
    -    def __init__(self):
    -        self.value = 0
    +class Calculator:
    +    #A simple calculator class.
    +    def __init__(self, initial_value: float = 0):
    +        self.value = initial_value
    ```

    Example 3: Function replacement preserving indentation
    ```
    -    def add(self, x):
    -        self.value += x
    -        return self.value
    +    def add(self, x: float) -> float:
    +        #Add a number to current value.
    +        self.value += x
    +        return self.value
    ```

    Example 4: Multiple separate changes (note double newline)
    ```
    -import os
    +import os.path


    -def process_file(filename):
    -    with open(filename) as f:
    +def process_file(filename: str) -> str:
    +    #Process a file and return its contents.
    +    with open(filename, encoding='utf-8') as f:
    ```

    Common Pitfalls:
    1. Missing exact indentation in match
    2. Not including enough context for unique matches
    3. Forgetting double newlines between changes
    4. Including line numbers from view() output
    """
    ignore_indentation: bool = True
    context_lines: int = 2
    try:
        encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252',
            'iso-8859-1']
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
            return (
                f"Error: Unable to read file with any of the attempted encodings: {', '.join(encodings)}"
                )
        if not diff_spec.strip():
            return 'Error: No changes specified'
        changes, errors = _parse_diff_spec(diff_spec=diff_spec)
        if errors:
            return 'Error parsing:' + '\n'.join(errors)
        original_lines = content.splitlines()
        current_lines = original_lines.copy()
        matched_changes = []
        unmatched_changes = []
        for remove, add in changes:
            match_found, line_num, prev_indent, match_score, best_index = (
                _find_matching_block(current_lines, remove, ignore_indentation)
                )
            if match_found:
                indented_add = _adjust_indentation(add, prev_indent)
                current_lines[line_num:line_num + len(remove)] = indented_add
                matched_changes.append(('\n'.join(remove), '\n'.join(
                    indented_add)))
            else:
                failure_context = ''
                if match_score > 0:
                    context = _get_context(current_lines, best_index,
                        context_lines)
                    failure_context = '\nNearest partial match found around:\n' + '\n'.join(context) + f"""
Match score: {match_score:.2f}"""
                    if ignore_indentation:
                        failure_context += (
                            '\n(Note: matching with ignore_indentation=True)')
                unmatched_changes.append(('\n'.join(remove), '\n'.join(add),
                    failure_context))
        if matched_changes:
            new_content = '\n'.join(current_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
        report = []
        report.append('Changes made:')
        if matched_changes:
            report.append(
                f'\nSuccessfully applied {len(matched_changes)} changes:')
            for old, new in matched_changes:
                report.append(f'\nChanged:\n{old}\nTo:\n{new}')
        if unmatched_changes:
            report.append(
                f'\nFailed to apply {len(unmatched_changes)} changes:')
            for old, new, context in unmatched_changes:
                report.append(f'\nCould not find:\n{old}')
        return '\n'.join(report) if report else 'No changes were applied'
    except Exception as e:
        return f'Error: {str(e)}\n{traceback.format_exc()}'


def _parse_diff_spec(diff_spec: str):
    changes = []
    remove = []
    add = []
    errors = []
    last_prefix = None
    diff_spec = textwrap.dedent(diff_spec)
    for line in diff_spec.splitlines():
        if not line:
            if add:
                changes.append((remove.copy(), add.copy()))
                remove.clear()
                add.clear()
                last_prefix = None
            continue
        if line.startswith('-'):
            last_prefix = '-'
            content = line[1:]
        elif line.startswith('+'):
            last_prefix = '+'
            content = line[1:]
        elif last_prefix is not None:
            content = line
        else:
            errors.append(
                f'Error: First line in a change block "{line}" does not start with + or -.'
                )
            continue
        if last_prefix == '-':
            remove.append(content)
        elif last_prefix == '+':
            add.append(content)
    if remove or add:
        changes.append((remove, add))
    if not changes and not errors:
        errors.append('Error: No valid changes found in diff spec')
    return changes, errors


def _find_matching_block(current_lines, remove_lines, ignore_indentation):
    """Find where a block of lines matches in the current file content.
    
    Args:
        current_lines: List of strings representing current file content
        remove_lines: List of strings to find in the file
        ignore_indentation: Whether to ignore leading whitespace when matching
    
    Returns:
        tuple (match_found: bool, line_num: int, indent: str, match_score: float, best_index: int)
        where:
        - match_found indicates if an exact match was found
        - line_num is the line where the match starts (or best partial match)
        - indent is the indentation to preserve
        - match_score indicates quality of best partial match (0-1)
        - best_index is the line number of best partial match
    """
    if not remove_lines:
        return True, len(current_lines), '', 1.0, len(current_lines)
    for i in range(len(current_lines) - len(remove_lines) + 1):
        current_block = current_lines[i:i + len(remove_lines)]
        if ignore_indentation:
            match = all(c.strip() == o.strip() for c, o in zip(
                current_block, remove_lines))
        else:
            match = all(c == o for c, o in zip(current_block, remove_lines))
        if match:
            return True, i, _get_indentation(current_lines[i]), 1.0, i
    best_match_score = 0
    best_match_index = 0
    for i in range(len(current_lines) - len(remove_lines) + 1):
        current_block = current_lines[i:i + len(remove_lines)]
        match_score = _calculate_block_match_score(current_block,
            remove_lines, ignore_indentation)
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_index = i
    return False, best_match_index, _get_indentation(current_lines[
        best_match_index]), best_match_score, best_match_index


def _get_indentation(line):
    """Extract the leading whitespace from a line."""
    return line[:len(line) - len(line.lstrip())]


def _adjust_indentation(lines, target_indent):
    """Adjust indentation of a block of lines to match target_indent."""
    if not lines:
        return lines
    non_empty_lines = [l for l in lines if l.strip()]
    if not non_empty_lines:
        return lines
    min_indent = min(len(_get_indentation(l)) for l in non_empty_lines)
    adjusted = []
    for line in lines:
        if not line.strip():
            adjusted.append(line)
        else:
            stripped = line[min_indent:]
            adjusted.append(target_indent + stripped)
    return adjusted


def _get_context(lines, center_idx, context_size):
    """Get context lines around an index with line numbers."""
    start = max(0, center_idx - context_size)
    end = min(len(lines), center_idx + context_size + 1)
    return [f'{i + 1}: {line}' for i, line in enumerate(lines[start:end],
        start)]


def _calculate_block_match_score(current_block, old_lines, ignore_indentation):
    """Calculate how well two blocks match, returning a score and matching line indices."""
    if ignore_indentation:
        current_joined = ' '.join(l.strip() for l in current_block)
        old_joined = ' '.join(l.strip() for l in old_lines)
        current_stripped = [c.strip() for c in current_block]
        old_stripped = [o.strip() for o in old_lines]
    else:
        current_joined = ' '.join(current_block)
        old_joined = ' '.join(old_lines)
        current_stripped = current_block
        old_stripped = old_lines
    exact_matches = sum(1 for c, o in zip(current_stripped, old_stripped) if
        c == o)
    if current_joined == old_joined:
        return len(current_block) * 3
    c_words = set(current_joined.split())
    o_words = set(old_joined.split())
    word_matches = len(c_words.intersection(o_words))
    partial_score = 0
    if word_matches > 0:
        partial_score = word_matches / max(len(c_words), len(o_words))
        if word_matches == len(c_words) and word_matches == len(o_words):
            partial_score *= 2
    total_score = exact_matches * 2 + partial_score
    return total_score


def _has_line_number_prefix(line: str) ->bool:
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


def _strip_line_number(line: str) ->str:
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


def overwrite(file_path: str, content: str):
    """
    ⚠️ CAUTION: This is a last-resort tool. Only use when more efficient tools have failed.

    Parameters:
    - file_path (str): Path to the file to overwrite
    - content (str): New content to write to the file

    Returns:
    str: Success message or error details
    """
    try:
        used_encoding = 'utf-8'
        if os.path.exists(file_path):
            encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252',
                'iso-8859-1']
            for encoding in encodings:
                try:
                    with open(file_path, 'r', encoding=encoding) as f:
                        f.read()
                        used_encoding = encoding
                        break
                except UnicodeDecodeError:
                    continue
        with open(file_path, 'w', encoding=used_encoding) as f:
            f.write(content)
        return (
            f'⚠️ File overwritten successfully using {used_encoding} encoding.'
            )
    except Exception as e:
        return f'Error: {str(e)}\n{traceback.format_exc()}'
