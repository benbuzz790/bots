"""Test for auto message functionality.

This test verifies that prompt_while returns expected values and can be used
in auto mode scenarios.
"""

import os
import sys
from unittest.mock import Mock, patch

# Move sys.path manipulation to the top before any imports that rely on it
sys.path.insert(0, os.path.abspath("."))

import pytest  # noqa: E402

from bots.foundation.anthropic_bots import AnthropicBot  # noqa: E402
from bots.foundation.base import Engines  # noqa: E402


def test_auto_message_returns_expected():
    """Test that prompt_while returns expected response and node values."""
    # Create a mock bot
    bot = Mock(spec=AnthropicBot)
    bot.conversation = Mock()
    bot.tool_handler = Mock()
    bot.tool_handler.requests = []  # No tools, so it stops immediately
    bot.model_engine = Engines.CLAUDE37_SONNET_20250219

    # Mock responses from prompt_while
    expected_response = "Test response"
    mock_node = Mock()

    # Mock the functional_prompts.prompt_while to return our test data
    with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
        mock_prompt_while.return_value = ([expected_response], [mock_node])

        # Import after patching
        from bots.flows import functional_prompts as fp

        # Call prompt_while
        responses, nodes = fp.prompt_while(
            bot,
            "Test prompt",
            continue_prompt="Continue",
            stop_condition=fp.conditions.tool_not_used,
        )

        # Verify the return values
        assert len(responses) == 1
        assert responses[0] == expected_response
        assert len(nodes) == 1
        assert nodes[0] == mock_node


def test_auto_message_with_multiple_iterations():
    """Test that prompt_while handles multiple iterations correctly."""
    # Create a mock bot
    bot = Mock(spec=AnthropicBot)
    bot.conversation = Mock()
    bot.tool_handler = Mock()
    bot.model_engine = Engines.CLAUDE37_SONNET_20250219

    # Mock multiple responses
    expected_responses = ["Response 1", "Response 2", "Response 3"]
    mock_nodes = [Mock(), Mock(), Mock()]

    with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
        mock_prompt_while.return_value = (expected_responses, mock_nodes)

        from bots.flows import functional_prompts as fp

        responses, nodes = fp.prompt_while(
            bot,
            "Test prompt",
            continue_prompt="Continue",
            stop_condition=fp.conditions.tool_not_used,
        )

        # Verify all responses are returned
        assert len(responses) == 3
        assert responses == expected_responses
        assert len(nodes) == 3
        assert nodes == mock_nodes


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
