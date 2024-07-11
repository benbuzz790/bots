
import os
import re

def rewrite(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"File '{file_path}' has been rewritten with the provided content.")

def insert_after(file_path, target_string, content_to_insert):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    with open(file_path, 'r') as file:
        content = file.read()

    if target_string in content:
        target_index = content.find(target_string) + len(target_string)
        updated_content = content[:target_index] + content_to_insert + content[target_index:]
        
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Content inserted after the first occurrence of '{target_string}' in the file.")
    else:
        print(f"Target string '{target_string}' not found in the file.")

def replace(file_path, target_string, new_string):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
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
