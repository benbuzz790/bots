"""Test CLI auto-backup behavior to ensure output is displayed correctly."""

from unittest.mock import MagicMock

import pytest

from bots.dev.cli import CLIContext
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


def test_cli_auto_backup_preserves_mailbox():
    """Test that auto-backup creates a copy with a working mailbox."""
    context = CLIContext()
    bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)
    context.bot_instance = bot

    # Verify original bot has mailbox
    assert bot.mailbox is not None

    # Create backup (simulates what happens before each message)
    success = context.create_backup("before_user_message")
    assert success is True

    # Verify backup was created
    assert context.bot_backup is not None

    # Verify backup has a mailbox (not None)
    assert context.bot_backup.mailbox is not None

    # Verify mailboxes are different objects
    assert context.bot_backup.mailbox is not bot.mailbox


def test_cli_auto_backup_preserves_callbacks():
    """Test that auto-backup preserves callbacks."""
    context = CLIContext()
    bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)

    # Set up callbacks
    mock_callback = MagicMock()
    bot.callbacks = mock_callback
    context.bot_instance = bot

    # Create backup
    success = context.create_backup("before_user_message")
    assert success is True

    # Verify callbacks are preserved (same object)
    assert context.bot_backup.callbacks is mock_callback


def test_cli_message_flow_with_auto_backup():
    """Test complete message flow with auto-backup enabled."""
    context = CLIContext()
    context.config.auto_backup = True

    bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)
    context.bot_instance = bot

    # Simulate what happens when user sends a message
    # 1. Auto-backup is created
    backup_success = context.create_backup("before_user_message")
    assert backup_success is True

    # 2. Verify backup still has working mailbox
    assert context.bot_backup.mailbox is not None


def test_bot_multiplication_preserves_mailbox():
    """Test that bot * 1 (used by auto-backup) preserves mailbox."""
    bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)

    # Verify original has mailbox
    assert bot.mailbox is not None

    # Create copy using multiplication (what auto-backup does)
    copies = bot * 1
    assert len(copies) == 1

    copy = copies[0]

    # Verify copy has mailbox
    assert copy.mailbox is not None

    # Verify mailboxes are different objects
    assert copy.mailbox is not bot.mailbox


def test_cli_output_display_with_callbacks():
    """Test that CLI callbacks work after auto-backup."""
    from io import StringIO

    context = CLIContext()
    bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)

    # Create a callback that captures output
    output_buffer = StringIO()

    class TestCallback:
        """Callback handler for processing events and writing responses to output buffer.

        Args:
            event_type (str): Type of event being processed.
            data: Event data to be processed and written to buffer.
        """
        def __call__(self, event_type, data):
            if event_type == "response":
                output_buffer.write(f"Response: {data}\n")

    bot.callbacks = TestCallback()
    context.bot_instance = bot

    # Create backup
    context.create_backup("before_user_message")

    # Simulate bot response with callback
    if bot.callbacks:
        bot.callbacks("response", "Test output")

    # Verify callback was called and output was captured
    output = output_buffer.getvalue()
    assert "Response: Test output" in output


def test_deepcopy_with_tool_management_tools():
    """Test deepcopy with actual tool management tools loaded."""
    from bots.tools.tool_management_tools import load_tools, view_tools

    bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)
    bot.add_tools(view_tools, load_tools)

    # Verify bot has tools
    assert len(bot.tool_handler.function_map) > 0

    # Test multiplication (used by auto-backup)
    copies = bot * 1
    assert len(copies) == 1

    copy = copies[0]

    # Verify copy has mailbox
    assert copy.mailbox is not None

    # Verify copy has tools
    assert len(copy.tool_handler.function_map) == len(bot.tool_handler.function_map)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
