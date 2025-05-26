from tests.test_python_edit import setup_test_file
from bots.tools.python_edit import python_edit

content = '''
# Top level comment
import os  # os import

def example():  # example function
    """Docstring."""

    # First we do x
    x = 1  # comment about x

    # Then we do y
    y = 2  # comment about y
'''

test_file = setup_test_file('tmp', content)
print(f"Test file: {test_file}")
result = python_edit(f'{test_file}::example', 'z = 3', insert_after='# Then we do y')
print(f'python_edit result: {result}')

with open(test_file) as f:
    final_content = f.read()
print(f'Final content:\n{final_content}')
