import sys
from bots.tools.python_edit import python_edit
sys.path.append(".")
print("=== Test 2: Replace entire class ===")
result = python_edit(target_scope="test_replace_behavior.py::TestClass", code='class TestClass:\n    def new_method(self):\n        return "completely new class"')
print("Result:", result)
with open("test_replace_behavior.py", "r") as f:
    content = f.read()
print("File content after class replacement:")
print(content)