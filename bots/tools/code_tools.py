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
            numbered_lines = [f'{i + 1}: {line.rstrip()}' for i, line in
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


def diff_edit(file_path: str, diff_spec: str) ->str:
    """Change code using a diff-like specification.

    Use when you need to make specific text replacements in code files.
    The diff spec uses a simplified format:
    - Lines starting with '-' indicate text to be replaced (no space after -)
    - Lines starting with '+' indicate replacement text (no space after +)
    - Alternatively, a line starting with '-#' (where # is a specific integer) can specify a line number to insert after
    - Blank lines separate different changes
    - Changes are applied in order
    - You must match indentation

    For text replacement:
    ```
    -def old_function(
    +def new_function(
    ```

    ```
    -\tdef do_stuff():
    -\t\tprint('starting')
    -\t\tdo_work(x)
    -\t\tprint('done')
    +\tdef do_stuff_better():
    +\t\tprint('starting work')
    +\t\tdo_work(y)
    +\t\tprint('done with work')

    For line insertion:
    ```
    -5
    +       new_line_of_code
    ```

    Parameters:
    - file_path (str): Path to the file to modify
    - diff_spec (str): Diff-style specification of changes

    Returns:
    str: Description of changes made or error message

    Example:
    ```
    diff_edit("my_file.py", '''
    -def old_function(
    +def new_function(

    -   return dict_value
    +   return json.dumps(dict_value)
    ''')
    ```

    Caution:
    Line numbers may change when using this function. Always check
    line numbers if calling with -# more than once.
    """
    try:
        if not diff_spec.strip():
            return 'No changes specified'
        with open(file_path, 'r', encoding='utf-8') as file:
            original_content = file.read()
            original_lines = original_content.splitlines()
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
                # Check if it's a line number specification
                try:
                    line_num = int(line[1:])
                    current_old = [str(line_num)]  # Store as string to differentiate from text match
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
        for old_lines, new_lines in changes:
            found = False
            # Check if old_lines[0] is a line number
            try:
                line_num = int(old_lines[0])
                # Insert after the specified line
                if line_num <= len(current_lines):
                    current_lines[line_num:line_num] = new_lines
                    applied_changes.append((f"after line {line_num}", '\n'.join(new_lines)))
                    found = True
            except ValueError:
                # Regular text replacement
                for i in range(len(current_lines) - len(old_lines) + 1):
                    current_block = current_lines[i:i + len(old_lines)]
                    matches = all(c.strip() == o.strip() for c, o in zip(current_block, old_lines))
                    if matches:
                        current_lines[i:i + len(old_lines)] = new_lines
                        applied_changes.append(('\n'.join(old_lines), '\n'.join(new_lines)))
                        found = True
                        break
            if not found:
                failed_changes.append(('\n'.join(old_lines), '\n'.join(new_lines)))
        if applied_changes:
            new_content = '\n'.join(current_lines)
            if not new_content.endswith('\n'):
                new_content += '\n'
            with open(file_path, 'w', encoding='utf-8') as file:
                file.write(new_content)
        report = []
        if applied_changes:
            report.append(
                f'Successfully applied {len(applied_changes)} changes:')
            for old, new in applied_changes:
                report.append(f'\nChanged:\n{old}\nTo:\n{new}')
        if failed_changes:
            report.append(f'\nFailed to apply {len(failed_changes)} changes:')
            for old, new in failed_changes:
                report.append(f'\nCould not find:\n{old}')
        return '\n'.join(report) if report else 'No changes were applied'
    except Exception as e:
        return f'Error: {str(e)}'
