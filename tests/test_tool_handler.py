import os
import tempfile
import textwrap
import unittest
from types import ModuleType
from typing import Dict, List

from bots.foundation.base import ToolHandler


class DummyToolHandler(ToolHandler):

    def generate_tool_schema(self, func):
        """Simple schema generation for testing"""
        return {
            "name": func.__name__,
            "description": func.__doc__ or "",
            "parameters": {param: {"type": "any"} for param in func.__code__.co_varnames[: func.__code__.co_argcount]},
        }

    def generate_request_schema(self, response):
        """Dummy implementation - returns empty list"""
        return []

    def tool_name_and_input(self, request_schema):
        """Dummy implementation"""
        return (None, {})

    def generate_response_schema(self, request, tool_output_kwargs):
        """Dummy implementation"""
        return {}

    def generate_error_schema(self, request_schema, error_msg):
        """Dummy implementation"""
        return {}


class TestToolHandlerPersistence(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.handler = DummyToolHandler()
        self.create_test_files()

    def tearDown(self):
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        module_content = textwrap.dedent(
            """
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
        """
        )
        self.module_path = os.path.join(self.temp_dir, "test_module.py")
        with open(self.module_path, "w") as f:
            f.write(module_content)

    def compare_tools(self, original_tools: List[Dict], loaded_tools: List[Dict], context: str):
        """Helper to compare tool schemas"""
        self.assertEqual(
            len(original_tools),
            len(loaded_tools),
            f"{context}: Different number of tools after loading",
        )
        original_tools = sorted(original_tools, key=lambda x: x["name"])
        loaded_tools = sorted(loaded_tools, key=lambda x: x["name"])
        for orig, loaded in zip(original_tools, loaded_tools):
            self.assertEqual(orig["name"], loaded["name"], f"{context}: Tool names don''t match")
            self.assertEqual(
                orig["description"],
                loaded["description"],
                f"{context}: Tool descriptions don't match",
            )
            self.assertEqual(
                orig["parameters"],
                loaded["parameters"],
                f"{context}: Tool parameters don't match",
            )

    def test_single_function_persistence(self):
        """Test saving and loading a single function tool"""
        # Create module with simple tool
        module_code = textwrap.dedent(
            """
            def simple_tool(x, y):
                '''A simple test tool'''
                return x + y
        """
        ).strip()
        # Create module and execute code
        module = ModuleType("test_simple")
        module.__source__ = module_code
        # Execute in module's namespace
        namespace = {"__name__": "test_simple"}
        exec(module_code, namespace)
        module.__dict__.update(namespace)
        # Add tool and save state
        self.handler._add_tools_from_module(module)
        original_state = self.handler.to_dict()
        self.assertEqual(len(self.handler.tools), 1, "Tool not added initially")
        self.assertEqual(len(self.handler.function_map), 1, "Function not mapped initially")
        new_handler = DummyToolHandler.from_dict(original_state)
        self.assertEqual(len(new_handler.tools), 1, "Tool not loaded")
        self.assertEqual(len(new_handler.function_map), 1, "Function not loaded")
        original_result = self.handler.function_map["simple_tool"](5, 3)
        loaded_result = new_handler.function_map["simple_tool"](5, 3)
        self.assertEqual(original_result, loaded_result, "Function execution results differ")

    def test_module_persistence(self):
        """Test saving and loading tools from a module"""
        module_code = textwrap.dedent(
            """
            def module_tool_1(x):
                '''A module test tool'''
                return x * 2

            def module_tool_2(y):
                '''Another module test tool'''
                return y + 10
            """
        ).strip()
        module = ModuleType("test_module")
        module.__source__ = module_code
        namespace = {"__name__": "test_module"}
        exec(module_code, namespace)
        module.__dict__.update(namespace)
        self.handler._add_tools_from_module(module)
        original_state = self.handler.to_dict()
        new_handler = DummyToolHandler.from_dict(original_state)
        self.assertEqual(len(new_handler.tools), 2, "Tools not loaded")
        self.assertEqual(len(new_handler.function_map), 2, "Functions not loaded")
        self.assertEqual(
            sorted(new_handler.function_map.keys()),
            ["module_tool_1", "module_tool_2"],
            "Missing expected functions",
        )
        test_value = 5
        for func_name in ["module_tool_1", "module_tool_2"]:
            self.assertIn(func_name, new_handler.function_map, f"Function {func_name} not found")
            original_result = self.handler.function_map[func_name](test_value)
            loaded_result = new_handler.function_map[func_name](test_value)
            self.assertEqual(
                original_result,
                loaded_result,
                f"Function {func_name} execution results differ",
            )

    def test_file_persistence(self):
        """Test saving and loading tools from a file"""
        self.handler._add_tools_from_file(self.module_path)
        original_state = self.handler.to_dict()
        original_tools = self.handler.tools.copy()
        new_handler = DummyToolHandler.from_dict(original_state)
        self.compare_tools(original_tools, new_handler.tools, "File")
        input_args = {"a": 5, "b": 3}
        result1 = self.handler.function_map["test_tool_1"](**input_args)
        result2 = new_handler.function_map["test_tool_1"](**input_args)
        self.assertEqual(result1["result"], result2["result"], "File tool execution results differ")
        self.assertEqual(result1["constant"], result2["constant"], "Module constant differs")
        self.assertEqual(result1["pi"], result2["pi"], "Math module constant differs")

    def test_tool_preservation(self):
        """Test that tools are properly preserved through serialization"""
        # Create module with test function
        module_code = textwrap.dedent(
            """
            def test_func(x: int) -> int:
                '''Test function'''
                return x * 2
        """
        ).strip()
        # Create module and execute code
        module = ModuleType("test_preserve")
        module.__source__ = module_code
        # Execute in module's namespace
        namespace = {"__name__": "test_preserve"}
        exec(module_code, namespace)
        module.__dict__.update(namespace)
        # Add tool and verify initial state
        self.handler._add_tools_from_module(module)
        self.assertEqual(len(self.handler.tools), 1, "Tool not added properly")
        self.assertEqual(len(self.handler.function_map), 1, "Function not mapped properly")
        state_dict = self.handler.to_dict()
        self.assertEqual(len(state_dict["tools"]), 1, "Tool not serialized")
        self.assertEqual(len(state_dict["function_paths"]), 1, "Function paths not serialized")
        new_handler = DummyToolHandler.from_dict(state_dict)
        self.assertEqual(len(new_handler.tools), 1, "Tool not deserialized")
        self.assertEqual(len(new_handler.function_map), 1, "Function map not deserialized")
        original_result = self.handler.function_map["test_func"](5)
        loaded_result = new_handler.function_map["test_func"](5)
        self.assertEqual(original_result, loaded_result, "Function behavior changed")
        self.assertEqual(self.handler.tools[0], new_handler.tools[0], "Tool schema changed")


def main():
    unittest.main()


if __name__ == "__main__":
    main()


class TestDecoratorHandling(unittest.TestCase):
    """Test cases for the general decorator handling fix"""

    def setUp(self):
        self.handler = DummyToolHandler()

    def test_single_decorator_handling(self):
        """Test that a single decorator is properly included in execution
        context"""
        # Test with the actual handle_errors decorator which is available
        # globally
        from bots.dev.decorators import handle_errors

        @handle_errors
        def test_function(x: int) -> str:
            """A test function with a decorator"""
            return str(x * 2)

        # Add the tool
        self.handler.add_tool(test_function)
        # Verify the tool was added successfully
        self.assertEqual(len(self.handler.tools), 1)
        self.assertEqual(self.handler.tools[0]["name"], "test_function")
        # Test that the tool can be executed (decorator should work)
        result = self.handler.function_map["test_function"](5)
        # Should return the result without decoration for successful calls
        self.assertEqual(result, "10")

    def test_multiple_decorators_handling(self):
        """Test that multiple decorators are properly handled"""
        # Use actual decorators that are available globally
        from bots.dev.decorators import debug_on_error, handle_errors

        @handle_errors
        @debug_on_error
        def multi_decorated_function(x: int) -> str:
            """A function with multiple decorators"""
            return str(x)

        # Add the tool
        self.handler.add_tool(multi_decorated_function)
        # Verify the tool was added successfully
        self.assertEqual(len(self.handler.tools), 1)
        self.assertEqual(self.handler.tools[0]["name"], "multi_decorated_function")
        # Test that the tool can be executed (both decorators should work)
        result = self.handler.function_map["multi_decorated_function"](42)
        # Should return the result for successful calls
        self.assertEqual(result, "42")

    def test_handle_errors_decorator(self):
        """Test the specific handle_errors decorator that caused the original
        issue"""
        # Import the actual handle_errors decorator
        from bots.dev.decorators import handle_errors

        @handle_errors
        def error_prone_function(should_fail: bool) -> str:
            """A function that might raise an error"""
            if should_fail:
                raise ValueError("Test error")
            return "success"

        # Add the tool
        self.handler.add_tool(error_prone_function)
        # Verify the tool was added successfully
        self.assertEqual(len(self.handler.tools), 1)
        self.assertEqual(self.handler.tools[0]["name"], "error_prone_function")
        # Test successful execution
        result = self.handler.function_map["error_prone_function"](False)
        self.assertEqual(result, "success")
        # Test error handling (should not raise, but return error message)
        result = self.handler.function_map["error_prone_function"](True)
        # handle_errors returns "Tool Failed: ..." format
        self.assertIn("Tool Failed", result)
