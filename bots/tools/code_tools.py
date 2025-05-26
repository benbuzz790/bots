import os
import traceback
import textwrap
import difflib

def read_file(file_path: str):
    """
    Display the contents of a file with line numbers.

    Parameters:
    - file_path (str): The path to the file to be viewed.

    Returns:
    A string containing the file contents with line numbers, 
    limited to the specified maximum number of lines.
    """
    encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252', 'iso-8859-1']
    max_lines = 2500
    for encoding in encodings:
        try:
            with open(file_path, 'r', encoding=encoding) as file:
                lines = file.readlines()
                # Slice the lines to max_lines
                truncated_lines = lines[:max_lines] if max_lines < len(lines)-1 else lines
                numbered_lines = [f'{i + 1}:{line.rstrip()}' for i, line in enumerate(truncated_lines)]
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

def patch_edit(file_path: str, patch_content: str):
    """
    Apply a git-style unified diff patch to a file.

    Use when you need to make a precise change to a file

    Tips:
    - Small, focused changes work best
    - Exact content matching is important
    - Including surrounding context helps matching
    - Whitespace in the target lines matters

    Parameters:
    - file_path (str): Path to the file to modify
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

        # Clean up to prevent some common errors.
        patch_content = textwrap.dedent(patch_content)
        patch_content = '\n' + patch_content
        
        
        hunks = patch_content.split('\n@@')[1:]
        if not hunks:
            return 'Error: No valid patch hunks found. (No instances of "\\n@@". Did you accidentally indent the headers?)'
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
                old_start = int(old_range.split(',')[0].lstrip('- ')) - 1  # Convert to 0-based
                #new_start = int(new_range.split(',')[0]) - 1  # Convert to 0-based, unused
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
                return f'Error: No additons or removals found in hunk starting with {hunk_lines[0][0:20]}'
                continue

            # Create a new file if appropriate
            if len(current_lines) == 0 and old_start == 0 and (not context_before) and (not removals):
                current_lines.extend(additions)
                changes_made.append('Applied changes to new file')
                continue


            adjusted_start = old_start + line_offset
            found = False
            match_line = adjusted_start
            exact_match = False

            # Try to match at expected position with or without whitespace
            if adjusted_start <= len(current_lines):
                found, was_whitespace = _check_match_type(current_lines, adjusted_start-1, context_before) #please forgive me for my off by one errors
                if found:
                    exact_match = not was_whitespace
                    if was_whitespace:
                        changes_made.append(f'Note: Applied hunk starting with {hunk_lines[0][0:20]}, but had to ignore whitespace to find match')
                    else:
                        changes_made.append(f'Applied hunk starting with {hunk_lines[0][0:20]} with exact match')

            # Try to match at any position with or without whitespace
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
                            exact_match = True
                
                # Apply exact match if exactly one is found
                if matches:
                    if len(matches) > 1: # If we find more than one match, we don't attempt to disambiguate
                        match_locations = '\n'.join((f'- at line {m}' for m in matches))
                        return f'Error: Multiple possible matches found:\n{match_locations} for hunk starting with {hunk_lines[0][0:20]}\nPlease provide more context to disambiguate.'
                    match_line = matches[0]
                    changes_made.append(f'Note: Applied hunk starting with {hunk_lines[0][0:20]} at line {match_line} (different from specified line {old_start})')
                    found = True
                
                # Apply whitespace match if exactly one is found (and no exact match found)
                elif whitespace_matches:
                    if len(whitespace_matches) > 1:
                        match_locations = '\n'.join((f'- at line {m}' for m in whitespace_matches))
                        return f'Error: Multiple possible matches found:\n{match_locations}\nPlease provide more context to disambiguate.'
                    match_line = whitespace_matches[0]
                    changes_made.append(f'Note: Applied hunk starting with {hunk_lines[0][0:20]} at line {match_line} (different from specified line {old_start}), and had to ignore whitespace to find match')
                    found = True
            
            # If no match found ignoring position and whitespace, send error with best match.
            if not found and context_before:
                _, best_line, match_quality, _ = _find_block_in_content(current_lines, context_before, ignore_whitespace=True)
                if match_quality > 0.05:
                    context = _get_context(current_lines, best_line - 1, 2)
                    return f'Error: Could not find match. Best potential match: {best_line}\nContext:\n{context}\nMatch quality: {match_quality:.2f}'
                else:
                    context = _get_context(current_lines, old_start - 1, 2) if old_start > 0 else []
                    return f'Error: Could not find match or close match.\nExpected:\n{context_before}\nFound:\n{context}'
                
            # Apply changes
            if len(context_before) == 0:
                pos = match_line + len(context_before) # I hate that I have to do this but I mixed up 0 / 1 based indexing somewhere and I can't find it.
            else:
                pos = match_line + len(context_before) -1
            if exact_match:
                indented_additions = additions
            else:
                target_indent = ''
                if len(current_lines) > 0:
                    if pos < len(current_lines):
                        if removals:
                            target_indent = _get_line_indentation(current_lines[pos])
                        else:
                            target_indent = _get_line_indentation(current_lines[pos - 1]) if pos > 0 else ''
                    elif pos > 0:
                        target_indent = _get_line_indentation(current_lines[pos - 1])
                indented_additions = _adjust_indentation(additions, target_indent)
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
    return [f'{i + 1}:{line}' for i, line in enumerate(lines[start:end], start)]

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
    if start_pos - 1 + len(context_lines) > len(content_lines):
        return (False, False)
    context_exact = True
    context_whitespace = True
    for i, ctx_line in enumerate(context_lines):
        content_line = content_lines[start_pos - 1 + i]
        if content_line != ctx_line:
            context_exact = False
        if content_line.strip() != ctx_line.strip():
            context_whitespace = False
    if not context_whitespace:
        return (False, False)
    if removal_lines:
        pos = start_pos -1 + len(context_lines)
        if pos + len(removal_lines) > len(content_lines):
            return (False, False)
        for i, rem_line in enumerate(removal_lines):
            content_line = content_lines[pos + i]
            if content_line != rem_line:
                context_exact = False
            if content_line.strip() != rem_line.strip():
                return (False, False)
    return (True, not context_exact)

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

def _adjust_indentation(lines: list, target_indent: str) -> list:
    """
    Adjust indentation of a block of lines to match target indent while preserving relative indentation.
    First applies target indentation to all lines, then preserves additional relative indentation.

    Args:
        lines (list[str]): Lines to adjust
        target_indent (str): Target base indentation

    Returns:
        list[str]: Lines with adjusted indentation
    """
    if not lines:
        return lines
    base_indent = None
    for line in lines:
        if line.strip():
            base_indent = _get_line_indentation(line)
            break
    if base_indent is None:
        return lines
    adjusted_lines = []
    for line in lines:
        if not line.strip():
            adjusted_lines.append('')
            continue
        current_indent = _get_line_indentation(line)
        relative_indent = len(current_indent) - len(base_indent)
        new_indent = target_indent + ' ' * max(0, relative_indent)
        adjusted_lines.append(new_indent + line.lstrip())
    return adjusted_lines

