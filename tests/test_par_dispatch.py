import unittest
from typing import Tuple
from bots.foundation.base import Bot, ConversationNode
from bots.flows.functional_prompts import par_dispatch, basic
import time


class MockBot(Bot):
    """A mock bot class that simulates Bot behavior for testing"""
    def __init__(self, name="test_bot"):
        self.name = name
        self.conversation = ConversationNode("", "", None)
        
    def respond(self, message: str) -> str:
        response = f"Mock response from {self.name}: {message}"
        self.conversation = ConversationNode(message, response, self.conversation)
        return response


class TestParDispatch(unittest.TestCase):

    def setUp(self):
        self.bots = [MockBot(f'test_bot_{i}') for i in range(3)]

    def test_basic_dispatch(self):
        """Test that par_dispatch works with a simple prompt function"""
        results = par_dispatch(self.bots, basic, prompt='Hello')
        self.assertEqual(len(results), len(self.bots))
        for i, result in enumerate(results):
            self.assertIsInstance(result, tuple)
            self.assertEqual(len(result), 2)
            response, node = result
            self.assertIsInstance(response, str)
            self.assertIsInstance(node, ConversationNode)
            self.assertTrue(f'test_bot_{i}' in response)

    def test_parallel_execution(self):
        """Test that execution actually happens in parallel"""

        def slow_prompt(bot: Bot, delay: float) ->Tuple[str, ConversationNode]:
            """A test prompt function that deliberately takes time"""
            time.sleep(delay)
            return basic(bot, 'Hello')
        start_time = time.time()
        results = par_dispatch(self.bots, slow_prompt, delay=1.0)
        end_time = time.time()
        self.assertLess(end_time - start_time, 2.0)
        self.assertEqual(len(results), len(self.bots))

    def test_error_handling(self):
        """Test that errors in individual bots don't crash the whole process"""

        def error_prompt(bot: Bot, fail_index: int) ->Tuple[str,
            ConversationNode]:
            """A prompt function that fails for a specific bot index"""
            if self.bots.index(bot) == fail_index:
                raise Exception('Deliberate test failure')
            return basic(bot, 'Hello')
        results = par_dispatch(self.bots, error_prompt, fail_index=1)
        self.assertEqual(len(results), len(self.bots))
        self.assertIsInstance(results[0], tuple)
        self.assertIsInstance(results[2], tuple)
        self.assertEqual(results[1], (None, None))

if __name__ == '__main__':
    unittest.main()