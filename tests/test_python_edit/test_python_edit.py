import sys
sys.path.append('.')
from bots.tools.python_edit import python_edit
# Test 1: Replace a method - should this replace or append?
print("=== Test 1: Replace existing_method ===")
result = python_edit(
    target_scope="test_replace_behavior.py::TestClass::existing_method",
    code='''def existing_method(self):
    return "replaced"'''
)
print("Result:", result)
# Check what happened
with open('test_replace_behavior.py', 'r') as f:
    content = f.read()
print("File content after replacement:")
print(content)
print("=" * 50)
