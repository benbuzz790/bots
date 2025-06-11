import unittest
from unittest.mock import MagicMock, patch
import sys
import os
# Add the project root to the path
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from bots.dev.cli import FunctionalPromptHandler, CLIContext
import bots.flows.functional_prompts as fp
class TestBroadcastToLeaves(unittest.TestCase):
    """Test broadcast_to_leaves functionality."""
    def setUp(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.respond = MagicMock(return_value="Test response")
        # Create a simple conversation tree for testing
        self.root = MagicMock()
        self.root.replies = []
        self.root.parent = None
        self.leaf1 = MagicMock()
        self.leaf1.parent = self.root
        self.leaf1.replies = []
        self.leaf1.labels = []
        self.leaf2 = MagicMock()
        self.leaf2.parent = self.root
        self.leaf2.replies = []
        self.leaf2.labels = ["skip_me"]
        self.root.replies = [self.leaf1, self.leaf2]
        self.mock_bot.conversation = self.root
    def test_broadcast_to_leaves_in_fp_functions(self):
        """Test that broadcast_to_leaves is properly registered in CLI."""
        fp_handler = FunctionalPromptHandler()
        # Check that the function is in the registry
        self.assertIn('broadcast_to_leaves', fp_handler.fp_functions)
        # Check that it points to the correct function
        self.assertEqual(
            fp_handler.fp_functions['broadcast_to_leaves'], 
            fp.broadcast_to_leaves
        )
    @patch('builtins.input')
    def test_broadcast_to_leaves_parameter_collection_basic(self, mock_input):
        """Test basic parameter collection for broadcast_to_leaves."""
        mock_input.side_effect = [
            "Test broadcast message",  # prompt
            "skip_me,archived",        # skip labels
            "n"                        # no iteration
        ]
        fp_handler = FunctionalPromptHandler()
        params = fp_handler._collect_parameters('broadcast_to_leaves', None)
        self.assertIsNotNone(params)
        self.assertEqual(params['prompt'], "Test broadcast message")
        self.assertEqual(params['skip'], ["skip_me", "archived"])
        self.assertNotIn('continue_prompt', params)
        self.assertNotIn('stop_condition', params)
    @patch('builtins.input')
    def test_broadcast_to_leaves_parameter_collection_with_iteration(self, mock_input):
        """Test parameter collection with iteration enabled."""
        mock_input.side_effect = [
            "Test broadcast message",  # prompt
            "",                        # no skip labels
            "y",                       # enable iteration
            "continue working",        # continue prompt
            "2"                        # select tool_not_used condition
        ]
        fp_handler = FunctionalPromptHandler()
        params = fp_handler._collect_parameters('broadcast_to_leaves', None)
        self.assertIsNotNone(params)
        self.assertEqual(params['prompt'], "Test broadcast message")
        self.assertEqual(params['skip'], [])
        self.assertEqual(params['continue_prompt'], "continue working")
        self.assertIsNotNone(params['stop_condition'])
    @patch('builtins.input')
    def test_broadcast_to_leaves_empty_prompt_cancellation(self, mock_input):
        """Test parameter collection with empty prompt cancels operation."""
        mock_input.side_effect = [""]  # empty prompt
        fp_handler = FunctionalPromptHandler()
        params = fp_handler._collect_parameters('broadcast_to_leaves', None)
        self.assertIsNone(params)
    def test_broadcast_to_leaves_function_exists(self):
        """Test that the broadcast_to_leaves function exists in functional_prompts."""
        self.assertTrue(hasattr(fp, 'broadcast_to_leaves'))
        self.assertTrue(callable(fp.broadcast_to_leaves))
if __name__ == '__main__':
    unittest.main()
