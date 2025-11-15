"""
Test for Issue #164: Metrics display inconsistency in CLI auto mode.

This test reproduces the bug where metrics are displayed twice per iteration
in auto mode - once in auto_callback and once in verbose_callback.
"""

from unittest.mock import Mock, patch

from bots.dev.cli_modules.config import CLIContext
from bots.dev.cli_modules.handlers.system import SystemHandler
from bots.foundation.anthropic_bots import AnthropicBot


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

    # Set requests as a normal attribute that will be mutated by simulate_prompt_while
    bot.tool_handler.requests = []

    # Mock metrics
    mock_metrics = {"input_tokens": 100, "output_tokens": 50, "cost": 0.001, "duration": 1.5}

    with patch("bots.dev.cli_modules.handlers.system.display_metrics", side_effect=mock_display_metrics):
        with patch("bots.observability.metrics.get_and_clear_last_metrics", return_value=mock_metrics):
            with patch("bots.dev.cli_modules.handlers.system.setup_raw_mode", return_value=None):
                with patch("bots.dev.cli_modules.handlers.system.restore_terminal"):
                    with patch("bots.dev.cli_modules.handlers.system.check_for_interrupt", return_value=False):
                        with patch("bots.dev.cli_modules.handlers.system.pretty"):
                            with patch("bots.flows.functional_prompts.prompt_while") as mock_prompt_while:
                                # Simulate prompt_while calling the callback once per iteration
                                def simulate_prompt_while(bot, prompt, continue_prompt, stop_condition, callback):
                                    # First iteration - bot responds, has tools
                                    bot.tool_handler.requests = [{"tool": "test"}]
                                    callback(["response1"], [Mock()])
                                    # Second iteration - bot responds, no tools (stop)
                                    bot.tool_handler.requests = []
                                    callback(["response2"], [Mock()])
                                    return (["response1", "response2"], [Mock(), Mock()])

                                mock_prompt_while.side_effect = simulate_prompt_while

                                # Execute auto command
                                system_handler = SystemHandler()
                                system_handler.auto(bot, context, [])

    # Verify metrics were displayed exactly twice (once per iteration)
    # NOT four times (which would happen if auto_callback also displayed them)
    assert len(display_calls) == 2, f"Expected 2 display_metrics calls, got {len(display_calls)}"
