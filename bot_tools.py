
import os
import re

def rewrite(file_path, content):
    """
    Rewrite the entire contents of a file.
    """
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"File '{file_path}' has been rewritten with the provided content.")

def insert_after(file_path, target_string, content_to_insert):
    """
    Insert content into a file after a target string, function, or class.

    This function can insert content after a simple string, a function definition, or a class definition.
    It determines the type of insertion based on the target_string:

    1. If target_string starts with 'def' followed by a function name, it inserts after the entire function.
    2. If target_string starts with 'class' followed by a class name, it inserts after the entire class.
    3. Otherwise, it performs a simple string insertion.

    For function and class insertions, it maintains the structure of the Python file,
    inserting the new content after the entire definition including its body.

    Args:
        file_path (str): The path to the file to be modified.
        target_string (str): The string after which to insert the new content. This can be a simple string,
                             a function definition (starting with 'def'), or a class
                             definition (starting with 'class').
        content_to_insert (str): The content to be inserted.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an issue reading from or writing to the file.

    Examples:
        # Inserting after a simple string
        insert_after('example.txt', 'Hello', ' World!')

        # Inserting after a function definition
        insert_after('example.py', 'def old_function():', 
                     "\n\ndef new_function():\n    print('This is the new function')")

        # Inserting after a class definition
        insert_after('example.py', 'class OldClass:', 
                     "\n\nclass NewClass:\n    def __init__(self):\n        print('This is the new class')")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    with open(file_path, 'r') as file:
        content = file.read()

    func_match = re.match(r'def\s+(\w+)\s*\(', target_string)
    class_match = re.match(r'class\s+(\w+)', target_string)

    if func_match:
        function_name = func_match.group(1)
        pattern = r'def\s+' + re.escape(function_name) + r'\s*\([^)]*\):.*?(?=\n(?=\S)|\Z)'
        match = re.search(pattern, content, re.DOTALL)
    elif class_match:
        class_name = class_match.group(1)
        pattern = r'class\s+' + re.escape(class_name) + r'\s*(?:\([^)]*\))?:.*?(?=\n(?=\S)|\Z)'
        match = re.search(pattern, content, re.DOTALL)
    else:
        match = re.search(re.escape(target_string), content)

    if match:
        insert_position = match.end()
        updated_content = content[:insert_position] + content_to_insert + content[insert_position:]
        
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Content inserted after '{target_string}' in the file.")
    else:
        print(f"Target '{target_string}' not found in the file.")

def replace(file_path, target_string, new_string):
    """
    Replace a target string in a file with new content.

    This function can replace simple strings, function definitions, or class definitions.
    It determines the type of replacement based on the target_string:

    1. If target_string starts with 'def' followed by a function name, it replaces the entire function.
    2. If target_string starts with 'class' followed by a class name, it replaces the entire class.
    3. Otherwise, it performs a simple string replacement.

    For function and class replacements, it maintains the structure of the Python file,
    replacing the entire definition including its body.

    Args:
        file_path (str): The path to the file to be modified.
        target_string (str): The string to be replaced. This can be a simple string,
                             a function definition (starting with 'def'), or a class
                             definition (starting with 'class').
        new_string (str): The new content to replace the target string. For function
                          and class replacements, this should be the entire new
                          definition including the body.

    Raises:
        FileNotFoundError: If the specified file does not exist.
        IOError: If there's an issue reading from or writing to the file.

    Examples:
        # Replacing a simple string
        replace('example.txt', 'old text', 'new text')

        # Replacing a function definition
        replace('example.py', 'def old_function():', 
                "def new_function():\n    print('This is the new function')")

        # Replacing a class definition
        replace('example.py', 'class OldClass:', 
                "class NewClass:\n    def __init__(self):\n        print('This is the new class')")
    """
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    
    func_match = re.match(r'def\s+(\w+)\s*\(', target_string)
    class_match = re.match(r'class\s+(\w+)', target_string)
    
    if func_match:
        function_name = func_match.group(1)
        overwrite_function(file_path, function_name, new_string)
    elif class_match:
        class_name = class_match.group(1)
        overwrite_class(file_path, class_name, new_string)
    else:
        with open(file_path, 'r') as file:
            content = file.read()
        target_index = content.find(target_string)
        if target_index != -1:
            updated_content = content[:target_index] + new_string + content[target_index + len(target_string):]
            with open(file_path, 'w') as file:
                file.write(updated_content)
            print(f"Content replaced '{target_string}' in the file.")
        else:
            print(f"Target string '{target_string}' not found in the file.")

def append(file_path, content_to_append):
    with open(file_path, 'a') as file:
        file.write(content_to_append)
    print(f"Content appended to the file '{file_path}'.")

def prepend(file_path, content_to_prepend):
    with open(file_path, 'r+') as file:
        content = file.read()
        file.seek(0, 0)
        file.write(content_to_prepend + content)
    print(f"Content prepended to the file '{file_path}'.")

def delete_match(file_path, pattern):
    try:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        with open(file_path, 'w') as file:
            for line in lines:
                if pattern.lower() not in line.lower():
                    file.write(line)
        
        print(f"Lines containing '{pattern}' (case-insensitive) have been deleted from '{file_path}'.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")

def overwrite_function(file_path, function_name, new_function_content):
    with open(file_path, 'r') as file:
        content = file.read()
    
    pattern = r'def\s+' + re.escape(function_name) + r'\s*\([^)]*\):.*?(?=\n(?=\S)|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        updated_content = content[:match.start()] + new_function_content.rstrip() + content[match.end():]
        with open(file_path, 'w') as file:
            file.write(updated_content)
        print(f"Function '{function_name}' has been overwritten in '{file_path}'.")
    else:
        print(f"Function '{function_name}' not found in '{file_path}'.")

def overwrite_class(file_path, class_name, new_class_content):
    with open(file_path, 'r') as file:
        content = file.read()
    
    pattern = r'class\s+' + re.escape(class_name) + r'\s*(?:\([^)]*\))?:.*?(?=\n(?=\S)|\Z)'
    match = re.search(pattern, content, re.DOTALL)
    
    if match:
        updated_content = content[:match.start()] + new_class_content.rstrip() + content[match.end():]
        with open(file_path, 'w') as file:
            file.write(updated_content)
        print(f"Class '{class_name}' has been overwritten in '{file_path}'.")
    else:
        print(f"Class '{class_name}' not found in '{file_path}'.")