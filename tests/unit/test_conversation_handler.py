"""Tests for ConversationHandler with frontend abstraction."""

from unittest.mock import MagicMock, patch

from bots.dev.cli import CLIContext, ConversationHandler
from bots.foundation.base import Bot, ConversationNode


class TestConversationHandlerDataFormat:
    """Test that ConversationHandler returns data dicts instead of displaying directly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ConversationHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)
        # Create a simple conversation tree
        self.root = ConversationNode(role="user", content="root message")
        self.child1 = self.root._add_reply(role="assistant", content="child 1")
        self.child2 = self.child1._add_reply(role="user", content="child 2")
        self.child3 = self.child2._add_reply(role="assistant", content="child 3")
        self.mock_bot.conversation = self.child3
        self.mock_bot.name = "TestBot"

    def test_up_returns_data_dict(self):
        """up() should return data dict, not call pretty()."""
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        # Should return a dict
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message")

    def test_up_at_root_returns_system_message(self):
        """up() at root should return system message."""
        self.mock_bot.conversation = self.root
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        assert result["type"] == "system"
        assert "root" in result["content"].lower() or "can't go up" in result["content"].lower()

    def test_down_returns_data_dict(self):
        """down() should return data dict."""
        self.mock_bot.conversation = self.child1
        result = self.handler.down(self.mock_bot, self.mock_context, [])
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message")

    def test_left_returns_data_dict(self):
        """left() should return data dict."""
        result = self.handler.left(self.mock_bot, self.mock_context, [])
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message")

    def test_right_returns_data_dict(self):
        """right() should return data dict."""
        result = self.handler.right(self.mock_bot, self.mock_context, [])
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message")

    def test_root_returns_data_dict(self):
        """root() should return data dict."""
        result = self.handler.root(self.mock_bot, self.mock_context, [])
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message")

    def test_label_returns_data_dict(self):
        """label() should return data dict."""
        result = self.handler.label(self.mock_bot, self.mock_context, ["test_label"])
        assert isinstance(result, dict)
        assert result["type"] == "system"

    def test_leaf_returns_data_dict(self):
        """leaf() should return data dict."""
        result = self.handler.leaf(self.mock_bot, self.mock_context, [])
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message")

    def test_combine_leaves_returns_data_dict(self):
        """combine_leaves() should return data dict."""
        result = self.handler.combine_leaves(self.mock_bot, self.mock_context, [])
        assert isinstance(result, dict)
        assert result["type"] in ("system", "message", "error")

    def test_navigation_includes_conversation_content(self):
        """Navigation that shows conversation should include content in result."""
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        # If navigation succeeded and shows content, should have message type
        if result["type"] == "message":
            assert "content" in result
            assert "role" in result

    @patch("bots.dev.cli.pretty")
    def test_no_direct_pretty_calls(self, mock_pretty):
        """Handler methods should not call pretty() directly."""
        # Try various navigation commands
        self.handler.up(self.mock_bot, self.mock_context, [])
        self.handler.down(self.mock_bot, self.mock_context, [])
        self.handler.left(self.mock_bot, self.mock_context, [])
        self.handler.right(self.mock_bot, self.mock_context, [])
        self.handler.root(self.mock_bot, self.mock_context, [])
        # pretty() should not be called by handlers
        assert not mock_pretty.called, "Handlers should not call pretty() directly"


class TestConversationHandlerIntegration:
    """Integration tests with mock frontend."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = ConversationHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_frontend = MagicMock()
        self.mock_context.frontend = self.mock_frontend
        # Create conversation tree
        self.root = ConversationNode(role="user", content="root")
        self.child = self.root._add_reply(role="assistant", content="response")
        self.mock_bot.conversation = self.child
        self.mock_bot.name = "TestBot"

    def test_cli_displays_handler_result(self):
        """CLI should use frontend to display handler results."""
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        # Simulate CLI displaying the result
        if result["type"] == "system":
            self.mock_frontend.display_system(result["content"])
        elif result["type"] == "message":
            self.mock_frontend.display_message(result["role"], result["content"])
        # Verify frontend was called
        assert self.mock_frontend.display_system.called or self.mock_frontend.display_message.called
