import os
import shutil
import tempfile
import unittest
from types import ModuleType

import bots
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


def create_test_file(content: str) -> str:
    """Creates a temporary Python file with the given content and returns
    its path."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".py", delete=False) as f:
        f.write(content)
        return f.name


def create_test_module(name: str, content: str) -> ModuleType:
    """Creates a module with the given name and content."""
    module = ModuleType(name)
    module.__source__ = content
    exec(content, module.__dict__)
    return module


class TestAddTools2(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=1000,
            temperature=0,
            name="TestBot",
            autosave=False,
        )
        # Create temp directory for all test files
        self.test_dir = tempfile.mkdtemp()
        self.test_file1_content = (
            '\ndef tool1():\n    """Test tool 1"""\n    return "tool1"\n'
            '\ndef tool2():\n    """Test tool 2"""\n    return "tool2"\n'
        )
        self.test_file2_content = (
            '\ndef tool3():\n    """Test tool 3"""\n    return "tool3"\n'
            '\ndef tool4():\n    """Test tool 4"""\n    return "tool4"\n'
        )
        self.test_file1 = create_test_file(self.test_file1_content)
        self.test_file2 = create_test_file(self.test_file2_content)
        self.module1 = create_test_module(
            "module1",
            (
                '\ndef module1_tool1():\n    """Module 1 Tool 1"""\n'
                '    return "module1_tool1"\n'
                '\ndef module1_tool2():\n    """Module 1 Tool 2"""\n'
                '    return "module1_tool2"\n'
            ),
        )
        self.module2 = create_test_module(
            "module2",
            (
                '\ndef module2_tool1():\n    """Module 2 Tool 1"""\n'
                '    return "module2_tool1"\n'
                '\ndef module2_tool2():\n    """Module 2 Tool 2"""\n'
                '    return "module2_tool2"\n'
            ),
        )

    def test_single_file(self):
        """Test adding tools from a single file."""
        self.bot.add_tools(self.test_file1)
        tools = self.bot.tool_handler.function_map
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)

    def test_multiple_files(self):
        """Test adding tools from multiple files."""
        self.bot.add_tools(self.test_file1, self.test_file2)
        tools = self.bot.tool_handler.function_map
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
        self.assertIn("tool3", tools)
        self.assertIn("tool4", tools)

    def test_single_module(self):
        """Test adding tools from a single module."""
        self.bot.add_tools(self.module1)
        tools = self.bot.tool_handler.function_map
        self.assertIn("module1_tool1", tools)
        self.assertIn("module1_tool2", tools)

    def test_multiple_modules(self):
        """Test adding tools from multiple modules."""
        self.bot.add_tools(self.module1, self.module2)
        tools = self.bot.tool_handler.function_map
        self.assertIn("module1_tool1", tools)
        self.assertIn("module1_tool2", tools)
        self.assertIn("module2_tool1", tools)
        self.assertIn("module2_tool2", tools)

    def test_mixed_files_and_modules(self):
        """Test adding tools from a mix of files and modules."""
        self.bot.add_tools(self.test_file1, self.module1, self.test_file2, self.module2)
        tools = self.bot.tool_handler.function_map
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
        self.assertIn("tool3", tools)
        self.assertIn("tool4", tools)
        self.assertIn("module1_tool1", tools)
        self.assertIn("module1_tool2", tools)
        self.assertIn("module2_tool1", tools)
        self.assertIn("module2_tool2", tools)

    def test_single_function(self):
        """Test adding a single function as a tool."""

        def test_function():
            """Test function"""
            return "test_function"

        self.bot.add_tools(test_function)
        tools = self.bot.tool_handler.function_map
        self.assertIn("test_function", tools)

    def test_list_input(self):
        """Test adding tools from a list containing mixed types."""

        def test_function():
            """Test function"""
            return "test_function"

        tool_list = [self.test_file1, self.module1, test_function]
        self.bot.add_tools(tool_list)
        tools = self.bot.tool_handler.function_map
        self.assertIn("tool1", tools)
        self.assertIn("tool2", tools)
        self.assertIn("module1_tool1", tools)
        self.assertIn("module1_tool2", tools)
        self.assertIn("test_function", tools)

    def test_invalid_input(self):
        """Test that invalid input types raise appropriate exceptions."""
        with self.assertRaises(TypeError):
            self.bot.add_tools(123)
        with self.assertRaises(FileNotFoundError):
            self.bot.add_tools("nonexistent_file.py")

    def test_save_load_dynamic_function(self):
        """Test that dynamically created functions persist through
        save/load."""

        def dynamic_func():
            """Test dynamic function"""
            return "dynamic_result"

        self.bot.add_tools(dynamic_func)
        save_path = os.path.join(self.test_dir, f"dynamic_func_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = bots.load(save_path)
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertEqual(
            self.bot.tool_handler.function_map["dynamic_func"].__doc__,
            loaded_bot.tool_handler.function_map["dynamic_func"].__doc__,
        )
        original_result = self.bot.tool_handler.function_map["dynamic_func"]()
        loaded_result = loaded_bot.tool_handler.function_map["dynamic_func"]()
        self.assertEqual(original_result, loaded_result)

    def test_save_load_mixed_sources(self):
        """Test persistence of tools from multiple sources."""

        def dynamic_func():
            """Test dynamic function"""
            return "dynamic_result"

        file_content = '\ndef file_func():\n    """Test file function"""\n' '    return "file_result"\n    '
        test_file = create_test_file(file_content)
        self.bot.add_tools([dynamic_func, test_file, self.module1])
        save_path = os.path.join(self.test_dir, f"mixed_sources_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = bots.load(save_path)
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertIn("dynamic_func", loaded_bot.tool_handler.function_map)
        self.assertIn("file_func", loaded_bot.tool_handler.function_map)
        self.assertIn("module1_tool1", loaded_bot.tool_handler.function_map)
        self.assertEqual(loaded_bot.tool_handler.function_map["dynamic_func"](), "dynamic_result")
        self.assertEqual(loaded_bot.tool_handler.function_map["file_func"](), "file_result")
        self.assertEqual(loaded_bot.tool_handler.function_map["module1_tool1"](), "module1_tool1")
        os.unlink(test_file)

    def test_multiple_save_load_cycles(self):
        """Test tools persist through multiple save/load cycles with usage."""

        def dynamic_func(x: str) -> str:
            """Test dynamic function"""
            return f"processed_{x}"

        self.bot.add_tools(dynamic_func)
        save_path1 = os.path.join(self.test_dir, f"cycle1_{self.bot.name}")
        self.bot.respond('Process the word "test"')
        save_path1 = self.bot.save(save_path1)
        loaded1 = bots.load(save_path1)
        self.assertIn("dynamic_func", loaded1.tool_handler.function_map)
        loaded1.respond('Process the word "again"')
        save_path2 = os.path.join(self.test_dir, f"cycle2_{self.bot.name}.bot")
        loaded1.save(save_path2)
        loaded2 = bots.load(save_path2)
        self.assertIn("dynamic_func", loaded2.tool_handler.function_map)
        result = loaded2.tool_handler.function_map["dynamic_func"]("final")
        self.assertEqual(result, "processed_final")

    def tearDown(self):
        """Clean up test files and directories."""
        # Clean up individual test files first
        for file in [self.test_file1, self.test_file2]:
            try:
                os.unlink(file)
            except (OSError, IOError) as e:
                print(f"Warning: Could not remove test file {file}: {e}")
        # Clean up test directory and all its contents
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")
        super().tearDown()


class TestCLIAddToolCommand(unittest.TestCase):
    """Test the CLI /add_tool command with file.py and file.py::function syntax."""

    def setUp(self):
        """Set up test fixtures."""
        from bots.dev.cli import CLIContext, SystemHandler
        from bots.testing.mock_bot import MockBot

        self.bot = MockBot()
        self.context = CLIContext()
        self.context.bot_instance = self.bot
        self.handler = SystemHandler()
        self.test_dir = tempfile.mkdtemp()

        # Create test file with multiple functions
        self.test_file_content = '''
def public_tool1(x: str) -> str:
    """Public tool 1"""
    return f"tool1: {x}"

def public_tool2(y: int) -> int:
    """Public tool 2"""
    return y * 2

def _private_tool():
    """Private tool - should not be added"""
    return "private"

class NotAFunction:
    """Class - should not be added"""
    pass
'''
        self.test_file = os.path.join(self.test_dir, "test_tools.py")
        with open(self.test_file, "w") as f:
            f.write(self.test_file_content)

    def tearDown(self):
        """Clean up test files."""
        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")

    def test_add_tool_no_args(self):
        """Test /add_tool with no arguments shows usage."""
        result = self.handler.add_tool(self.bot, self.context, [])
        self.assertIn("Usage:", result)
        self.assertIn("file.py", result)
        self.assertIn("::", result)

    def test_add_tool_whole_file(self):
        """Test /add_tool with file.py adds all public functions."""
        result = self.handler.add_tool(self.bot, self.context, [self.test_file])

        # Check result message
        self.assertIn("Added tools:", result)
        self.assertIn("public_tool1", result)
        self.assertIn("public_tool2", result)
        self.assertNotIn("_private_tool", result)
        self.assertNotIn("NotAFunction", result)

        # Check tools were actually added
        self.assertIn("public_tool1", self.bot.tool_handler.function_map)
        self.assertIn("public_tool2", self.bot.tool_handler.function_map)
        self.assertNotIn("_private_tool", self.bot.tool_handler.function_map)
        self.assertNotIn("NotAFunction", self.bot.tool_handler.function_map)

    def test_add_tool_specific_function(self):
        """Test /add_tool with file.py::function adds only that function."""
        result = self.handler.add_tool(self.bot, self.context, [f"{self.test_file}::public_tool1"])

        # Check result message
        self.assertIn("Added tools:", result)
        self.assertIn("public_tool1", result)
        self.assertNotIn("public_tool2", result)

        # Check only specified tool was added
        self.assertIn("public_tool1", self.bot.tool_handler.function_map)
        self.assertNotIn("public_tool2", self.bot.tool_handler.function_map)

    def test_add_tool_nonexistent_file(self):
        """Test /add_tool with nonexistent file shows error."""
        result = self.handler.add_tool(self.bot, self.context, ["nonexistent.py"])

        self.assertIn("Errors:", result)
        self.assertIn("File not found", result)
        self.assertIn("nonexistent.py", result)

    def test_add_tool_nonexistent_function(self):
        """Test /add_tool with nonexistent function shows error."""
        result = self.handler.add_tool(self.bot, self.context, [f"{self.test_file}::nonexistent_func"])

        self.assertIn("Errors:", result)
        self.assertIn("not found", result)
        self.assertIn("nonexistent_func", result)

    def test_add_tool_non_python_file(self):
        """Test /add_tool with non-Python file shows error."""
        txt_file = os.path.join(self.test_dir, "test.txt")
        with open(txt_file, "w") as f:
            f.write("not python")

        result = self.handler.add_tool(self.bot, self.context, [txt_file])

        self.assertIn("Errors:", result)
        self.assertIn("Not a Python file", result)

    def test_add_tool_multiple_files(self):
        """Test /add_tool with multiple files."""
        # Create second test file
        test_file2 = os.path.join(self.test_dir, "test_tools2.py")
        with open(test_file2, "w") as f:
            f.write(
                '''
def another_tool():
    """Another tool"""
    return "another"
'''
            )

        result = self.handler.add_tool(self.bot, self.context, [self.test_file, test_file2])

        # Check all tools were added
        self.assertIn("Added tools:", result)
        self.assertIn("public_tool1", result)
        self.assertIn("public_tool2", result)
        self.assertIn("another_tool", result)

        self.assertIn("public_tool1", self.bot.tool_handler.function_map)
        self.assertIn("public_tool2", self.bot.tool_handler.function_map)
        self.assertIn("another_tool", self.bot.tool_handler.function_map)

    def test_add_tool_mixed_syntax(self):
        """Test /add_tool with mix of whole file and specific function."""
        # Create second test file
        test_file2 = os.path.join(self.test_dir, "test_tools2.py")
        with open(test_file2, "w") as f:
            f.write(
                '''
def tool_a():
    """Tool A"""
    return "a"

def tool_b():
    """Tool B"""
    return "b"
'''
            )

        # Add whole first file and specific function from second
        self.handler.add_tool(self.bot, self.context, [self.test_file, f"{test_file2}::tool_a"])

        # Check correct tools were added
        self.assertIn("public_tool1", self.bot.tool_handler.function_map)
        self.assertIn("public_tool2", self.bot.tool_handler.function_map)
        self.assertIn("tool_a", self.bot.tool_handler.function_map)
        self.assertNotIn("tool_b", self.bot.tool_handler.function_map)

    def test_add_tool_file_with_no_public_functions(self):
        """Test /add_tool with file containing only private functions."""
        empty_file = os.path.join(self.test_dir, "empty_tools.py")
        with open(empty_file, "w") as f:
            f.write(
                '''
def _private_only():
    """Private function"""
    return "private"
'''
            )

        result = self.handler.add_tool(self.bot, self.context, [empty_file])

        self.assertIn("Errors:", result)
        self.assertIn("No public functions found", result)


if __name__ == "__main__":
    unittest.main()
