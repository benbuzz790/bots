"""Tests for branch_self compatibility with parallel tool calling."""

from unittest.mock import Mock, patch

from bots.foundation.base import Bot, ConversationNode
from bots.tools.self_tools import branch_self


class TestBranchSelfParallelTools:
    """Test branch_self with parallel tool calls."""

    def test_branch_self_handles_parallel_tool_calls(self):
        """Test that branch_self creates dummy tool_results for all parallel tool calls."""
        bot = Mock(spec=Bot)
        bot.autosave = False

        # Create a mock conversation node with parallel tool calls
        original_node = Mock(spec=ConversationNode)
        original_node.content = None  # Add content attribute
        original_node.tool_calls = [
            {"id": "call_1", "name": "branch_self", "input": {"self_prompts": "['test']"}},
            {"id": "call_2", "name": "other_tool", "input": {"param": "value"}},
            {"id": "call_3", "name": "another_tool", "input": {"x": "y"}},
        ]
        original_node.replies = []

        # Mock the dummy node that will be created
        dummy_node = Mock(spec=ConversationNode)
        dummy_node.replies = []

        # Setup _add_reply to add dummy_node to replies and return it
        def add_reply_side_effect(*args, **kwargs):
            """Adds a dummy node to the original node's replies list and returns it.

            This function serves as a side effect handler that appends a dummy_node
            to the replies collection of the original_node.

            Returns:
                The dummy_node that was added to the replies list.
            """
            """Adds a dummy node to the original node's replies list and returns it.

            This function serves as a side effect handler that appends a dummy_node
            to the replies of an original_node.

            Returns:
                The dummy_node that was appended to the replies list.
            """
            """Adds a dummy node to the original node's replies list and returns it.

            This function serves as a side effect handler that appends a dummy_node
            to the replies collection of the original_node.

            Returns:
                The dummy_node that was added to the replies list.
            """
            """Adds a dummy node to the original node's replies list and returns it.

            This function serves as a side effect handler that appends a dummy_node
            to the replies collection of an original_node.

            Returns:
                The dummy_node that was added to the replies list.
            """
            """Adds a dummy node to the original node's replies list and returns it.

            This function serves as a side effect handler that appends a dummy_node
            to the replies collection of an original_node.

            Returns:
                The dummy_node that was added to the replies list.
            """
            original_node.replies.append(dummy_node)
            return dummy_node

        original_node._add_reply = Mock(side_effect=add_reply_side_effect)

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

                # Call branch_self (without _bot parameter since we're patching _get_calling_bot)
                branch_self(self_prompts="['test 1', 'test 2']", allow_work="False")

        # Verify that _add_reply was called with tool_results for ALL tool calls
        assert original_node._add_reply.called
        call_args = original_node._add_reply.call_args

        # Check that tool_results were provided
        assert "tool_results" in call_args.kwargs
        tool_results = call_args.kwargs["tool_results"]

        # Should have 3 tool results (one for each parallel tool call)
        assert len(tool_results) == 3

        # Verify each tool call has a corresponding result
        tool_ids = {result["tool_use_id"] for result in tool_results}
        assert "call_1" in tool_ids
        assert "call_2" in tool_ids
        assert "call_3" in tool_ids

        # Verify the branch_self result has "in progress" message
        branch_self_result = next(r for r in tool_results if r["tool_use_id"] == "call_1")
        assert "Branching in progress" in branch_self_result["content"]

        # Verify other tools have placeholder results
        other_result = next(r for r in tool_results if r["tool_use_id"] == "call_2")
        assert "[Parallel tool execution - result pending]" in other_result["content"]

    def test_branch_self_without_parallel_tools(self):
        """Test that branch_self works correctly when it's the only tool called."""
        bot = Mock(spec=Bot)
        bot.autosave = False

        # Create a mock conversation node with only branch_self
        original_node = Mock(spec=ConversationNode)
        original_node.content = None  # Add content attribute
        original_node.tool_calls = [
            {"id": "call_1", "name": "branch_self", "input": {"self_prompts": "['test']"}},
        ]
        original_node.replies = []

        # Mock the dummy node that will be created
        dummy_node = Mock(spec=ConversationNode)
        dummy_node.replies = []

        # Setup _add_reply to add dummy_node to replies and return it
        def add_reply_side_effect(*args, **kwargs):
            original_node.replies.append(dummy_node)
            return dummy_node

        original_node._add_reply = Mock(side_effect=add_reply_side_effect)

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

                # Call branch_self (without _bot parameter since we're patching _get_calling_bot)
                branch_self(self_prompts="['test 1', 'test 2']", allow_work="False")

        # Verify that _add_reply was called
        assert original_node._add_reply.called
        call_args = original_node._add_reply.call_args

        # Check that tool_results were provided
        assert "tool_results" in call_args.kwargs
        tool_results = call_args.kwargs["tool_results"]

        # Should have 1 tool result (only branch_self)
        assert len(tool_results) == 1

        # Verify the branch_self result has "in progress" message
        assert tool_results[0]["tool_use_id"] == "call_1"
        assert "Branching in progress" in tool_results[0]["content"]

    def test_branch_self_no_tool_calls(self):
        """Test that branch_self works when there are no tool_calls on the node."""
        bot = Mock(spec=Bot)
        bot.autosave = False

        # Create a mock conversation node with no tool_calls
        original_node = Mock(spec=ConversationNode)
        original_node.content = None  # Add content attribute
        original_node.tool_calls = None  # No tool calls
        original_node.replies = []

        # Mock the dummy node that will be created
        dummy_node = Mock(spec=ConversationNode)
        dummy_node.replies = []
        original_node._add_reply = Mock(return_value=dummy_node)

        bot.conversation = original_node

        # Mock tool handler
        bot.tool_handler = Mock()
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

                # Call branch_self (without _bot parameter since we're patching _get_calling_bot)
                result = branch_self(self_prompts="['test 1', 'test 2']", allow_work="False")

        # Should succeed even without tool_calls
        assert "Successfully completed" in result
