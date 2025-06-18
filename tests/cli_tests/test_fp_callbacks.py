"""Tests for functional prompt callback functionality."""

from unittest.mock import Mock

from bots.flows.functional_prompts import chain
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

    def respond(self, prompt):
        if self.response_index < len(self.responses):
            response = self.responses[self.response_index]
            self.response_index += 1
        else:
            default_resp = "Default response"
            response = self.responses[-1] if self.responses else default_resp
        # Create a new conversation node
        p_node = ConversationNode("user", prompt, parent=self.conversation)
        self.conversation.replies.append(p_node)
        resp_node = ConversationNode("assistant", response, parent=p_node)
        p_node.replies.append(resp_node)
        self.conversation = resp_node
        return response

    def save(self, filename):
        pass

    def load(self, filename):
        pass


def test_chain_with_callback():
    """Test that chain function calls callback before returning."""
    callback_called = False
    callback_args = None

    def test_callback(responses, nodes):
        nonlocal callback_called, callback_args
        callback_called = True
        callback_args = (responses, nodes)

    bot = MockBot(["Response 1", "Response 2"])
    prompts = ["Prompt 1", "Prompt 2"]
    responses, nodes = chain(bot, prompts, callback=test_callback)
    assert callback_called, "Callback should have been called"
    assert callback_args is not None, "Callback should have received arguments"
    assert callback_args[0] == responses, "Callback should receive responses"
    assert callback_args[1] == nodes, "Callback should receive nodes"
    assert len(responses) == 2
    assert responses == ["Response 1", "Response 2"]


def test_callback_none_does_not_error():
    """Test that passing None as callback doesn't cause errors."""
    bot = MockBot(["Response"])
    # Should not raise any exceptions
    responses, nodes = chain(bot, ["Prompt"], callback=None)
    assert len(responses) == 1
    assert responses[0] == "Response"


def test_callback_not_provided_does_not_error():
    """Test that not providing callback parameter doesn't cause errors."""
    bot = MockBot(["Response"])
    # Should not raise any exceptions when callback is not provided
    responses, nodes = chain(bot, ["Prompt"])
    assert len(responses) == 1
    assert responses[0] == "Response"


def test_callback_with_exception_handling():
    """Test that exceptions in callbacks don't break the main function."""

    def failing_callback(responses, nodes):
        raise Exception("Callback failed!")

    bot = MockBot(["Response"])
    # Should not raise the callback exception
    responses, nodes = chain(bot, ["Prompt"], callback=failing_callback)
    assert len(responses) == 1
    assert responses[0] == "Response"
