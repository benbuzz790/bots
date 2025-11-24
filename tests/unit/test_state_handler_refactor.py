"""Tests for StateHandler returning data instead of displaying directly."""

from unittest.mock import MagicMock, patch

from bots.dev.cli import CLIContext, EscapeException, StateHandler
from bots.foundation.base import Bot


class TestStateHandlerDataReturn:
    """Test that StateHandler returns structured data instead of displaying."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = StateHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.config = MagicMock()
        self.mock_context.config.width = 80
        self.mock_context.config.indent = 4

    @patch("bots.dev.cli.input_with_esc", return_value="test_bot")
    def test_save_returns_success_data(self, mock_input):
        """Save should return success data dict."""
        self.mock_bot.save = MagicMock()

        result = self.handler.save(self.mock_bot, self.mock_context, [])

        # Should return a dict with type and message
        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "test_bot.bot" in result["message"]
        assert "saved" in result["message"].lower()

    @patch("bots.dev.cli.input_with_esc", side_effect=Exception("ESC pressed"))
    def test_save_returns_cancel_data(self, mock_input):
        """Save cancellation should return cancel data dict."""
        # Patch to raise EscapeException
        with patch("bots.dev.cli.input_with_esc", side_effect=EscapeException("Cancelled")):
            result = self.handler.save(self.mock_bot, self.mock_context, [])

        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "cancel" in result["message"].lower()

    @patch("bots.dev.cli.input_with_esc", return_value="")
    def test_save_returns_error_for_empty_filename(self, mock_input):
        """Save with empty filename should return error data dict."""
        result = self.handler.save(self.mock_bot, self.mock_context, [])

        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "cancel" in result["message"].lower()

    @patch("bots.dev.cli.input_with_esc", return_value="test_bot")
    def test_save_returns_error_data_on_exception(self, mock_input):
        """Save exception should return error data dict."""
        self.mock_bot.save = MagicMock(side_effect=Exception("Save failed"))

        result = self.handler.save(self.mock_bot, self.mock_context, [])

        assert isinstance(result, dict)
        assert result["type"] == "error"
        assert "error" in result["message"].lower()

    @patch("glob.glob", return_value=["bot1.bot", "bot2.bot"])
    @patch("bots.dev.cli.input_with_esc", return_value="bot1.bot")
    @patch("os.path.exists", return_value=True)
    @patch("bots.foundation.base.Bot.load")
    @patch("builtins.print")
    def test_load_returns_success_data(self, mock_print, mock_bot_load, mock_exists, mock_input, mock_glob):
        """Load should return success data dict."""
        mock_loaded_bot = MagicMock(spec=Bot)
        mock_loaded_bot.conversation = MagicMock()
        mock_loaded_bot.conversation.replies = []
        mock_bot_load.return_value = mock_loaded_bot

        result = self.handler.load(self.mock_bot, self.mock_context, [])

        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "loaded" in result["message"].lower()
        assert "bot1.bot" in result["message"]

    @patch("glob.glob", return_value=[])
    @patch("bots.dev.cli.input_with_esc", side_effect=Exception("ESC"))
    @patch("builtins.print")
    def test_load_returns_cancel_data(self, mock_print, mock_input, mock_glob):
        """Load cancellation should return cancel data dict."""
        with patch("bots.dev.cli.input_with_esc", side_effect=EscapeException("Cancelled")):
            result = self.handler.load(self.mock_bot, self.mock_context, [])

        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "cancel" in result["message"].lower()

    @patch("glob.glob", return_value=[])
    @patch("bots.dev.cli.input_with_esc", return_value="")
    @patch("builtins.print")
    def test_load_returns_error_for_empty_filename(self, mock_print, mock_input, mock_glob):
        """Load with empty filename should return error data dict."""
        result = self.handler.load(self.mock_bot, self.mock_context, [])

        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "cancel" in result["message"].lower()

    @patch("os.path.exists", return_value=False)
    def test_load_bot_from_file_returns_error_for_missing_file(self, mock_exists):
        """Load missing file should return error data dict."""
        result = self.handler._load_bot_from_file("missing.bot", self.mock_context)

        assert isinstance(result, dict)
        assert result["type"] == "error"
        assert "not found" in result["message"].lower()

    @patch("os.path.exists", return_value=True)
    @patch("bots.foundation.base.Bot.load")
    def test_load_bot_from_file_returns_success_data(self, mock_bot_load, mock_exists):
        """Load existing file should return success data dict."""
        mock_loaded_bot = MagicMock(spec=Bot)
        mock_loaded_bot.conversation = MagicMock()
        mock_loaded_bot.conversation.replies = []
        mock_bot_load.return_value = mock_loaded_bot

        result = self.handler._load_bot_from_file("test.bot", self.mock_context)

        assert isinstance(result, dict)
        assert result["type"] == "system"
        assert "loaded" in result["message"].lower()


class TestCLIHandlesStateHandlerData:
    """Test that CLI._handle_command properly displays StateHandler data."""

    def setup_method(self):
        """Set up test fixtures."""
        from bots.dev.cli import CLI
        from bots.dev.cli_frontend import TerminalFrontend

        self.cli = CLI()
        self.mock_bot = MagicMock(spec=Bot)
        self.cli.context.bot_instance = self.mock_bot

        # Add frontend to context
        self.mock_frontend = MagicMock(spec=TerminalFrontend)
        self.cli.context.frontend = self.mock_frontend

    @patch("bots.dev.cli.input_with_esc", return_value="test")
    def test_cli_displays_save_success(self, mock_input):
        """CLI should use frontend to display save success."""
        self.mock_bot.save = MagicMock()

        self.cli._handle_command(self.mock_bot, "/save")

        # Frontend should have been called to display system message
        assert self.mock_frontend.display_system.called or self.mock_frontend.display_error.called

    @patch("glob.glob", return_value=["test.bot"])
    @patch("bots.dev.cli.input_with_esc", return_value="test.bot")
    @patch("os.path.exists", return_value=True)
    @patch("bots.foundation.base.Bot.load")
    @patch("builtins.print")
    def test_cli_displays_load_success(self, mock_print, mock_bot_load, mock_exists, mock_input, mock_glob):
        """CLI should use frontend to display load success."""
        mock_loaded_bot = MagicMock(spec=Bot)
        mock_loaded_bot.conversation = MagicMock()
        mock_loaded_bot.conversation.replies = []
        mock_bot_load.return_value = mock_loaded_bot

        self.cli._handle_command(self.mock_bot, "/load")

        # Frontend should have been called
        assert self.mock_frontend.display_system.called or self.mock_frontend.display_error.called
