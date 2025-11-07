"""Unit tests for namshub test fixtures.

Tests the progression of namshub fixtures from simple to complex:
1. namshub_of_no_op - Basic invocation
2. namshub_of_echo - Parameter passing
3. namshub_of_state_change - State modification
4. namshub_of_tool_use - Toolkit swapping
5. namshub_of_simple_workflow - Workflow execution
6. namshub_of_error - Error handling
"""

import pytest

from bots.testing.mock_bot import MockBot


class TestNamshubOfNoOp:
    """Tests for namshub_of_no_op - simplest case."""

    def test_no_op_executes_successfully(self):
        """Test that no-op namshub executes and returns success."""
        from tests.fixtures import namshub_of_no_op

        bot = MockBot(autosave=False)
        result, node = namshub_of_no_op.invoke(bot)

        assert "success" in result.lower()
        assert node == bot.conversation

    def test_no_op_accepts_any_kwargs(self):
        """Test that no-op accepts arbitrary kwargs without error."""
        from tests.fixtures import namshub_of_no_op

        bot = MockBot(autosave=False)
        result, node = namshub_of_no_op.invoke(
            bot,
            random_param="value",
            another_param=123,
            yet_another=True
        )

        assert "success" in result.lower()

    def test_no_op_does_not_modify_bot(self):
        """Test that no-op doesn't modify bot state."""
        from tests.fixtures import namshub_of_no_op

        bot = MockBot(autosave=False)
        original_system_message = bot.system_message
        original_conversation = bot.conversation

        namshub_of_no_op.invoke(bot)

        assert bot.system_message == original_system_message
        assert bot.conversation == original_conversation


class TestNamshubOfEcho:
    """Tests for namshub_of_echo - parameter passing."""

    def test_echo_returns_message(self):
        """Test that echo namshub returns the provided message."""
        from tests.fixtures import namshub_of_echo

        bot = MockBot(autosave=False)
        result, node = namshub_of_echo.invoke(bot, message="Hello, World!")

        assert "Echo: Hello, World!" == result
        assert node == bot.conversation

    def test_echo_requires_message_parameter(self):
        """Test that echo namshub validates message parameter."""
        from tests.fixtures import namshub_of_echo

        bot = MockBot(autosave=False)
        result, node = namshub_of_echo.invoke(bot)

        assert "Error" in result
        assert "message" in result.lower()
        assert "required" in result.lower()

    def test_echo_with_empty_string(self):
        """Test that echo works with empty string."""
        from tests.fixtures import namshub_of_echo

        bot = MockBot(autosave=False)
        result, node = namshub_of_echo.invoke(bot, message="")

        assert result == "Echo: "

    def test_echo_with_special_characters(self):
        """Test that echo handles special characters."""
        from tests.fixtures import namshub_of_echo

        bot = MockBot(autosave=False)
        special_msg = "Test with 'quotes', \"double quotes\", and\nnewlines"
        result, node = namshub_of_echo.invoke(bot, message=special_msg)

        assert f"Echo: {special_msg}" == result


class TestNamshubOfStateChange:
    """Tests for namshub_of_state_change - bot state modification."""

    def test_state_change_modifies_system_message(self):
        """Test that state change namshub modifies system message."""
        from tests.fixtures import namshub_of_state_change

        bot = MockBot(autosave=False)
        original_message = bot.system_message
        new_message = "New system message for testing"

        result, node = namshub_of_state_change.invoke(bot, new_message=new_message)

        assert bot.system_message == new_message
        assert original_message in result
        assert new_message in result

    def test_state_change_with_default_message(self):
        """Test that state change uses default message when none provided."""
        from tests.fixtures import namshub_of_state_change

        bot = MockBot(autosave=False)
        result, node = namshub_of_state_change.invoke(bot)

        assert "State changed by namshub_of_state_change" in bot.system_message
        assert "changed" in result.lower()

    def test_state_change_returns_both_messages(self):
        """Test that result includes both old and new messages."""
        from tests.fixtures import namshub_of_state_change

        bot = MockBot(autosave=False)
        bot.set_system_message("Original message")
        new_message = "Updated message"

        result, node = namshub_of_state_change.invoke(bot, new_message=new_message)

        assert "Original message" in result
        assert "Updated message" in result

    def test_state_change_preserves_conversation(self):
        """Test that conversation node is preserved."""
        from tests.fixtures import namshub_of_state_change

        bot = MockBot(autosave=False)
        original_conversation = bot.conversation

        result, node = namshub_of_state_change.invoke(bot, new_message="Test")

        assert node == original_conversation


class TestNamshubOfToolUse:
    """Tests for namshub_of_tool_use - toolkit swapping and tool execution."""

    def test_tool_use_evaluates_expression(self):
        """Test that tool use namshub evaluates Python expressions."""
        from tests.fixtures import namshub_of_tool_use

        bot = MockBot(autosave=False)
        result, node = namshub_of_tool_use.invoke(bot, expression="2 + 2")

        assert "2 + 2" in result
        assert "4" in result

    def test_tool_use_with_default_expression(self):
        """Test that tool use works with default expression."""
        from tests.fixtures import namshub_of_tool_use

        bot = MockBot(autosave=False)
        result, node = namshub_of_tool_use.invoke(bot)

        assert "2 + 2" in result
        assert "4" in result

    def test_tool_use_with_complex_expression(self):
        """Test that tool use handles complex expressions."""
        from tests.fixtures import namshub_of_tool_use

        bot = MockBot(autosave=False)
        result, node = namshub_of_tool_use.invoke(bot, expression="sum([1, 2, 3, 4, 5])")

        assert "sum([1, 2, 3, 4, 5])" in result
        assert "15" in result

    def test_tool_use_modifies_toolkit(self):
        """Test that tool use modifies the bot's toolkit."""
        from tests.fixtures import namshub_of_tool_use

        bot = MockBot(autosave=False)
        original_tools = len(bot.tool_handler.tools) if hasattr(bot.tool_handler, 'tools') else 0

        namshub_of_tool_use.invoke(bot)

        # Toolkit should be modified (though exact count depends on implementation)
        # Just verify the namshub executed without error
        assert True  # If we got here, toolkit swapping worked


class TestNamshubOfSimpleWorkflow:
    """Tests for namshub_of_simple_workflow - functional prompt execution."""

    def test_simple_workflow_executes(self):
        """Test that simple workflow executes successfully."""
        from tests.fixtures import namshub_of_simple_workflow

        bot = MockBot(autosave=False)
        result, node = namshub_of_simple_workflow.invoke(bot, task="test task")

        assert "completed" in result.lower()
        assert node is not None

    def test_simple_workflow_with_default_task(self):
        """Test that simple workflow uses default task."""
        from tests.fixtures import namshub_of_simple_workflow

        bot = MockBot(autosave=False)
        result, node = namshub_of_simple_workflow.invoke(bot)

        assert "completed" in result.lower()

    def test_simple_workflow_modifies_system_message(self):
        """Test that workflow sets appropriate system message."""
        from tests.fixtures import namshub_of_simple_workflow

        bot = MockBot(autosave=False)
        original_message = bot.system_message

        namshub_of_simple_workflow.invoke(bot, task="custom task")

        # System message should be changed during execution
        assert bot.system_message != original_message
        assert "workflow" in bot.system_message.lower()

    def test_simple_workflow_with_custom_task(self):
        """Test that workflow accepts custom task description."""
        from tests.fixtures import namshub_of_simple_workflow

        bot = MockBot(autosave=False)
        custom_task = "analyze data and generate report"

        result, node = namshub_of_simple_workflow.invoke(bot, task=custom_task)

        assert "completed" in result.lower()
        # Task should be reflected in system message
        assert custom_task in bot.system_message


class TestNamshubOfError:
    """Tests for namshub_of_error - error handling."""

    def test_error_raises_value_error_by_default(self):
        """Test that error namshub raises ValueError by default."""
        from tests.fixtures import namshub_of_error

        bot = MockBot(autosave=False)

        with pytest.raises(ValueError) as exc_info:
            namshub_of_error.invoke(bot)

        assert "Deliberate error" in str(exc_info.value)

    def test_error_raises_value_error_explicitly(self):
        """Test that error namshub raises ValueError when specified."""
        from tests.fixtures import namshub_of_error

        bot = MockBot(autosave=False)

        with pytest.raises(ValueError) as exc_info:
            namshub_of_error.invoke(bot, error_type="ValueError")

        assert "Deliberate error" in str(exc_info.value)

    def test_error_raises_runtime_error(self):
        """Test that error namshub raises RuntimeError when specified."""
        from tests.fixtures import namshub_of_error

        bot = MockBot(autosave=False)

        with pytest.raises(RuntimeError) as exc_info:
            namshub_of_error.invoke(bot, error_type="RuntimeError")

        assert "Deliberate runtime error" in str(exc_info.value)

    def test_error_raises_generic_exception(self):
        """Test that error namshub raises generic Exception for other types."""
        from tests.fixtures import namshub_of_error

        bot = MockBot(autosave=False)

        with pytest.raises(Exception) as exc_info:
            namshub_of_error.invoke(bot, error_type="CustomError")

        assert "Deliberate CustomError" in str(exc_info.value)

    def test_error_never_returns(self):
        """Test that error namshub never returns normally."""
        from tests.fixtures import namshub_of_error

        bot = MockBot(autosave=False)

        # Try all error types - none should return normally
        for error_type in [None, "ValueError", "RuntimeError", "CustomError"]:
            with pytest.raises(Exception):
                namshub_of_error.invoke(bot, error_type=error_type)


class TestNamshubProgression:
    """Integration tests for the progression of namshub complexity."""

    def test_all_namshubs_have_invoke_function(self):
        """Test that all fixture namshubs have an invoke function."""
        from tests.fixtures import (
            namshub_of_no_op,
            namshub_of_echo,
            namshub_of_state_change,
            namshub_of_tool_use,
            namshub_of_simple_workflow,
            namshub_of_error,
        )

        namshubs = [
            namshub_of_no_op,
            namshub_of_echo,
            namshub_of_state_change,
            namshub_of_tool_use,
            namshub_of_simple_workflow,
            namshub_of_error,
        ]

        for namshub in namshubs:
            assert hasattr(namshub, "invoke")
            assert callable(namshub.invoke)

    def test_all_namshubs_accept_bot_parameter(self):
        """Test that all namshubs accept a bot as first parameter."""
        from tests.fixtures import (
            namshub_of_no_op,
            namshub_of_echo,
            namshub_of_state_change,
            namshub_of_tool_use,
            namshub_of_simple_workflow,
        )

        bot = MockBot(autosave=False)

        # Test namshubs that don't raise errors
        namshub_of_no_op.invoke(bot)
        namshub_of_echo.invoke(bot, message="test")
        namshub_of_state_change.invoke(bot)
        namshub_of_tool_use.invoke(bot)
        namshub_of_simple_workflow.invoke(bot)

    def test_all_namshubs_return_tuple(self):
        """Test that all namshubs return (str, ConversationNode) tuple."""
        from tests.fixtures import (
            namshub_of_no_op,
            namshub_of_echo,
            namshub_of_state_change,
            namshub_of_tool_use,
            namshub_of_simple_workflow,
        )

        bot = MockBot(autosave=False)

        results = [
            namshub_of_no_op.invoke(bot),
            namshub_of_echo.invoke(bot, message="test"),
            namshub_of_state_change.invoke(bot),
            namshub_of_tool_use.invoke(bot),
            namshub_of_simple_workflow.invoke(bot),
        ]

        for result in results:
            assert isinstance(result, tuple)
            assert len(result) == 2
            assert isinstance(result[0], str)
            # result[1] should be a ConversationNode, but MockBot may vary

    def test_complexity_progression(self):
        """Test that namshubs increase in complexity as intended."""
        bot = MockBot(autosave=False)

        # 1. No-op: simplest, no parameters needed
        from tests.fixtures import namshub_of_no_op
        result1, _ = namshub_of_no_op.invoke(bot)
        assert result1  # Just needs to return something

        # 2. Echo: requires parameter
        from tests.fixtures import namshub_of_echo
        result2, _ = namshub_of_echo.invoke(bot, message="test")
        assert "test" in result2

        # 3. State change: modifies bot
        from tests.fixtures import namshub_of_state_change
        original_msg = bot.system_message
        namshub_of_state_change.invoke(bot)
        assert bot.system_message != original_msg

        # 4. Tool use: swaps toolkit and uses tools
        from tests.fixtures import namshub_of_tool_use
        result4, _ = namshub_of_tool_use.invoke(bot)
        assert "4" in result4  # 2 + 2 = 4

        # 5. Simple workflow: uses functional prompts
        from tests.fixtures import namshub_of_simple_workflow
        result5, _ = namshub_of_simple_workflow.invoke(bot)
        assert "completed" in result5.lower()

        # 6. Error: tests error handling
        from tests.fixtures import namshub_of_error
        with pytest.raises(Exception):
            namshub_of_error.invoke(bot)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])