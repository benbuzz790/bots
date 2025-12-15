import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import pytest

import bots.dev.cli as cli_module
from bots.foundation.base import ConversationNode

pytestmark = pytest.mark.e2e

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

    @patch("builtins.print")
    @patch("bots.flows.functional_prompts.recombine")
    def test_combine_leaves_success(self, mock_recombine, mock_print):
        """Test successful combination of leaves."""
        # New API: pass recombinator as argument instead of prompting
        mock_recombine.return_value = ("Combined result", MagicMock())
        result = self.handler.combine_leaves(self.mock_bot, self.context, ["1"])  # Pass "1" for concatenate
        # Result is now a dict
        self.assertIsInstance(result, dict)
        self.assertEqual(result["type"], "message")
        self.assertEqual(result["content"], "Combined result")
        mock_recombine.assert_called_once()

    def test_combine_leaves_no_leaves(self):
        """Test combine_leaves when no leaves exist."""
        # Mock _find_leaves to return empty list
        with patch.object(self.handler, "_find_leaves", return_value=[]):
            result = self.handler.combine_leaves(self.mock_bot, self.context, [])
            # Result is now a dict
            self.assertIsInstance(result, dict)
            content = result.get("content", "")
            self.assertIn("No leaves found", content)

    def test_combine_leaves_insufficient_leaves(self):
        """Test combine_leaves with only one leaf."""
        # Create tree with only one leaf
        root = ConversationNode("system", "System")
        leaf = ConversationNode("assistant", "Only leaf", parent=root)
        root.replies.append(leaf)
        self.mock_bot.conversation = root
        result = self.handler.combine_leaves(self.mock_bot, self.context, [])
        # Result is now a dict
        self.assertIsInstance(result, dict)
        content = result.get("content", "")
        self.assertIn("Need at least 2 leaves", content)

    def test_combine_leaves_invalid_recombinator(self):
        """Test combine_leaves with invalid recombinator selection."""
        # New API: pass invalid recombinator as argument
        result = self.handler.combine_leaves(self.mock_bot, self.context, ["invalid"])
        # Result is now a dict
        self.assertIsInstance(result, dict)
        content = result.get("content", "")
        self.assertIn("Invalid recombinator selection", content)

    @patch("bots.flows.functional_prompts.recombine")
    def test_combine_leaves_error_handling(self, mock_recombine):
        """Test combine_leaves error handling."""
        # New API: pass recombinator as argument
        mock_recombine.side_effect = Exception("Test error")
        result = self.handler.combine_leaves(self.mock_bot, self.context, ["1"])
        # Result is now a dict
        self.assertIsInstance(result, dict)
        content = result.get("content", "")
        self.assertIn("Error combining leaves", content)
        self.assertIn("Test error", content)


if __name__ == "__main__":
    unittest.main()
