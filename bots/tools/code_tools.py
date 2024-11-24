def view(file_path):
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


def add_lines(file_path, new_content, start_line):
    """
    Add new lines to a file at a specified position. Creates the file if it doesn't exist.
    Note: INSERTS lines at the specified position, shifting existing lines down.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - new_content (str): String containing the new content, with lines separated by newlines.
    - start_line (int): The line number where the new lines should be inserted.
                       If file is being created, this must be 1.

    Returns:
    A string confirming the operation and showing the new file, or a description of an error encountered.
    """
    from bots.tools.code_tools import view
    try:
        start_line = int(start_line)
        new_lines = new_content.split('\n')
        while new_lines and not new_lines[-1]:
            new_lines.pop()
        try:
            with open(file_path, 'r', encoding='utf-8') as file:
                lines = file.readlines()
        except FileNotFoundError:
            if start_line != 1:
                return 'Error: When creating a new file, start_line must be 1'
            lines = []
        normalized_lines = [(line + '\n' if not line.endswith('\n') else
            line) for line in new_lines]
        for i, line in enumerate(normalized_lines):
            if start_line - 1 + i > len(lines):
                lines.append(line)
            else:
                lines.insert(start_line - 1 + i, line)
        from pathlib import Path
        Path(file_path).parent.mkdir(parents=True, exist_ok=True)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        action = 'created new file and added' if len(lines) == len(
            normalized_lines) else 'added'
        return f"""Successfully {action} {len(normalized_lines)} lines starting at line {start_line}:

{view(file_path)}"""
    except Exception as e:
        return f'Error: {str(e)}'


def change_lines(file_path, new_content, start_line, end_line):
    """
    Change specific lines in a file.
    Note: DELETES the lines from start_line to end_line (both inclusive), replacing them with new_content

    Parameters:
    - file_path (str): The path to the file to be modified.
    - new_content (str): String containing the new content, with lines separated by newlines.
    - start_line (int): The starting line number of the lines to be changed.
    - end_line (int): The ending line number of the lines to be changed.

    Returns:
    A string confirming the operation and showing the new file, or a description of an error encountered.
    """
    from bots.tools.code_tools import view
    try:
        start_line = int(start_line)
        end_line = int(end_line)
        new_lines = new_content.split('\n')
        while new_lines and not new_lines[-1]:
            new_lines.pop()
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        if start_line < 1 or end_line > len(lines):
            return 'Error: Invalid line range.'
        normalized_lines = [(line + '\n' if not line.endswith('\n') else
            line) for line in new_lines]
        lines[start_line - 1:end_line + 1] = normalized_lines
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        return (
            f'Successfully changed lines {start_line} to {end_line}:\n\n{view(file_path)}'
            )
    except Exception as e:
        return f'Error: {str(e)}'


def delete_lines(file_path, start_line, end_line):
    """
    Delete specific lines from a file.
    Note: Removes the specified lines entirely, shifting remaining lines up.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - start_line (int): The starting line number of the lines to be deleted.
    - end_line (int): The ending line number of the lines to be deleted.

    Returns:
    A string confirming the operation and showing the new file, or a description of an error encountered.
    """
    from bots.tools.code_tools import view
    try:
        start_line = int(start_line)
        end_line = int(end_line)
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        if start_line < 1 or end_line > len(lines):
            return 'Error: Invalid line range.'
        del lines[start_line - 1:end_line]
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        return (
            f'Successfully deleted lines {start_line} to {end_line}:\n\n{view(file_path)}'
            )
    except Exception as e:
        return f'Error: {str(e)}'


def find_lines(file_path, pattern):
    """
    Find lines in a file that match a specific pattern.

    Parameters:
    - file_path (str): The path to the file to be searched.
    - pattern (str): The pattern to search for in each line.

    Returns:
    A list of tuples containing line numbers and matching lines.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        matches = [(i + 1, line.strip()) for i, line in enumerate(lines) if
            pattern in line]
        if matches:
            return f'Found {len(matches)} matches:\n' + '\n'.join([
                f'Line {m[0]}: {m[1]}' for m in matches])
        else:
            return 'No matches found.'
    except Exception as e:
        return f'Error: {str(e)}'


def replace_in_lines(file_path, old_text, new_text, start_line, end_line):
    """
    Replace specific text within a range of lines in a file.
    Note: OVERWRITES portions of lines containing the old_text with new_text.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - old_text (str): The text to be replaced.
    - new_text (str): The text to replace the old text.
    - start_line (int): The starting line number of the range to modify.
    - end_line (int): The ending line number of the range to modify.

    Returns:
    A string confirming the operation and showing the new file, or a description of an error encountered.
    """
    try:
        start_line = int(start_line)
        end_line = int(end_line)
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        if start_line < 1 or end_line > len(lines):
            return 'Error: Invalid line range.'
        count = 0
        for i in range(start_line - 1, end_line):
            if old_text in lines[i]:
                lines[i] = lines[i].replace(old_text, new_text)
                count += 1
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        return f"""Successfully replaced {count} occurrences of '{old_text}' with '{new_text}'                 in lines {start_line} to {end_line}:

{view(file_path)}"""
    except Exception as e:
        return f'Error: {str(e)}'
