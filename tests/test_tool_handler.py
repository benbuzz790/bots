import unittest
import os
import tempfile
import textwrap
from types import ModuleType
from typing import Dict, Any, List
from bots.foundation.base import ToolHandler

# First, let's create a concrete implementation of ToolHandler for testing
class TestToolHandler(ToolHandler):
    def generate_tool_schema(self, func):
        """Simple schema generation for testing"""
        return {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {
                param: {"type": "any"}
                for param in func.__code__.co_varnames[:func.__code__.co_argcount]
            }
        }

    def generate_request_schema(self, response):
        """Dummy implementation - returns empty list"""
        return []

    def tool_name_and_input(self, request_schema):
        """Dummy implementation"""
        return None, {}

    def generate_response_schema(self, request, tool_output_kwargs):
        """Dummy implementation"""
        return {}

class TestToolHandlerPersistence(unittest.TestCase):
    def setUp(self):
        # Create temporary directory for test files
        self.temp_dir = tempfile.mkdtemp()
        self.handler = TestToolHandler()
        
        # Create test files
        self.create_test_files()

    def tearDown(self):
        # Clean up temporary files
        import shutil
        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        # Create a test module file with dependencies
        module_content = textwrap.dedent("""
            import math
            from datetime import datetime

            CONSTANT = 42

            def helper_function(x):
                return x * 2

            def test_tool_1(a, b):
                '''A test tool that uses module-level dependencies'''
                result = helper_function(a)
                return {
                    'result': result + b,
                    'constant': CONSTANT,
                    'pi': math.pi,
                    'timestamp': datetime.now().isoformat()
                }

            def test_tool_2(x):
                '''A test tool that uses the helper function'''
                return helper_function(x)
        """)
        
        self.module_path = os.path.join(self.temp_dir, 'test_module.py')
        with open(self.module_path, 'w') as f:
            f.write(module_content)

    def compare_tools(self, original_tools: List[Dict], loaded_tools: List[Dict], context: str):
        """Helper to compare tool schemas"""
        self.assertEqual(
            len(original_tools), len(loaded_tools),
            f"{context}: Different number of tools after loading"
        )
        
        # Sort tools by name for comparison
        original_tools = sorted(original_tools, key=lambda x: x['name'])
        loaded_tools = sorted(loaded_tools, key=lambda x: x['name'])
        
        for orig, loaded in zip(original_tools, loaded_tools):
            # Compare tool schemas
            self.assertEqual(
                orig['name'], loaded['name'],
                f"{context}: Tool names don't match"
            )
            self.assertEqual(
                orig['description'], loaded['description'],
                f"{context}: Tool descriptions don't match"
            )
            self.assertEqual(
                orig['parameters'], loaded['parameters'],
                f"{context}: Tool parameters don't match"
            )

    def test_single_function_persistence(self):
        """Test saving and loading a single function tool"""
        
        def simple_tool(x, y):
            """A simple test tool"""
            return x + y
        
        # Add tool and save state
        self.handler.add_tool(simple_tool)
        original_state = self.handler.to_dict()
        
        # Verify initial state
        self.assertEqual(len(self.handler.tools), 1, "Tool not added initially")
        self.assertEqual(len(self.handler.function_map), 1, "Function not mapped initially")
        
        # Create new handler and load state
        new_handler = TestToolHandler.from_dict(original_state)
        
        # Verify loaded state
        self.assertEqual(len(new_handler.tools), 1, "Tool not loaded")
        self.assertEqual(len(new_handler.function_map), 1, "Function not loaded")
        
        # Test function execution
        original_result = self.handler.function_map['simple_tool'](5, 3)
        loaded_result = new_handler.function_map['simple_tool'](5, 3)
        self.assertEqual(original_result, loaded_result, "Function execution results differ")

    def test_module_persistence(self):
        """Test saving and loading tools from a module"""
        
        # Create a test module with clean indentation
        module_code = textwrap.dedent("""
            def module_tool_1(x):
                '''A module test tool'''
                return x * 2

            def module_tool_2(y):
                '''Another module test tool'''
                return y + 10
        """)
        
        # Create module and execute code
        module = ModuleType('test_module')
        module.__source__ = module_code
        exec(module_code, module.__dict__)
        
        # Add tools and save state
        self.handler.add_tools_from_module(module)
        original_state = self.handler.to_dict()
        
        # Verify initial state
        self.assertEqual(len(self.handler.tools), 2, "Tools not added initially")
        self.assertEqual(len(self.handler.function_map), 2, "Functions not mapped initially")
        
        # Create new handler and load state
        new_handler = TestToolHandler.from_dict(original_state)
        
        # Verify loaded state
        self.assertEqual(len(new_handler.tools), 2, "Tools not loaded")
        self.assertEqual(len(new_handler.function_map), 2, "Functions not loaded")
        
        # Test both functions
        test_value = 5
        for func_name in ['module_tool_1', 'module_tool_2']:
            original_result = self.handler.function_map[func_name](test_value)
            loaded_result = new_handler.function_map[func_name](test_value)
            self.assertEqual(original_result, loaded_result, f"Function {func_name} execution results differ")

    def test_module_persistence(self):
        """Test saving and loading tools from a module"""
        
        # Create a test module with clean indentation
        module_code = textwrap.dedent("""
def module_tool_1(x):
    '''A module test tool'''
    return x * 2

def module_tool_2(y):
    '''Another module test tool'''
    return y + 10
""").strip()
        
        # Create module and execute code
        module = ModuleType('test_module')
        module.__file__ = 'test_module.py'
        module.__source__ = module_code
        
        # Execute in module's namespace
        namespace = {'__name__': 'test_module', '__file__': 'test_module.py'}
        exec(module_code, namespace)
        module.__dict__.update(namespace)
        
        # Add tools and save state
        self.handler.add_tools_from_module(module)
        original_state = self.handler.to_dict()
        
        # Debug output
        print("\nOriginal state:")
        print(f"Tools: {len(self.handler.tools)}")
        print(f"Functions: {list(self.handler.function_map.keys())}")
        print(f"Module source:\n{module_code}")
        
        # Create new handler and load state
        new_handler = TestToolHandler.from_dict(original_state)
        
        # Debug output
        print("\nLoaded state:")
        print(f"Tools: {len(new_handler.tools)}")
        print(f"Functions: {list(new_handler.function_map.keys())}")
        if new_handler.modules:
            print(f"Module source:\n{next(iter(new_handler.modules.values())).source}")
        
        # Verify loaded state
        self.assertEqual(len(new_handler.tools), 2, "Tools not loaded")
        self.assertEqual(len(new_handler.function_map), 2, "Functions not loaded")
        self.assertEqual(
            sorted(new_handler.function_map.keys()),
            ['module_tool_1', 'module_tool_2'],
            "Missing expected functions"
        )
        
        # Test both functions
        test_value = 5
        for func_name in ['module_tool_1', 'module_tool_2']:
            self.assertIn(func_name, new_handler.function_map, f"Function {func_name} not found")
            original_result = self.handler.function_map[func_name](test_value)
            loaded_result = new_handler.function_map[func_name](test_value)
            self.assertEqual(original_result, loaded_result, 
                            f"Function {func_name} execution results differ")

    def test_file_persistence(self):
        """Test saving and loading tools from a file"""
        
        # Add tools from file and save state
        self.handler.add_tools_from_file(self.module_path)
        original_state = self.handler.to_dict()
        original_tools = self.handler.tools.copy()
        
        # Create new handler and load state
        new_handler = TestToolHandler.from_dict(original_state)
        
        # Compare tools
        self.compare_tools(original_tools, new_handler.tools, "File")
        
        # Test function execution with dependencies
        input_args = {'a': 5, 'b': 3}
        result1 = self.handler.function_map['test_tool_1'](**input_args)
        result2 = new_handler.function_map['test_tool_1'](**input_args)
        
        # Compare deterministic parts of the result
        self.assertEqual(result1['result'], result2['result'], 
                        "File tool execution results differ")
        self.assertEqual(result1['constant'], result2['constant'], 
                        "Module constant differs")
        self.assertEqual(result1['pi'], result2['pi'], 
                        "Math module constant differs")

    def test_tool_preservation(self):
        """Test that tools are properly preserved through serialization"""
        
        # Add a simple function
        def test_func(x: int) -> int:
            """Test function"""
            return x * 2
        
        # Add tool and verify initial state
        self.handler.add_tool(test_func)
        self.assertEqual(len(self.handler.tools), 1, "Tool not added properly")
        self.assertEqual(len(self.handler.function_map), 1, "Function not mapped properly")
        
        # Serialize
        state_dict = self.handler.to_dict()
        
        # Verify serialized state
        self.assertEqual(len(state_dict['tools']), 1, "Tool not serialized")
        self.assertEqual(len(state_dict['function_map']), 1, "Function map not serialized")
        
        # Deserialize to new handler
        new_handler = TestToolHandler.from_dict(state_dict)
        
        # Verify deserialized state
        self.assertEqual(len(new_handler.tools), 1, "Tool not deserialized")
        self.assertEqual(len(new_handler.function_map), 1, "Function map not deserialized")
        
        # Test function execution
        original_result = self.handler.function_map['test_func'](5)
        loaded_result = new_handler.function_map['test_func'](5)
        self.assertEqual(original_result, loaded_result, "Function behavior changed")
        
        # Compare tool schemas
        self.assertEqual(self.handler.tools[0], new_handler.tools[0], "Tool schema changed")



if __name__ == '__main__':
    unittest.main()