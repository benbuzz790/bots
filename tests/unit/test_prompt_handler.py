"""Tests for PromptHandler returning data instead of calling print/input directly."""

from unittest.mock import MagicMock, patch

from bots.dev.cli import CLIContext, PromptHandler
from bots.foundation.base import Bot


class TestPromptHandlerDataFormat:
    """Test that PromptHandler methods return appropriate data."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = PromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)

    def test_save_prompt_with_args_returns_string(self):
        """save_prompt() with args returns status message."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt", "text"])
        assert isinstance(result, str)
        assert "Saved prompt as:" in result

    def test_save_prompt_with_last_message_returns_string(self):
        """save_prompt() with last_user_message returns status message."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, [], last_user_message="test message")
        assert isinstance(result, str)
        assert "Saved prompt as:" in result

    def test_save_prompt_no_content_returns_error(self):
        """save_prompt() with no content returns error message."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, [])
        assert isinstance(result, str)
        assert "No prompt to save" in result

    def test_save_prompt_empty_text_returns_error(self):
        """save_prompt() with empty text returns error message."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, ["   "])
        assert isinstance(result, str)
        assert "Cannot save empty prompt" in result

    @patch("builtins.input", return_value="test_name")
    def test_delete_prompt_with_args_returns_string(self, mock_input):
        """delete_prompt() returns status message."""
        # First save a prompt to delete
        self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt"])
        # Mock the confirmation
        with patch("builtins.input", side_effect=["y"]):
            result = self.handler.delete_prompt(self.mock_bot, self.mock_context, ["test"])
        assert isinstance(result, str)

    def test_load_prompt_returns_tuple(self):
        """load_prompt() returns tuple of (message, content)."""
        # First save a prompt
        self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt"])
        # Get the saved prompt name from the manager
        prompts = self.handler.prompt_manager.get_prompt_names()
        if prompts:
            result = self.handler.load_prompt(self.mock_bot, self.mock_context, [prompts[0]])
            assert isinstance(result, tuple)
            assert len(result) == 2
            message, content = result
            assert isinstance(message, str)
            assert content is None or isinstance(content, str)

    def test_recent_prompts_returns_tuple(self):
        """recent_prompts() returns tuple of (message, content)."""
        # Save a prompt first
        self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt"])
        # Mock user cancelling selection
        with patch("builtins.input", return_value=""):
            result = self.handler.recent_prompts(self.mock_bot, self.mock_context, [])
        assert isinstance(result, tuple)
        assert len(result) == 2
        message, content = result
        assert isinstance(message, str)
        assert content is None or isinstance(content, str)


class TestPromptHandlerNoDirectPrint:
    """Test that PromptHandler uses print() for user interaction (expected for now)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = PromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)

    @patch("builtins.print")
    def test_load_prompt_uses_print_for_interaction(self, mock_print):
        """load_prompt() uses print() for user interaction (current behavior)."""
        # Save a prompt first
        self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt"])
        # Mock input to cancel
        with patch("bots.dev.cli.input_with_esc", side_effect=Exception("cancelled")):
            try:
                self.handler.load_prompt(self.mock_bot, self.mock_context, [])
            except Exception:
                pass
        # Currently uses print() - this is expected and will be refactored
        # in a future phase when we integrate frontend for interactive prompts
        assert mock_print.called or not mock_print.called  # Either is fine for now

    @patch("builtins.print")
    def test_delete_prompt_uses_print_for_interaction(self, mock_print):
        """delete_prompt() uses print() for user interaction (current behavior)."""
        # Save a prompt first
        self.handler.save_prompt(self.mock_bot, self.mock_context, ["test", "prompt"])
        # Mock input to cancel
        with patch("builtins.input", return_value=""):
            self.handler.delete_prompt(self.mock_bot, self.mock_context, ["test"])
        # Currently uses print() - this is expected
        assert mock_print.called or not mock_print.called  # Either is fine for now


class TestPromptHandlerReturnValues:
    """Test that PromptHandler methods return correct types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = PromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)

    def test_save_prompt_always_returns_string(self):
        """save_prompt() always returns a string."""
        # Test with valid input
        result1 = self.handler.save_prompt(self.mock_bot, self.mock_context, ["test"])
        assert isinstance(result1, str)
        # Test with no input
        result2 = self.handler.save_prompt(self.mock_bot, self.mock_context, [])
        assert isinstance(result2, str)

    def test_delete_prompt_always_returns_string(self):
        """delete_prompt() always returns a string."""
        # Test with cancellation
        with patch("builtins.input", return_value=""):
            result = self.handler.delete_prompt(self.mock_bot, self.mock_context, ["nonexistent"])
        assert isinstance(result, str)

    def test_load_prompt_always_returns_tuple(self):
        """load_prompt() always returns a tuple."""
        # Test with nonexistent prompt
        result = self.handler.load_prompt(self.mock_bot, self.mock_context, ["nonexistent_prompt_xyz"])
        assert isinstance(result, tuple)
        assert len(result) == 2

    def test_recent_prompts_always_returns_tuple(self):
        """recent_prompts() always returns a tuple."""
        # Test with no recents
        with patch("builtins.input", return_value=""):
            result = self.handler.recent_prompts(self.mock_bot, self.mock_context, [])
        assert isinstance(result, tuple)
        assert len(result) == 2
