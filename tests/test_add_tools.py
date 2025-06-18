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
            model_engine=Engines.CLAUDE35_SONNET_20241022, max_tokens=1000, temperature=0, name="TestBot", autosave=False
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


if __name__ == "__main__":
    unittest.main()
