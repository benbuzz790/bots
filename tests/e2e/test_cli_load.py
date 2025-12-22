import unittest
from unittest.mock import MagicMock, patch

import pytest

import bots.dev.cli as cli_module
from bots import AnthropicBot, Engines
from bots.dev.cli import CLI, CLIContext, RealTimeDisplayCallbacks, StateHandler

pytestmark = pytest.mark.e2e


class TestCLILoad:
    """Test suite for CLI load functionality."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.content = "Original response"
        self.mock_bot.conversation.replies = []
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot
        self.context.labeled_nodes = {"test": "node"}
        # Use StateHandler which contains the load function
        self.handler = cli_module.StateHandler()

    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_success_updates_context(self, mock_bot_load, mock_exists, monkeypatch):
        """Test that load function updates context.bot_instance."""
        test_filename = "test_bot.bot"
        # Setup mocks
        inputs = iter([test_filename])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        mock_exists.return_value = True
        new_mock_bot = MagicMock()
        new_mock_bot.name = "LoadedBot"
        new_mock_bot.conversation = MagicMock()
        new_mock_bot.conversation.content = "Loaded response"
        new_mock_bot.conversation.replies = []
        mock_bot_load.return_value = new_mock_bot
        # Store original bot reference
        original_bot = self.context.bot_instance
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify the load was called
        mock_bot_load.assert_called_once_with(test_filename)
        # Verify context.bot_instance was updated (this should pass now)
        assert self.context.bot_instance != original_bot, "Context bot_instance should be updated after load"
        assert self.context.bot_instance == new_mock_bot, "Context should reference the loaded bot"
        # Result is now a dict
        assert isinstance(result, dict)
        assert "Bot loaded from test_bot.bot" in result["message"]

    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_clears_labeled_nodes(self, mock_bot_load, mock_exists, monkeypatch):
        """Test that load function clears labeled nodes."""
        # Setup mocks
        inputs = iter(["test_bot.bot"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        mock_exists.return_value = True
        new_bot = MagicMock()
        new_bot.conversation = MagicMock()
        new_bot.conversation.replies = []
        mock_bot_load.return_value = new_bot
        # Ensure labeled_nodes has content
        self.context.labeled_nodes = {"node1": "value1", "node2": "value2"}
        # Call load function
        self.handler.load(self.mock_bot, self.context, [])
        # Verify labeled_nodes was cleared
        assert self.context.labeled_nodes == {}, "Labeled nodes should be cleared after load"

    def test_load_cancelled_by_user(self, monkeypatch):
        """Test load function when user cancels by providing empty filename."""
        # User cancels by providing empty filename
        inputs = iter([""])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        original_bot = self.context.bot_instance
        original_nodes = self.context.labeled_nodes.copy()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify nothing changed
        assert self.context.bot_instance == original_bot
        assert self.context.labeled_nodes == original_nodes
        # Verify the cancellation message
        assert isinstance(result, dict)
        assert "cancelled" in result["message"].lower()

    @patch("os.path.exists")
    def test_load_file_not_found(self, mock_exists, monkeypatch):
        """Test load function when file doesn't exist."""
        inputs = iter(["nonexistent.bot"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        mock_exists.return_value = False
        original_bot = self.context.bot_instance
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify bot wasn't changed
        assert self.context.bot_instance == original_bot
        # Result is now a dict
        assert isinstance(result, dict)
        assert "File not found" in result["message"]

    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_file_error(self, mock_bot_load, mock_exists, monkeypatch):
        """Test load function when Bot.load raises an exception."""
        inputs = iter(["corrupted.bot"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        mock_exists.return_value = True
        mock_bot_load.side_effect = Exception("File corrupted")
        original_bot = self.context.bot_instance
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify bot wasn't changed
        assert self.context.bot_instance == original_bot
        # Result is now a dict
        assert isinstance(result, dict)
        assert "Error loading bot" in result["message"]

    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_calls_rebuild_labels(self, mock_bot_load, mock_exists, monkeypatch):
        """Test that load function calls _rebuild_labels."""
        # Setup mocks
        inputs = iter(["test_bot.bot"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        mock_exists.return_value = True
        new_bot = MagicMock()
        new_bot.conversation = MagicMock()
        new_bot.conversation.replies = []
        mock_bot_load.return_value = new_bot
        # Mock the _rebuild_labels method
        self.handler._rebuild_labels = MagicMock()
        # Call load function
        self.handler.load(self.mock_bot, self.context, [])
        # Verify _rebuild_labels was called
        self.handler._rebuild_labels.assert_called_once_with(new_bot.conversation, self.context)

    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_navigates_to_conversation_end(self, mock_bot_load, mock_exists, monkeypatch):
        """Test that load function navigates to the end of conversation."""
        inputs = iter(["test_bot.bot"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
        mock_exists.return_value = True
        # Create a conversation tree with multiple replies
        root = MagicMock()
        reply1 = MagicMock()
        reply2 = MagicMock()
        reply1.replies = [reply2]
        reply2.replies = []
        root.replies = [reply1]
        new_bot = MagicMock()
        new_bot.conversation = root
        mock_bot_load.return_value = new_bot
        # Mock _rebuild_labels to avoid issues
        self.handler._rebuild_labels = MagicMock()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify bot conversation was navigated to the end
        assert new_bot.conversation == reply2
        # Result is now a dict
        assert isinstance(result, dict)
        assert "Conversation restored to most recent message" in result["message"]

    @patch("os.path.exists")
    @patch("bots.foundation.base.Bot.load")
    def test_load_handles_extension_automatically(self, mock_bot_load, mock_exists, monkeypatch):
        """Test that load function automatically adds .bot extension."""
        # Setup mocks - user provides filename without extension
        inputs = iter(["test_bot"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))

        def mock_exists_side_effect(path):
            # First call: "test_bot" doesn't exist
            # Second call: "test_bot.bot" exists
            return path == "test_bot.bot"

        mock_exists.side_effect = mock_exists_side_effect
        new_bot = MagicMock()
        new_bot.conversation = MagicMock()
        new_bot.conversation.replies = []
        mock_bot_load.return_value = new_bot
        # Mock _rebuild_labels to avoid issues
        self.handler._rebuild_labels = MagicMock()
        # Call load function
        result = self.handler.load(self.mock_bot, self.context, [])
        # Verify the load was called with .bot extension added
        mock_bot_load.assert_called_once_with("test_bot.bot")
        # Result is now a dict
        assert isinstance(result, dict)
        assert "Bot loaded from test_bot.bot" in result["message"]

    def test_load_function_is_fixed(self, monkeypatch):
        """Verify that the load function correctly updates context."""
        # This test demonstrates that the load function has been fixed
        # It should update context.bot_instance, not just create a local
        # variable
        # Create a mock scenario
        original_bot = self.context.bot_instance
        with (
            patch("os.path.exists") as mock_exists,
            patch("bots.foundation.base.Bot.load") as mock_load,
        ):
            inputs = iter(["test.bot"])
            monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(inputs, ""))
            mock_exists.return_value = True
            new_bot = MagicMock()
            new_bot.name = "NewBot"
            new_bot.conversation = MagicMock()
            new_bot.conversation.replies = []
            mock_load.return_value = new_bot
            # Mock _rebuild_labels to avoid AttributeError
            self.handler._rebuild_labels = MagicMock()
            # Call load
            result = self.handler.load(self.mock_bot, self.context, [])
            # Verify the fix works
            assert self.context.bot_instance != original_bot
            assert self.context.bot_instance == new_bot
            assert self.context.labeled_nodes == {}
            # Result is now a dict
            assert isinstance(result, dict)
            assert "Bot loaded from test.bot" in result["message"]


if __name__ == "__main__":
    unittest.main()


class TestCLILoadCallbacksRegression:
    """Test that verifies callbacks are properly attached when loading bots in CLI."""

    def test_loaded_bot_missing_cli_callbacks(self, tmp_path):
        """
        REGRESSION TEST: When loading a bot in the CLI, the RealTimeDisplayCallbacks
        are not attached, causing the CLI to not display tool execution properly.

        This test reproduces the bug where:
        1. A bot is saved with some state
        2. The bot is loaded via CLI startup or /load command
        3. The loaded bot doesn't have the CLI's RealTimeDisplayCallbacks attached
        4. Tool execution and streaming don't work properly in the CLI
        """
        # Create and save a bot
        bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)
        bot_file = tmp_path / "test_bot.bot"
        bot.save(str(bot_file))

        # Simulate CLI loading the bot (current behavior)
        context = CLIContext()
        state_handler = StateHandler()

        # Load the bot using the CLI's method
        state_handler._load_bot_from_file(str(bot_file), context)

        # The bug: loaded bot should have RealTimeDisplayCallbacks but doesn't
        loaded_bot = context.bot_instance

        # This assertion should pass but currently fails
        assert isinstance(loaded_bot.callbacks, RealTimeDisplayCallbacks), (
            f"Loaded bot should have RealTimeDisplayCallbacks attached, "
            f"but has {type(loaded_bot.callbacks).__name__} instead. "
            f"This causes CLI display issues."
        )

    def test_cli_startup_with_bot_file_missing_callbacks(self, tmp_path):
        """
        Test that CLI startup with a bot file doesn't attach proper callbacks.
        """
        # Create and save a bot
        bot = AnthropicBot(model_engine=Engines.CLAUDE45_SONNET)
        bot_file = tmp_path / "startup_bot.bot"
        bot.save(str(bot_file))

        # Initialize CLI with bot filename (simulates: python -m bots.dev startup_bot.bot)
        cli = CLI(bot_filename=str(bot_file))

        # Mock the run loop to just load and stop
        with patch.object(cli, "_initialize_new_bot"):
            with patch("builtins.input", side_effect=["/exit"]):
                with patch("bots.dev.cli.setup_raw_mode", return_value=None):
                    with patch("bots.dev.cli.restore_terminal"):
                        try:
                            cli.run()
                        except SystemExit:
                            pass

        # Check if callbacks were attached
        loaded_bot = cli.context.bot_instance
        if loaded_bot:
            callback_type = type(loaded_bot.callbacks).__name__
            assert isinstance(
                loaded_bot.callbacks, RealTimeDisplayCallbacks
            ), f"CLI-loaded bot should have RealTimeDisplayCallbacks, but has {callback_type}"
