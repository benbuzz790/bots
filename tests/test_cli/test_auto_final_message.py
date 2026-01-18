"""Test that /auto command displays the final message, not the first message.

This test addresses GitHub issue #231 and WO023.
"""

from unittest.mock import Mock, patch

from bots.dev.cli import CLIConfig, CLIContext, SystemHandler
from bots.foundation.base import Bot


class TestAutoFinalMessage:
    """Test /auto command message display behavior."""

    def test_auto_returns_final_response_not_first(self):
        """Test that /auto command returns the final response from prompt_while.

        This test verifies the fix for issue #231 where /auto was displaying
        the first message instead of the final message.
        """
        # Create mock bot
        bot = Mock(spec=Bot)
        bot.conversation = Mock()
        bot.tool_handler = Mock()
        bot.tool_handler.requests = []  # No tools, so it stops immediately

        # Mock responses from prompt_while - simulating multiple iterations
        first_response = "This is the first response"
        middle_response = "This is a middle response"
        final_response = "This is the FINAL response"

        mock_responses = [first_response, middle_response, final_response]
        mock_nodes = [Mock(), Mock(), Mock()]

        # Create context
        context = CLIContext()
        context.config = CLIConfig()
        context.callbacks = Mock()
        context.callbacks.get_standard_callback = Mock(return_value=None)

        # Create handler
        handler = SystemHandler()

        # Mock the functional_prompts.prompt_while to return our test data
        with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
            mock_prompt_while.return_value = (mock_responses, mock_nodes)

            # Mock terminal functions
            with patch("bots.dev.cli.setup_raw_mode", return_value=None):
                with patch("bots.dev.cli.restore_terminal"):
                    with patch("bots.dev.cli.display_metrics"):
                        with patch("bots.dev.cli.pretty"):
                            # Call auto command
                            result = handler.auto(bot, context, [])

                            # The result should contain or be the final response
                            # Currently this will FAIL because auto() returns ""
                            # After the fix, it should return the final response
                            assert result != "", "auto() should return the final message, not empty string"
                            assert (
                                final_response in result or result == final_response
                            ), f"Expected final response '{final_response}' but got '{result}'"

                            # Verify it's NOT the first response
                            if result and result != final_response:
                                assert first_response not in result, f"Should not return first response '{first_response}'"

    def test_auto_with_single_response(self):
        """Test /auto with only one response (edge case)."""
        bot = Mock(spec=Bot)
        bot.conversation = Mock()
        bot.tool_handler = Mock()
        bot.tool_handler.requests = []

        single_response = "Only one response"
        mock_responses = [single_response]
        mock_nodes = [Mock()]

        context = CLIContext()
        context.config = CLIConfig()
        context.callbacks = Mock()
        context.callbacks.get_standard_callback = Mock(return_value=None)

        handler = SystemHandler()

        with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
            mock_prompt_while.return_value = (mock_responses, mock_nodes)

            with patch("bots.dev.cli.setup_raw_mode", return_value=None):
                with patch("bots.dev.cli.restore_terminal"):
                    with patch("bots.dev.cli.display_metrics"):
                        with patch("bots.dev.cli.pretty"):
                            result = handler.auto(bot, context, [])

                            # Should return the single response
                            assert result != "", "Should return the response, not empty string"
                            assert single_response in result or result == single_response

    def test_auto_with_empty_responses(self):
        """Test /auto with no responses (edge case)."""
        bot = Mock(spec=Bot)
        bot.conversation = Mock()
        bot.tool_handler = Mock()
        bot.tool_handler.requests = []

        mock_responses = []
        mock_nodes = []

        context = CLIContext()
        context.config = CLIConfig()
        context.callbacks = Mock()
        context.callbacks.get_standard_callback = Mock(return_value=None)

        handler = SystemHandler()

        with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
            mock_prompt_while.return_value = (mock_responses, mock_nodes)

            with patch("bots.dev.cli.setup_raw_mode", return_value=None):
                with patch("bots.dev.cli.restore_terminal"):
                    with patch("bots.dev.cli.display_metrics"):
                        with patch("bots.dev.cli.pretty"):
                            result = handler.auto(bot, context, [])

                            # With no responses, returning empty string is acceptable
                            assert isinstance(result, str)
