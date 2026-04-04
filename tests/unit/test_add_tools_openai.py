import os
import shutil
import tempfile
import unittest
from types import ModuleType

import pytest

import bots
from bots.foundation.openai_bots import ChatGPT_Bot


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


@pytest.mark.api
class TestAddToolsOpenAI(unittest.TestCase):
    def setUp(self):
        self.bot = ChatGPT_Bot(model_engine="gpt-4", max_tokens=1000, temperature=0, name="TestBotOpenAI", autosave=False)
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

    def tearDown(self):
        # Clean up temp files
        if hasattr(self, "test_file1") and os.path.exists(self.test_file1):
            os.unlink(self.test_file1)
        if hasattr(self, "test_file2") and os.path.exists(self.test_file2):
            os.unlink(self.test_file2)
        if hasattr(self, "test_dir") and os.path.exists(self.test_dir):
            shutil.rmtree(self.test_dir)

    def test_list_input(self):
        """Test adding tools from a list of file paths"""
        result = self.bot.add_tools(self.test_file1, self.test_file2)
        self.assertIsInstance(result, list)
        self.assertEqual(len(result), 4)  # 2 tools from each file

    def test_invalid_input(self):
        """Test that invalid input raises appropriate error"""
        with self.assertRaises(TypeError):
            self.bot.add_tools(123)  # Invalid type

    def test_multiple_files(self):
        """Test adding tools from multiple files"""
        result = self.bot.add_tools(self.test_file1, self.test_file2)
        self.assertEqual(len(result), 4)
        tool_names = [t.__name__ for t in result]
        self.assertIn("tool1", tool_names)
        self.assertIn("tool2", tool_names)
        self.assertIn("tool3", tool_names)
        self.assertIn("tool4", tool_names)

    def test_mixed_files_and_modules(self):
        """Test adding tools from both files and modules"""
        module = create_test_module("test_module", self.test_file1_content)
        result = self.bot.add_tools(self.test_file1, module)
        self.assertEqual(len(result), 4)  # 2 from file + 2 from module

    def test_multiple_modules(self):
        """Test adding tools from multiple modules"""
        module1 = create_test_module("module1", self.test_file1_content)
        module2 = create_test_module("module2", self.test_file2_content)
        result = self.bot.add_tools(module1, module2)
        self.assertEqual(len(result), 4)

    def test_multiple_save_load_cycles(self):
        """Test that tools persist through multiple save/load cycles"""
        # Add tools
        self.bot.add_tools(self.test_file1)

        # First save/load cycle
        with tempfile.NamedTemporaryFile(suffix=".bot", delete=False) as f:
            temp_file = f.name
        try:
            self.bot.save(temp_file)
            loaded_bot1 = bots.load(temp_file)
            self.assertEqual(len(loaded_bot1.tool_handler.tools), 2)

            # Second save/load cycle
            loaded_bot1.save(temp_file)
            loaded_bot2 = bots.load(temp_file)
            self.assertEqual(len(loaded_bot2.tool_handler.tools), 2)

            # Third save/load cycle
            loaded_bot2.save(temp_file)
            loaded_bot3 = bots.load(temp_file)
            self.assertEqual(len(loaded_bot3.tool_handler.tools), 2)
        finally:
            if os.path.exists(temp_file):
                os.unlink(temp_file)


if __name__ == "__main__":
    unittest.main()