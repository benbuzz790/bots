import ast
import astor
import os
import re
import inspect


def rewrite(file_path, content):
    with open(file_path, 'w') as file:
        file.write(content)
    print(f"File '{file_path}' has been rewritten with the provided content.")


def replace_string(file_path, old_string, new_string):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    with open(file_path, 'r') as file:
        content = file.read()
    updated_content = re.sub(re.escape(old_string), new_string, content)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(
        f"Replaced all instances of '{old_string}' with '{new_string}' in '{file_path}'."
        )


def replace_class(file_path, new_class_def, old_class_name=None):
    with open(file_path, 'r') as file:
        content = file.read()
    new_class_node = ast.parse(_remove_common_indent(new_class_def)).body[0]
    if not isinstance(new_class_node, ast.ClassDef):
        raise ValueError('Provided definition is not a class')
    tree = ast.parse(content)

    class ClassReplacer(ast.NodeTransformer):
        def visit_ClassDef(self, node):
            if old_class_name:
                if node.name == old_class_name:
                    return new_class_node
            elif node.name == new_class_node.name:
                return new_class_node
            return node

    tree = ClassReplacer().visit(tree)
    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    replaced_class_name = (old_class_name if old_class_name else
        new_class_node.name)
    print(
        f"Class '{replaced_class_name}' has been replaced with '{new_class_node.name}' in '{file_path}'."
        )


def replace_function(file_path, new_function_def):
    with open(file_path, 'r') as file:
        content = file.read()
    new_func_node: ast.FunctionDef = ast.parse(_remove_common_indent(
        new_function_def)).body[0]
    if not isinstance(new_func_node, ast.FunctionDef):
        raise ValueError('Provided definition is not a function')
    tree = ast.parse(content)


    class FunctionReplacer(ast.NodeTransformer):

        def __init__(self):
            self.success = False

        def visit_FunctionDef(self, node):
            self.success = True
            if node.name == new_func_node.name:
                return new_func_node
            return node
    transformer = FunctionReplacer()
    tree = transformer.visit(tree)
    if not transformer.success:
        ValueError(
            f"Function'{new_func_node.name}' not found in the file:\n\n{content}\n\n."
            )
    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(
        f"Function '{new_func_node.name}' has been replaced in '{file_path}'.")


def add_function_to_class(file_path, class_name, new_method_def):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    with open(file_path, 'r') as file:
        content = file.read()
    new_method_node = ast.parse(_remove_common_indent(new_method_def)).body[0]
    if not isinstance(new_method_node, ast.FunctionDef):
        raise ValueError('Provided definition is not a function')
    tree = ast.parse(content)


    class MethodAdder(ast.NodeTransformer):

        def __init__(self):
            self.success = False

        def visit_ClassDef(self, node):
            if node.name == class_name:
                self.success = True
                node.body.append(new_method_node)
                return node
            return node
    transformer = MethodAdder()
    tree = transformer.visit(tree)
    if not transformer.success:
        raise ValueError(
            f"Class '{class_name}' not found in the file:\n\n{content}\n\n.")
    updated_content = astor.to_source(tree)
    with open(file_path, 'w') as file:
        file.write(updated_content)
    print(
        f"Method '{new_method_node.name}' has been added to class '{class_name}' in '{file_path}'."
        )


def add_class_to_file(file_path, class_def):
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"File '{file_path}' not found.")
    with open(file_path, 'r') as file:
        content = file.read()
    new_class_node = ast.parse(_remove_common_indent(class_def)).body[0]
    if not isinstance(new_class_node, ast.ClassDef):
        raise ValueError('Provided definition is not a class')
    tree = ast.parse(content)
    tree.body.append(new_class_node)
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
        print(
            f"Lines containing '{pattern}' (case-insensitive) have been deleted from '{file_path}'."
            )
    except FileNotFoundError:
        print(f"File '{file_path}' not found.")


def read_file(file_path):
    with open(file_path, 'r', encoding='utf-8') as file:
        return file.read()


def _remove_common_indent(code):
    return inspect.cleandoc(code)
