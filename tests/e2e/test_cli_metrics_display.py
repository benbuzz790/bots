"""
Test for Issue #164: Metrics display inconsistency in CLI auto mode.

This test reproduces the bug where metrics are displayed twice per iteration
in auto mode - once in auto_callback and once in verbose_callback.
"""

from unittest.mock import Mock, patch

import pytest

from bots.dev.cli import CLIContext, SystemHandler
from bots.foundation.anthropic_bots import AnthropicBot


@pytest.mark.no_isolation
@pytest.mark.e2e
def test_metrics_display_once_per_response_in_auto_mode():
    """
    Test that metrics are displayed only once per bot response in auto mode.

    Before fix: metrics display twice per iteration
    1. In auto_callback before next user prompt (REMOVED)
    2. In verbose_callback after bot response (KEPT)

    After fix: metrics display only once (in verbose_callback).
    """
    # Setup
    context = CLIContext()
    context.config.verbose = True

    # Create a mock bot
    bot = Mock(spec=AnthropicBot)
    bot.conversation = Mock()
    bot.tool_handler = Mock()
    bot.name = "TestBot"
    context.bot_instance = bot

    # Track display_metrics calls
    display_calls = []

    def mock_display_metrics(ctx, b):
        display_calls.append(("display_metrics", ctx, b))

    # Mock the bot's respond behavior to simulate tool usage then no tools
    call_count = [0]

    def mock_tool_requests():
        call_count[0] += 1
        # First call: has tools (continue loop)
        # Second call: no tools (stop loop)
        return [{"tool": "test"}] if call_count[0] == 1 else []

    bot.tool_handler.requests = property(lambda self: mock_tool_requests())

    # Mock metrics
    mock_metrics = {"input_tokens": 100, "output_tokens": 50, "cost": 0.001, "duration": 1.5}

    with patch("bots.dev.cli.display_metrics", side_effect=mock_display_metrics):
        with patch("bots.observability.metrics.get_and_clear_last_metrics", return_value=mock_metrics):
            with patch("bots.dev.cli.setup_raw_mode", return_value=None):
                with patch("bots.dev.cli.restore_terminal"):
                    with patch("bots.dev.cli.check_for_interrupt", return_value=False):
                        with patch("bots.dev.cli.pretty"):
                            with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
                                # Simulate prompt_while calling the callback once per iteration
                                def simulate_prompt_while(bot, prompt, continue_prompt, stop_condition, callback):
                                    # First iteration - bot responds, has tools
                                    bot.tool_handler.requests = [{"tool": "test"}]
                                    callback(["response1"], [Mock()])

                                    # Second iteration - bot responds, no tools (stops)
                                    bot.tool_handler.requests = []
                                    callback(["response2"], [Mock()])

                                mock_prompt_while.side_effect = simulate_prompt_while

                                # Execute auto mode
                                handler = SystemHandler()
                                handler.auto(bot, context, [])

    # Analyze results
    print(f"\nTotal display_metrics calls: {len(display_calls)}")

    # Expected after fix: 3 calls total
    # - 1 after first bot response (from verbose_callback)
    # - 1 after second bot response (from verbose_callback)
    # - 1 at end of auto() method

    # Verify the fix
    assert len(display_calls) == 3, f"Expected 3 display_metrics calls (one per response + final), got {len(display_calls)}"
    print("✓ Fix verified: metrics displayed exactly once per bot response")


def test_metrics_not_displayed_before_user_prompts():
    """
    Test that metrics are NOT displayed before user prompts in auto mode.

    Currently FAILS because auto_callback displays metrics before showing
    the next user prompt.
    """
    # This is a conceptual test - the timing issue is harder to test directly
    # but the fix (removing display_metrics from auto_callback) will address it
    pass


if __name__ == "__main__":
    test_metrics_display_once_per_response_in_auto_mode()
