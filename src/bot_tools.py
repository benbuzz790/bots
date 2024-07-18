import ast
import astor
import os
import re

def rewrite(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"File '{file_path}' has been rewritten with the provided content.")

def replace_string(file_path, old_string, new_string):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    with open(file_path, 'r') as file:
        content = file.read()

    # Using regex to replace all instances of old_string with new_string
    updated_content = re.sub(re.escape(old_string), new_string, content)

    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(f"Replaced all instances of '{old_string}' with '{new_string}' in '{file_path}'.")

def replace_class(file_path, new_class_def):
    with open(file_path, 'r') as file:
        content = file.read()

    new_class_node = ast.parse(new_class_def).body[0]
    if not isinstance(new_class_node, ast.ClassDef):
        raise ValueError("Provided definition is not a class")

    tree = ast.parse(content)

    class ClassReplacer(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            if node.name == new_class_node.name:
                return new_class_node
            return node

    tree = ClassReplacer().visit(tree)

    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(f"Class '{new_class_node.name}' has been replaced in '{file_path}'.")

def replace_function(file_path, new_function_def):
    with open(file_path, 'r') as file:
        content = file.read()

    new_func_node = ast.parse(new_function_def).body[0]
    if not isinstance(new_func_node, ast.FunctionDef):
        raise ValueError("Provided definition is not a function")

    tree = ast.parse(content)

    class FunctionReplacer(ast.NodeTransformer):
        def visit_FunctionDef(self, node):
            if node.name == new_func_node.name:
                return new_func_node
            return node

    tree = FunctionReplacer().visit(tree)

    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(f"Function '{new_func_node.name}' has been replaced in '{file_path}'.")

def add_function_to_class(file_path, class_name, new_method_def):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    with open(file_path, 'r') as file:
        content = file.read()

    new_method_node = ast.parse(new_method_def).body[0]
    if not isinstance(new_method_node, ast.FunctionDef):
        raise ValueError("Provided definition is not a function")

    tree = ast.parse(content)

    class MethodAdder(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            if node.name == class_name:
                node.body.append(new_method_node)  # Append the new method to the class
                return node
            return node

    tree = MethodAdder().visit(tree)

    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(f"Method '{new_method_node.name}' has been added to class '{class_name}' in '{file_path}'.")

def add_class_to_file(file_path, class_def):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")

    with open(file_path, 'r') as file:
        content = file.read()

    new_class_node = ast.parse(class_def).body[0]
    if not isinstance(new_class_node, ast.ClassDef):
        raise ValueError("Provided definition is not a class")

    tree = ast.parse(content)
    tree.body.append(new_class_node)  # Append the new class to the module's body

    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(f"Class '{new_class_node.name}' has been added to '{file_path}'.")

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