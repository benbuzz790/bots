from unittest.mock import Mock

import pytest

from bots.flows.functional_prompts import conditions

"""
Test suite for functional prompt conditions.
This module tests all condition functions in
bots.flows.functional_prompts.conditions to ensure they behave correctly
and provide reliable stop conditions for iterative bot interactions.
"""


class MockBot:
    """Mock bot for testing conditions without requiring actual bot instances."""

    def __init__(self, content="", tool_requests=None, name="TestBot"):
        self.name = name
        self.conversation = Mock()
        self.conversation.content = content
        self.tool_handler = Mock()
        self.tool_handler.requests = tool_requests or []
        self.tool_handler.results = []

    def set_content(self, content):
        """Update the bot's conversation content."""
        self.conversation.content = content

    def set_tool_requests(self, requests):
        """Update the bot's tool requests."""
        self.tool_handler.requests = requests

    def add_tool_request(self, tool_name, tool_input):
        """Add a tool request to the bot."""
        request = {"tool_name": tool_name, "input": tool_input}
        self.tool_handler.requests.append(request)
        # Mock the tool_name_and_input method
        self.tool_handler.tool_name_and_input = Mock(return_value=(tool_name, tool_input))


class TestBasicConditions:
    """Test basic condition functions."""

    def test_tool_used_with_tools(self):
        """Test tool_used returns True when bot has used tools."""
        bot = MockBot()
        bot.set_tool_requests([{"tool": "test_tool"}])
        assert conditions.tool_used(bot) is True

    def test_tool_used_without_tools(self):
        """Test tool_used returns False when bot has not used tools."""
        bot = MockBot()
        bot.set_tool_requests([])
        assert conditions.tool_used(bot) is False

    def test_tool_not_used_with_tools(self):
        """Test tool_not_used returns False when bot has used tools."""
        bot = MockBot()
        bot.set_tool_requests([{"tool": "test_tool"}])
        assert conditions.tool_not_used(bot) is False

    def test_tool_not_used_without_tools(self):
        """Test tool_not_used returns True when bot has not used tools."""
        bot = MockBot()
        bot.set_tool_requests([])
        assert conditions.tool_not_used(bot) is True


class TestCompletionConditions:
    """Test completion-related condition functions."""

    def test_said_DONE_positive(self):
        """Test said_DONE returns True when response contains 'DONE'."""
        bot = MockBot(content="Task is DONE")
        assert conditions.said_DONE(bot) is True

    def test_said_DONE_negative(self):
        """Test said_DONE returns False when response doesn't contain 'DONE'."""
        bot = MockBot(content="Task is in progress")
        assert conditions.said_DONE(bot) is False

    def test_said_READY_positive(self):
        """Test said_READY returns True when response contains 'READY'."""
        bot = MockBot(content="System is READY")
        assert conditions.said_READY(bot) is True

    def test_said_READY_negative(self):
        """Test said_READY returns False when response doesn't contain 'READY'."""
        bot = MockBot(content="System is initializing")
        assert conditions.said_READY(bot) is False


class TestAdvancedConditions:
    """Test advanced condition functions."""

    def test_no_new_tools_used_first_iteration(self):
        """Test no_new_tools_used on first iteration."""
        bot = MockBot()
        bot.add_tool_request("file_tool", {"action": "read"})
        # First iteration should always return False
        assert conditions.no_new_tools_used(bot) is False

    def test_no_new_tools_used_with_new_tools(self):
        """Test no_new_tools_used when new tools are used."""
        bot = MockBot()
        bot.tool_handler.tool_name_and_input = Mock()
        # First iteration
        bot.set_tool_requests([{"tool": "file_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("file_tool", {})
        assert conditions.no_new_tools_used(bot) is False
        # Second iteration with new tool
        bot.set_tool_requests([{"tool": "web_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("web_tool", {})
        assert conditions.no_new_tools_used(bot) is False

    def test_no_new_tools_used_with_same_tools(self):
        """Test no_new_tools_used when same tools are used."""
        bot = MockBot()
        bot.tool_handler.tool_name_and_input = Mock()
        # First iteration
        bot.set_tool_requests([{"tool": "file_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("file_tool", {})
        assert conditions.no_new_tools_used(bot) is False
        # Second iteration with same tool
        bot.set_tool_requests([{"tool": "file_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("file_tool", {})
        assert conditions.no_new_tools_used(bot) is True

    def test_error_in_response_positive(self):
        """Test error_in_response returns True when response contains error indicators."""
        test_cases = [
            "An error occurred during processing",
            "The operation failed",
            "Exception: Invalid input",
            "Traceback (most recent call last):",
            "SyntaxError: invalid syntax",
        ]
        for content in test_cases:
            bot = MockBot(content=content)
            assert conditions.error_in_response(bot) is True, f"Failed for content: {content}"

    def test_error_in_response_negative(self):
        """Test error_in_response returns False when response doesn't contain error indicators."""
        bot = MockBot(content="Operation completed successfully")
        assert conditions.error_in_response(bot) is False

    def test_error_in_response_case_insensitive(self):
        """Test error_in_response is case insensitive."""
        bot = MockBot(content="AN ERROR OCCURRED")
        assert conditions.error_in_response(bot) is True


class TestConditionIntegration:
    """Test conditions in realistic scenarios."""

    def test_multiple_conditions_workflow(self):
        """Test using multiple conditions in a typical workflow."""
        bot = MockBot()
        # Simulate a workflow where bot starts with tools, then finishes
        bot.set_content("Starting analysis...")
        bot.set_tool_requests([{"tool": "analyzer"}])
        # Should continue (tools used, not done)
        assert conditions.tool_not_used(bot) is False
        assert conditions.said_DONE(bot) is False
        # Bot finishes and says DONE
        bot.set_content("Analysis complete. DONE.")
        bot.set_tool_requests([])
        # Should stop (no tools, said DONE)
        assert conditions.tool_not_used(bot) is True
        assert conditions.said_DONE(bot) is True


if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])
