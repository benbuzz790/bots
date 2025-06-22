import json
import os
import shutil
import tempfile
import unittest

import bots.tools.python_editing_tools as python_editing_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines

"""Test suite for AnthropicBot save and load functionality.

This module contains comprehensive tests for verifying the persistence
and restoration capabilities of AnthropicBot instances. It tests:

- Basic bot attribute persistence (name, model, settings)
- Conversation history preservation
- Tool configuration and execution state
- Custom attribute handling
- Error cases and edge conditions
- Working directory independence
- Multiple save/load cycles

The test suite ensures that bots can be properly serialized and
deserialized while maintaining their complete state and functionality.
"""


class TestSaveLoadAnthropic(unittest.TestCase):
    """Test suite for AnthropicBot save and load functionality.

    This test suite verifies the complete serialization and deserialization
    capabilities of AnthropicBot instances. It ensures that all bot state
    is properly preserved across save/load operations.

    Attributes:
        temp_dir (str): Temporary directory path for test file operations
        bot (AnthropicBot): Test bot instance with Claude 3.5 Sonnet configuration

    Test Categories:
        - Basic Persistence: Core bot attribute preservation
        - Conversation: Chat history and structure preservation
        - Tools: Tool configuration and execution state
        - Custom State: User-defined attribute handling
        - Error Handling: Corrupt files and edge cases
        - Directory Handling: Path resolution and working directory
    """

    def setUp(self) -> "TestSaveLoadAnthropic":
        """Set up test environment before each test.

        Creates a temporary directory and initializes a test AnthropicBot instance
        with Claude 3.5 Sonnet configuration.

        Args:
            self: Test class instance

        Returns:
            TestSaveLoadAnthropic: Self reference for method chaining

        Note:
            The temporary directory is created using tempfile.mkdtemp()
            and will be cleaned up in tearDown().
        """
        self.temp_dir = tempfile.mkdtemp()
        self.bot = AnthropicBot(name="TestClaude", model_engine=Engines.CLAUDE35_SONNET_20240620)
        return self

    def tearDown(self) -> None:
        """Clean up test environment after each test.

        Removes the temporary directory and all its contents created during setUp.
        Also cleans up any .bot files that might have been created in the current directory.
        Handles cleanup errors gracefully with warning messages.

        Args:
            self: Test class instance

        Returns:
            None

        Note:
            Uses shutil.rmtree with ignore_errors=True for robust cleanup
        """
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.temp_dir}: {e}")
        # Clean up any .bot files that might have been created in current directory
        import glob

        for bot_file in glob.glob("*.bot"):
            try:
                if os.path.exists(bot_file):
                    os.unlink(bot_file)
                    print(f"Cleaned up bot file: {bot_file}")
            except Exception as e:
                print(f"Warning: Could not clean up {bot_file}: {e}")
        # Clean up any specific test files that might be created
        cleanup_files = ["CICD.bot", "Claude.bot", "TestClaude.bot", "TestBot.bot"]
        for cleanup_file in cleanup_files:
            try:
                if os.path.exists(cleanup_file):
                    os.unlink(cleanup_file)
                    print(f"Cleaned up: {cleanup_file}")
            except Exception as e:
                print(f"Warning: Could not clean up {cleanup_file}: {e}")

    def test_basic_save_load(self) -> None:
        """Test basic bot attribute persistence during save and load operations.

        Use when verifying that fundamental bot attributes (name, model, settings)
        are correctly preserved during serialization and deserialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Bot name preservation
            - Model engine configuration
            - Token limits
            - Temperature settings
            - Role configurations

        Raises:
            AssertionError: If any bot attributes don't match after reload
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
        """Test conversation history persistence during save and load operations.

        Use when verifying that complete conversation trees and their content
        are correctly preserved during serialization and deserialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Conversation node count preservation
            - Conversation content preservation
            - Conversation structure integrity

        Raises:
            AssertionError: If conversation state doesn't match after reload

        Note:
            Tests a three-message conversation sequence to ensure proper
            conversation tree structure preservation
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
        """Test tool execution result persistence in conversation nodes.

        Use when verifying that tool execution results are properly saved
        and restored within the conversation history nodes.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Tool result storage in conversation nodes
            - Tool result preservation during save/load
            - Result accessibility after loading
            - Tool result value verification

        Raises:
            AssertionError: If tool results are not properly preserved

        Note:
            Uses a simple addition tool to generate verifiable results
            and checks both completed and pending tool results
        """

        def simple_addition(x: str | int | float, y: str | int | float) -> str:
            """Returns x + y with appropriate type conversion"""
            return str(int(x) + int(y))

        self.bot.add_tools(simple_addition)
        self.bot.respond("What is 2 + 3?")
        tool_results = self.bot.conversation.tool_results[0].values() if self.bot.conversation.tool_results else []
        pending_results = self.bot.conversation.pending_results[0].values() if self.bot.conversation.pending_results else []
        self.assertTrue(any(("5" in str(v) for v in tool_results)) or any(("5" in str(v) for v in pending_results)))
        save_path = os.path.join(self.temp_dir, f"tool_exec_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
        loaded_pending_results = (
            loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
        )
        self.assertTrue(
            any(("5" in str(v) for v in loaded_tool_results)) or any(("5" in str(v) for v in loaded_pending_results))
        )

    def test_save_load_with_tool_use(self) -> None:
        """Test tool functionality persistence through multiple interactions.

        Use when verifying that tools remain functional across multiple
        save/load cycles and continue to produce correct results.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Tool execution before and after save/load
            - Multiple sequential tool operations
            - Tool result persistence
            - Tool handler state preservation
            - Result value accuracy across operations

        Raises:
            AssertionError: If tool functionality or results don't match
                after save/load operations

        Note:
            Performs multiple arithmetic operations to verify both
            tool functionality and result accuracy
        """

        def simple_addition(x: str | int | float, y: str | int | float) -> str:
            """Returns x + y with appropriate type conversion"""
            return str(int(x) + int(y))

        self.bot.add_tools(simple_addition)
        interactions = ["What is 5 + 3?", "Can you add 10 and 20?", "Please add 7 and 15"]
        for query in interactions:
            _ = self.bot.respond(query)
        tool_results = self.bot.conversation.tool_results[0].values() if self.bot.conversation.tool_results else []
        pending_results = self.bot.conversation.pending_results[0].values() if self.bot.conversation.pending_results else []
        self.assertTrue(any(("22" in str(v) for v in tool_results)) or any(("22" in str(v) for v in pending_results)))
        save_path = os.path.join(self.temp_dir, f"tool_use_{self.bot.name}")
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        loaded_bot.save(save_path + "2")
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
        loaded_pending_results = (
            loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
        )
        self.assertTrue(
            any(("22" in str(v) for v in loaded_tool_results)) or any(("22" in str(v) for v in loaded_pending_results))
        )
        new_response = loaded_bot.respond("What is 25 + 17?")
        self.assertIsNotNone(new_response)
        loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
        loaded_pending_results = (
            loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
        )
        self.assertTrue(
            any(("42" in str(v) for v in loaded_tool_results)) or any(("42" in str(v) for v in loaded_pending_results))
        )

    def test_module_tool_persistence(self) -> None:
        """Test module-based tool persistence through multiple save/load cycles.

        Use when verifying that tools imported from modules maintain their
        functionality and configuration through multiple serialization cycles.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Module tool count preservation
            - Function name mapping preservation
            - Tool callability after multiple save/load cycles
            - Tool configuration consistency
            - Function map integrity

        Raises:
            AssertionError: If tool configurations don't match or functions
                become uncallable after save/load cycles

        Note:
            Uses python_editing_tools module as test subject and performs
            multiple save/load cycles to ensure stability
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
                f"Function {func_name} is not callable after two save/load cycles",
            )

    def test_save_load_empty_bot(self) -> None:
        """Test save/load operations on a bot with no conversation history.

        Use when verifying that new bots can be properly serialized and
        maintain correct initial state after deserialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Empty conversation tree structure
            - Root node properties
            - Post-load conversation capabilities
            - Node count and structure after first interaction
            - Node role assignments

        Raises:
            AssertionError: If initial state or conversation structure
                doesn't match expected values

        Note:
            Verifies both the initial empty state and the bot's ability
            to properly function after loading from an empty state
        """
        fresh_bot = AnthropicBot(name="TestClaude", model_engine=Engines.CLAUDE35_SONNET_20240620)
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
            loaded_bot.conversation._node_count(), 3, "Expected root node + user message + assistant response (3 nodes total)"
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
        """Test persistence of tools loaded from file paths.

        Use when verifying that tools loaded from file paths maintain
        their configuration and functionality after serialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Tool count preservation
            - Tool configuration matching
            - Tool parameter preservation
            - Tool return type consistency
            - Function type preservation
            - Tool source path handling

        Raises:
            AssertionError: If tool configurations don't match after reload

        Note:
            Uses python_editing_tools.py as a test subject for file-based
            tool loading and persistence verification
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
        """Test persistence of tools loaded from imported modules.

        Use when verifying that tools imported directly from modules
        maintain their configuration after serialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Tool count preservation
            - Tool name preservation
            - Parameter configuration matching
            - Return type consistency
            - Tool type verification
            - Module import path handling

        Raises:
            AssertionError: If tool configurations or functionality
                don't match after reload

        Note:
            Differs from file_tools test by using direct module imports
            rather than file paths for tool loading
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
        """Test persistence of custom bot attributes.

        Use when verifying that arbitrary custom attributes added to the bot
        are correctly preserved during serialization and deserialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - String attribute preservation
            - Integer attribute preservation
            - Dictionary attribute preservation
            - Type consistency after loading
            - Non-existent attribute handling
            - AttributeError raising

        Raises:
            AssertionError: If attribute values or types don't match after reload
            AttributeError: When accessing non-existent attributes (expected)

        Note:
            Tests both simple and complex data types to ensure proper
            serialization of custom attributes
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
        """Test bot save file creation and naming.

        Use when verifying that bot save files are created in the correct
        locations with proper file extensions.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Explicit path save file creation
            - Automatic path save file creation
            - File extension handling
            - File existence verification
            - Path resolution

        Raises:
            AssertionError: If files aren't created in expected locations
                or with correct extensions

        Note:
            Tests both explicit path saving and automatic path generation
            to ensure consistent file handling
        """
        save_path = os.path.join(self.temp_dir, f"explicit_{self.bot.name}")
        actual_path = self.bot.save(save_path)
        self.assertTrue(os.path.exists(actual_path))
        self.assertEqual(actual_path, save_path + ".bot")
        auto_path = self.bot.save()
        self.assertTrue(os.path.exists(auto_path))
        self.assertTrue(auto_path.endswith(".bot"))

    def test_corrupted_save(self) -> None:
        """Test handling of corrupted save file scenarios.

        Use when verifying that the system properly handles and reports
        errors when loading corrupted or invalid save files.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Invalid JSON handling
            - Invalid model configuration handling
            - Appropriate error raising
            - Error message clarity

        Raises:
            AssertionError: If incorrect error types are raised
            json.JSONDecodeError: When loading invalid JSON (expected)
            ValueError: When loading invalid model configuration (expected)

        Note:
            Tests multiple corruption scenarios to ensure robust error
            handling and appropriate error reporting
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
        """Test bot persistence across different working directories.

        Use when verifying that bots can be saved and loaded from different
        working directories while maintaining proper tool functionality.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Cross-directory loading
            - Tool functionality in new directory
            - Result persistence across directories
            - Path resolution handling
            - Relative path handling

        Raises:
            AssertionError: If tool functionality or results don't match
                when loading from different directories

        Note:
            Changes working directory during test to verify path independence,
            ensures cleanup of working directory state
        """
        subdir = os.path.join(self.temp_dir, "subdir")
        os.makedirs(subdir, exist_ok=True)
        self.bot.add_tools(simple_addition)
        original_path = os.path.join(self.temp_dir, f"original_{self.bot.name}")
        self.bot.save(original_path)
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            loaded_bot = Bot.load(os.path.join("..", f"original_{self.bot.name}.bot"))
            loaded_bot.respond("What is 7 + 8?")
            loaded_tool_results = (
                loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
            )
            loaded_pending_results = (
                loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
            )
            self.assertTrue(
                any(("15" in str(v) for v in loaded_tool_results)) or any(("15" in str(v) for v in loaded_pending_results))
            )
            new_path = os.path.join("..", f"from_subdir_{self.bot.name}")
            loaded_bot.save(new_path)
        finally:
            os.chdir(original_cwd)

    def test_mixed_tool_sources(self) -> None:
        """Test persistence of tools from multiple sources.

        Use when verifying that bots with tools from different sources
        (inline functions, imported modules, etc.) maintain functionality
        after serialization.

        Args:
            self: Test class instance

        Returns:
            None

        Tests:
            - Multiple tool source handling
            - Tool result consistency
            - Pre-save tool functionality
            - Post-load tool functionality
            - Result accuracy verification
            - Tool source independence

        Raises:
            AssertionError: If tool results don't match expected values
                or if tool functionality is lost after reload

        Note:
            Combines inline functions, imported functions, and module tools
            to verify comprehensive tool persistence
        """

        def floor_str(x) -> str:
            """Returns floor of x as a string"""
            import math

            return str(math.floor(float(x)))

        bot = self.bot
        bot.add_tools(simple_addition)
        bot.add_tools(floor_str)
        bot.add_tools(python_editing_tools)
        bot.respond("What is 3 + 4?")
        result1 = bot.tool_handler.get_results()
        bot.respond("What is the floor of 7.8?")
        result2 = bot.tool_handler.get_results()
        save_path = os.path.join(self.temp_dir, f"mixed_tools_{bot.name}")
        bot.save(save_path)
        loaded_bot = Bot.load(save_path + ".bot")
        loaded_bot.respond("What is 8 + 9?")
        result3 = loaded_bot.tool_handler.get_results()
        loaded_bot.respond("What is the floor of 5.6?")
        result4 = loaded_bot.tool_handler.get_results()
        self.assertEqual("7", result1[0]["content"])
        self.assertEqual("7", result2[0]["content"])
        self.assertEqual("17", result3[0]["content"])
        self.assertEqual("5", result4[0]["content"])


def simple_addition(x, y) -> str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))
    def test_self_tools_get_calling_bot_issue(self) -> None:
        """Test that self_tools functions can find the calling bot during tool execution.
        This test reproduces the issue where _get_calling_bot() fails to find the bot
        when tools are executed through the normal tool execution pipeline.
        """
        import bots.tools.self_tools as self_tools
        # Add self_tools to the bot
        self.bot.add_tools(self_tools)
        # Try to use a self_tools function that relies on _get_calling_bot()
        response = self.bot.respond("Please get your own info using get_own_info")
        # The response should contain bot information, not an error
        self.assertNotIn("Error: Could not find calling bot", response)
        self.assertIn("name", response.lower())
    def test_self_tools_branch_functionality(self) -> None:
        """Test that branch_self function works correctly when called as a tool."""
        import bots.tools.self_tools as self_tools
        # Add self_tools to the bot
        self.bot.add_tools(self_tools)
        # Try to use branch_self
        response = self.bot.respond("Please create 2 branches with prompts ['Hello world', 'Goodbye world'] using branch_self")
        # Should not contain error about not finding calling bot
        self.assertNotIn("Error: Could not find calling bot", response)
        # Should indicate successful branching
        self.assertIn("branch", response.lower())
    def test_self_tools_add_tools_functionality(self) -> None:
        """Test that add_tools function works when called as a tool."""
        import bots.tools.self_tools as self_tools
        # Add self_tools to the bot
        self.bot.add_tools(self_tools)
        # Get initial tool count
        initial_count = len(self.bot.tool_handler.tools)
        # Try to add more tools using the self_tools add_tools function
        response = self.bot.respond("Please add tools from 'bots/tools/code_tools.py' using add_tools")
        # Should not contain error about not finding calling bot
        self.assertNotIn("Error: Could not find calling bot", response)
        # Should have more tools now
        final_count = len(self.bot.tool_handler.tools)
        self.assertGreater(final_count, initial_count)
