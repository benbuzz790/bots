import os


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
    "['py']"):
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

def diff_edit(file_path: str, diff_spec: str, ignore_indentation: bool=
    False, preview: bool=False, context_lines: int=2) ->str:
    """Diff spec editing with flexible matching.

    Use when you need to make specific text replacements in code files.
    The diff spec uses a simplified format:
    - Lines starting with '-' indicate text to be replaced (no space after -)
    - Lines starting with '+' indicate replacement text (no space after +)
    - Alternatively, a line starting with '-#' (where # is a specific integer) can specify a line number to insert after
    - Blank lines separate different changes
    - Changes are applied in order

    When ignore_indentation is True:
    - Matches text ignoring leading whitespace
    - Preserves the indentation level where the match is found
    - All lines in the replacement maintain their relative indentation

    Parameters:
    - file_path (str): Path to the file to modify
    - diff_spec (str): Diff-style specification of changes
    - ignore_indentation (bool): If True, ignores whitespace at start of lines when matching
    - preview (bool): If True, shows what would change without making changes
    - context_lines (int): Number of lines of context to show around failed matches

    Returns:
    str: Description of changes made/to be made or error message with context
    """
    try:
        encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252',
            'iso-8859-1']
        content = None
        used_encoding = None
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
            return 'No changes specified'
        original_lines = content.splitlines()
        changes = []
        current_old = []
        current_new = []
        for line in diff_spec.splitlines():
            if not line:
                if current_old and current_new:
                    changes.append((current_old.copy(), current_new.copy()))
                    current_old.clear()
                    current_new.clear()
                continue
            if line.startswith('-'):
                try:
                    line_num = int(line[1:])
                    current_old = [str(line_num)]
                except ValueError:
                    current_old.append(line[1:])
            elif line.startswith('+'):
                current_new.append(line[1:])
        if current_old and current_new:
            changes.append((current_old, current_new))
        if not changes:
            return 'No valid changes found in diff specification'
        current_lines = original_lines.copy()
        applied_changes = []
        failed_changes = []

        def get_indentation(line):
            """Extract the leading whitespace from a line."""
            return line[:len(line) - len(line.lstrip())]

        def adjust_indentation(lines, target_indent):
            """Adjust indentation of a block of lines to match target_indent."""
            if not lines:
                return lines
            non_empty_lines = [l for l in lines if l.strip()]
            if not non_empty_lines:
                return lines
            min_indent = min(len(get_indentation(l)) for l in non_empty_lines)
            adjusted = []
            for line in lines:
                if not line.strip():
                    adjusted.append(line)
                else:
                    stripped = line[min_indent:]
                    adjusted.append(target_indent + stripped)
            return adjusted

        def calculate_block_match_score(current_block, old_lines):
            """Calculate how well two blocks match, returning a score and matching line indices."""
            if ignore_indentation:
                current_stripped = [c.strip() for c in current_block]
                old_stripped = [o.strip() for o in old_lines]
            else:
                current_stripped = current_block
                old_stripped = old_lines
            exact_matches = sum(1 for c, o in zip(current_stripped,
                old_stripped) if c == o)
            partial_matches = 0
            for c, o in zip(current_stripped, old_stripped):
                c_words = set(c.split())
                o_words = set(o.split())
                word_matches = len(c_words.intersection(o_words))
                if word_matches > 0:
                    partial_matches += word_matches / max(len(c_words), len
                        (o_words))
            total_score = exact_matches * 2 + partial_matches
            return total_score

        def get_context(lines, center_idx, context_size):
            """Get context lines around an index with line numbers."""
            start = max(0, center_idx - context_size)
            end = min(len(lines), center_idx + context_size + 1)
            return [f'{i + 1}: {line}' for i, line in enumerate(lines[start
                :end], start)]
        for old_lines, new_lines in changes:
            found = False
            try:
                line_num = int(old_lines[0])
                if line_num <= len(current_lines):
                    if line_num > 0:
                        prev_indent = get_indentation(current_lines[
                            line_num - 1])
                        adjusted_new = adjust_indentation(new_lines,
                            prev_indent)
                    else:
                        adjusted_new = new_lines
                    if not preview:
                        current_lines[line_num:line_num] = adjusted_new
                    applied_changes.append((f'after line {line_num}', '\n'.
                        join(adjusted_new)))
                    found = True
                else:
                    failed_changes.append((
                        f'Line number {line_num} exceeds file length {len(current_lines)}'
                        , '\n'.join(new_lines), ''))
            except ValueError:
                best_match_score = 0
                best_match_index = None
                for i in range(len(current_lines) - len(old_lines) + 1):
                    current_block = current_lines[i:i + len(old_lines)]
                    if ignore_indentation:
                        match = all(c.strip() == o.strip() for c, o in zip(
                            current_block, old_lines))
                    else:
                        match = all(c == o for c, o in zip(current_block,
                            old_lines))
                    if match:
                        if ignore_indentation:
                            target_indent = get_indentation(current_block[0])
                            adjusted_new = adjust_indentation(new_lines,
                                target_indent)
                        else:
                            adjusted_new = new_lines
                        if not preview:
                            current_lines[i:i + len(old_lines)] = adjusted_new
                        applied_changes.append(('\n'.join(old_lines), '\n'.
                            join(adjusted_new)))
                        found = True
                        break
                    else:
                        match_score = calculate_block_match_score(current_block
                            , old_lines)
                        if match_score > best_match_score:
                            best_match_score = match_score
                            best_match_index = i
            if not found:
                failure_context = ''
                if best_match_index is not None and best_match_score > 0:
                    context = get_context(current_lines, best_match_index,
                        context_lines)
                    failure_context = (
                        '\nNearest partial match found at:\n' + '\n'.join(
                        context))
                    if ignore_indentation:
                        failure_context += (
                            '\n(Note: matching with ignore_indentation=True)')
                    failure_context += f'\nMatch score: {best_match_score:.2f}'
                failed_changes.append(('\n'.join(old_lines), '\n'.join(
                    new_lines), failure_context))
        report = []
        if preview:
            report.append('Preview of changes to be made:')
        if applied_changes:
            report.append(
                f"""
Successfully {'previewed' if preview else 'applied'} {len(applied_changes)} changes:"""
                )
            for old, new in applied_changes:
                report.append(f'\nChanged:\n{old}\nTo:\n{new}')
        if failed_changes:
            report.append(
                f"""
Failed to {'preview' if preview else 'apply'} {len(failed_changes)} changes:"""
                )
            for old, new, context in failed_changes:
                report.append(
                    f'\nCould not find:\n{old}\nTo replace with:\n{new}{context}'
                    )
        if not preview and applied_changes:
            new_content = '\n'.join(current_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding=used_encoding) as file:
                file.write(new_content)
        return '\n'.join(report) if report else 'No changes were applied'
    except Exception as e:
        import traceback
        return f'Error: {str(e)}\n{traceback.format_exc()}'
