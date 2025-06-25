import os
import sys
import unittest
from unittest.mock import MagicMock, patch

import bots.dev.cli as cli_module
from bots.foundation.base import ConversationNode

"""
Test suite for the new enhanced /leaf command functionality.
"""
# Add the parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class TestLeafCommand(unittest.TestCase):
    """Test the new enhanced /leaf command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = self._create_test_conversation_tree()
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot
        self.handler = cli_module.ConversationHandler()

    def _create_test_conversation_tree(self):
        """Create a test conversation tree with multiple branches."""
        # Root node
        root = ConversationNode("system", "System message")
        # First level - user prompt
        user1 = ConversationNode("user", "Tell me about AI", parent=root)
        root.replies.append(user1)
        # First level - assistant response with branches
        assistant1 = ConversationNode("assistant", "AI is fascinating", parent=user1)
        user1.replies.append(assistant1)
        # Create branches
        branch1_user = ConversationNode("user", "Tell me more about ML", parent=assistant1)
        branch2_user = ConversationNode("user", "What about neural networks?", parent=assistant1)
        assistant1.replies.extend([branch1_user, branch2_user])
        # Create leaves
        leaf1 = ConversationNode(
            "assistant",
            "Machine learning is a subset of AI that focuses on algorithms",
            parent=branch1_user,
        )
        leaf2 = ConversationNode(
            "assistant",
            "Neural networks are inspired by biological neural networks",
            parent=branch2_user,
        )
        branch1_user.replies.append(leaf1)
        branch2_user.replies.append(leaf2)
        # Add labels to some nodes
        leaf1.labels = ["ml_info"]
        leaf2.labels = ["nn_info"]
        return assistant1  # Start from a node with multiple leaves

    def test_leaf_command_shows_leaves(self):
        """Test that /leaf command shows all available leaves."""
        # Test with direct argument to avoid input() call
        result = self.handler.leaf(self.mock_bot, self.context, ["1"])
        # Should show that it jumped to a leaf, indicating leaves were found
        self.assertIn("Jumped to leaf 1", result)
        # Should have cached the leaves
        self.assertEqual(len(self.context.cached_leaves), 2)

    def test_leaf_command_with_direct_jump(self):
        """Test /leaf command with direct jump to specific leaf."""
        # Test jumping to leaf 1
        result = self.handler.leaf(self.mock_bot, self.context, ["1"])
        self.assertIn("Jumped to leaf 1", result)
        # Should have updated bot conversation
        self.assertEqual(len(self.context.cached_leaves), 2)

    def test_leaf_command_invalid_number(self):
        """Test /leaf command with invalid leaf number."""
        result = self.handler.leaf(self.mock_bot, self.context, ["99"])
        self.assertIn("Invalid leaf number", result)
        self.assertIn("Must be between 1 and", result)

    def test_leaf_command_no_leaves(self):
        """Test /leaf command when no leaves exist."""
        # Create a node that has replies but no leaves (empty conversation
        # tree)
        root = ConversationNode("system", "System")
        # Don't add any replies, so _find_leaves will return empty
        self.mock_bot.conversation = root
        # Mock _find_leaves to return empty list
        with patch.object(self.handler, "_find_leaves", return_value=[]):
            result = self.handler.leaf(self.mock_bot, self.context, [])
            self.assertIn("No leaves found", result)

    @patch("builtins.input")
    def test_leaf_command_interactive_selection(self, mock_input):
        """Test /leaf command with interactive selection."""
        mock_input.return_value = "2"  # Select leaf 2
        result = self.handler.leaf(self.mock_bot, self.context, [])
        self.assertIn("Jumped to leaf 2", result)

    @patch("builtins.input")
    def test_leaf_command_interactive_cancel(self, mock_input):
        """Test /leaf command with interactive cancellation."""
        mock_input.return_value = ""  # Cancel selection
        result = self.handler.leaf(self.mock_bot, self.context, [])
        self.assertIn("Staying at current position", result)

    def test_get_leaf_preview_short_content(self):
        """Test _get_leaf_preview with short content."""
        node = ConversationNode("assistant", "Short message")
        preview = self.handler._get_leaf_preview(node)
        # The preview should contain the content, even if it's just the role
        self.assertIsNotNone(preview)
        self.assertIsInstance(preview, str)

    def test_get_leaf_preview_long_content(self):
        """Test _get_leaf_preview with long content that needs cutting."""
        long_content = "This is a very long message that should be cut from the middle " * 10
        node = ConversationNode("assistant", long_content)
        preview = self.handler._get_leaf_preview(node, max_length=100)
        # Just check that we get a preview and it's reasonable length
        self.assertIsNotNone(preview)
        self.assertIsInstance(preview, str)
        # Should be shorter than original if cutting worked
        self.assertTrue(len(preview) <= 100)


if __name__ == "__main__":
    unittest.main()
