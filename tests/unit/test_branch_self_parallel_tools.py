"""Tests for branch_self compatibility with parallel tool calling."""

from unittest.mock import Mock, patch

from bots.foundation.base import Bot, ConversationNode
from bots.tools.self_tools import branch_self


class TestBranchSelfParallelTools:
    """Test branch_self with parallel tool calls."""

    def test_branch_self_handles_parallel_tool_calls(self):
        """Test that branch_self creates dummy results for all parallel tool calls."""
        # Create a mock bot
        bot = Mock(spec=Bot)
        bot.autosave = True
        bot.temperature = 0.7
        bot.max_tokens = 1000

        # Create a mock conversation node with parallel tool calls
        original_node = Mock(spec=ConversationNode)
        original_node.tool_calls = [
            {"id": "call_1", "name": "branch_self", "input": {"self_prompts": "['test']"}},
            {"id": "call_2", "name": "other_tool", "input": {"param": "value"}},
            {"id": "call_3", "name": "another_tool", "input": {"x": "y"}},
        ]
        original_node.replies = []

        # Mock the dummy node that will be created
        dummy_node = Mock(spec=ConversationNode)
        dummy_node.replies = []
        original_node._add_reply = Mock(return_value=dummy_node)

        bot.conversation = original_node

        # Mock tool handler
        bot.tool_handler = Mock()
        bot.tool_handler.generate_response_schema = Mock(
            side_effect=lambda call, msg: {"tool_use_id": call["id"], "content": msg}
        )
        bot.tool_handler.clear = Mock()
        bot.tool_handler.tools = []

        # Mock respond to avoid actual API calls
        bot.respond = Mock(return_value="Branch response")

        # Patch _get_calling_bot to return our mock bot
        with patch("bots.tools.self_tools._get_calling_bot", return_value=bot):
            # Patch deepcopy to return a new mock bot
            with patch("copy.deepcopy") as mock_deepcopy:
                branch_bot = Mock(spec=Bot)
                branch_bot.autosave = False
                branch_bot.conversation = Mock(spec=ConversationNode)
                branch_bot.conversation.replies = []
                branch_bot.tool_handler = Mock()
                branch_bot.tool_handler.clear = Mock()
                branch_bot.respond = Mock(return_value="Branch response")
                mock_deepcopy.return_value = branch_bot

                # Call branch_self
                branch_self(self_prompts="['test 1', 'test 2']", allow_work="False")

        # Verify that _add_reply was called with tool_results for ALL tool calls
        assert original_node._add_reply.called
        call_args = original_node._add_reply.call_args

        # Check that tool_results were provided
        assert "tool_results" in call_args.kwargs
        tool_results = call_args.kwargs["tool_results"]

        # Should have 3 tool results (one for each parallel tool call)
        assert len(tool_results) == 3

        # Verify each tool call got a result
        result_ids = {r["tool_use_id"] for r in tool_results}
        assert "call_1" in result_ids  # branch_self
        assert "call_2" in result_ids  # other_tool
        assert "call_3" in result_ids  # another_tool

        # Verify branch_self got the "in progress" message
        branch_self_result = next(r for r in tool_results if r["tool_use_id"] == "call_1")
        assert "Branching in progress" in branch_self_result["content"]

        # Verify other tools got placeholder messages
        other_result = next(r for r in tool_results if r["tool_use_id"] == "call_2")
        assert "Parallel tool execution" in other_result["content"]

    def test_branch_self_without_parallel_tools(self):
        """Test that branch_self still works when it's the only tool call."""
        # Create a mock bot
        bot = Mock(spec=Bot)
        bot.autosave = True

        # Create a mock conversation node with only branch_self
        original_node = Mock(spec=ConversationNode)
        original_node.tool_calls = [
            {"id": "call_1", "name": "branch_self", "input": {"self_prompts": "['test']"}},
        ]
        original_node.replies = []

        # Mock the dummy node
        dummy_node = Mock(spec=ConversationNode)
        dummy_node.replies = []
        original_node._add_reply = Mock(return_value=dummy_node)

        bot.conversation = original_node

        # Mock tool handler
        bot.tool_handler = Mock()
        bot.tool_handler.generate_response_schema = Mock(
            side_effect=lambda call, msg: {"tool_use_id": call["id"], "content": msg}
        )
        bot.tool_handler.clear = Mock()
        bot.tool_handler.tools = []

        bot.respond = Mock(return_value="Branch response")

        # Patch _get_calling_bot
        with patch("bots.tools.self_tools._get_calling_bot", return_value=bot):
            with patch("copy.deepcopy") as mock_deepcopy:
                branch_bot = Mock(spec=Bot)
                branch_bot.autosave = False
                branch_bot.conversation = Mock(spec=ConversationNode)
                branch_bot.conversation.replies = []
                branch_bot.tool_handler = Mock()
                branch_bot.tool_handler.clear = Mock()
                branch_bot.respond = Mock(return_value="Branch response")
                mock_deepcopy.return_value = branch_bot

                branch_self(self_prompts="['test']", allow_work="False")

        # Verify that _add_reply was called with exactly 1 tool_result
        assert original_node._add_reply.called
        call_args = original_node._add_reply.call_args
        tool_results = call_args.kwargs["tool_results"]

        # Should have 1 tool result
        assert len(tool_results) == 1
        assert tool_results[0]["tool_use_id"] == "call_1"

    def test_branch_self_no_tool_calls(self):
        """Test that branch_self works when there are no tool_calls on the current node."""
        # Create a mock bot
        bot = Mock(spec=Bot)
        bot.autosave = True

        # Create a mock conversation node with NO tool calls
        original_node = Mock(spec=ConversationNode)
        original_node.tool_calls = []  # No tool calls
        original_node.replies = []

        bot.conversation = original_node
        bot.tool_handler = Mock()
        bot.tool_handler.clear = Mock()
        bot.tool_handler.tools = []
        bot.respond = Mock(return_value="Branch response")

        # Patch _get_calling_bot
        with patch("bots.tools.self_tools._get_calling_bot", return_value=bot):
            with patch("copy.deepcopy") as mock_deepcopy:
                branch_bot = Mock(spec=Bot)
                branch_bot.autosave = False
                branch_bot.conversation = Mock(spec=ConversationNode)
                branch_bot.conversation.replies = []
                branch_bot.tool_handler = Mock()
                branch_bot.tool_handler.clear = Mock()
                branch_bot.respond = Mock(return_value="Branch response")
                mock_deepcopy.return_value = branch_bot

                result = branch_self(self_prompts="['test']", allow_work="False")

        # Verify that _add_reply was NOT called (no dummy node needed)
        assert not original_node._add_reply.called

        # Should still succeed
        assert "Successfully completed" in result
