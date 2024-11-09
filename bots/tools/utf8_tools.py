import os
import re
import traceback


def overwrite(file_path, content):
    """
    Completely rewrites the content of a file with new content, or writes a new file.

    Use when you want to replace the ENTIRE contents of a file or write a new file.
    If you have other tools to make precise changes available, you should use them 
    rather than this.

    Parameters:
    - file_path (str): The path to the file that will be rewritten.
    - content (str): The new content that will be written to the file.

    Returns 'success' or an error message string.
    """
    try:
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(content)
        return f'Rewrote {file_path} successfully'
    except Exception as error:
        return _process_error(error)

def replace(file_path, old_string, new_string):
    """
    Replaces all occurrences of a specified string with a new string in a file.

    Use when you need to find and replace a specific string throughout an entire file.

    Parameters:
    - file_path (str): The path to the file where the replacements will be made.
    - old_string (str): The string to be replaced.
    - new_string (str): The string that will replace the old string.

    Returns a confirmation message or an error message.
    """
    if not os.path.exists(file_path):
        return _process_error(FileNotFoundError(
            f"File '{file_path}' not found."))
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            content = file.read()
        updated_content = re.sub(re.escape(old_string), new_string, content)
        with open(file_path, 'w', encoding='utf-8') as file:
            file.write(updated_content)
    except Exception as e:
        return _process_error(e)
    return (
        f"Replaced all instances of '{old_string}' with '{new_string}' in '{file_path}'."
        )

def append(file_path, content):
    """
    Appends content to the end of a file.

    Use when you want to add new content to a file without modifying its existing content.

    Parameters:
    - file_path (str): The path to the file where content will be appended.
    - content (str): The content to be added to the end of the file.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'a', encoding='utf-8') as file:
            file.write(content+"\n")
    except Exception as e:
        return _process_error(e)
    return f"Content appended to the file '{file_path}'."

def prepend(file_path, content):
    """
    Prepends content to the beginning of a file.

    Use when you need to add new content to the start of a file, before any existing content.

    Parameters:
    - file_path (str): The path to the file where content will be prepended.
    - content (str): The content to be added to the beginning of the file.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'r+', encoding='utf-8') as file:
            content = file.read()
            file.seek(0, 0)
            file.write(content + "\n" + content)
    except Exception as e:
        return _process_error(e)
    return f"Content prepended to the file '{file_path}'."

def delete_match(file_path, pattern):
    """
    Deletes all lines in a file that contain a specified pattern (case-insensitive).

    Use to remove specific content from a file based on a search pattern.

    Parameters:
    - file_path (str): The path to the file from which lines will be deleted.
    - pattern (str): The pattern to search for in each line.

    Returns a confirmation message or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        with open(file_path, 'w', encoding='utf-8') as file:
            for line in lines:
                if pattern.lower() not in line.lower():
                    file.write(line)
            return (
                f"Lines containing '{pattern}' (case-insensitive) have been deleted from '{file_path}'."
                )
    except Exception as e:
        return _process_error(e)

def read_file(file_path):
    """
    Reads and returns the entire content of a file as a string.

    Use when you need to retrieve the complete content of a file for further processing or analysis.

    Parameters:
    - file_path (str): The path to the file to be read.

    Returns the file content as a string or an error message.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            return file.read()
    except Exception as e:
        return _process_error(e)


def _process_error(error):
    error_message = f'Tool Failed: {str(error)}\n'
    error_message += (
        f"Traceback:\n{''.join(traceback.format_tb(error.__traceback__))}")
    return error_message


