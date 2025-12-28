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

    def test_up_changes_conversation_content(self):
        """Test that /up actually changes the bot.conversation node and returns different content."""
        # Create a conversation tree with distinct content at each level
        root = ConversationNode(role="user", content="user message 1")
        assistant1 = root._add_reply(role="assistant", content="assistant response 1")
        user2 = assistant1._add_reply(role="user", content="user message 2")
        assistant2 = user2._add_reply(role="assistant", content="assistant response 2")
        user3 = assistant2._add_reply(role="user", content="user message 3")
        assistant3 = user3._add_reply(role="assistant", content="assistant response 3")

        # Start at the bottom of the tree
        self.mock_bot.conversation = assistant3
        original_content = self.mock_bot.conversation.content
        assert original_content == "assistant response 3"

        # Move up once - should go to assistant2
        result = self.handler.up(self.mock_bot, self.mock_context, [])

        # Verify the conversation node actually changed
        assert self.mock_bot.conversation.content != original_content
        assert self.mock_bot.conversation.content == "assistant response 2"

        # Verify the result contains the new content
        if result["type"] == "message":
            assert result["content"] == "assistant response 2"
            assert result["role"] == "assistant"

        # Move up again - should go to assistant1
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        assert self.mock_bot.conversation.content == "assistant response 1"

        if result["type"] == "message":
            assert result["content"] == "assistant response 1"

    def test_up_command_displays_correct_content_in_cli(self):
        """Test that /up command returns the correct content for CLI display."""
        # Create a realistic conversation tree
        root = ConversationNode(role="user", content="First question")
        assistant1 = root._add_reply(role="assistant", content="First answer with unique content ABC")
        user2 = assistant1._add_reply(role="user", content="Second question")
        assistant2 = user2._add_reply(role="assistant", content="Second answer with unique content XYZ")

        # Start at assistant2
        self.mock_bot.conversation = assistant2

        # Execute /up command
        result = self.handler.up(self.mock_bot, self.mock_context, [])

        # Verify result structure matches what CLI expects
        assert isinstance(result, dict), "Result should be a dict"
        assert "type" in result, "Result should have 'type' key"

        # Should return message type with content
        assert result["type"] == "message", f"Expected 'message' type, got {result['type']}"
        assert "content" in result, "Result should have 'content' key"
        assert "role" in result, "Result should have 'role' key"

        # Verify the content is from assistant1, not assistant2
        assert (
            result["content"] == "First answer with unique content ABC"
        ), f"Expected assistant1 content, got: {result['content']}"
        assert result["role"] == "assistant"

        # Verify bot.conversation was actually updated
        assert self.mock_bot.conversation.content == "First answer with unique content ABC"
        assert self.mock_bot.conversation == assistant1

    def test_up_with_tool_calls_bug(self):
        """Test that /up doesn't get stuck when previous assistant message has tool_calls.

        This reproduces the bug where _ensure_valid_conversation_position moves you
        forward after /up moves you back, causing you to stay at the same message.
        """
        # Create conversation tree with tool usage
        root = ConversationNode(role="user", content="First question")
        assistant1 = root._add_reply(role="assistant", content="First answer ABC")
        # Simulate assistant1 having tool_calls
        assistant1.tool_calls = [{"id": "call_123", "name": "some_tool", "args": {}}]

        user_tool_result = assistant1._add_reply(role="user", content="")
        user_tool_result.tool_results = [{"tool_use_id": "call_123", "content": "tool output"}]

        assistant1_continued = user_tool_result._add_reply(role="assistant", content="After tool result")

        user2 = assistant1_continued._add_reply(role="user", content="Second question")
        assistant2 = user2._add_reply(role="assistant", content="Second answer XYZ")

        # Start at assistant2
        self.mock_bot.conversation = assistant2
        original_content = assistant2.content

        # Execute /up command
        self.handler.up(self.mock_bot, self.mock_context, [])

        # BUG: The conversation should move to assistant1_continued or earlier,
        # but _ensure_valid_conversation_position might move it forward again

        # Verify we actually moved to a different message
        assert (
            self.mock_bot.conversation.content != original_content
        ), f"Bug: /up didn't change position! Still at: {self.mock_bot.conversation.content}"

        # Should be at assistant1_continued, not back at assistant2
        assert self.mock_bot.conversation.content != "Second answer XYZ", "Bug: /up moved back to the same position!"

    def test_up_multiple_times_shows_different_content(self):
        """Test that calling /up multiple times shows different content each time."""
        # Create a longer conversation tree
        root = ConversationNode(role="user", content="Q1")
        a1 = root._add_reply(role="assistant", content="A1")
        u2 = a1._add_reply(role="user", content="Q2")
        a2 = u2._add_reply(role="assistant", content="A2")
        u3 = a2._add_reply(role="user", content="Q3")
        a3 = u3._add_reply(role="assistant", content="A3")
        u4 = a3._add_reply(role="user", content="Q4")
        a4 = u4._add_reply(role="assistant", content="A4")

        # Start at a4
        self.mock_bot.conversation = a4

        # Track what content we see
        seen_contents = [a4.content]

        # Call /up three times
        for i in range(3):
            self.handler.up(self.mock_bot, self.mock_context, [])
            current_content = self.mock_bot.conversation.content
            seen_contents.append(current_content)

            # Each call should show different content
            assert (
                current_content not in seen_contents[:-1]
            ), f"Iteration {i+1}: /up showed repeated content '{current_content}'. Seen: {seen_contents}"

        # Should have seen: A4, A3, A2, A1
        assert seen_contents == ["A4", "A3", "A2", "A1"], f"Expected to see A4->A3->A2->A1, but got: {seen_contents}"

    def test_up_with_every_message_having_tool_calls(self):
        """Test /up when every assistant message has tool_calls.

        This is the most likely scenario to reproduce the bug where
        _ensure_valid_conversation_position keeps moving you forward.
        """
        # Create conversation where every assistant uses tools
        root = ConversationNode(role="user", content="Q1")

        # Assistant 1 with tool call
        a1 = root._add_reply(role="assistant", content="A1")
        a1.tool_calls = [{"id": "call_1", "name": "tool1", "args": {}}]
        u1_tool = a1._add_reply(role="user", content="")
        u1_tool.tool_results = [{"tool_use_id": "call_1", "content": "result1"}]
        a1_cont = u1_tool._add_reply(role="assistant", content="A1_continued")

        # User asks next question
        u2 = a1_cont._add_reply(role="user", content="Q2")

        # Assistant 2 with tool call
        a2 = u2._add_reply(role="assistant", content="A2")
        a2.tool_calls = [{"id": "call_2", "name": "tool2", "args": {}}]
        u2_tool = a2._add_reply(role="user", content="")
        u2_tool.tool_results = [{"tool_use_id": "call_2", "content": "result2"}]
        a2_cont = u2_tool._add_reply(role="assistant", content="A2_continued")

        # User asks next question
        u3 = a2_cont._add_reply(role="user", content="Q3")

        # Assistant 3 with tool call
        a3 = u3._add_reply(role="assistant", content="A3")
        a3.tool_calls = [{"id": "call_3", "name": "tool3", "args": {}}]
        u3_tool = a3._add_reply(role="user", content="")
        u3_tool.tool_results = [{"tool_use_id": "call_3", "content": "result3"}]
        a3_cont = u3_tool._add_reply(role="assistant", content="A3_continued")

        # Start at a3_cont
        self.mock_bot.conversation = a3_cont

        # First /up - should show A2_continued
        result1 = self.handler.up(self.mock_bot, self.mock_context, [])
        content1 = result1.get("content", "")

        # Second /up - should show A1_continued
        result2 = self.handler.up(self.mock_bot, self.mock_context, [])
        content2 = result2.get("content", "")

        # Third /up - should show something earlier or hit root
        result3 = self.handler.up(self.mock_bot, self.mock_context, [])
        content3 = result3.get("content", "") if result3.get("type") == "message" else result3.get("content", "")

        # Verify we're seeing different content each time
        assert content1 != "A3_continued", "First /up still showing A3_continued"
        assert content2 != content1, f"Second /up showing same as first: {content1}"
        assert content3 != content2, f"Third /up showing same as second: {content2}"

        print(f"Contents seen: {content1}, {content2}, {content3}")

    def test_up_lands_on_assistant_with_tool_calls(self):
        """Test that /up can land on an assistant with tool_calls (for viewing).

        The user should be able to navigate to and VIEW an assistant message with tool_calls,
        but if they try to send a message from that position, it should automatically
        move forward to include the tool_results.
        """
        # Create conversation with tool usage
        root = ConversationNode(role="user", content="Q1")
        a1 = root._add_reply(role="assistant", content="A1 - used a tool")
        a1.tool_calls = [{"id": "call_1", "name": "tool1", "args": {}}]

        u1_tool = a1._add_reply(role="user", content="")
        u1_tool.tool_results = [{"tool_use_id": "call_1", "content": "result1"}]

        a1_cont = u1_tool._add_reply(role="assistant", content="A1 - after tool result")

        u2 = a1_cont._add_reply(role="user", content="Q2")
        a2 = u2._add_reply(role="assistant", content="A2")

        # Start at a2
        self.mock_bot.conversation = a2

        # /up should land on a1_cont
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        assert result["content"] == "A1 - after tool result"
        assert self.mock_bot.conversation == a1_cont

        # /up again should land on a1 (which has tool_calls)
        result = self.handler.up(self.mock_bot, self.mock_context, [])
        assert result["content"] == "A1 - used a tool"
        assert self.mock_bot.conversation == a1

        # Verify we're at a node with tool_calls
        assert self.mock_bot.conversation.tool_calls is not None
        assert len(self.mock_bot.conversation.tool_calls) > 0

        # This is OK for viewing! The user can see this message.
        # But if they try to send a message, _handle_chat should move forward
        # to include the tool_results before processing the message.
