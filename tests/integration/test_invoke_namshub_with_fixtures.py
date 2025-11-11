"""Integration tests for invoke_namshub tool with test fixtures.

Tests the complete flow of invoking namshubs through the invoke_namshub tool
using test fixture namshubs. No API calls - uses MockBot only.
"""

import os
from unittest.mock import patch

import pytest

from bots.testing.mock_bot import MockBot
from bots.tools.invoke_namshub import invoke_namshub


class TestInvokeNamshubBasicFlow:
    """Test basic invocation flow with simple namshubs."""

    def test_invoke_no_op_namshub(self):
        """Test invoking the no-op namshub through invoke_namshub tool."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        # Get the path to the no-op namshub
        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path)

        assert "success" in result.lower()
        assert "Error" not in result

    def test_invoke_echo_namshub_with_parameter(self):
        """Test invoking echo namshub with parameter."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_echo.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"message": "Hello from test!"}')

        assert "Echo: Hello from test!" in result
        assert "Error" not in result

    def test_invoke_echo_namshub_missing_parameter(self):
        """Test that echo namshub validates missing parameter."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_echo.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path)

        assert "Error" in result
        assert "message" in result.lower()
        assert "required" in result.lower()


class TestInvokeNamshubStateManagement:
    """Test that invoke_namshub properly manages bot state."""

    def test_state_restored_after_no_op(self):
        """Test that bot state is restored after no-op namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_system_message = bot.system_message
        original_tool_count = len(bot.tool_handler.tools) if hasattr(bot.tool_handler, "tools") else 0

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            invoke_namshub(fixture_path)

        # State should be restored
        assert bot.system_message == original_system_message
        current_tool_count = len(bot.tool_handler.tools) if hasattr(bot.tool_handler, "tools") else 0
        assert current_tool_count == original_tool_count

    def test_state_restored_after_state_change_namshub(self):
        """Test that bot state is restored even after namshub modifies it."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_system_message = "Original test message"
        bot.set_system_message(original_system_message)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_state_change.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"new_message": "Temporary message"}')

        # During execution, message was changed
        assert "changed" in result.lower()

        # After execution, state should be restored
        assert bot.system_message == original_system_message

    def test_state_restored_after_tool_use_namshub(self):
        """Test that toolkit is restored after tool_use namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        # Save the original tool handler reference
        original_tool_handler = bot.tool_handler

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_tool_use.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"expression": "10 * 5"}')

        assert "50" in result

        # Tool handler should be restored to the original reference
        assert bot.tool_handler is original_tool_handler


class TestInvokeNamshubWithToolUse:
    """Test namshubs that use tools."""

    def test_tool_use_namshub_evaluates_expression(self):
        """Test that tool_use namshub can execute Python code."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_tool_use.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"expression": "7 * 8"}')

        assert "7 * 8" in result
        assert "56" in result

    def test_tool_use_namshub_with_default_expression(self):
        """Test tool_use namshub with default expression."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_tool_use.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path)

        assert "2 + 2" in result
        assert "4" in result

    def test_tool_use_namshub_with_complex_expression(self):
        """Test tool_use namshub with complex Python expression."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_tool_use.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"expression": "len(\'hello world\')"}')

        assert "len('hello world')" in result
        assert "11" in result


class TestInvokeNamshubWithWorkflow:
    """Test namshubs that execute workflows."""

    def test_simple_workflow_executes(self):
        """Test that simple_workflow namshub executes successfully."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_simple_workflow.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"task": "test workflow execution"}')

        assert "completed" in result.lower()

    def test_simple_workflow_with_custom_task(self):
        """Test simple_workflow with custom task description."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_simple_workflow.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"task": "analyze data"}')

        assert "completed" in result.lower()

    def test_workflow_system_message_restored(self):
        """Test that system message is restored after workflow execution."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_message = "Original system message"
        bot.set_system_message(original_message)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_simple_workflow.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            invoke_namshub(fixture_path, kwargs='{"task": "test task"}')

        # System message should be restored
        assert bot.system_message == original_message


class TestInvokeNamshubErrorHandling:
    """Test error handling in invoke_namshub."""

    def test_error_namshub_raises_and_restores_state(self):
        """Test that errors are propagated and state is still restored."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_system_message = "Original message"
        bot.set_system_message(original_system_message)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_error.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"error_type": "ValueError"}')

        # Error should be caught and returned as string
        assert "Error" in result or "error" in result.lower()
        assert "ValueError" in result or "Deliberate" in result

        # State should still be restored
        assert bot.system_message == original_system_message

    def test_error_namshub_runtime_error(self):
        """Test that RuntimeError is handled properly."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_error.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"error_type": "RuntimeError"}')

        assert "Error" in result or "error" in result.lower()
        assert "RuntimeError" in result or "runtime" in result.lower()

    def test_nonexistent_namshub_file(self):
        """Test that nonexistent namshub file is handled gracefully."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub("nonexistent_namshub_file.py")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_invalid_namshub_path(self):
        """Test that invalid path is handled gracefully."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub("/invalid/path/to/namshub.py")

        assert "Error" in result
        assert "not found" in result.lower()

    def test_invalid_json_kwargs(self):
        """Test that invalid JSON in kwargs is handled gracefully."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"invalid json}')

        assert "Error" in result
        assert "JSON" in result or "json" in result


class TestInvokeNamshubMultipleInvocations:
    """Test multiple sequential namshub invocations."""

    def test_sequential_no_op_invocations(self):
        """Test multiple no-op invocations in sequence."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result1 = invoke_namshub(fixture_path)
            result2 = invoke_namshub(fixture_path)
            result3 = invoke_namshub(fixture_path)

        assert "success" in result1.lower()
        assert "success" in result2.lower()
        assert "success" in result3.lower()

    def test_sequential_different_namshubs(self):
        """Test invoking different namshubs in sequence."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_message = bot.system_message

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            # Invoke no-op
            result1 = invoke_namshub(os.path.join("tests", "fixtures", "namshub_of_no_op.py"))
            assert "success" in result1.lower()

            # Invoke echo
            result2 = invoke_namshub(os.path.join("tests", "fixtures", "namshub_of_echo.py"), kwargs='{"message": "test"}')
            assert "Echo: test" in result2

            # Invoke tool_use
            result3 = invoke_namshub(
                os.path.join("tests", "fixtures", "namshub_of_tool_use.py"), kwargs='{"expression": "3 + 3"}'
            )
            assert "6" in result3

        # State should be restored after all invocations
        assert bot.system_message == original_message

    def test_alternating_state_changes(self):
        """Test that state is properly managed across alternating invocations."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_message = "Original"
        bot.set_system_message(original_message)

        state_change_path = os.path.join("tests", "fixtures", "namshub_of_state_change.py")
        no_op_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            # Alternate between state-changing and no-op namshubs
            invoke_namshub(state_change_path, kwargs='{"new_message": "Change 1"}')
            assert bot.system_message == original_message

            invoke_namshub(no_op_path)
            assert bot.system_message == original_message

            invoke_namshub(state_change_path, kwargs='{"new_message": "Change 2"}')
            assert bot.system_message == original_message


class TestInvokeNamshubDirectoryListing:
    """Test directory listing functionality."""

    def test_list_namshubs_in_directory(self):
        """Test that providing a directory lists available namshubs."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub("tests/fixtures/")

        assert "namshub" in result.lower()
        assert "namshub_of_no_op.py" in result or "no_op" in result

    def test_empty_directory_error(self):
        """Test that empty directory returns appropriate error."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        # Create a temp empty directory
        import tempfile

        with tempfile.TemporaryDirectory() as tmpdir:
            with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
                result = invoke_namshub(tmpdir)

            assert "Error" in result or "No namshub" in result


class TestInvokeNamshubEdgeCases:
    """Test edge cases and boundary conditions."""

    def test_invoke_with_empty_kwargs_string(self):
        """Test invoking namshub with empty kwargs string."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs="{}")

        assert "success" in result.lower()

    def test_echo_with_special_characters(self):
        """Test echo namshub with special characters in message."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_echo.py")

        special_msg = "Test with 'quotes' and newlines"

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs=f'{{"message": "{special_msg}"}}')

        assert "Echo:" in result
        assert "Test with" in result

    def test_echo_with_empty_string(self):
        """Test echo namshub with empty string message."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_echo.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"message": ""}')

        assert "Echo: " in result
class TestInvokeNamshubPostExecution:
    """Test that bot can continue conversation after namshub execution."""

    def test_conversation_continues_after_no_op(self):
        """Test that bot can respond normally after no-op namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path)
            assert "success" in result.lower()

        # Continue conversation after namshub
        response = bot.respond("What is 2 + 2?")
        assert response is not None
        assert len(response) > 0

    def test_conversation_continues_after_echo(self):
        """Test that bot can respond after echo namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_echo.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"message": "test"}')
            assert "Echo: test" in result

        # Continue conversation
        response = bot.respond("Continue the conversation")
        assert response is not None

    def test_conversation_continues_after_state_change(self):
        """Test that bot can respond after state_change namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_message = "Original"
        bot.set_system_message(original_message)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_state_change.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"new_message": "Changed"}')
            assert "changed" in result.lower()

        # Verify state was restored
        assert bot.system_message == original_message

        # Continue conversation
        response = bot.respond("What's your system message?")
        assert response is not None

    def test_conversation_continues_after_tool_use(self):
        """Test that bot can respond after tool_use namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_tool_use.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"expression": "5 * 5"}')
            assert "25" in result

        # Continue conversation
        response = bot.respond("What was the result?")
        assert response is not None

    def test_conversation_continues_after_workflow(self):
        """Test that bot can respond after simple_workflow namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_simple_workflow.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"task": "test"}')
            assert "completed" in result.lower()

        # Continue conversation
        response = bot.respond("Summarize what you did")
        assert response is not None

    def test_multiple_messages_after_namshub(self):
        """Test multiple conversation turns after namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_no_op.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path)

        # Multiple conversation turns
        response1 = bot.respond("First message after namshub")
        assert response1 is not None

        response2 = bot.respond("Second message after namshub")
        assert response2 is not None

        response3 = bot.respond("Third message after namshub")
        assert response3 is not None

    def test_conversation_after_error_namshub(self):
        """Test that bot can continue even after error namshub."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        original_message = bot.system_message

        fixture_path = os.path.join("tests", "fixtures", "namshub_of_error.py")

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            result = invoke_namshub(fixture_path, kwargs='{"error_type": "ValueError"}')
            assert "Error" in result or "error" in result.lower()

        # State should be restored
        assert bot.system_message == original_message

        # Continue conversation
        response = bot.respond("Are you still working?")
        assert response is not None

    def test_sequential_namshubs_with_conversation(self):
        """Test conversation between multiple namshub invocations."""
        bot = MockBot(autosave=False)
        bot.add_tools(invoke_namshub)

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            # First namshub
            result1 = invoke_namshub(os.path.join("tests", "fixtures", "namshub_of_no_op.py"))
            assert "success" in result1.lower()

        # Conversation after first namshub
        response1 = bot.respond("First namshub completed")
        assert response1 is not None

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            # Second namshub
            result2 = invoke_namshub(os.path.join("tests", "fixtures", "namshub_of_echo.py"), kwargs='{"message": "test"}')
            assert "Echo: test" in result2

        # Conversation after second namshub
        response2 = bot.respond("Second namshub completed")
        assert response2 is not None

        with patch("bots.tools.invoke_namshub._get_calling_bot", return_value=bot):
            # Third namshub
            result3 = invoke_namshub(os.path.join("tests", "fixtures", "namshub_of_tool_use.py"))
            assert "4" in result3

        # Final conversation
        response3 = bot.respond("All namshubs completed")
        assert response3 is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])