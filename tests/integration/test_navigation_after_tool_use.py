"""
Integration test for issue #206: Navigation after tool use crashes the CLI.

This test verifies that navigating up/down the conversation tree after tool use
doesn't cause API errors due to orphaned tool_calls without corresponding tool_results.

The issue occurs when:
1. Bot makes a tool call (assistant node with tool_calls)
2. Tool results are stored in a child user node
3. Navigation moves bot.conversation to the assistant node
4. _build_messages() only walks UP the tree, missing the tool_results in child nodes
5. API call fails because tool_use blocks lack corresponding tool_result blocks

The fix (_ensure_valid_conversation_position) automatically advances the conversation
position to include tool_results when navigating to an assistant node with tool_calls.
"""

import pytest

from bots.dev.cli import CLIContext, ConversationHandler
from bots.foundation.anthropic_bots import AnthropicNode
from bots.testing.mock_bot import MockBot

pytestmark = pytest.mark.integration


class TestNavigationAfterToolUse:
    """Test navigation commands after tool use to verify issue #206 is fixed."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot = MockBot(name="TestBot")
        self.context = CLIContext()
        self.handler = ConversationHandler()

    def _create_conversation_with_tool_use(self):
        """
        Create a conversation tree with tool calls and results.
        Structure:
        root (system) -> user1 -> assistant1 (with tool_calls) -> user2 (with tool_results) -> assistant2
        """
        # Root node
        root = AnthropicNode(content="System message", role="system")

        # User message 1
        user1 = AnthropicNode(content="Please use a tool", role="user", parent=root)
        root.replies.append(user1)

        # Assistant response with tool calls
        assistant1 = AnthropicNode(
            content="I'll use the tool",
            role="assistant",
            parent=user1,
            tool_calls=[{"id": "toolu_123", "name": "test_tool", "input": {"param": "value"}}],
        )
        user1.replies.append(assistant1)

        # User node with tool results
        user2 = AnthropicNode(
            content="",
            role="user",
            parent=assistant1,
            tool_results=[{"tool_use_id": "toolu_123", "content": "Tool result", "type": "tool_result"}],
        )
        assistant1.replies.append(user2)

        # Final assistant response
        assistant2 = AnthropicNode(content="Here's the final answer", role="assistant", parent=user2)
        user2.replies.append(assistant2)

        return root, assistant1, assistant2

    def test_navigate_up_after_tool_use(self):
        """Test that navigating up after tool use doesn't crash.

        This is the core issue #206 scenario.
        """
        root, assistant1, assistant2 = self._create_conversation_with_tool_use()

        # Start at the final assistant node
        self.bot.conversation = assistant2

        # Navigate up - should move to assistant1, but _ensure_valid_conversation_position
        # should automatically advance to include tool_results
        result = self.handler.up(self.bot, self.context, [])

        # Verify we didn't crash
        assert result is not None
        assert "type" in result

        # Verify we're at a valid position (not on assistant1 with orphaned tool_calls)
        # The fix should have moved us forward to assistant2 or user2
        if self.bot.conversation.role == "assistant":
            # If we're on an assistant node, it should not have orphaned tool_calls
            if self.bot.conversation.tool_calls:
                # If it has tool_calls, verify tool_results are accessible
                messages = self.bot.conversation._build_messages()
                # Check that the messages don't have orphaned tool_use blocks
                for i, msg in enumerate(messages):
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        # Next message should have tool_results
                        if i + 1 < len(messages):
                            next_msg = messages[i + 1]
                            assert next_msg.get("role") == "user"
                            # For Anthropic, tool_results are in content
                            assert "content" in next_msg

    def test_navigate_down_after_tool_use(self):
        """Test that navigating down through tool use doesn't crash."""
        root, assistant1, assistant2 = self._create_conversation_with_tool_use()

        # Start at root
        self.bot.conversation = root

        # Navigate down to user1
        result = self.handler.down(self.bot, self.context, [])
        assert result is not None

        # Navigate down again - should handle tool_calls properly
        result = self.handler.down(self.bot, self.context, [])
        assert result is not None

        # Verify we're at a valid position
        if self.bot.conversation.role == "assistant" and self.bot.conversation.tool_calls:
            # Should have been moved forward to include tool_results
            messages = self.bot.conversation._build_messages()
            # Verify no orphaned tool_calls
            for i, msg in enumerate(messages):
                if msg.get("role") == "assistant" and "tool_calls" in msg:
                    if i + 1 < len(messages):
                        next_msg = messages[i + 1]
                        assert next_msg.get("role") == "user"

    def test_multiple_tool_calls_navigation(self):
        """Test navigation with multiple tool calls in sequence."""
        # Root node
        root = AnthropicNode(content="System message", role="system")

        # First tool call sequence
        user1 = AnthropicNode(content="Use tool 1", role="user", parent=root)
        root.replies.append(user1)

        assistant1 = AnthropicNode(
            content="Using tool 1",
            role="assistant",
            parent=user1,
            tool_calls=[{"id": "toolu_1", "name": "tool1", "input": {}}],
        )
        user1.replies.append(assistant1)

        user2 = AnthropicNode(
            content="",
            role="user",
            parent=assistant1,
            tool_results=[{"tool_use_id": "toolu_1", "content": "Result 1", "type": "tool_result"}],
        )
        assistant1.replies.append(user2)

        assistant2 = AnthropicNode(content="Got result 1", role="assistant", parent=user2)
        user2.replies.append(assistant2)

        # Second tool call sequence
        user3 = AnthropicNode(content="Use tool 2", role="user", parent=assistant2)
        assistant2.replies.append(user3)

        assistant3 = AnthropicNode(
            content="Using tool 2",
            role="assistant",
            parent=user3,
            tool_calls=[{"id": "toolu_2", "name": "tool2", "input": {}}],
        )
        user3.replies.append(assistant3)

        user4 = AnthropicNode(
            content="",
            role="user",
            parent=assistant3,
            tool_results=[{"tool_use_id": "toolu_2", "content": "Result 2", "type": "tool_result"}],
        )
        assistant3.replies.append(user4)

        assistant4 = AnthropicNode(content="Got result 2", role="assistant", parent=user4)
        user4.replies.append(assistant4)

        # Start at the end
        self.bot.conversation = assistant4

        # Navigate up multiple times
        for _ in range(3):
            result = self.handler.up(self.bot, self.context, [])
            assert result is not None
            # Verify no orphaned tool_calls at each step
            if self.bot.conversation.role == "assistant" and self.bot.conversation.tool_calls:
                messages = self.bot.conversation._build_messages()
                for i, msg in enumerate(messages):
                    if msg.get("role") == "assistant" and "tool_calls" in msg:
                        if i + 1 < len(messages):
                            next_msg = messages[i + 1]
                            assert next_msg.get("role") == "user"

    def test_navigation_without_tool_use(self):
        """Test that normal navigation still works without tool use."""
        # Create a simple conversation without tools
        root = AnthropicNode(content="System", role="system")
        user1 = AnthropicNode(content="Hello", role="user", parent=root)
        root.replies.append(user1)
        assistant1 = AnthropicNode(content="Hi there", role="assistant", parent=user1)
        user1.replies.append(assistant1)
        user2 = AnthropicNode(content="How are you?", role="user", parent=assistant1)
        assistant1.replies.append(user2)
        assistant2 = AnthropicNode(content="I'm good", role="assistant", parent=user2)
        user2.replies.append(assistant2)

        self.bot.conversation = assistant2

        # Navigate up
        result = self.handler.up(self.bot, self.context, [])
        assert result is not None
        assert "type" in result

        # Navigate down
        result = self.handler.down(self.bot, self.context, [])
        assert result is not None
        assert "type" in result

    def test_ensure_valid_conversation_position_with_tool_calls(self):
        """Test _ensure_valid_conversation_position directly."""
        root, assistant1, assistant2 = self._create_conversation_with_tool_use()

        # Position at assistant1 (has tool_calls)
        self.bot.conversation = assistant1

        # Call the validation method
        adjusted = self.handler._ensure_valid_conversation_position(self.bot)

        # Should have adjusted position
        assert adjusted is True

        # Should have moved forward (to user2 or assistant2)
        assert self.bot.conversation != assistant1

    def test_ensure_valid_conversation_position_without_tool_calls(self):
        """Test _ensure_valid_conversation_position with no tool calls."""
        root = AnthropicNode(content="System", role="system")
        user1 = AnthropicNode(content="Hello", role="user", parent=root)
        root.replies.append(user1)
        assistant1 = AnthropicNode(content="Hi", role="assistant", parent=user1)
        user1.replies.append(assistant1)

        self.bot.conversation = assistant1

        # Call the validation method
        adjusted = self.handler._ensure_valid_conversation_position(self.bot)

        # Should not have adjusted position
        assert adjusted is False

        # Should still be at assistant1
        assert self.bot.conversation == assistant1


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
