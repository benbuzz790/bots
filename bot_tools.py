import os

def rewrite(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"File '{file_path}' has been rewritten with the provided content.")

def insert_after(file_path, target_string, content_to_insert):
    with open(file_path, 'r') as file:
        content = file.read()

    if target_string in content:
        target_index = content.find(target_string) + len(target_string)
        updated_content = content[:target_index] + '\n' + content_to_insert + content[target_index:]
        
        with open(file_path, 'w') as file:
            file.write(updated_content)
        
        print(f"Content inserted after the first occurrence of '{target_string}' in the file.")
    else:
        print(f"Target string '{target_string}' not found in the file.")

def paste_over(file_path, target_string, content_to_paste):
    try:
        with open(file_path, 'r') as file:
            content = file.read()
            target_index = content.find(target_string)
            if target_index != -1:
                updated_content = content[:target_index] + content_to_paste + content[target_index + len(target_string):]
                with open(file_path, 'w') as file:
                    file.write(updated_content)
                print(f"Content pasted over the first occurrence of '{target_string}' in the file.")
            else:
                print(f"Target string '{target_string}' not found in the file.")
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")

def find_function_definition(file_path, function_name):
    with open(file_path, 'r') as file:
        lines = file.readlines()
    
    for i, line in enumerate(lines):
        if line.startswith(f"def {function_name}("):
            function_definition = line
            j = i + 1
            while j < len(lines) and (lines[j].startswith(' ') or lines[j].startswith('	')):
                function_definition += lines[j]
                j += 1
            return i + 1, function_definition.strip()
    
    return None, None

def replace_function_definition(file_path, function_name, new_function_definition):
    line_number, existing_definition = find_function_definition(file_path, function_name)
    if existing_definition:
        with open(file_path, 'r') as file:
            lines = file.readlines()
        
        lines[line_number - 1] = new_function_definition + '\n'
        
        with open(file_path, 'w') as file:
            file.writelines(lines)
        
        print(f"Function definition for '{function_name}' replaced in the file.")
    else:
        print(f"Function '{function_name}' not found in the file.")

def append_to_file(file_path, content_to_append):
    with open(file_path, 'a') as file:
        file.write(content_to_append)
    print(f"Content appended to the file '{file_path}'.")

def prepend_to_file(file_path, content_to_prepend):
    with open(file_path, 'r+') as file:
        content = file.read()
        file.seek(0, 0)
        file.write(content_to_prepend + content)
    print(f"Content prepended to the file '{file_path}'.")

def create_directory(directory_path):
    if not os.path.exists(directory_path):
        os.makedirs(directory_path)
        print(f"Directory '{directory_path}' created.")
    else:
        print(f"Directory '{directory_path}' already exists.")

# Add more tool functions as needed
