import os
import tempfile
import textwrap
import unittest

from bots.foundation.base import ToolHandler


class DummyToolHandler(ToolHandler):
    """Simple schema generation for testing purposes.

    Args:
        func: The function to generate a schema for.

    Returns:
        dict: A dictionary containing the function name and description, with keys
            'name' (function name as string) and 'description' (docstring or empty string).
    """
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
    """Test class for verifying tool handler persistence functionality.

    Sets up a temporary directory and dummy tool handler for testing persistence
    operations across test methods.

    Attributes:
        temp_dir (str): Temporary directory path for test files.
        handler (DummyToolHandler): Mock tool handler instance for testing.
    """
    def setUp(self):
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh DummyToolHandler object
        assigned to self.handler for use in test methods.
        """
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh handler instance for each test case.
        """
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh DummyToolHandler object
        assigned to self.handler for use in test methods.
        """
        """Set up test fixtures by initializing a DummyToolHandler instance.

        This method is called before each test method to ensure a clean test environment
        with a fresh handler instance.

        Note:
            This is a test setup method typically used with unittest framework.
        """
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh DummyToolHandler object
        assigned to self.handler for use in test methods.
        """
        """Initialize test fixture with a DummyToolHandler instance.

        Sets up the test environment by creating a DummyToolHandler object
        and assigning it to the handler attribute for use in test methods.
        """
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh DummyToolHandler object
        assigned to self.handler for use in test methods.
        """
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh DummyToolHandler object
        assigned to self.handler for use in test methods.
        """
        """Initialize test fixture by creating a DummyToolHandler instance.

        Sets up the test environment with a fresh DummyToolHandler object
        assigned to self.handler for use in test methods.
        """
        """Set up test environment with temporary directory and test files.

        Creates a temporary directory, initializes a DummyToolHandler instance,
        and generates necessary test files for the test suite.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.handler = DummyToolHandler()
        self.create_test_files()

    def tearDown(self):
        """Clean up test resources by removing the temporary directory.

        This method is called after each test method to ensure proper cleanup
        of the temporary directory and all its contents created during testing.

        Raises:
            OSError: If the temporary directory cannot be removed due to
                permission issues or if it doesn't exist.
        """
        import shutil

        shutil.rmtree(self.temp_dir)

    def create_test_files(self):
        """Creates test module files with sample content for testing purposes.

        This method generates a Python module containing a simple test function
        that doubles an integer input value.

        Returns:
            None: Method performs file creation as a side effect.
        """
        module_content = textwrap.dedent(
            """
            def test_function(x: int) -> int:
                '''Test function'''
                return x * 2
            """
        )
        self.test_file = os.path.join(self.temp_dir, "test_module.py")
        with open(self.test_file, "w") as f:
            f.write(module_content)

    def test_add_tool_from_file(self):
        """Test adding a tool from a file"""
        self.handler._add_tools_from_file(self.test_file)
        self.assertEqual(len(self.handler.tools), 1)
        self.assertIn("test_function", self.handler.function_map)

    def test_serialization_roundtrip(self):
        """Test that handler state can be serialized and restored"""
        self.handler._add_tools_from_file(self.test_file)
        serialized = self.handler.to_dict()
        new_handler = DummyToolHandler.from_dict(serialized)
        self.assertEqual(len(new_handler.tools), len(self.handler.tools))
        self.assertIn("test_function", new_handler.function_map)

    def test_decorator_handling(self):
        """Test that decorators are properly handled during serialization"""
        from bots.dev.decorators import toolify

        @toolify()
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
        self.assertEqual(result, "10")


class TestToolRegistry(unittest.TestCase):
    """Test lazy-loading tool registry functionality."""

    def setUp(self):
        self.handler = DummyToolHandler()

    def test_register_tool(self):
        """Test registering a tool without loading it."""

        def test_tool(x: int) -> int:
            """A test tool."""
            return x * 2

        # Register tool without loading
        self.handler.register_tool(test_tool)

        # Should be in registry but not in active tools
        self.assertIn("test_tool", self.handler.tool_registry)
        self.assertNotIn("test_tool", self.handler.function_map)
        self.assertEqual(len(self.handler.tools), 0)
        self.assertFalse(self.handler.tool_registry["test_tool"]["loaded"])

    def test_load_tool_by_name(self):
        """Test loading a tool from registry."""

        def test_tool(x: int) -> int:
            """A test tool."""
            return x * 2

        # Register and load
        self.handler.register_tool(test_tool)
        result = self.handler.load_tool_by_name("test_tool")

        self.assertTrue(result)
        self.assertIn("test_tool", self.handler.function_map)
        self.assertEqual(len(self.handler.tools), 1)
        self.assertTrue(self.handler.tool_registry["test_tool"]["loaded"])

        # Test the function works
        self.assertEqual(self.handler.function_map["test_tool"](5), 10)

    def test_load_nonexistent_tool(self):
        """Test loading a tool that doesn't exist in registry."""
        result = self.handler.load_tool_by_name("nonexistent")
        self.assertFalse(result)

    def test_unload_tool(self):
        """Test unloading a tool from active set."""

        def test_tool(x: int) -> int:
            """A test tool."""
            return x * 2

        # Register, load, then unload
        self.handler.register_tool(test_tool)
        self.handler.load_tool_by_name("test_tool")
        result = self.handler.unload_tool("test_tool")

        self.assertTrue(result)
        self.assertNotIn("test_tool", self.handler.function_map)
        self.assertEqual(len(self.handler.tools), 0)
        self.assertIn("test_tool", self.handler.tool_registry)
        self.assertFalse(self.handler.tool_registry["test_tool"]["loaded"])

    def test_get_registry_info(self):
        """Test getting registry information."""

        def tool_one(x: int) -> int:
            """First tool."""
            return x

        def tool_two(y: str) -> str:
            """Second tool."""
            return y

        # Register both, load only one
        self.handler.register_tool(tool_one)
        self.handler.register_tool(tool_two)
        self.handler.load_tool_by_name("tool_one")

        # Get all info
        info = self.handler.get_registry_info()
        self.assertEqual(len(info), 2)

        # Check loaded status
        tool_one_info = [i for i in info if i["name"] == "tool_one"][0]
        tool_two_info = [i for i in info if i["name"] == "tool_two"][0]

        self.assertTrue(tool_one_info["loaded"])
        self.assertFalse(tool_two_info["loaded"])

    def test_get_registry_info_with_filter(self):
        """Test filtering registry information."""

        def tool_one(x: int) -> int:
            """First tool."""
            return x

        def tool_two(y: str) -> str:
            """Second tool."""
            return y

        self.handler.register_tool(tool_one)
        self.handler.register_tool(tool_two)

        # Test filtering
        filtered = self.handler.get_registry_info(filter="one")
        self.assertEqual(len(filtered), 1)
        self.assertEqual(filtered[0]["name"], "tool_one")

    def test_registry_serialization(self):
        """Test that tool registry is preserved across save/load."""

        def registered_tool(x: int) -> int:
            """A registered tool."""
            return x * 5

        # Register tool without loading
        self.handler.register_tool(registered_tool)

        # Serialize
        handler_dict = self.handler.to_dict()

        # Check registry is in serialized data
        self.assertIn("tool_registry", handler_dict)
        self.assertIn("registered_tool", handler_dict["tool_registry"])

        # Deserialize
        new_handler = DummyToolHandler.from_dict(handler_dict)

        # Check registry is restored
        self.assertIn("registered_tool", new_handler.tool_registry)
        self.assertFalse(new_handler.tool_registry["registered_tool"]["loaded"])

        # Should be able to load it
        result = new_handler.load_tool_by_name("registered_tool")
        self.assertTrue(result)
        self.assertIn("registered_tool", new_handler.function_map)
