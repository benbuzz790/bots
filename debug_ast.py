from tests.test_python_edit import setup_test_file
from bots.tools.python_edit import _tokenize_source, _detokenize_source
from bots.utils.helpers import _py_ast_to_source
import ast

content = """
# Top level comment
import os  # os import

def example():  # example function
    \"\"\"Docstring.\"\"\"

    # First we do x
    x = 1  # comment about x

    # Then we do y
    y = 2  # comment about y
"""

test_file = setup_test_file('tmp', content)

with open(test_file, 'r') as f:
    file_content = f.read()

print("=== ORIGINAL ===")
print(repr(file_content))

tokenized, token_map = _tokenize_source(file_content)
print("\n=== TOKENIZED ===")
print(repr(tokenized))

tree = ast.parse(tokenized)
ast_output = _py_ast_to_source(tree)
print("\n=== AFTER AST PROCESSING ===")
print(repr(ast_output))

final = _detokenize_source(ast_output, token_map)
print("\n=== FINAL ===")
print(repr(final))
print("\n=== FINAL FORMATTED ===")
print(final)
