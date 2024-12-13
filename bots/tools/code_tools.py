import os
from typing import List

def view(file_path: str):
    """
    Display the contents of a file with line numbers.

    Parameters:
    - file_path (str): The path to the file to be viewed.

    Returns:
    A string containing the file contents with line numbers.
    """
    encodings = ['utf-8', 'utf-16', 'utf-16le', 'ascii', 'cp1252', 'iso-8859-1']
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


def add_lines(file_path: str, new_content: str, start_line: str):
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


def change_lines(file_path: str, new_content: str, start_line: str,  end_line: str):
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
        lines[start_line - 1:end_line] = normalized_lines
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        return (
            f'Successfully changed lines {start_line} to {end_line}:\n\n{view(file_path)}'
            )
    except Exception as e:
        return f'Error: {str(e)}'


def delete_lines(file_path: str, start_line: str, end_line: str):
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
    

def view_dir(start_path: str = '.', output_file='dir.txt', target_extensions: str = "['py']"):
    """
    Creates a summary of the directory structure starting from the given path, writing only files 
    with specified extensions. The output is written to a text file and returned as a string.
    
    Parameters:
    - start_path (str): The root directory to start scanning from.
    - output_file (str): The name of the file to write the directory structure to.
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
    # Parse the string representation of list into actual list
    # Remove brackets, split by comma, strip whitespace and quotes
    extensions_list = [ext.strip().strip("'\"") for ext in target_extensions.strip('[]').split(',')]
    # Add dot prefix if not present
    extensions_list = ['.' + ext if not ext.startswith('.') else ext for ext in extensions_list]
    
    output_text = []
    with open(output_file, 'w') as f:
        for root, dirs, files in os.walk(start_path):
            # Only include directories that have target_extension files somewhere in their tree
            has_py = False
            for _, _, fs in os.walk(root):
                if any(f.endswith(tuple(extensions_list)) for f in fs):
                    has_py = True
                    break
                
            if has_py:
                level = root.replace(start_path, '').count(os.sep)
                indent = '    ' * level
                line = f'{indent}{os.path.basename(root)}/'
                f.write(line + '\n')
                output_text.append(line)
                
                # List python files in this directory
                subindent = '    ' * (level + 1)
                for file in files:
                    if file.endswith(tuple(extensions_list)):
                        line = f'{subindent}{file}'
                        f.write(line + '\n')
                        output_text.append(line)
    
    return '\n'.join(output_text)