def view(file_path):
    """
    Display the contents of a file with line numbers.

    Parameters:
    - file_path (str): The path to the file to be viewed.

    Returns:
    A string containing the file contents with line numbers.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        numbered_lines = [f"{i+1}: {line.rstrip()}" for i, line in enumerate(lines)]
        return "\n".join(numbered_lines)
    except Exception as e:
        return f"Error: {str(e)}"

def add_lines(file_path, new_content, start_line):
    """
    Add new lines to a file at a specified position.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - new_content (str): String containing the new content, with lines separated by newlines.
    - start_line (int): The line number where the new lines should be inserted.

    Returns:
    A string confirming the operation or describing an error.
    """
    try:
        start_line = int(start_line)
        
        # Split the input string into lines
        new_lines = new_content.split('\n')
        # Remove empty lines from the end if present
        while new_lines and not new_lines[-1]:
            new_lines.pop()
            
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        # Ensure each line ends with exactly one newline
        normalized_lines = [line + '\n' if not line.endswith('\n') else line 
                          for line in new_lines]
        
        for i, line in enumerate(normalized_lines):
            lines.insert(start_line - 1 + i, line)
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        return f"Successfully added {len(normalized_lines)} lines starting at line {start_line}."
    except Exception as e:
        return f"Error: {str(e)}"

def change_lines(file_path, new_content, start_line, end_line):
    """
    Change specific lines in a file.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - new_content (str): String containing the new content, with lines separated by newlines.
    - start_line (int): The starting line number of the lines to be changed.
    - end_line (int): The ending line number of the lines to be changed.

    Returns:
    A string confirming the operation or describing an error.
    """
    try:
        start_line = int(start_line)
        end_line = int(end_line)
        
        # Split the input string into lines
        new_lines = new_content.split('\n')
        # Remove empty lines from the end if present
        while new_lines and not new_lines[-1]:
            new_lines.pop()
        
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if start_line < 1 or end_line > len(lines):
            return "Error: Invalid line range."
        
        # Ensure each line ends with exactly one newline
        normalized_lines = [line + '\n' if not line.endswith('\n') else line 
                          for line in new_lines]
        
        lines[start_line-1:end_line] = normalized_lines
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        return f"Successfully changed lines {start_line} to {end_line}."
    except Exception as e:
        return f"Error: {str(e)}"

def delete_lines(file_path, start_line, end_line):
    """
    Delete specific lines from a file.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - start_line (int): The starting line number of the lines to be deleted.
    - end_line (int): The ending line number of the lines to be deleted.

    Returns:
    A string confirming the operation or describing an error.
    """
    try:
        start_line = int(start_line)
        end_line = int(end_line)
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if start_line < 1 or end_line > len(lines):
            return "Error: Invalid line range."
        
        del lines[start_line-1:end_line]
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        return f"Successfully deleted lines {start_line} to {end_line}."
    except Exception as e:
        return f"Error: {str(e)}"

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
        
        matches = [(i+1, line.strip()) for i, line in enumerate(lines) if pattern in line]
        
        if matches:
            return f"Found {len(matches)} matches:\n" + "\n".join([f"Line {m[0]}: {m[1]}" for m in matches])
        else:
            return "No matches found."
    except Exception as e:
        return f"Error: {str(e)}"

def replace_in_lines(file_path, old_text, new_text, start_line, end_line):
    """
    Replace specific text within a range of lines in a file.

    Parameters:
    - file_path (str): The path to the file to be modified.
    - old_text (str): The text to be replaced.
    - new_text (str): The text to replace the old text.
    - start_line (int): The starting line number of the range to modify.
    - end_line (int): The ending line number of the range to modify.

    Returns:
    A string confirming the operation or describing an error.
    """
    try:
        start_line = int(start_line)
        end_line = int(end_line)
        with open(file_path, 'r', encoding='utf-8') as file:
            lines = file.readlines()
        
        if start_line < 1 or end_line > len(lines):
            return "Error: Invalid line range."
        
        count = 0
        for i in range(start_line-1, end_line):
            if old_text in lines[i]:
                lines[i] = lines[i].replace(old_text, new_text)
                count += 1
        
        with open(file_path, 'w', encoding='utf-8') as file:
            file.writelines(lines)
        
        return f"Successfully replaced {count} occurrences of '{old_text}' with '{new_text}' in lines {start_line} to {end_line}."
    except Exception as e:
        return f"Error: {str(e)}"
    
# Suggested additional tools:

# 1. project_structure(directory_path):
#    """
#    Generate a tree-like structure of the project directory.
#    This would help in understanding the overall structure of the project.
#    """

# 2. summarize_file(file_path):
#    """
#    Provide a summary of a file's contents, including key functions, classes, and overall purpose.
#    This would be useful for quickly understanding the role of a file in a large project.
#    """

# 3. diff_changes(file_path, start_line, end_line):
#    """
#    Show a visual diff of recent changes made to a specific part of a file.
#    This would help in reviewing and confirming changes made during the conversation.
#    """

# 4. run_tests(test_path):
#    """
#    Run specified tests and return the results.
#    This would allow for immediate validation of changes made to the codebase.
#    """

# 5. generate_docstring(file_path, function_name):
#    """
#    Automatically generate or update a docstring for a specified function.
#    This would help in maintaining up-to-date documentation as code changes.
#    """

# 6. find_references(project_path, symbol):
#    """
#    Find all references to a particular symbol (function, class, variable) across the project.
#    This would be useful for understanding dependencies and the impact of potential changes.
#    """

# 7. code_quality_check(file_path):
#    """
#    Perform a code quality check on a file, reporting potential issues or improvements.
#    This could include style checks, complexity analysis, and common error detection.
#    """

# 8. context_summary():
#    """
#    Provide a summary of the current conversation context, including main topics discussed and actions taken.
#    This would help in managing long conversations and maintaining focus.
#    """
