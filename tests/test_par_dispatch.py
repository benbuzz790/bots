"""Test module for parallel dispatch functionality in the bots framework.
Use when testing the parallel execution capabilities of multiple bots,
including basic functionality, timing verification, and error handling
scenarios.
The module provides mock bot implementations and test cases to verify:
- Basic parallel dispatch functionality
- True parallel execution timing
- Error handling across multiple parallel bot executions
"""

import time
import unittest
from typing import Tuple

from bots.flows.functional_prompts import par_dispatch, single_prompt
from bots.foundation.base import Bot, ConversationNode


class MockBot(Bot):
    """A mock bot class that simulates Bot behavior for testing parallel
    dispatch functionality.
    Use when you need to test parallel bot operations without making actual
    API calls. Simulates basic bot behavior by returning predictable responses
    based on bot name.
    Inherits from:
        Bot: Base bot class, providing standard bot interface
    Attributes:
        name (str): Identifier for the mock bot instance
        conversation (ConversationNode): Tracks conversation history in a tree
            structure
    """

    def __init__(self, name: str = "test_bot"):
        self.name = name
        self.conversation = ConversationNode("", "", None)

    def respond(self, message: str) -> str:
        """Generate a mock response incorporating the bot's name.
        Parameters:
            message (str): The input message to respond to
        Returns:
            str: A mock response in the format "Mock response from
                {bot_name}: {message}"
        """
        response = f"Mock response from {self.name}: {message}"
        self.conversation = ConversationNode(message, response, self.conversation)
        return response


class TestParDispatch(unittest.TestCase):
    """Test suite for parallel dispatch functionality in the bots framework.
    Tests the parallel execution of multiple bots using par_dispatch,
    including:
    - Basic functionality with simple prompts
    - True parallel execution verification
    - Error handling across multiple bots
    Attributes:
        bots (List[MockBot]): List of mock bot instances used for testing
            parallel operations
    """

    def setUp(self):
        """Initialize test environment with three mock bots.
        Creates three MockBot instances with names 'test_bot_0' through
        'test_bot_2'.
        """
        self.bots = [MockBot(f"test_bot_{i}") for i in range(3)]

    def test_basic_dispatch(self):
        """Test that par_dispatch works with a simple prompt function.
        Verifies:
        - Correct number of results returned
        - Each result is properly structured (tuple of str and
          ConversationNode)
        - Response content matches expected bot behavior
        Returns:
            None
        """
        results = par_dispatch(self.bots, single_prompt, prompt="Hello")
        self.assertEqual(len(results), len(self.bots))
        for i, result in enumerate(results):
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            response, node = result
            self.assertIsInstance(response, str)
            self.assertIsInstance(node, ConversationNode)
            self.assertTrue(f"test_bot_{i}" in response)

    def test_parallel_execution(self):
        """Test that execution actually happens in parallel.
        Uses a deliberately slow prompt function to verify that total
        execution time is less than would be required for sequential
        execution.
        Returns:
            None
        """

        def slow_prompt(bot: Bot, delay: float) -> Tuple[str, ConversationNode]:
            """A test prompt function that deliberately introduces delay.
            Use when testing parallel execution timing.
            Parameters:
                bot (Bot): The bot instance to use
                delay (float): Time in seconds to delay execution
            Returns:
                Tuple[str, ConversationNode]: Standard prompt return format
            """
            time.sleep(delay)
            return single_prompt(bot, "Hello")

        start_time = time.time()
        results = par_dispatch(self.bots, slow_prompt, delay=1.0)
        end_time = time.time()
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(len(results), len(self.bots))

    def test_error_handling(self):
        """Test that errors in individual bots don't crash the whole process.
        Verifies that when one bot fails:
        - Other bots continue execution
        - Failed bot returns (None, None)
        - Overall process completes
        Returns:
            None
        """

        def error_prompt(bot: Bot, fail_index: int) -> Tuple[str, ConversationNode]:
            """A prompt function that fails for a specific bot index.
            Use when testing error handling in parallel execution.
            Parameters:
                bot (Bot): The bot instance to use
                fail_index (int): Index of the bot that should fail
            Returns:
                Tuple[str, ConversationNode]: Standard prompt return format
            Raises:
                Exception: Deliberately raised for the specified fail_index bot
            """
            if self.bots.index(bot) == fail_index:
                raise Exception("Deliberate test failure")
            return single_prompt(bot, "Hello")

        results = par_dispatch(self.bots, error_prompt, fail_index=1)
        self.assertEqual(len(results), len(self.bots))
        self.assertIsInstance(results[0], tuple)
        self.assertIsInstance(results[2], tuple)
        self.assertEqual(results[1], (None, None))


if __name__ == "__main__":
    unittest.main()
