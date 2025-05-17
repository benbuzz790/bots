import os
import traceback
import textwrap
import difflib

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
    """
    Creates a summary of the directory structure starting from the given path, writing only files
    with specified extensions and showing venv directories without their contents.

    Parameters:
    - start_path (str): The root directory to start scanning from.
    - output_file (str): The name of the file to optionally write the directory structure to.
    - target_extensions (str): String representation of a list of file extensions (e.g. "['py', 'txt']").

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
    extensions_list = [ext.strip().strip('\'"') for ext in target_extensions.strip('[]').split(',')]
    extensions_list = ['.' + ext if not ext.startswith('.') else ext for ext in extensions_list]
    output_text = []
    for root, dirs, files in os.walk(start_path):
        level = root.replace(start_path, '').count(os.sep)
        indent = '    ' * level
        basename = os.path.basename(root)
        is_venv = basename in ['venv', 'env', '.env'] or 'pyvenv.cfg' in files
        if is_venv:
            line = f'{indent}{basename}/'
            output_text.append(line)
            dirs[:] = []
            continue
        has_relevant_files = False
        for _, _, fs in os.walk(root):
            if any((f.endswith(tuple(extensions_list)) for f in fs)):
                has_relevant_files = True
                break
        if has_relevant_files:
            line = f'{indent}{basename}/'
            output_text.append(line)
            subindent = '    ' * (level + 1)
            for file in files:
                if file.endswith(tuple(extensions_list)):
                    line = f'{subindent}{file}'
                    output_text.append(line)
    if output_file is not None:
        with open(output_file, 'w') as file:
            file.write('\n'.join(output_text))
    return '\n'.join(output_text)

def apply_git_patch(file_path: str, patch_content: str):
    """
    Apply a git-style unified diff patch to a file.
    Creates the file if it doesn't exist.

    Parameters:
    - file_path (str): Path to the file to modify (supports both / and \\ separators)
    - patch_content (str): Unified diff format patch content

    Returns:
    str: Description of changes made or error message

    cost: low
    """
    try:
        file_path = _normalize_path(file_path)
        encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252', 'iso-8859-1']
        content = None
        used_encoding = 'utf-8'
        dir_path = os.path.dirname(file_path)
        if dir_path:
            os.makedirs(dir_path, exist_ok=True)
        if not os.path.exists(file_path):
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
        if content is None and os.path.exists(file_path):
            return f"Error: Unable to read existing file with any of the attempted encodings: {', '.join(encodings)}"
        if not patch_content.strip():
            return 'Error: patch_content is empty.'
        original_lines = content.splitlines() if content else []
        current_lines = original_lines.copy()
        changes_made = []
        line_offset = 0
        hunks = patch_content.split('\n@@')[1:]
        if not hunks:
            return 'Error: No valid patch hunks found. (No instances of "\\n@@")'
        for hunk in hunks:
            hunk = hunk.strip()
            if not hunk:
                continue
            try:
                header_end = hunk.index('\n')
                header = hunk[:header_end].strip()
                if not header.endswith('@@'):
                    header = header + ' @@'
                old_range, new_range = header.rstrip(' @').split(' +')
                old_start = int(old_range.split(',')[0].lstrip('- '))
                new_start = int(new_range.split(',')[0])
                hunk_lines = _normalize_header_lines(hunk[header_end:].splitlines()[1:])
            except (ValueError, IndexError) as e:
                return f'Error parsing hunk header: {str(e)}\nHeader: {header}'
            context_before = []
            context_after = []
            removals = []
            additions = []
            for line in hunk_lines:
                if not line:
                    continue
                if not (line.startswith('+') or line.startswith('-')):
                    if not removals and (not additions):
                        context_before.append(line)
                    else:
                        context_after.append(line)
                elif line.startswith('-'):
                    removals.append(line[1:])
                elif line.startswith('+'):
                    additions.append(line[1:])
            if not removals and (not additions):
                continue
            if len(current_lines) == 0 and old_start == 0 and (not context_before) and (not removals):
                current_lines.extend(additions)
                changes_made.append('Applied changes to new file')
                continue
            adjusted_start = old_start + line_offset
            found = False
            match_line = adjusted_start
            if adjusted_start <= len(current_lines):
                found, was_whitespace = _check_match_type(current_lines, adjusted_start, context_before)
                if found:
                    if was_whitespace:
                        changes_made.append(f'Note: Applied hunk at line {adjusted_start} (ignoring whitespace)')
                    else:
                        changes_made.append(f'Applied hunk at line {adjusted_start}')
            if not found:
                matches = []
                whitespace_matches = []
                for i in range(1, len(current_lines) - len(context_before) + 2):
                    found, was_whitespace = _check_match_type(current_lines, i, context_before)
                    if found:
                        if was_whitespace:
                            whitespace_matches.append(i)
                        else:
                            matches.append(i)
                if matches:
                    if len(matches) > 1:
                        match_locations = '\n'.join((f'- at line {m}' for m in matches))
                        return f'Error: Multiple possible matches found:\n{match_locations}\nPlease provide more context to disambiguate.'
                    match_line = matches[0]
                    changes_made.append(f'Note: Applied hunk at line {match_line} (different from specified line {old_start})')
                    found = True
                elif whitespace_matches:
                    if len(whitespace_matches) > 1:
                        match_locations = '\n'.join((f'- at line {m}' for m in whitespace_matches))
                        return f'Error: Multiple possible matches found:\n{match_locations}\nPlease provide more context to disambiguate.'
                    match_line = whitespace_matches[0]
                    changes_made.append(f'Note: Applied hunk at line {match_line} (ignoring whitespace)')
                    found = True
            if not found and context_before:
                _, best_line, match_quality, _ = _find_block_in_content(current_lines, context_before, ignore_whitespace=True)
                if match_quality > 0.8:
                    context = _get_context(current_lines, best_line - 1, 2)
                    return f'Error: Found similar but not exact match at line {best_line}\nContext:\n{context}\nMatch quality: {match_quality:.2f}'
                else:
                    context = _get_context(current_lines, old_start - 1, 2) if old_start > 0 else []
                    return f'Error: Could not find matching content anywhere in file.\nExpected:\n{context_before}\nFound:\n{context}'
            pos = match_line - 1 + len(context_before)
            original_indent = ''
            if len(current_lines) > 0:
                if pos < len(current_lines):
                    if removals:
                        original_indent = _get_line_indentation(current_lines[pos])
                    else:
                        original_indent = _get_line_indentation(current_lines[pos - 1]) if pos > 0 else ''
                elif pos > 0:
                    original_indent = _get_line_indentation(current_lines[pos - 1])
            indented_additions = [original_indent + line.lstrip() for line in additions]
            if removals:
                current_lines[pos:pos + len(removals)] = indented_additions
            else:
                current_lines[pos:pos] = indented_additions
            line_offset += len(additions) - len(removals)
        if changes_made:
            new_content = '\n'.join(current_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
            return 'Successfully applied patches:\n' + '\n'.join(changes_made)
        return 'No changes were applied'
    except Exception as e:
        return f'Error: {str(e)}\n{traceback.format_exc()}'

def _get_context(lines, center_idx, context_size):
    """Get context lines around an index with line numbers."""
    start = max(0, center_idx - context_size)
    end = min(len(lines), center_idx + context_size + 1)
    return [f'{i + 1}: {line}' for i, line in enumerate(lines[start:end], start)]

def _find_block_in_content(content_lines: list, block_lines: list, ignore_whitespace: bool=False) -> tuple[bool, int, float, bool]:
    """Helper function to find a block of lines anywhere in the content.
    Returns (found, line_number, match_quality, was_whitespace_match)"""
    if not block_lines:
        return (False, 0, 0.0, False)
    for i in range(len(content_lines) - len(block_lines) + 1):
        current_block = content_lines[i:i + len(block_lines)]
        if current_block == block_lines:
            return (True, i + 1, 1.0, False)
    if ignore_whitespace:
        for i in range(len(content_lines) - len(block_lines) + 1):
            current_block = [l.strip() for l in content_lines[i:i + len(block_lines)]]
            block_to_match = [l.strip() for l in block_lines]
            if current_block == block_to_match:
                return (True, i + 1, 0.9, True)
    best_match = 0.0
    best_line = 0
    for i in range(len(content_lines) - len(block_lines) + 1):
        current_block = content_lines[i:i + len(block_lines)]
        matcher = difflib.SequenceMatcher(None, '\n'.join(current_block), '\n'.join(block_lines))
        ratio = matcher.ratio()
        if ratio > best_match:
            best_match = ratio
            best_line = i + 1
    return (False, best_line, best_match, False)

def _get_line_indentation(line: str) -> str:
    """Extract the indentation from a line."""
    return line[:len(line) - len(line.lstrip())]

def _check_match_type(content_lines: list, start_pos: int, context_lines: list, removal_lines: list=None) -> tuple[bool, bool]:
    """
    Check if there's a match at the given position.
    Returns (found_match, was_whitespace_match)
    """
    print(f'\nDEBUG _check_match_type:')
    print(f'  start_pos: {start_pos}')
    print(f'  context_lines: {context_lines}')
    print(f"  content at pos: {(content_lines[start_pos - 1] if start_pos - 1 < len(content_lines) else 'out of range')}")
    if start_pos - 1 + len(context_lines) > len(content_lines):
        return (False, False)
    context_exact = True
    context_whitespace = True
    for i, ctx_line in enumerate(context_lines):
        content_line = content_lines[start_pos - 1 + i]
        print(f"  comparing: '{content_line}' with '{ctx_line}'")
        if content_line != ctx_line:
            context_exact = False
        if content_line.strip() != ctx_line.strip():
            context_whitespace = False
    if not context_whitespace:
        return (False, False)
    if removal_lines:
        pos = start_pos - 1 + len(context_lines)
        if pos + len(removal_lines) > len(content_lines):
            return (False, False)
        for i, rem_line in enumerate(removal_lines):
            content_line = content_lines[pos + i]
            if content_line != rem_line:
                context_exact = False
            if content_line.strip() != rem_line.strip():
                return (False, False)
    print(f'  Match found! exact={context_exact}, whitespace={not context_exact}')
    return (True, not context_exact)

def _patch(file_path: str, patch_content: str):
    """
    Apply a git-style unified diff patch to a file.
    Internal implementation - use apply_git_patch instead.
    This version preserves the basic functionality that passed initial tests.
    """
    try:
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
        if not patch_content.strip():
            return 'Error: No valid patch hunks found'
        original_lines = content.splitlines()
        current_lines = original_lines.copy()
        changes_made = []
        line_offset = 0
        hunks = patch_content.split('\n@@')[1:]
        if not hunks:
            return 'Error: No valid patch hunks found'
        for hunk in hunks:
            hunk = hunk.strip()
            if not hunk:
                continue
            try:
                header_end = hunk.index('\n')
                header = hunk[:header_end].strip()
                if not header.endswith('@@'):
                    header = header + ' @@'
                old_range, new_range = header.rstrip(' @').split(' +')
                old_start = int(old_range.split(',')[0].lstrip('- '))
                new_start = int(new_range.split(',')[0])
                hunk_lines = hunk[header_end:].splitlines()[1:]
            except (ValueError, IndexError) as e:
                return f'Error parsing hunk header: {str(e)}\nHeader: {header}'
            context_before = []
            context_after = []
            removals = []
            additions = []
            for line in hunk_lines:
                if not line:
                    continue
                if line.startswith(' '):
                    if not removals and (not additions):
                        context_before.append(line[1:])
                    else:
                        context_after.append(line[1:])
                elif line.startswith('-'):
                    removals.append(line[1:])
                elif line.startswith('+'):
                    additions.append(line[1:])
            adjusted_start = old_start + line_offset
            context_matches = True
            if adjusted_start <= len(current_lines):
                for i, ctx_line in enumerate(context_before):
                    if adjusted_start - 1 + i >= len(current_lines) or current_lines[adjusted_start - 1 + i] != ctx_line:
                        context_matches = False
                        break
            else:
                context_matches = False
            if not context_matches:
                found, match_line, match_quality = _find_block_in_content(current_lines, context_before)
                if found:
                    adjusted_start = match_line
                    changes_made.append(f'Note: Applied hunk at line {adjusted_start} (different from specified line {old_start})')
                elif match_quality > 0.8:
                    context = _get_context(current_lines, match_line - 1, 2)
                    return f'Error: Found similar but not exact match at line {match_line}\nContext:\n{context}\nMatch quality: {match_quality:.2f}'
                else:
                    context = _get_context(current_lines, old_start - 1, 2)
                    return f'Error: Could not find matching content anywhere in file.\nExpected:\n{context_before}\nFound:\n{context}'
            pos = adjusted_start - 1
            pos += len(context_before)
            if removals:
                current_lines[pos:pos + len(removals)] = additions
                pos += len(additions)
            else:
                current_lines[pos:pos] = additions
                pos += len(additions)
            line_offset += len(additions) - len(removals)
            if not any(('Note:' in change for change in changes_made)):
                changes_made.append(f'Applied hunk at line {adjusted_start}')
        if changes_made:
            new_content = '\n'.join(current_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
            return 'Successfully applied patches:\n' + '\n'.join(changes_made)
        return 'No changes were applied'
    except Exception as e:
        return f'Error: {str(e)}\n{traceback.format_exc()}'

def _diff_edit(file_path: str, diff_spec: str):
    """
    Obsolete - kept for internal reference
    Diff spec editing with flexible matching.

    Use when you need to make precision changes in text files.

    Parameters:
    - file_path (str): Path to the file to modify
    - diff_spec (str): Diff-style specification of changes.
    Lines beginning with '-' are removed, and lines
    beginning with '+' are added at the starting index of the
    removed lines. All lines must start with + or -, and white
    space must be matched exactly.

    Returns:
    str: Description of changes made/to be made or error message with context

    ex) diff_spec:
    -import numpy
    +import scipy

    ex) diff_spec:
    -    def mergesort():
    -        pass
    +    def mergesort(arr:List) -> List
    +        if len(arr) <= 1:
    +            return arr
    +        # Divide the array into two halves
    +        mid = len(arr) // 2
    (etc)

    cost: low
    """
    ignore_indentation: bool = True
    context_lines: int = 2
    try:
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
        changes, errors = _parse_diff_spec(diff_spec=diff_spec)
        if errors:
            return 'Error parsing:' + '\n'.join(errors)
        original_lines = content.splitlines()
        current_lines = original_lines.copy()
        matched_changes = []
        unmatched_changes = []
        for remove, add in changes:
            match_found, line_num, prev_indent, match_score, best_index = _find_matching_block(current_lines, remove, ignore_indentation)
            if match_found:
                indented_add = _adjust_indentation(add, prev_indent)
                current_lines[line_num:line_num + len(remove)] = indented_add
                matched_changes.append(('\n'.join(remove), '\n'.join(indented_add)))
            else:
                failure_context = ''
                if match_score > 0:
                    context = _get_context(current_lines, best_index, context_lines)
                    failure_context = '\nNearest partial match found around:\n' + '\n'.join(context) + f'\n\nMatch score: {match_score:.2f}'
                unmatched_changes.append(('\n'.join(remove), '\n'.join(add), failure_context))
        if matched_changes:
            new_content = '\n'.join(current_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
        report = []
        report.append('Changes made:')
        if matched_changes:
            report.append(f'\nSuccessfully applied {len(matched_changes)} changes:')
        if unmatched_changes:
            report.append(f'\nFailed to apply {len(unmatched_changes)} changes:')
            for old, new, context in unmatched_changes:
                report.append(f'\nCould not find:\n{old}\n\n{context}')
        return '\n'.join(report) if report else 'No changes were applied'
    except Exception as e:
        return f'Error: {str(e)}\n{traceback.format_exc()}'

def _preserve_indentation(original_line: str, new_line: str) -> str:
    """Preserve indentation from original line when replacing with new line."""
    original_indent = _get_line_indentation(original_line)
    return original_indent + new_line.lstrip()

def _check_exact_match(content_lines: list, start_pos: int, context_lines: list) -> bool:
    """Check if there's an exact match (including whitespace) at the given position"""
    if start_pos - 1 + len(context_lines) > len(content_lines):
        return False
    return all((content_lines[start_pos - 1 + i] == line for i, line in enumerate(context_lines)))

def _check_whitespace_match(content_lines: list, start_pos: int, context_lines: list) -> bool:
    """Check if there's a match ignoring whitespace at the given position"""
    if start_pos - 1 + len(context_lines) > len(content_lines):
        return False
    return all((content_lines[start_pos - 1 + i].strip() == line.strip() for i, line in enumerate(context_lines)))

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

def _adjust_indentation(lines, target_indent):
    """Adjust indentation of a block of lines to match target_indent."""
    if not lines:
        return lines
    non_empty_lines = [l for l in lines if l.strip()]
    if not non_empty_lines:
        return lines
    min_indent = min((len(_get_indentation(l)) for l in non_empty_lines))
    adjusted = []
    for line in lines:
        if not line.strip():
            adjusted.append(line)
        else:
            stripped = line[min_indent:]
            adjusted.append(target_indent + stripped)
    return adjusted

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
            errors.append(f'Error: "{line}" does not start with + or -. All lines must start with + or -.')
            continue
        if last_prefix == '-':
            remove.append(content)
        elif last_prefix == '+':
            add.append(content)
    if remove or add:
        changes.append((remove, add))
    if not changes and (not errors):
        errors.append('Error: No valid changes found in diff spec')
    return (changes, errors)

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
        return (True, len(current_lines), '', 1.0, len(current_lines))

    def filter_empty_lines(lines):
        return [line for line in lines if line.strip()]
    filtered_current = filter_empty_lines(current_lines)
    filtered_remove = filter_empty_lines(remove_lines)
    current_map = []
    for i, line in enumerate(current_lines):
        if line.strip():
            current_map.append(i)
    if len(filtered_remove) > len(filtered_current):
        return (False, 0, '', 0.0, 0)
    for i in range(len(filtered_current) - len(filtered_remove) + 1):
        current_block = filtered_current[i:i + len(filtered_remove)]
        if ignore_indentation:
            match = all((c.strip() == o.strip() for c, o in zip(current_block, filtered_remove)))
        else:
            match = all((c == o for c, o in zip(current_block, filtered_remove)))
        if match:
            orig_index = current_map[i]
            end_index = current_map[i + len(filtered_remove) - 1]
            return (True, orig_index, _get_indentation(current_lines[orig_index]), 1.0, orig_index)
    best_match_score = 0
    best_match_index = 0
    for i in range(len(filtered_current) - len(filtered_remove) + 1):
        current_block = filtered_current[i:i + len(filtered_remove)]
        match_score = _calculate_block_match_score(current_block, filtered_remove, ignore_indentation)
        if match_score > best_match_score:
            best_match_score = match_score
            best_match_index = current_map[i]
    return (False, best_match_index, _get_indentation(current_lines[best_match_index]), best_match_score, best_match_index)

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

def _calculate_block_match_score(current_block, old_lines, ignore_indentation):
    """Calculate how well two blocks match, returning a score and matching line indices."""
    if ignore_indentation:
        current_joined = ' '.join((l.strip() for l in current_block))
        old_joined = ' '.join((l.strip() for l in old_lines))
        current_stripped = [c.strip() for c in current_block]
        old_stripped = [o.strip() for o in old_lines]
    else:
        current_joined = ' '.join(current_block)
        old_joined = ' '.join(old_lines)
        current_stripped = current_block
        old_stripped = old_lines
    exact_matches = sum((1 for c, o in zip(current_stripped, old_stripped) if c == o))
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

def _get_indentation(line):
    """Extract the leading whitespace from a line."""
    return line[:len(line) - len(line.lstrip())]

def _normalize_path(file_path: str) -> str:
    """
    Normalize file path to use consistent separators and handle both / and \\.

    Args:
        file_path (str): The file path to normalize

    Returns:
        str: Normalized path using os.path.sep
    """
    return os.path.normpath(file_path.replace('\\', '/').replace('//', '/'))

def _normalize_header_lines(lines):
    """
    Normalize only the hunk headers (@@ lines) in a patch.
    Leaves all other lines unchanged.

    Args:
        lines (list[str]): List of patch lines

    Returns:
        list[str]: Lines with normalized hunk headers
    """
    normalized = []
    for line in lines:
        if not line:
            normalized.append(line)
            continue
        if line.startswith('@@'):
            parts = line.split('@@')
            if len(parts) >= 2:
                ranges = parts[1].strip()
                line = f'@@ {ranges} @@'
        normalized.append(line)
    return normalized