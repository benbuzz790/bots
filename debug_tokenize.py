from tests.test_python_edit import setup_test_file
from bots.tools.python_edit import _tokenize_source, _detokenize_source
import ast

# Test with the exact content from the failing test
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

print(f"Original content:\n{repr(file_content)}")

try:
    tokenized, token_map = _tokenize_source(file_content)
    print(f"\nTokenized content:\n{repr(tokenized)}")
    print(f"\nToken map: {token_map}")
    
    # Let's see what happens line by line
    lines = tokenized.split('\n')
    for i, line in enumerate(lines):
        print(f"Line {i}: {repr(line)}")
    
    # Try to parse the tokenized content
    tree = ast.parse(tokenized)
    print("\nTokenized content parses successfully!")
    
except Exception as e:
    print(f"\nError during tokenization/parsing: {e}")
    print(f"Error type: {type(e)}")
    
    # Let's try to parse each line individually to see which one fails
    lines = tokenized.split('\n')
    for i, line in enumerate(lines):
        if line.strip():
            try:
                ast.parse(line)
                print(f"Line {i} parses OK: {repr(line)}")
            except Exception as line_e:
                print(f"Line {i} FAILS: {repr(line)} - {line_e}")
