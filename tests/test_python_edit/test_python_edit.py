import sys
from bots.tools.python_edit import python_edit  # noqa: E402
# Test 1: Replace a method - should this replace or append?
print("=== Test 1: Replace existing_method ===")
result = python_edit(target_scope="test_replace_behavior.py::TestClass::existing_method", code='''def existing_method(self):
    return "replaced"''')
print("Result:", result)
# Check what happened
with open("test_replace_behavior.py", "r") as f:
    content = f.read()
print("File content after replacement:")
print(content)
print("=" * 50)
# Test 2: Add a new method
print("\n=== Test 2: Add new_method ===")
result = python_edit(target_scope="test_replace_behavior.py::TestClass::new_method", code='''def new_method(self):
    return "new method added"''')
print("Result:", result)
# Check what happened
with open("test_replace_behavior.py", "r") as f:
    content = f.read()
print("File content after adding new method:")
print(content)
print("=" * 50)
# Test 3: Replace entire class
print("\n=== Test 3: Replace entire TestClass ===")
result = python_edit(target_scope="test_replace_behavior.py::TestClass", code='''class TestClass:
    def __init__(self):
        self.value = "completely replaced class"

    def get_value(self):
        return self.value''')
print("Result:", result)
# Check what happened
with open("test_replace_behavior.py", "r") as f:
    content = f.read()
print("File content after class replacement:")
print(content)
print("=" * 50)
# Test 4: Test insert_after functionality
print("\n=== Test 4: Test insert_after ===")
# First, let's create a fresh test file
test_content = '''class TestInsert:
    def method1(self):
        return "method1"

    def method3(self):
        return "method3"
'''
with open("test_insert.py", "w") as f:
    f.write(test_content)
# Now insert method2 after method1
result = python_edit(target_scope="test_insert.py::TestInsert", code='''def method2(self):
    return "method2 inserted"''', insert_after="method1")
print("Result:", result)
# Check what happened
with open("test_insert.py", "r") as f:
    content = f.read()
print("File content after insert_after:")
print(content)
print("=" * 50)
# Test 5: Test function-level operations
print("\n=== Test 5: Function-level operations ===")
# Create a file with standalone functions
func_content = '''def func1():
    return "original func1"

def func2():
    return "original func2"

def func3():
    return "original func3"
'''
with open("test_functions.py", "w") as f:
    f.write(func_content)
# Replace func2
result = python_edit(target_scope="test_functions.py::func2", code='''def func2():
    return "replaced func2"
    # with extra comment''')
print("Result:", result)
# Check what happened
with open("test_functions.py", "r") as f:
    content = f.read()
print("File content after function replacement:")
print(content)
print("=" * 50)
# Test 6: Test nested class operations
print("\n=== Test 6: Nested class operations ===")
nested_content = '''class Outer:
    def outer_method(self):
        return "outer"

    class Inner:
        def inner_method(self):
            return "original inner"

        def another_inner(self):
            return "another inner"
'''
with open("test_nested.py", "w") as f:
    f.write(nested_content)
# Replace inner method
result = python_edit(target_scope="test_nested.py::Outer::Inner::inner_method", code='''def inner_method(self):
    return "replaced inner method"''')
print("Result:", result)
# Check what happened
with open("test_nested.py", "r") as f:
    content = f.read()
print("File content after nested method replacement:")
print(content)
print("=" * 50)
print("All tests completed!")