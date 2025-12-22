"""Tests for PromptHandler returning data instead of calling print/input directly.

NOTE: These tests are skipped when running with pytest-xdist because patching
builtins.input causes worker processes to crash. See TEST_PATCHING_HARD_WALL.md
for details.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from bots.dev.cli import CLIContext, PromptHandler
from bots.foundation.base import Bot

# Skip all tests in this module when running with xdist
# Input patching is incompatible with xdist worker processes
pytestmark = pytest.mark.skipif(
    "xdist" in sys.modules, reason="Input patching incompatible with xdist workers - causes worker crashes"
)


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
        assert "No prompt content" in result

    @patch("builtins.input", return_value="test_name")
    def test_load_prompt_returns_tuple(self, mock_input):
        """load_prompt() returns tuple of (prompt_text, should_execute)."""
        # Mock the prompt manager to return a prompt
        self.mock_context.prompt_manager = MagicMock()
        self.mock_context.prompt_manager.load_prompt.return_value = "test prompt text"
        result = self.handler.load_prompt(self.mock_bot, self.mock_context, ["test_name"])
        assert isinstance(result, tuple)
        assert len(result) == 2
        prompt_text, should_execute = result
        assert isinstance(prompt_text, str)
        assert isinstance(should_execute, bool)

    def test_delete_prompt_returns_string(self):
        """delete_prompt() returns status message."""
        self.mock_context.prompt_manager = MagicMock()
        self.mock_context.prompt_manager.delete_prompt.return_value = True
        result = self.handler.delete_prompt(self.mock_bot, self.mock_context, ["test_name"])
        assert isinstance(result, str)

    @patch("builtins.input", return_value="1")
    def test_recent_prompts_returns_tuple(self, mock_input):
        """recent_prompts() returns tuple of (prompt_text, should_execute)."""
        self.mock_context.prompt_manager = MagicMock()
        self.mock_context.prompt_manager.get_recents.return_value = [("test_name", "test prompt")]
        result = self.handler.recent_prompts(self.mock_bot, self.mock_context, [])
        assert isinstance(result, tuple)
        assert len(result) == 2


class TestPromptHandlerReturnValues:
    """Test that methods always return expected types."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = PromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.prompt_manager = MagicMock()

    def test_save_prompt_always_returns_string(self):
        """save_prompt() always returns a string."""
        result = self.handler.save_prompt(self.mock_bot, self.mock_context, ["test"])
        assert isinstance(result, str)

    def test_delete_prompt_always_returns_string(self):
        """delete_prompt() always returns a string."""
        self.mock_context.prompt_manager.delete_prompt.return_value = False
        result = self.handler.delete_prompt(self.mock_bot, self.mock_context, ["nonexistent"])
        assert isinstance(result, str)

    @patch("builtins.input", return_value="")
    def test_load_prompt_cancelled_returns_tuple(self, mock_input):
        """load_prompt() returns tuple even when cancelled."""
        result = self.handler.load_prompt(self.mock_bot, self.mock_context, [])
        assert isinstance(result, tuple)
        assert len(result) == 2

    @patch("builtins.input", return_value="")
    def test_recent_prompts_always_returns_tuple(self, mock_input):
        """recent_prompts() always returns a tuple."""
        self.mock_context.prompt_manager.get_recents.return_value = []
        result = self.handler.recent_prompts(self.mock_bot, self.mock_context, [])
        assert isinstance(result, tuple)
        assert len(result) == 2
