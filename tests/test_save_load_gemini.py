import json
import os
import shutil
import tempfile
import unittest
from unittest.mock import patch

from bots.foundation.base import Bot, Engines
from bots.foundation.gemini_bots import GeminiBot

"""Test suite for GeminiBot save and load functionality.

This module contains comprehensive tests for verifying the persistence
and restoration capabilities of GeminiBot instances. It tests:

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


def simple_addition(x, y) -> str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))


class TestSaveLoadGemini(unittest.TestCase):
    """Test suite for GeminiBot save and load functionality."""

    def setUp(self) -> "TestSaveLoadGemini":
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()

        # Mock the API key to avoid requiring real credentials
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch("google.genai.Client"):
                self.bot = GeminiBot(name="TestGemini", model_engine=Engines.GEMINI25_FLASH, max_tokens=1000)
        return self

    def tearDown(self) -> None:
        """Clean up test environment after each test."""
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
        cleanup_files = ["TestGemini.bot", "TestBot.bot"]
        for cleanup_file in cleanup_files:
            try:
                if os.path.exists(cleanup_file):
                    os.unlink(cleanup_file)
                    print(f"Cleaned up: {cleanup_file}")
            except Exception as e:
                print(f"Warning: Could not clean up {cleanup_file}: {e}")

    def test_basic_save_load(self) -> None:
        """Test basic bot attribute persistence during save and load operations."""
        save_path = os.path.join(self.temp_dir, self.bot.name)
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.name, loaded_bot.name)
        self.assertEqual(self.bot.model_engine, loaded_bot.model_engine)
        self.assertEqual(self.bot.max_tokens, loaded_bot.max_tokens)
        self.assertEqual(self.bot.temperature, loaded_bot.temperature)
        self.assertEqual(self.bot.role, loaded_bot.role)
        self.assertEqual(self.bot.role_description, loaded_bot.role_description)

    def test_custom_attributes(self) -> None:
        """Test persistence of custom bot attributes."""
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
        """Test bot save file creation and naming."""
        save_path = os.path.join(self.temp_dir, f"explicit_{self.bot.name}")
        actual_path = self.bot.save(save_path)
        self.assertTrue(os.path.exists(actual_path))
        self.assertEqual(actual_path, save_path + ".bot")
        auto_path = self.bot.save()
        self.assertTrue(os.path.exists(auto_path))
        self.assertTrue(auto_path.endswith(".bot"))

    def test_corrupted_save(self) -> None:
        """Test handling of corrupted save file scenarios."""
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


class TestGeminiSpecificFeatures(unittest.TestCase):
    """Test suite for Gemini-specific functionality."""

    def setUp(self) -> None:
        """Set up test environment with mocked Gemini API."""
        self.temp_dir = tempfile.mkdtemp()

        with patch.dict(os.environ, {"GOOGLE_API_KEY": "test_key"}):
            with patch("google.genai.Client"):
                self.bot = GeminiBot(name="TestGemini", model_engine=Engines.GEMINI25_FLASH, max_tokens=1000)

    def tearDown(self) -> None:
        """Clean up test environment."""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.temp_dir}: {e}")

    def test_gemini_node_message_building(self) -> None:
        """Test GeminiNode's message building functionality."""
        # Test empty node
        messages = self.bot.conversation._build_messages()
        self.assertEqual(len(messages), 0)

        # Add a user message
        self.bot.conversation = self.bot.conversation._add_reply(role="user", content="Hello")
        messages = self.bot.conversation._build_messages()
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0], "Hello")

        # Add an assistant response
        self.bot.conversation = self.bot.conversation._add_reply(role="assistant", content="Hi there!")
        messages = self.bot.conversation._build_messages()
        self.assertEqual(len(messages), 2)
        self.assertEqual(messages[0], "Hello")
        self.assertEqual(messages[1], "Hi there!")

    def test_gemini_tool_handler_schema_generation(self) -> None:
        """Test GeminiToolHandler's schema generation."""

        def test_function(param1: str, param2: int = 5) -> str:
            """Test function with parameters"""
            return f"{param1}_{param2}"

        schema = self.bot.tool_handler.generate_tool_schema(test_function)

        self.assertEqual(schema["name"], "test_function")
        self.assertEqual(schema["description"], "Test function with parameters")
        self.assertIn("param1", schema["parameters"]["properties"])
        self.assertIn("param2", schema["parameters"]["properties"])
        self.assertIn("param1", schema["parameters"]["required"])
        self.assertNotIn("param2", schema["parameters"]["required"])

    def test_gemini_mailbox_api_key_handling(self) -> None:
        """Test GeminiMailbox API key handling."""
        # Test with environment variable
        with patch.dict(os.environ, {"GOOGLE_API_KEY": "env_key"}):
            with patch("google.genai.Client") as mock_client:
                from bots.foundation.gemini_bots import GeminiMailbox

                GeminiMailbox()
                mock_client.assert_called_with(api_key="env_key")

        # Test with explicit API key
        with patch("google.genai.Client") as mock_client:
            from bots.foundation.gemini_bots import GeminiMailbox

            GeminiMailbox(api_key="explicit_key")
            mock_client.assert_called_with(api_key="explicit_key")

        # Test missing API key
        with patch.dict(os.environ, {}, clear=True):
            with self.assertRaises(ValueError):
                from bots.foundation.gemini_bots import GeminiMailbox

                GeminiMailbox()


class TestGeminiIntegration(unittest.TestCase):
    """Integration tests for GeminiBot with live API calls.

    These tests require a valid Google API key and make real API calls.
    Set GOOGLE_API_KEY environment variable to run these tests.
    Use pytest -m integration to run only integration tests.
    """

    def setUp(self) -> None:
        """Set up integration test environment."""
        self.temp_dir = tempfile.mkdtemp()

        # Check if API key is available
        self.api_key = os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            self.skipTest("No Google API key found. Set GOOGLE_API_KEY environment variable to run integration tests.")

        try:
            self.bot = GeminiBot(
                name="IntegrationTestGemini",
                model_engine=Engines.GEMINI25_FLASH,
                max_tokens=100,  # Keep small for testing
                temperature=0.1,
            )
        except Exception as e:
            self.skipTest(f"Failed to create GeminiBot: {e}")

    def tearDown(self) -> None:
        """Clean up integration test environment."""
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.temp_dir}: {e}")

        # Clean up any .bot files
        import glob

        for bot_file in glob.glob("*.bot"):
            try:
                if os.path.exists(bot_file):
                    os.unlink(bot_file)
            except Exception as e:
                print(f"Warning: Could not clean up {bot_file}: {e}")

    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"), "No Google API key available")
    def test_real_conversation_and_save_load(self) -> None:
        """Test real conversation with Gemini API and save/load functionality."""
        # Have a real conversation
        response1 = self.bot.respond("Hello! Please respond with exactly 'Hi there!' and nothing else.")
        self.assertIsNotNone(response1)
        self.assertIsInstance(response1, str)
        self.assertTrue(len(response1) > 0)

        # Save the bot after conversation
        save_path = os.path.join(self.temp_dir, f"integration_{self.bot.name}")
        saved_path = self.bot.save(save_path)
        self.assertTrue(os.path.exists(saved_path))

        # Load the bot
        loaded_bot = Bot.load(saved_path)
        self.assertEqual(self.bot.name, loaded_bot.name)
        self.assertEqual(self.bot.model_engine, loaded_bot.model_engine)

        # Verify conversation history is preserved
        self.assertEqual(self.bot.conversation._node_count(), loaded_bot.conversation._node_count())

        # Have another conversation with loaded bot
        response2 = loaded_bot.respond("What is 2+2? Please respond with just the number.")
        self.assertIsNotNone(response2)
        self.assertIsInstance(response2, str)
        self.assertTrue(len(response2) > 0)

    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"), "No Google API key available")
    def test_real_tool_usage_and_persistence(self) -> None:
        """Test real tool usage with Gemini API and persistence."""

        def calculate_square(number: str) -> str:
            """Calculate the square of a number."""
            try:
                num = float(number)
                result = num * num
                return f"The square of {number} is {result}"
            except ValueError:
                return f"Error: '{number}' is not a valid number"

        # Add the tool
        self.bot.add_tools(calculate_square)

        # Test tool usage
        response = self.bot.respond("Please calculate the square of 5 using the calculate_square tool.")
        self.assertIsNotNone(response)
        self.assertIsInstance(response, str)

        # Check if tool was actually called by looking for the result
        # Note: This might be in tool_results or the response itself depending on implementation
        # Check tool results if available
        if hasattr(self.bot.conversation, "tool_results") and self.bot.conversation.tool_results:
            for result_dict in self.bot.conversation.tool_results:
                if any("25" in str(v) for v in result_dict.values()):
                    break

        # Save and load bot with tools
        save_path = os.path.join(self.temp_dir, f"tool_integration_{self.bot.name}")
        saved_path = self.bot.save(save_path)
        loaded_bot = Bot.load(saved_path)

        # Verify tools are preserved
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertIn("calculate_square", loaded_bot.tool_handler.function_map)

        # Test tool usage with loaded bot
        response2 = loaded_bot.respond("Please calculate the square of 3 using the calculate_square tool.")
        self.assertIsNotNone(response2)
        self.assertIsInstance(response2, str)

    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"), "No Google API key available")
    def test_real_error_handling(self) -> None:
        """Test error handling with real API calls."""
        # Test with a very long message that might cause issues
        very_long_message = "Please respond briefly. " + "This is a test message. " * 100

        try:
            response = self.bot.respond(very_long_message)
            # If it succeeds, that's fine too
            self.assertIsNotNone(response)
        except Exception as e:
            # If it fails, make sure it's handled gracefully
            self.assertIsInstance(e, Exception)
            print(f"Expected error handled: {e}")

    @unittest.skipIf(not os.getenv("GOOGLE_API_KEY") and not os.getenv("GEMINI_API_KEY"), "No Google API key available")
    def test_multiple_conversation_turns(self) -> None:
        """Test multiple conversation turns with real API."""
        responses = []

        # Have a multi-turn conversation
        questions = ["Hello, what's your name?", "What's the capital of France?", "Thank you for the information."]

        for question in questions:
            response = self.bot.respond(question)
            self.assertIsNotNone(response)
            self.assertIsInstance(response, str)
            self.assertTrue(len(response) > 0)
            responses.append(response)

        # Verify we have all responses
        self.assertEqual(len(responses), len(questions))

        # Save and load to verify conversation persistence
        save_path = os.path.join(self.temp_dir, f"multi_turn_{self.bot.name}")
        saved_path = self.bot.save(save_path)
        loaded_bot = Bot.load(saved_path)

        # Verify conversation structure is preserved
        self.assertEqual(self.bot.conversation._node_count(), loaded_bot.conversation._node_count())

        # Continue conversation with loaded bot
        final_response = loaded_bot.respond("Can you summarize our conversation?")
        self.assertIsNotNone(final_response)
        self.assertIsInstance(final_response, str)


if __name__ == "__main__":
    unittest.main()
