import json
import os
import shutil
import tempfile
import unittest

import bots.tools.python_editing_tools as python_editing_tools
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot

"""Test module for OpenAI bot persistence functionality.

This module contains tests that verify the save/load capabilities of
OpenAI-based bots,
ensuring proper persistence of:
- Bot configuration and attributes
- Conversation history and structure
- Tool definitions and execution results
- Custom attributes and state

The tests cover various scenarios including:
- Basic save/load operations
- Conversation preservation
- Tool handling across save/load cycles
- Error handling for corrupted saves
- Working directory independence
"""
# Standard library imports
# Local application imports


class TestSaveLoadOpenAI(unittest.TestCase):

    def setUp(self) -> "TestSaveLoadOpenAI":
        """Set up test environment before each test.

        Creates a temporary directory and initializes a ChatGPT bot instance
        with GPT4-Turbo engine for testing.

        Returns:
            TestSaveLoadOpenAI: The test class instance
        """
        self.temp_dir = tempfile.mkdtemp()
        self.bot = ChatGPT_Bot(name="TestGPT", model_engine=Engines.GPT4TURBO)
        return self

    def tearDown(self) -> None:
        """Clean up test environment after each test.

        Removes the temporary directory and all its contents.
        Also cleans up any .bot files that might have been created in the
        current directory.
        Handles potential cleanup failures gracefully by:
        - Using ignore_errors=True with rmtree
        - Catching and logging any exceptions that occur
        - Continuing test execution even if cleanup fails

        Returns:
            None
        """
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.temp_dir}: {e}")
        # Clean up any .bot files that might have been created in current
        # directory
        import glob

        for bot_file in glob.glob("*.bot"):
            try:
                if os.path.exists(bot_file):
                    os.unlink(bot_file)
                    print(f"Cleaned up bot file: {bot_file}")
            except Exception as e:
                print(f"Warning: Could not clean up {bot_file}: {e}")
        # Clean up any specific test files that might be created
        cleanup_files = ["CICD.bot", "Claude.bot", "TestGPT.bot", "TestBotOpenAI.bot"]
        for cleanup_file in cleanup_files:
            try:
                if os.path.exists(cleanup_file):
                    os.unlink(cleanup_file)
                    print(f"Cleaned up: {cleanup_file}")
            except Exception as e:
                print(f"Warning: Could not clean up {cleanup_file}: {e}")

    def test_basic_save_load(self) -> None:
        """Test basic bot attribute preservation during save and load
        operations.

        Verifies that fundamental bot attributes are correctly preserved:
        - name
        - model engine
        - max tokens
        - temperature
        - role
        - role description
        """
        save_path = os.path.join(self.temp_dir, self.bot.name)
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.name, loaded_bot.name)
        self.assertEqual(self.bot.model_engine, loaded_bot.model_engine)
        self.assertEqual(self.bot.max_tokens, loaded_bot.max_tokens)
        self.assertEqual(self.bot.temperature, loaded_bot.temperature)
        self.assertEqual(self.bot.role, loaded_bot.role)
        self.assertEqual(self.bot.role_description, loaded_bot.role_description)

    def test_save_load_after_conversation(self) -> None:
        """Test conversation history preservation during save and load.

        Verifies that the complete conversation history, including:
        - Message content
        - Conversation structure
        - Node count
        is preserved when saving and loading a bot that has had multiple
        interactions.
        """
        self.bot.respond("Hello, how are you?")
        self.bot.respond("What's the weather like today?")
        self.bot.respond("Thank you for the information.")
        save_path = os.path.join(self.temp_dir, f"convo_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.conversation._node_count(), loaded_bot.conversation._node_count())
        self.assertEqual(self.bot.conversation.content, loaded_bot.conversation.content)

    def test_tool_execution_results(self) -> None:
        """Test preservation of tool execution results in conversation nodes.

        Verifies that:
        - Tool execution results are properly stored in conversation nodes
        - Results persist through save/load operations
        - Result values remain accessible and accurate
        """
        self.bot.add_tools(_simple_addition)
        self.bot.respond("What is 2 + 3?")
        self.assertTrue(
            any(("5" in str(v) for v in self.bot.conversation.parent.tool_results[0].values()))
            if self.bot.conversation.parent.tool_results
            else False
        )
        save_path = os.path.join(self.temp_dir, f"tool_exec_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertTrue(
            any(("5" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
            if loaded_bot.conversation.parent.tool_results
            else False
        )

    def test_save_load_with_tool_use(self) -> None:
        """Test comprehensive tool functionality preservation across save/load
        cycles.

        Verifies that:
        - Tools remain functional after save/load operations
        - Multiple tool executions are preserved correctly
        - Tool results are maintained in conversation nodes
        - New tool executions work correctly after loading
        """
        self.bot.add_tools(_simple_addition)
        interactions = ["What is 5 + 3?", "Can you add 10 and 20?", "Please add 7 and 15"]
        for query in interactions:
            _ = self.bot.respond(query)
        self.assertTrue(
            any(("22" in str(v) for v in self.bot.conversation.parent.tool_results[0].values()))
            if self.bot.conversation.parent.tool_results
            else False
        )
        save_path = os.path.join(self.temp_dir, f"tool_use_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        loaded_bot.save(save_path + "2")
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertTrue(
            any(("22" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
            if loaded_bot.conversation.parent.tool_results
            else False
        )
        new_response = loaded_bot.respond("What is 25 + 17?")
        self.assertIsNotNone(new_response)
        self.assertTrue(
            any(("42" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
            if loaded_bot.conversation.parent.tool_results
            else False
        )

    def test_module_tool_persistence(self) -> None:
        """Test persistence of module-based tools through multiple save/load
        cycles.

        Verifies that:
        - Module tools are correctly preserved across multiple save/load operations
        - Tool count remains consistent
        - Function names are preserved
        - Functions remain callable after multiple cycles
        - Tool functionality remains intact
        """
        self.bot.add_tools(python_editing_tools)
        initial_tool_count = len(self.bot.tool_handler.tools)
        initial_function_names = set(self.bot.tool_handler.function_map.keys())
        save_path1 = os.path.join(self.temp_dir, f"module_tools_1_{self.bot.name}")
        self.bot.save(save_path1)
        loaded_bot1 = Bot.load(save_path1 + ".bot")
        self.assertEqual(initial_tool_count, len(loaded_bot1.tool_handler.tools))
        self.assertEqual(initial_function_names, set(loaded_bot1.tool_handler.function_map.keys()))
        save_path2 = os.path.join(self.temp_dir, f"module_tools_2_{self.bot.name}")
        loaded_bot1.save(save_path2)
        loaded_bot2 = Bot.load(save_path2 + ".bot")
        self.assertEqual(initial_tool_count, len(loaded_bot2.tool_handler.tools))
        self.assertEqual(initial_function_names, set(loaded_bot2.tool_handler.function_map.keys()))
        for func_name in initial_function_names:
            self.assertTrue(
                callable(loaded_bot2.tool_handler.function_map[func_name]),
                "Function {} is not callable after two save/load cycles".format(func_name),
            )

    def test_save_load_empty_bot(self) -> None:
        """Test saving and loading a bot with no conversation history.

        Verifies that:
        - Empty bots can be saved and loaded correctly
        - Initial conversation state is properly initialized
        - Root node properties are correct
        - Bot remains functional after loading
        - Conversation structure develops correctly after loading
        """
        fresh_bot = ChatGPT_Bot(name="TestGPT", model_engine=Engines.GPT4TURBO)
        save_path = os.path.join(self.temp_dir, f"empty_{fresh_bot.name}")
        save_path = fresh_bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertIsNotNone(loaded_bot.conversation)
        self.assertEqual(loaded_bot.conversation._node_count(), 1, "Expected only root node initially")
        root = loaded_bot.conversation._find_root()
        self.assertEqual(root.role, "empty")
        self.assertEqual(root.content, "")
        self.assertEqual(len(root.replies), 0)
        response = loaded_bot.respond("Hello!")
        self.assertIsNotNone(response)
        self.assertTrue(len(response) > 0)
        self.assertEqual(
            loaded_bot.conversation._node_count(),
            3,
            "Expected root node + user message + assistant response " + "(3 nodes total)",
        )
        root = loaded_bot.conversation._find_root()
        self.assertEqual(len(root.replies), 1, "Root should have one reply")
        user_message = root.replies[0]
        self.assertEqual(user_message.role, "user")
        self.assertEqual(user_message.content, "Hello!")
        self.assertEqual(len(user_message.replies), 1, "User message should have one reply")
        assistant_response = user_message.replies[0]
        self.assertEqual(assistant_response.role, "assistant")
        self.assertTrue(len(assistant_response.content) > 0)

    def test_save_load_with_file_tools(self) -> None:
        """Test saving and loading bots with file-based tools.

        Verifies that:
        - Tools loaded from files are correctly preserved
        - Tool attributes (name, parameters, return types) remain intact
        - Function objects maintain their type after loading
        - Tool functionality remains consistent
        """
        tool_file_path = "bots/tools/python_editing_tools.py"
        self.bot.add_tools(tool_file_path)
        save_path = os.path.join(self.temp_dir, f"file_tool_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        for original_tool, loaded_tool in zip(self.bot.tool_handler.tools, loaded_bot.tool_handler.tools):
            self.assertEqual(original_tool.get("name"), loaded_tool.get("name"))
            self.assertEqual(original_tool.get("parameters"), loaded_tool.get("parameters"))
            self.assertEqual(original_tool.get("returns", {}).get("type"), loaded_tool.get("returns", {}).get("type"))
            self.assertEqual(original_tool.get("type"), loaded_tool.get("type"))
            if "function" in original_tool and "function" in loaded_tool:
                self.assertEqual(type(original_tool["function"]), type(loaded_tool["function"]))

    def test_save_load_with_module_tools(self) -> None:
        """Test saving and loading bots with module-based tools.

        Verifies that:
        - Tools loaded from modules are correctly preserved
        - Tool count remains consistent
        - Tool attributes (name, parameters, return types) remain intact
        - Tool functionality is preserved after loading
        """
        self.bot.add_tools(python_editing_tools)
        save_path = os.path.join(self.temp_dir, f"module_tool_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        for original_tool, loaded_tool in zip(self.bot.tool_handler.tools, loaded_bot.tool_handler.tools):
            self.assertEqual(original_tool.get("name"), loaded_tool.get("name"))
            self.assertEqual(original_tool.get("parameters"), loaded_tool.get("parameters"))
            self.assertEqual(original_tool.get("returns", {}).get("type"), loaded_tool.get("returns", {}).get("type"))
            self.assertEqual(original_tool.get("type"), loaded_tool.get("type"))

    def test_custom_attributes(self) -> None:
        """Test preservation of custom bot attributes during save/load
        operations.

        Verifies that:
        - Custom attributes of various types (str, int, dict) are preserved
        - Data types remain consistent after loading
        - Non-existent attributes raise appropriate errors
        - Attribute values remain accurate
        """
        self.bot.custom_attr1 = "Test Value"
        self.bot.custom_attr2 = 42
        self.bot.custom_attr3 = {"key": "value"}
        save_path = os.path.join(self.temp_dir, f"custom_attr_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.custom_attr1, loaded_bot.custom_attr1)
        self.assertEqual(self.bot.custom_attr2, loaded_bot.custom_attr2)
        self.assertEqual(self.bot.custom_attr3, loaded_bot.custom_attr3)
        self.assertIsInstance(loaded_bot.custom_attr1, str)
        self.assertIsInstance(loaded_bot.custom_attr2, int)
        self.assertIsInstance(loaded_bot.custom_attr3, dict)
        with self.assertRaises(AttributeError):
            _ = loaded_bot.non_existent_attr

    def test_file_creation(self) -> None:
        """Test bot save file creation and naming conventions.

        Verifies that:
        - Save files are created in the specified location
        - File extension (.bot) is correctly appended
        - Both explicit and automatic path generation work
        - Files are actually created on disk
        """
        save_path = os.path.join(self.temp_dir, f"explicit_{self.bot.name}")
        actual_path = self.bot.save(save_path)
        self.assertTrue(os.path.exists(actual_path))
        self.assertEqual(actual_path, save_path + ".bot")
        auto_path = self.bot.save()
        self.assertTrue(os.path.exists(auto_path))
        self.assertTrue(auto_path.endswith(".bot"))

    def test_corrupted_save(self) -> None:
        """Test handling of corrupted save files.

        Verifies that:
        - Invalid JSON content raises JSONDecodeError
        - Invalid model configurations raise ValueError
        - Error handling is consistent and appropriate
        """
        save_path = os.path.join(self.temp_dir, f"corrupted_{self.bot.name}.bot")
        self.bot.save(save_path[:-4])
        with open(save_path, "w") as f:
            f.write('{"invalid": "json')
        with self.assertRaises(json.JSONDecodeError):
            Bot.load(save_path)
        with open(save_path, "w") as f:
            f.write('{"name": "test", "model_engine": "invalid-model"}')
        with self.assertRaises(ValueError):
            Bot.load(save_path)

    def test_working_directory_independence(self) -> None:
        """Test bot save/load operations from different working directories.

        Verifies that:
        - Bots can be saved and loaded from different working directories
        - Tool results state is maintained correctly
        - Relative paths work properly
        - File operations are path-independent
        """
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        self.bot.add_tools(_simple_addition)
        original_path = os.path.join(self.temp_dir, f"original_{self.bot.name}")
        self.bot.save(original_path)
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            loaded_bot = Bot.load(os.path.join("..", f"original_{self.bot.name}.bot"))
            loaded_bot.respond("What is 7 + 8?")
            self.assertTrue(
                any(("15" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
                if loaded_bot.conversation.parent.tool_results
                else False
            )
            new_path = os.path.join("..", f"from_subdir_{self.bot.name}")
            loaded_bot.save(new_path)
        finally:
            os.chdir(original_cwd)

    def test_mixed_tool_sources(self) -> None:
        """Test bot functionality with tools from multiple sources.

        Verifies that:
        - Bots can handle tools from different sources simultaneously
        - Individual function tools work correctly
        - Module-based tools work correctly
        - Tool results are preserved across save/load operations
        - Multiple tool types remain functional after loading
        """

        def floor_str(x) -> str:
            """Calculate the floor of a number and return it as a string.

            Use when you need to get the floor value of a decimal number as a
            string.

            Parameters:
                x (str): A string representation of a number (integer or float)

            Returns:
                str: The floor value of the input number as a string

            Example:
                >>> floor_str("5.7")
                "5"
            """
            import math

            return str(math.floor(float(x)))

        self.bot.add_tools(_simple_addition)
        self.bot.add_tools(floor_str)
        self.bot.add_tools(python_editing_tools)
        self.bot.respond("What is 3 + 4?")
        self.assertTrue(
            any(("7" in str(v) for v in self.bot.conversation.parent.tool_results[0].values()))
            if self.bot.conversation.parent.tool_results
            else False
        )
        self.bot.respond("What is the floor of 7.8?")
        self.assertTrue(
            any(("7" in str(v) for v in self.bot.conversation.parent.tool_results[0].values()))
            if self.bot.conversation.parent.tool_results
            else False
        )
        save_path = os.path.join(self.temp_dir, f"mixed_tools_{self.bot.name}")
        self.bot.save(save_path)
        loaded_bot = Bot.load(save_path + ".bot")
        loaded_bot.respond("What is 8 + 9?")
        self.assertTrue(
            any(("17" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
            if loaded_bot.conversation.parent.tool_results
            else False
        )
        loaded_bot.respond("What is the floor of 5.6?")
        self.assertTrue(
            any(("5" in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values()))
            if loaded_bot.conversation.parent.tool_results
            else False
        )


def _simple_addition(x: str, y: str) -> str:
    """Add two numbers and return the result as a string.

    Use when you need to perform basic addition with string conversion
    handling.

    Parameters:
        x (str): First number as a string
        y (str): Second number as a string

    Returns:
        str: The sum of x and y as a string, or error message if conversion
        fails

    Example:
        >>> _simple_addition("5", "3")
        "8"
    """
    try:
        return str(int(x) + int(y))
    except (ValueError, TypeError) as e:
        return f"Error: {str(e)}"
