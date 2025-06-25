"""Tests for CLI callback functionality and *_while functions."""

from unittest.mock import Mock, patch

from bots.flows.functional_prompts import (
    branch_while,
    chain_while,
    par_branch_while,
)
from bots.foundation.base import ConversationNode


class MockBot:
    """Mock bot for testing purposes."""

    def __init__(self, responses=None):
        self.responses = responses or ["Mock response"]
        self.response_index = 0
        self.conversation = ConversationNode("system", "System message")
        self.autosave = False
        self.tool_handler = Mock()
        self.tool_handler.requests = []
        self.tool_handler.results = []
        self.name = "MockBot"

    def respond(self, prompt):
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
        else:
            default_response = "Default response"
            response = self.responses[-1] if self.responses else default_response
        # Create a new conversation node
        prompt_node = ConversationNode("user", prompt, parent=self.conversation)
        self.conversation.replies.append(prompt_node)
        response_node = ConversationNode("assistant", response, parent=prompt_node)
        prompt_node.replies.append(response_node)
        self.conversation = response_node
        return response

    def save(self, filename):
        pass

    @staticmethod
    def load(filename):
        return MockBot()


def test_chain_while_with_prompt_array():
    """Test that chain_while properly handles an array of prompts."""

    def stop_immediately(bot):
        return True  # Stop after first response for each prompt

    bot = MockBot(["Response 1", "Response 2", "Response 3"])
    prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
    responses, nodes = chain_while(bot, prompts, stop_condition=stop_immediately)
    # Should have one response per prompt
    assert len(responses) == 3
    assert responses == ["Response 1", "Response 2", "Response 3"]
    assert len(nodes) == 3


def test_branch_while_with_prompt_array():
    """Test that branch_while properly handles an array of prompts."""

    def stop_immediately(bot):
        return True  # Stop after first response for each prompt

    bot = MockBot(["Branch 1", "Branch 2"])
    prompts = ["Branch prompt 1", "Branch prompt 2"]
    responses, nodes = branch_while(bot, prompts, stop_condition=stop_immediately)
    # Should have responses for each branch
    assert len(responses) == 2
    assert len(nodes) == 2
    assert all(r is not None for r in responses)


def test_par_branch_while_with_prompt_array():
    """Test that par_branch_while properly handles an array of prompts."""

    def stop_immediately(bot):
        return True  # Stop after first response for each prompt

    # Mock the file operations for parallel processing
    with (
        patch("os.remove"),
        patch.object(MockBot, "save"),
        patch.object(MockBot, "load", return_value=MockBot(["Par response"])),
    ):
        bot = MockBot(["Par 1", "Par 2", "Par 3"])
        prompts = ["Par prompt 1", "Par prompt 2", "Par prompt 3"]
        responses, nodes = par_branch_while(bot, prompts, stop_condition=stop_immediately)
        # Should have responses for each parallel branch
        assert len(responses) == 3
        assert len(nodes) == 3


def test_chain_while_with_callback():
    """Test that chain_while calls callback with prompt array results."""
    callback_called = False
    callback_responses = None

    def test_callback(responses, nodes):
        nonlocal callback_called, callback_responses
        callback_called = True
        callback_responses = responses

    def stop_immediately(bot):
        return True

    bot = MockBot(["R1", "R2"])
    prompts = ["P1", "P2"]
    responses, nodes = chain_while(
        bot,
        prompts,
        stop_condition=stop_immediately,
        callback=test_callback,
    )
    assert callback_called, "Callback should have been called"
    assert callback_responses == responses, "Should receive all responses"
    assert len(callback_responses) == 2


def test_while_functions_with_empty_prompt_array():
    """Test that *_while functions handle empty prompt arrays gracefully."""

    def stop_immediately(bot):
        return True

    bot = MockBot(["Response"])
    # Test chain_while with empty array
    responses, nodes = chain_while(bot, [], stop_condition=stop_immediately)
    assert len(responses) == 0
    assert len(nodes) == 0
    # Test branch_while with empty array
    responses, nodes = branch_while(bot, [], stop_condition=stop_immediately)
    assert len(responses) == 0
    assert len(nodes) == 0


def test_while_functions_with_single_prompt():
    """Test *_while functions work with single prompt (compatibility)."""

    def stop_immediately(bot):
        return True

    bot = MockBot(["Single response"])
    # Test with single prompt in array
    responses, nodes = chain_while(bot, ["Single prompt"], stop_condition=stop_immediately)
    assert len(responses) == 1
    assert responses[0] == "Single response"
