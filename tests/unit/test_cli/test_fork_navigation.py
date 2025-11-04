import unittest
from unittest.mock import MagicMock

import pytest

import bots.dev.cli as cli_module
from bots.foundation.base import ConversationNode

"""
Test suite for the /lastfork and /nextfork navigation commands.
"""


class TestForkNavigationCommands(unittest.TestCase):
    """Test the /lastfork and /nextfork navigation commands."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = self._create_test_conversation_tree()
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot
        self.handler = cli_module.ConversationHandler()

    def _create_test_conversation_tree(self):
        """Create a test conversation tree with multiple forks.

    Structure:
    root -> A -> B -> C -> E -> F
                 |         |
                 D         G

    Forks at: B (2 branches), E (2 branches)
    """
        # Root node
        root = ConversationNode("System message", "system")

        # A
        a = ConversationNode("Message A", "user", parent=root)
        root.replies.append(a)
        a_response = ConversationNode("Response to A", "assistant", parent=a)
        a.replies.append(a_response)

        # B (fork point - 2 branches)
        b = ConversationNode("Message B", "user", parent=a_response)
        a_response.replies.append(b)
        b_response = ConversationNode("Response to B", "assistant", parent=b)
        b.replies.append(b_response)

        # C (branch 1 from B)
        c = ConversationNode("Message C", "user", parent=b_response)
        b_response.replies.append(c)
        c_response = ConversationNode("Response to C", "assistant", parent=c)
        c.replies.append(c_response)

        # D (branch 2 from B)
        d = ConversationNode("Message D", "user", parent=b_response)
        b_response.replies.append(d)
        d_response = ConversationNode("Response to D", "assistant", parent=d)
        d.replies.append(d_response)

        # E (fork point - 2 branches, child of C)
        e = ConversationNode("Message E", "user", parent=c_response)
        c_response.replies.append(e)
        e_response = ConversationNode("Response to E", "assistant", parent=e)
        e.replies.append(e_response)

        # F (branch 1 from E)
        f = ConversationNode("Message F", "user", parent=e_response)
        e_response.replies.append(f)
        f_response = ConversationNode("Response to F", "assistant", parent=f)
        f.replies.append(f_response)

        # G (branch 2 from E)
        g = ConversationNode("Message G", "user", parent=e_response)
        e_response.replies.append(g)
        g_response = ConversationNode("Response to G", "assistant", parent=g)
        g.replies.append(g_response)

        # Return F's response as starting point (deep in tree, past both forks)
        return f_response

    def test_lastfork_finds_previous_fork(self):
        """Test that /lastfork finds the nearest fork going up the tree."""
        # Mock _ensure_assistant_node to always return True
        self.handler._ensure_assistant_node = MagicMock(return_value=True)
        # Mock _display_conversation_context to avoid display issues
        self.handler._display_conversation_context = MagicMock()

        # Starting from F (deep in tree), should find fork at E
        result = self.handler.lastfork(self.mock_bot, self.context, [])

        self.assertIn("Moved to previous fork", result)
        self.assertIn("2 branches", result)
        # Should have moved to E's response (the fork point)
        self.assertEqual(self.mock_bot.conversation.content, "Response to E")

    def test_lastfork_finds_earlier_fork(self):
        """Test that /lastfork can find earlier forks when called multiple times."""
        # Mock _ensure_assistant_node to always return True
        self.handler._ensure_assistant_node = MagicMock(return_value=True)
        # Mock _display_conversation_context to avoid display issues
        self.handler._display_conversation_context = MagicMock()

        # First call: F -> E
        self.handler.lastfork(self.mock_bot, self.context, [])
        self.assertEqual(self.mock_bot.conversation.content, "Response to E")

        # Second call: E -> B
        result = self.handler.lastfork(self.mock_bot, self.context, [])
        self.assertIn("Moved to previous fork", result)
        self.assertEqual(self.mock_bot.conversation.content, "Response to B")

    def test_lastfork_no_fork_found(self):
        """Test /lastfork when no fork exists going up."""
        # Start from a node before any forks
        root = ConversationNode("System", "system")
        a = ConversationNode("A", "user", parent=root)
        root.replies.append(a)
        a_response = ConversationNode("Response A", "assistant", parent=a)
        a.replies.append(a_response)

        self.mock_bot.conversation = a_response

        result = self.handler.lastfork(self.mock_bot, self.context, [])
        self.assertIn("No fork found going up the tree", result)

    def test_nextfork_finds_next_fork(self):
        """Test that /nextfork finds the nearest fork going down the tree."""
        # Mock _ensure_assistant_node to always return True
        self.handler._ensure_assistant_node = MagicMock(return_value=True)
        # Mock _display_conversation_context to avoid display issues
        self.handler._display_conversation_context = MagicMock()

        # Start from root, should find fork at B
        root = ConversationNode("System message", "system")
        a = ConversationNode("Message A", "user", parent=root)
        root.replies.append(a)
        a_response = ConversationNode("Response to A", "assistant", parent=a)
        a.replies.append(a_response)

        # B (fork point)
        b = ConversationNode("Message B", "user", parent=a_response)
        a_response.replies.append(b)
        b_response = ConversationNode("Response to B", "assistant", parent=b)
        b.replies.append(b_response)

        # Two branches from B
        c = ConversationNode("Message C", "user", parent=b_response)
        d = ConversationNode("Message D", "user", parent=b_response)
        b_response.replies.extend([c, d])

        self.mock_bot.conversation = root

        result = self.handler.nextfork(self.mock_bot, self.context, [])
        self.assertIn("Moved to next fork", result)
        self.assertIn("2 branches", result)
        self.assertEqual(self.mock_bot.conversation.content, "Response to B")

    def test_nextfork_finds_later_fork(self):
        """Test that /nextfork finds forks further down the tree."""
        # Mock _ensure_assistant_node to always return True
        self.handler._ensure_assistant_node = MagicMock(return_value=True)
        # Mock _display_conversation_context to avoid display issues
        self.handler._display_conversation_context = MagicMock()

        # Start from B (first fork), should find E (second fork)
        # Use the full tree from setUp
        root = ConversationNode("System message", "system")
        a = ConversationNode("Message A", "user", parent=root)
        root.replies.append(a)
        a_response = ConversationNode("Response to A", "assistant", parent=a)
        a.replies.append(a_response)

        b = ConversationNode("Message B", "user", parent=a_response)
        a_response.replies.append(b)
        b_response = ConversationNode("Response to B", "assistant", parent=b)
        b.replies.append(b_response)

        # Two branches from B
        c = ConversationNode("Message C", "user", parent=b_response)
        d = ConversationNode("Message D", "user", parent=b_response)
        b_response.replies.extend([c, d])
        c_response = ConversationNode("Response to C", "assistant", parent=c)
        c.replies.append(c_response)

        # E (second fork, child of C)
        e = ConversationNode("Message E", "user", parent=c_response)
        c_response.replies.append(e)
        e_response = ConversationNode("Response to E", "assistant", parent=e)
        e.replies.append(e_response)

        # Two branches from E
        f = ConversationNode("Message F", "user", parent=e_response)
        g = ConversationNode("Message G", "user", parent=e_response)
        e_response.replies.extend([f, g])

        # Start from B
        self.mock_bot.conversation = b_response

        result = self.handler.nextfork(self.mock_bot, self.context, [])
        self.assertIn("Moved to next fork", result)
        self.assertEqual(self.mock_bot.conversation.content, "Response to E")

    def test_nextfork_no_fork_found(self):
        """Test /nextfork when no fork exists going down."""
        # Create a linear tree with no forks
        root = ConversationNode("System", "system")
        a = ConversationNode("A", "user", parent=root)
        root.replies.append(a)
        a_response = ConversationNode("Response A", "assistant", parent=a)
        a.replies.append(a_response)
        b = ConversationNode("B", "user", parent=a_response)
        a_response.replies.append(b)
        b_response = ConversationNode("Response B", "assistant", parent=b)
        b.replies.append(b_response)

        self.mock_bot.conversation = root

        result = self.handler.nextfork(self.mock_bot, self.context, [])
        self.assertIn("No fork found going down the tree", result)

    def test_lastfork_backs_up_conversation(self):
        """Test that /lastfork backs up the conversation before moving."""
        original_node = self.mock_bot.conversation
        self.handler.lastfork(self.mock_bot, self.context, [])

        # Should have backed up the original position
        self.assertEqual(self.context.conversation_backup, original_node)

    def test_nextfork_backs_up_conversation(self):
        """Test that /nextfork backs up the conversation before moving."""
        root = ConversationNode("System", "system")
        a = ConversationNode("A", "user", parent=root)
        root.replies.append(a)
        a_response = ConversationNode("Response A", "assistant", parent=a)
        a.replies.append(a_response)

        # Create fork
        b = ConversationNode("B", "user", parent=a_response)
        c = ConversationNode("C", "user", parent=a_response)
        a_response.replies.extend([b, c])

        self.mock_bot.conversation = root
        original_node = self.mock_bot.conversation

        self.handler.nextfork(self.mock_bot, self.context, [])

        # Should have backed up the original position
        self.assertEqual(self.context.conversation_backup, original_node)

    def test_fork_navigation_integration(self):
        """Test using /lastfork and /nextfork together."""
        # Mock _ensure_assistant_node to always return True
        self.handler._ensure_assistant_node = MagicMock(return_value=True)
        # Mock _display_conversation_context to avoid display issues
        self.handler._display_conversation_context = MagicMock()

        # Start deep in tree at F
        original_position = self.mock_bot.conversation
        self.assertEqual(original_position.content, "Response to F")

        # Go back to E fork
        self.handler.lastfork(self.mock_bot, self.context, [])
        self.assertEqual(self.mock_bot.conversation.content, "Response to E")

        # Go back to B fork
        self.handler.lastfork(self.mock_bot, self.context, [])
        self.assertEqual(self.mock_bot.conversation.content, "Response to B")

        # Go forward to E fork
        self.handler.nextfork(self.mock_bot, self.context, [])
        self.assertEqual(self.mock_bot.conversation.content, "Response to E")

        # Try to go forward again (should find no fork)
        result = self.handler.nextfork(self.mock_bot, self.context, [])
        self.assertIn("No fork found going down the tree", result)


if __name__ == "__main__":
    unittest.main()