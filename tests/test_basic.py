"""Unit tests for basic bot functionality and parallel processing capabilities.

This module contains test cases for the core functionality of both AnthropicBot
and ChatGPT_Bot classes from the bots package. Tests cover initialization
parameters, conversation handling, context retention, and parallel processing
through bot multiplication.
Test Dependencies:
    - unittest: Python's built-in testing framework
    - bots.foundation.base: Provides Engines enumeration
    - bots: Main package providing AnthropicBot and ChatGPT_Bot classes

The test suite verifies:
    - Basic initialization with default parameters
    - Custom initialization with user-defined parameters
    - Conversation flow and response validation
    - Multi-turn conversation context retention
    - Bot multiplication for parallel processing capabilities
    - Deep copy integrity during bot multiplication
"""

import unittest
from typing import List

from bots import AnthropicBot, ChatGPT_Bot
from bots.foundation.base import Engines


class TestAnthropicBot(unittest.TestCase):
    """Test suite for AnthropicBot functionality.

    This test class verifies the core functionality of the AnthropicBot class,
    including initialization with both default and custom parameters, basic
    conversation capabilities, and multi-turn conversation handling.

    Attributes:
        bot (AnthropicBot): Test instance of AnthropicBot with default settings
            and autosave disabled for testing purposes.

    Test Coverage:
        - Default parameter initialization
        - Custom parameter initialization
        - Basic conversation responses
        - Multi-turn conversation context
        - Response type validation
        - Response content validation
    """

    def setUp(self) -> None:
        """Initialize a test AnthropicBot instance with autosave disabled.

        Creates a fresh bot instance before each test method to ensure
        test isolation.
        """
        self.bot = AnthropicBot(autosave=False)

    def test_initialization(self) -> None:
        """Test default initialization parameters of AnthropicBot.

        Verifies that a newly created AnthropicBot instance has the correct
        default values for all important attributes.

        Returns:
            None

        Raises:
            AssertionError: If any default parameter doesn't match expected
                value
        """
        self.assertIsInstance(self.bot, AnthropicBot)
        self.assertEqual(self.bot.model_engine, Engines.CLAUDE4_SONNET)
        self.assertEqual(self.bot.temperature, 0.3)
        self.assertEqual(self.bot.name, "Claude")

    def test_custom_initialization(self) -> None:
        """Test initialization with custom parameters.

        Creates a bot with custom values for all major parameters and verifies
        that they are correctly set.

        Returns:
            None

        Raises:
            AssertionError: If any custom parameter doesn't match its set value
        """
        custom_bot = AnthropicBot(
            model_engine=Engines.CLAUDE3_HAIKU,
            max_tokens=1000,
            temperature=0.7,
            name="CustomClaude",
            role="expert",
            role_description="an AI language expert",
            autosave=False,
        )
        self.assertEqual(custom_bot.model_engine, Engines.CLAUDE3_HAIKU)
        self.assertEqual(custom_bot.max_tokens, 1000)
        self.assertEqual(custom_bot.temperature, 0.7)
        self.assertEqual(custom_bot.name, "CustomClaude")
        self.assertEqual(custom_bot.role, "expert")
        self.assertEqual(custom_bot.role_description, "an AI language expert")

    def test_basic_conversation(self) -> None:
        """Test basic conversation functionality with a simple greeting.

        Sends a basic greeting and verifies that the response meets basic
        validity criteria (is a non-empty string).

        Returns:
            None

        Raises:
            AssertionError: If response is not a string or is empty
        """
        response = self.bot.respond("Hello, how are you?")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_multiple_turns(self) -> None:
        """Test multi-turn conversation with context retention.

        Conducts a two-turn conversation about France to verify that the bot
        maintains context between responses and provides relevant information.

        Returns:
            None

        Raises:
            AssertionError: If responses don't contain expected information
        """
        response1 = self.bot.respond("What's the capital of France?")
        self.assertIn("Paris", response1)
        response2 = self.bot.respond("What's its population?")
        self.assertIn("million", response2.lower())


class TestGPTBot(unittest.TestCase):
    """Test suite for ChatGPT_Bot functionality.

    This test class verifies the core functionality of the ChatGPT_Bot class,
    including initialization with both default and custom parameters, basic
    conversation capabilities, and multi-turn conversation handling.

    Attributes:
        bot (ChatGPT_Bot): Test instance of ChatGPT_Bot with default settings
            used as the base test fixture.

    Test Coverage:
        - Default parameter initialization
        - Custom parameter initialization
        - Basic conversation responses
        - Multi-turn conversation context
        - Response type validation
        - Response content validation
    """

    def setUp(self) -> None:
        """Initialize a test ChatGPT_Bot instance.

        Creates a fresh bot instance before each test method to ensure
        test isolation.
        """
        self.bot = ChatGPT_Bot()

    def test_initialization(self) -> None:
        """Test default initialization parameters of ChatGPT_Bot.

        Verifies that a newly created ChatGPT_Bot instance has the correct
        default values for all important attributes.

        Returns:
            None

        Raises:
            AssertionError: If any default parameter doesn't match expected
                value
        """
        self.assertIsInstance(self.bot, ChatGPT_Bot)
        self.assertEqual(self.bot.model_engine, Engines.GPT4)
        self.assertEqual(self.bot.max_tokens, 4096)
        self.assertEqual(self.bot.temperature, 0.3)
        self.assertEqual(self.bot.name, "bot")

    def test_custom_initialization(self) -> None:
        """Test initialization with custom parameters.

        Creates a bot with custom values for all major parameters and verifies
        that they are correctly set.

        Returns:
            None

        Raises:
            AssertionError: If any custom parameter doesn't match its set value
        """
        custom_bot = ChatGPT_Bot(
            model_engine=Engines.GPT4,
            max_tokens=2000,
            temperature=0.5,
            name="CustomGPT",
            role="assistant",
            role_description="a helpful AI assistant",
        )
        self.assertEqual(custom_bot.model_engine, Engines.GPT4)
        self.assertEqual(custom_bot.max_tokens, 2000)
        self.assertEqual(custom_bot.temperature, 0.5)
        self.assertEqual(custom_bot.name, "CustomGPT")
        self.assertEqual(custom_bot.role, "assistant")
        self.assertEqual(custom_bot.role_description, "a helpful AI assistant")

    def test_basic_conversation(self) -> None:
        """Test basic conversation functionality with a simple greeting.

        Sends a basic greeting and verifies that the response meets basic
        validity criteria (is a non-empty string).

        Returns:
            None

        Raises:
            AssertionError: If response is not a string or is empty
        """
        response = self.bot.respond("Hello, how are you?")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_multiple_turns(self) -> None:
        """Test multi-turn conversation with context retention.

        Conducts a two-turn conversation about France to verify that the bot
        maintains context between responses and provides relevant information.

        Returns:
            None

        Raises:
            AssertionError: If responses don't contain expected information
        """
        response1 = self.bot.respond("What's the capital of France?")
        self.assertIn("Paris", response1)
        response2 = self.bot.respond("What's its population?")
        self.assertIn("million", response2.lower())


def test_bot_multiplication() -> None:
    """Test the bot multiplication operator for parallel processing capability.

    This test verifies that the __mul__ operator correctly creates deep copies
    of a Bot instance for parallel processing purposes. The test creates a bot
    with specific parameters and conversation history, then multiplies it to
    create copies.

    Test Steps:
        1. Create a bot with custom parameters
        2. Add conversation history
        3. Create multiple copies using multiplication
        4. Verify copy integrity

    Verification Points:
        - Correct number of copies created
        - Each copy is a proper instance of AnthropicBot
        - Each copy is a distinct object (not shallow copies)
        - All bot attributes are preserved in the copies
        - Conversation history is properly deep copied
        - Parent-child relationships in conversation trees are maintained

    Returns:
        None

    Raises:
        AssertionError: If any verification check fails, indicating improper
            copying of bot instances or their attributes
    """
    bot = AnthropicBot(
        api_key=None,
        model_engine=Engines.CLAUDE3_HAIKU,
        max_tokens=100,
        temperature=0.7,
        name="TestBot",
        role="test",
        role_description="A test bot",
        autosave=False,
    )
    bot.conversation = bot.conversation._add_reply(content="Hello", role="user")
    bot.conversation = bot.conversation._add_reply(content="Hi there!", role="assistant")
    bot_copies: List[AnthropicBot] = bot * 3
    assert len(bot_copies) == 3
    assert all((isinstance(copy, AnthropicBot) for copy in bot_copies))
    assert all((copy is not bot for copy in bot_copies))
    assert all((copy is not bot_copies[0] for copy in bot_copies[1:]))
    for copy in bot_copies:
        assert copy.name == bot.name
        assert copy.model_engine == bot.model_engine
        assert copy.max_tokens == bot.max_tokens
        assert copy.temperature == bot.temperature
        assert copy.role == bot.role
        assert copy.role_description == bot.role_description
        assert copy.conversation is not bot.conversation
        assert copy.conversation.content == bot.conversation.content
        assert copy.conversation.role == bot.conversation.role
        assert copy.conversation.parent is not None
        assert copy.conversation.parent is not bot.conversation.parent


if __name__ == "__main__":
    unittest.main()
