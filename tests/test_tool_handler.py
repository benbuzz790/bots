import unittest
import os
import tempfile
import textwrap
from types import ModuleType
from typing import Dict, Any, List
from bots.foundation.base import ToolHandler


class DummyToolHandler(ToolHandler):

    def generate_tool_schema(self, func):
        """Simple schema generation for testing"""
        return {'name': func.__name__, 'description': func.__doc__ or '',
            'parameters': {param: {'type': 'any'} for param in func.
            __code__.co_varnames[:func.__code__.co_argcount]}}

    def generate_request_schema(self, response):
        """Dummy implementation - returns empty list"""
        return []

    def tool_name_and_input(self, request_schema):
        """Dummy implementation"""
        return None, {}

    def generate_response_schema(self, request, tool_output_kwargs):
        """Dummy implementation"""
        return {}

    def generate_error_schema(self, request_schema, error_msg):
        """Dummy implementation"""
        return {}


def helper_function(x):
    return x * 2


def main_function(x):
    """A function that depends on a helper"""
    return helper_function(x)


def simple_tool(x, y):
    """A simple test tool"""
    return x + y


def sample_func(x: int) ->int:
    """Test function"""
    return x * 2


class TestToolHandlerPersistence(unittest.TestCase):

    def test_helper_function_context(self):
        """Test that helper function context is preserved when adding a single callable"""
        self.handler.add_tool(main_function)
        original_result = self.handler.function_map['main_function'](5)
        self.assertEqual(original_result, 10,
            'Original function execution failed')
        state_dict = self.handler.to_dict()
        new_handler = DummyToolHandler.from_dict(state_dict)
        loaded_result = new_handler.function_map['main_function'](5)
        self.assertEqual(loaded_result, 10,
            'Restored function execution failed')
        self.assertEqual(original_result, loaded_result,
            'Results differ after restoration')

    def test_tool_preservation(self):
        """Test that tools are properly preserved through serialization"""
        self.handler.add_tool(sample_func)
        self.assertEqual(len(self.handler.tools), 1, 'Tool not added properly')
        self.assertEqual(len(self.handler.function_map), 1,
            'Function not mapped properly')
        state_dict = self.handler.to_dict()
        self.assertEqual(len(state_dict['tools']), 1, 'Tool not serialized')
        self.assertEqual(len(state_dict['function_paths']), 1,
            'Function paths not serialized')
        new_handler = DummyToolHandler.from_dict(state_dict)
        self.assertEqual(len(new_handler.tools), 1, 'Tool not deserialized')
        self.assertEqual(len(new_handler.function_map), 1,
            'Function map not deserialized')
        original_result = self.handler.function_map['sample_func'](5)
        loaded_result = new_handler.function_map['sample_func'](5)
        self.assertEqual(original_result, loaded_result,
            'Function behavior changed')
        self.assertEqual(self.handler.tools[0], new_handler.tools[0],
            'Tool schema changed')

    def setUp(self):
        """Initialize a fresh DummyToolHandler instance before each test"""
        self.handler = DummyToolHandler()

    def tearDown(self):
        """Clean up after each test"""
        self.handler = None


def main():
    unittest.main()


if __name__ == '__main__':
    main()
