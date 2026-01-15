"""Tests for ToolHandler save/load with module tools (Issue #230)."""

import os
import shutil
import sys
import tempfile
from pathlib import Path

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


class TestModuleToolsSaveLoad:
    """Tests for module tools persistence across save/load cycles."""

    def test_module_tools_save_load_same_directory(self):
        """Test that module tools work when saved and loaded from same directory."""
        tmpdir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        try:
            # Create a tools module
            tools_dir = Path(tmpdir) / "tools"
            tools_dir.mkdir()

            tools_file = tools_dir / "my_tools.py"
            tools_file.write_text(
                """
def greet(name: str) -> str:
    return f"Hello, {name}!"
"""
            )

            # Create and save bot
            os.chdir(tmpdir)
            bot1 = AnthropicBot(
                name="TestBot",
                api_key="test-key",
                model_engine=Engines.CLAUDE35_HAIKU,
                max_tokens=1000,
                temperature=0.7,
                role="assistant",
                role_description="A test bot",
            )

            sys.path.insert(0, str(tmpdir))
            try:
                import tools.my_tools as my_tools

                bot1.add_tools(my_tools)
            finally:
                sys.path.pop(0)
                if "tools" in sys.modules:
                    del sys.modules["tools"]
                if "tools.my_tools" in sys.modules:
                    del sys.modules["tools.my_tools"]

            save_path = Path(tmpdir) / "test_bot.bot"
            bot1.save(str(save_path))

            # Load bot
            bot2 = AnthropicBot.load(str(save_path))

            # Verify tools loaded
            assert len(bot2.tool_handler.tools) == 1
            assert "greet" in bot2.tool_handler.function_map

            # Verify tool works
            result = bot2.tool_handler.function_map["greet"]("World")
            assert result == "Hello, World!"

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(tmpdir, ignore_errors=True)

    def test_module_tools_save_load_different_directory(self):
        """Test that module tools work when project is moved (Issue #230)."""
        tmpdir = tempfile.mkdtemp()
        original_cwd = os.getcwd()
        try:
            # Create tools in project1
            project1 = Path(tmpdir) / "project1"
            tools_dir1 = project1 / "tools"
            tools_dir1.mkdir(parents=True)

            tools_file = tools_dir1 / "my_tools.py"
            tools_file.write_text(
                """
def add_numbers(a: int, b: int) -> int:
    return a + b
"""
            )

            # Create save directory
            save_dir = Path(tmpdir) / "saves"
            save_dir.mkdir()

            # Create bot from project1
            os.chdir(project1)
            bot1 = AnthropicBot(
                name="TestBot",
                api_key="test-key",
                model_engine=Engines.CLAUDE35_HAIKU,
                max_tokens=1000,
                temperature=0.7,
                role="assistant",
                role_description="A test bot",
            )

            sys.path.insert(0, str(project1))
            try:
                import tools.my_tools as my_tools

                bot1.add_tools(my_tools)
            finally:
                sys.path.pop(0)
                if "tools" in sys.modules:
                    del sys.modules["tools"]
                if "tools.my_tools" in sys.modules:
                    del sys.modules["tools.my_tools"]

            save_path = save_dir / "test_bot.bot"
            bot1.save(str(save_path))

            # Simulate moving project - copy tools to project2
            project2 = Path(tmpdir) / "project2"
            tools_dir2 = project2 / "tools"
            tools_dir2.mkdir(parents=True)
            shutil.copy(tools_file, tools_dir2 / "my_tools.py")

            # Delete original project
            os.chdir(tmpdir)
            shutil.rmtree(project1)

            # Load bot from project2
            os.chdir(project2)
            bot2 = AnthropicBot.load(str(save_path))

            # Verify tools loaded and path was remapped
            assert len(bot2.tool_handler.tools) == 1
            assert "add_numbers" in bot2.tool_handler.function_map

            # Verify the module path was updated
            module_paths = list(bot2.tool_handler.modules.keys())
            assert len(module_paths) == 1
            assert "project2" in module_paths[0]  # Should be in project2 now
            assert os.path.exists(module_paths[0])  # Path should exist

            # Verify tool works
            result = bot2.tool_handler.function_map["add_numbers"](5, 3)
            assert result == 8

        finally:
            os.chdir(original_cwd)
            shutil.rmtree(tmpdir, ignore_errors=True)
