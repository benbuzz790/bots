import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import bots.dev.cli as cli_module
from bots.foundation.base import ConversationNode

"""
Test suite for the new /combine_leaves command functionality.
"""
# Add the parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class TestCombineLeavesCommand(unittest.TestCase):
    """Test the new /combine_leaves command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = self._create_test_conversation_tree()
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot
        self.handler = cli_module.ConversationHandler()

    def _create_test_conversation_tree(self):
        """Create a test conversation tree with multiple leaves."""
        root = ConversationNode("system", "System message")
        # Create branches with leaves
        branch1 = ConversationNode("user", "Branch 1", parent=root)
        branch2 = ConversationNode("user", "Branch 2", parent=root)
        root.replies.extend([branch1, branch2])
        leaf1 = ConversationNode(
            "assistant",
            "Analysis from perspective 1: Security is important",
            parent=branch1,
        )
        leaf2 = ConversationNode(
            "assistant",
            "Analysis from perspective 2: Performance matters",
            parent=branch2,
        )
        branch1.replies.append(leaf1)
        branch2.replies.append(leaf2)
        return root

    @patch("builtins.input")
    @patch("builtins.print")
    @patch("bots.flows.functional_prompts.recombine")
    def test_combine_leaves_success(self, mock_recombine, mock_print, mock_input):
        """Test successful combination of leaves."""
        mock_input.return_value = "1"  # Select concatenate recombinator
        mock_recombine.return_value = ("Combined result", MagicMock())
        with patch("bots.dev.cli.pretty") as mock_pretty:
            result = self.handler.combine_leaves(self.mock_bot, self.context, [])
        self.assertIn("Successfully combined 2 leaves", result)
        self.assertIn("concatenate", result)
        mock_recombine.assert_called_once()
        mock_pretty.assert_called_once()

    def test_combine_leaves_no_leaves(self):
        """Test combine_leaves when no leaves exist."""
        # Mock _find_leaves to return empty list
        with patch.object(self.handler, "_find_leaves", return_value=[]):
            result = self.handler.combine_leaves(self.mock_bot, self.context, [])
            self.assertIn("No leaves found", result)

    def test_combine_leaves_insufficient_leaves(self):
        """Test combine_leaves with only one leaf."""
        # Create tree with only one leaf
        root = ConversationNode("system", "System")
        leaf = ConversationNode("assistant", "Only leaf", parent=root)
        root.replies.append(leaf)
        self.mock_bot.conversation = root
        result = self.handler.combine_leaves(self.mock_bot, self.context, [])
        self.assertIn("Need at least 2 leaves", result)

    @patch("builtins.input")
    def test_combine_leaves_invalid_recombinator(self, mock_input):
        """Test combine_leaves with invalid recombinator selection."""
        mock_input.return_value = "invalid"
        result = self.handler.combine_leaves(self.mock_bot, self.context, [])
        self.assertIn("Invalid recombinator selection", result)

    @patch("builtins.input")
    @patch("bots.flows.functional_prompts.recombine")
    def test_combine_leaves_error_handling(self, mock_recombine, mock_input):
        """Test combine_leaves error handling."""
        mock_input.return_value = "1"
        mock_recombine.side_effect = Exception("Test error")
        result = self.handler.combine_leaves(self.mock_bot, self.context, [])
        self.assertIn("Error combining leaves", result)
        self.assertIn("Test error", result)


if __name__ == "__main__":
    unittest.main()
