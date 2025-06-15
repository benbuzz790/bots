import pytest
from unittest.mock import Mock, MagicMock
from bots.flows.functional_prompts import conditions
from bots.foundation.base import Bot, ConversationNode
"""
Test suite for functional prompt conditions.

This module tests all condition functions in bots.flows.functional_prompts.conditions
to ensure they behave correctly and provide reliable stop conditions for iterative
bot interactions.
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
        assert conditions.tool_used(bot) == True

    def test_tool_used_without_tools(self):
        """Test tool_used returns False when bot has not used tools."""
        bot = MockBot()
        bot.set_tool_requests([])
        assert conditions.tool_used(bot) == False

    def test_tool_not_used_with_tools(self):
        """Test tool_not_used returns False when bot has used tools."""
        bot = MockBot()
        bot.set_tool_requests([{"tool": "test_tool"}])
        assert conditions.tool_not_used(bot) == False

    def test_tool_not_used_without_tools(self):
        """Test tool_not_used returns True when bot has not used tools."""
        bot = MockBot()
        bot.set_tool_requests([])
        assert conditions.tool_not_used(bot) == True

class TestCompletionConditions:
    """Test completion-related condition functions."""

    def test_said_DONE_positive(self):
        """Test said_DONE returns True when response contains 'DONE'."""
        bot = MockBot(content="Task is DONE")
        assert conditions.said_DONE(bot) == True

    def test_said_DONE_negative(self):
        """Test said_DONE returns False when response doesn't contain 'DONE'."""
        bot = MockBot(content="Task is in progress")
        assert conditions.said_DONE(bot) == False

    def test_said_COMPLETE_positive(self):
        """Test said_COMPLETE returns True when response contains 'COMPLETE'."""
        bot = MockBot(content="Analysis is COMPLETE")
        assert conditions.said_COMPLETE(bot) == True

    def test_said_COMPLETE_negative(self):
        """Test said_COMPLETE returns False when response doesn't contain 'COMPLETE'."""
        bot = MockBot(content="Analysis is ongoing")
        assert conditions.said_COMPLETE(bot) == False

    def test_said_FINISHED_positive(self):
        """Test said_FINISHED returns True when response contains 'FINISHED'."""
        bot = MockBot(content="Work is FINISHED")
        assert conditions.said_FINISHED(bot) == True

    def test_said_FINISHED_negative(self):
        """Test said_FINISHED returns False when response doesn't contain 'FINISHED'."""
        bot = MockBot(content="Work continues")
        assert conditions.said_FINISHED(bot) == False

    def test_said_SUCCESS_positive(self):
        """Test said_SUCCESS returns True when response contains 'SUCCESS'."""
        bot = MockBot(content="Operation was a SUCCESS")
        assert conditions.said_SUCCESS(bot) == True

    def test_said_SUCCESS_negative(self):
        """Test said_SUCCESS returns False when response doesn't contain 'SUCCESS'."""
        bot = MockBot(content="Operation failed")
        assert conditions.said_SUCCESS(bot) == False

    def test_said_READY_positive(self):
        """Test said_READY returns True when response contains 'READY'."""
        bot = MockBot(content="System is READY")
        assert conditions.said_READY(bot) == True

    def test_said_READY_negative(self):
        """Test said_READY returns False when response doesn't contain 'READY'."""
        bot = MockBot(content="System is initializing")
        assert conditions.said_READY(bot) == False

class TestLengthConditions:
    """Test response length-based condition functions."""

    def test_response_length_exceeds_default(self):
        """Test response_length_exceeds with default threshold."""
        condition = conditions.response_length_exceeds()
        # Test with long content (> 500 chars)
        long_content = "x" * 600
        bot = MockBot(content=long_content)
        assert condition(bot) == True
        # Test with short content (< 500 chars)
        short_content = "x" * 400
        bot = MockBot(content=short_content)
        assert condition(bot) == False

    def test_response_length_exceeds_custom(self):
        """Test response_length_exceeds with custom threshold."""
        condition = conditions.response_length_exceeds(100)
        # Test with content exceeding custom threshold
        long_content = "x" * 150
        bot = MockBot(content=long_content)
        assert condition(bot) == True
        # Test with content below custom threshold
        short_content = "x" * 50
        bot = MockBot(content=short_content)
        assert condition(bot) == False

    def test_response_length_below_default(self):
        """Test response_length_below with default threshold."""
        condition = conditions.response_length_below()
        # Test with very short content (< 50 chars)
        short_content = "x" * 30
        bot = MockBot(content=short_content)
        assert condition(bot) == True
        # Test with longer content (> 50 chars)
        long_content = "x" * 100
        bot = MockBot(content=long_content)
        assert condition(bot) == False

    def test_response_length_below_custom(self):
        """Test response_length_below with custom threshold."""
        condition = conditions.response_length_below(20)
        # Test with content below custom threshold
        short_content = "x" * 10
        bot = MockBot(content=short_content)
        assert condition(bot) == True
        # Test with content above custom threshold
        long_content = "x" * 30
        bot = MockBot(content=long_content)
        assert condition(bot) == False

class TestPhraseConditions:
    """Test phrase-based condition functions."""

    def test_contains_phrase_case_insensitive(self):
        """Test contains_phrase with case-insensitive matching."""
        condition = conditions.contains_phrase("hello world")
        # Test exact match
        bot = MockBot(content="Say hello world to everyone")
        assert condition(bot) == True
        # Test case insensitive match
        bot = MockBot(content="Say HELLO WORLD to everyone")
        assert condition(bot) == True
        # Test no match
        bot = MockBot(content="Say goodbye to everyone")
        assert condition(bot) == False

    def test_contains_phrase_case_sensitive(self):
        """Test contains_phrase with case-sensitive matching."""
        condition = conditions.contains_phrase("Hello World", case_sensitive=True)
        # Test exact match
        bot = MockBot(content="Say Hello World to everyone")
        assert condition(bot) == True
        # Test case mismatch
        bot = MockBot(content="Say hello world to everyone")
        assert condition(bot) == False
        # Test no match
        bot = MockBot(content="Say goodbye to everyone")
        assert condition(bot) == False

class TestIterationConditions:
    """Test iteration-based condition functions."""

    def test_max_iterations(self):
        """Test max_iterations condition."""
        condition = conditions.max_iterations(3)
        bot = MockBot()
        # First three calls should return False
        assert condition(bot) == False  # iteration 1
        assert condition(bot) == False  # iteration 2
        assert condition(bot) == True   # iteration 3 (reaches max)
        # Subsequent calls should continue returning True
        assert condition(bot) == True   # iteration 4

    def test_max_iterations_different_instances(self):
        """Test that different max_iterations instances have separate counters."""
        condition1 = conditions.max_iterations(2)
        condition2 = conditions.max_iterations(2)
        bot = MockBot()
        # Each condition should have its own counter
        assert condition1(bot) == False  # condition1: iteration 1
        assert condition2(bot) == False  # condition2: iteration 1
        assert condition1(bot) == True   # condition1: iteration 2 (reaches max)
        assert condition2(bot) == True   # condition2: iteration 2 (reaches max)

class TestAdvancedConditions:
    """Test advanced condition functions."""

    def test_no_new_tools_used_first_iteration(self):
        """Test no_new_tools_used on first iteration."""
        bot = MockBot()
        bot.add_tool_request("file_tool", {"action": "read"})
        # First iteration should always return False
        assert conditions.no_new_tools_used(bot) == False

    def test_no_new_tools_used_with_new_tools(self):
        """Test no_new_tools_used when new tools are used."""
        bot = MockBot()
        bot.tool_handler.tool_name_and_input = Mock()
        # First iteration
        bot.set_tool_requests([{"tool": "file_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("file_tool", {})
        assert conditions.no_new_tools_used(bot) == False
        # Second iteration with new tool
        bot.set_tool_requests([{"tool": "web_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("web_tool", {})
        assert conditions.no_new_tools_used(bot) == False

    def test_no_new_tools_used_with_same_tools(self):
        """Test no_new_tools_used when same tools are used."""
        bot = MockBot()
        bot.tool_handler.tool_name_and_input = Mock()
        # First iteration
        bot.set_tool_requests([{"tool": "file_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("file_tool", {})
        assert conditions.no_new_tools_used(bot) == False
        # Second iteration with same tool
        bot.set_tool_requests([{"tool": "file_tool"}])
        bot.tool_handler.tool_name_and_input.return_value = ("file_tool", {})
        assert conditions.no_new_tools_used(bot) == True

    def test_error_in_response_positive(self):
        """Test error_in_response returns True when response contains error indicators."""
        test_cases = ["An error occurred during processing", "The operation failed", "Exception: Invalid input", "Traceback (most recent call last):", "SyntaxError: invalid syntax"]
        for content in test_cases:
            bot = MockBot(content=content)
            assert conditions.error_in_response(bot) == True, f"Failed for content: {content}"

    def test_error_in_response_negative(self):
        """Test error_in_response returns False when response doesn't contain error indicators."""
        bot = MockBot(content="Operation completed successfully")
        assert conditions.error_in_response(bot) == False

    def test_error_in_response_case_insensitive(self):
        """Test error_in_response is case insensitive."""
        bot = MockBot(content="AN ERROR OCCURRED")
        assert conditions.error_in_response(bot) == True

class TestConditionIntegration:
    """Test conditions in realistic scenarios."""

    def test_multiple_conditions_workflow(self):
        """Test using multiple conditions in a typical workflow."""
        bot = MockBot()
        # Simulate a workflow where bot starts with tools, then finishes
        bot.set_content("Starting analysis...")
        bot.set_tool_requests([{"tool": "analyzer"}])
        # Should continue (tools used, not done)
        assert conditions.tool_not_used(bot) == False
        assert conditions.said_DONE(bot) == False
        # Bot finishes and says DONE
        bot.set_content("Analysis complete. DONE.")
        bot.set_tool_requests([])
        # Should stop (no tools, said DONE)
        assert conditions.tool_not_used(bot) == True
        assert conditions.said_DONE(bot) == True

    def test_condition_factory_functions(self):
        """Test that condition factory functions return proper callables."""
        # Test factory functions return callables
        length_condition = conditions.response_length_exceeds(100)
        assert callable(length_condition)
        phrase_condition = conditions.contains_phrase("test")
        assert callable(phrase_condition)
        max_iter_condition = conditions.max_iterations(5)
        assert callable(max_iter_condition)
        # Test they work as expected
        bot = MockBot(content="x" * 150)
        assert length_condition(bot) == True
        bot = MockBot(content="this is a test message")
        assert phrase_condition(bot) == True
if __name__ == "__main__":
    # Run tests if executed directly
    pytest.main([__file__, "-v"])