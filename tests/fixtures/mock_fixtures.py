"""Mock fixtures for common test scenarios.

Provides mocks for user input, print output, and bot loading.
"""

from io import StringIO
from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_input():
    """Mock user input for testing interactive features.

    Returns a mock that can be configured to return specific inputs.

    Usage:
        def test_something(mock_input):
            mock_input.side_effect = ["first input", "second input"]
            with patch('builtins.input', mock_input):
                # Test code that calls input()
    """
    return Mock()


@pytest.fixture
def mock_print():
    """Mock print output for testing console output.

    Returns a mock that captures print calls.

    Usage:
        def test_something(mock_print):
            with patch('builtins.print', mock_print):
                # Test code that calls print()
            assert mock_print.call_count == 2
            assert "expected output" in str(mock_print.call_args)
    """
    return Mock()


@pytest.fixture
def mock_stdout():
    """Mock stdout for capturing output.

    Returns a StringIO object that captures stdout.

    Usage:
        def test_something(mock_stdout):
            with patch('sys.stdout', mock_stdout):
                print("test output")
            output = mock_stdout.getvalue()
            assert "test output" in output
    """
    return StringIO()


@pytest.fixture
def mock_bot_load():
    """Mock bot loading to avoid file I/O in unit tests.

    Returns a mock function that simulates bot loading.

    Usage:
        def test_something(mock_bot_load):
            mock_bot = Mock()
            mock_bot_load.return_value = mock_bot
            with patch('bots.load', mock_bot_load):
                # Test code that calls bots.load()
    """
    mock_load = Mock()
    mock_bot = Mock()
    mock_bot.respond = Mock(return_value="Mock response")
    mock_bot.conversation = Mock()
    mock_load.return_value = mock_bot
    return mock_load


@pytest.fixture
def mock_exists():
    """Mock os.path.exists for file existence checks.

    Returns a mock that can be configured for different paths.

    Usage:
        def test_something(mock_exists):
            mock_exists.return_value = True
            with patch('os.path.exists', mock_exists):
                # Test code that checks file existence
    """
    return Mock()


@pytest.fixture
def mock_check_interrupt():
    """Mock keyboard interrupt checking.

    Returns a mock for interrupt handling in CLI tests.
    """
    return Mock(return_value=False)


@pytest.fixture
def safe_cli_context():
    """Create a safe CLI context for testing with MagicMock bots.

    This fixture prevents recursive issues when using MagicMock bots by:
    1. Disabling auto_backup (which tries to copy the bot with bot * 1)
    2. Disabling auto_stash (which can trigger git operations)
    3. Disabling auto_restore_on_error (which depends on backups)

    The issue: When a MagicMock bot is assigned to context.bot_instance,
    and then callbacks are attached (callbacks.context.bot_instance -> mock_bot),
    this creates a circular reference. When auto_backup tries to copy the bot
    using (bot * 1), it attempts to deep copy the MagicMock, causing infinite
    recursion or memory issues.

    Usage:
        def test_something(safe_cli_context):
            context, mock_bot = safe_cli_context
            # Use context and mock_bot safely
            cli = CLI()
            cli.context = context
            cli._handle_chat(mock_bot, "test input")

    Returns:
        tuple: (CLIContext, MagicMock) - A safe context and mock bot
    """
    from bots.dev.cli import CLIContext

    context = CLIContext()
    # Disable features that try to copy/serialize the bot
    context.config.auto_backup = False
    context.config.auto_stash = False
    context.config.auto_restore_on_error = False

    # Create a mock bot with basic attributes
    mock_bot = MagicMock()
    mock_bot.name = "TestBot"
    mock_bot.conversation = MagicMock()
    mock_bot.tool_handler = MagicMock()
    mock_bot.tool_handler.requests = []
    mock_bot.tool_handler.results = []

    # Assign to context
    context.bot_instance = mock_bot

    return context, mock_bot
