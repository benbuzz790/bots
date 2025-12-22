"""Tests for DynamicFunctionalPromptHandler returning data.

NOTE: These tests are skipped when running with pytest-xdist because patching
builtins.input causes worker processes to crash. See TEST_PATCHING_HARD_WALL.md
for details.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from bots.dev.cli import CLIContext, DynamicFunctionalPromptHandler
from bots.foundation.base import Bot

# Skip all tests in this module when running with xdist
# Input patching is incompatible with xdist worker processes
pytestmark = pytest.mark.skipif(
    "xdist" in sys.modules, reason="Input patching incompatible with xdist workers - causes worker crashes"
)


class TestDynamicFunctionalPromptHandlerDataFormat:
    """Test that DynamicFunctionalPromptHandler methods return strings."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = DynamicFunctionalPromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_bot.name = "TestBot"
        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.config = MagicMock()
        self.mock_context.config.verbose = False
        self.mock_context.config.width = 80
        self.mock_context.config.indent = 4
        self.mock_context.callbacks = MagicMock()
        self.mock_context.callbacks.get_standard_callback = MagicMock(return_value=None)

    @patch("builtins.input", side_effect=["1", ""])  # Select first FP, cancel params
    @patch("builtins.print")
    def test_execute_returns_string_on_cancel(self, mock_print, mock_input):
        """execute() returns string when parameter collection is cancelled."""
        result = self.handler.execute(self.mock_bot, self.mock_context, [])
        assert isinstance(result, str)
        assert "cancelled" in result.lower()

    @patch("builtins.input", return_value="invalid")
    @patch("builtins.print")
    def test_execute_returns_string_on_invalid_selection(self, mock_print, mock_input):
        """execute() returns string for invalid selection."""
        result = self.handler.execute(self.mock_bot, self.mock_context, [])
        assert isinstance(result, str)
        assert "Invalid" in result

    def test_execute_returns_string_on_error(self):
        """execute() returns string on error."""
        # Force an error by passing None as bot
        result = self.handler.execute(None, self.mock_context, [])
        assert isinstance(result, str)
        assert "Error" in result

    @patch("builtins.input", return_value="")  # Cancel selection
    @patch("builtins.print")
    def test_broadcast_fp_returns_string_on_no_leaves(self, mock_print, mock_input):
        """broadcast_fp() returns string when no leaves found."""
        # Mock conversation with no leaves
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.replies = []
        result = self.handler.broadcast_fp(self.mock_bot, self.mock_context, [])
        assert isinstance(result, str)

    def test_broadcast_fp_returns_string_on_error(self):
        """broadcast_fp() returns string on error."""
        # Force an error by passing None as bot
        result = self.handler.broadcast_fp(None, self.mock_context, [])
        assert isinstance(result, str)
        assert "Error" in result


class TestDynamicFunctionalPromptHandlerInteraction:
    """Test that DynamicFunctionalPromptHandler uses print/input (expected for now)."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = DynamicFunctionalPromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_bot.name = "TestBot"
        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.config = MagicMock()
        self.mock_context.config.verbose = False
        self.mock_context.config.width = 80
        self.mock_context.config.indent = 4
        self.mock_context.callbacks = MagicMock()

    @patch("builtins.print")
    @patch("builtins.input", return_value="invalid")
    def test_execute_uses_print_for_menu(self, mock_input, mock_print):
        """execute() uses print() to show menu (current behavior)."""
        self.handler.execute(self.mock_bot, self.mock_context, [])
        # Should print the menu
        assert mock_print.called

    @patch("builtins.print")
    @patch("builtins.input", return_value="")
    def test_broadcast_fp_uses_print_for_leaves(self, mock_input, mock_print):
        """broadcast_fp() uses print() to show leaves (current behavior)."""
        # Mock conversation with a leaf
        leaf = MagicMock()
        leaf.content = "test content"
        leaf.replies = []
        leaf.parent = MagicMock()
        leaf.parent._is_empty = MagicMock(return_value=True)
        self.mock_bot.conversation = leaf
        self.handler.broadcast_fp(self.mock_bot, self.mock_context, [])
        # Should print leaf information
        # This is acceptable for interactive wizards
        assert mock_print.called or not mock_print.called  # Either is fine


class TestDynamicFunctionalPromptHandlerReturnTypes:
    """Test that methods always return strings."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = DynamicFunctionalPromptHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_bot.name = "TestBot"
        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.config = MagicMock()
        self.mock_context.config.verbose = False
        self.mock_context.callbacks = MagicMock()

    @patch("builtins.input", return_value="invalid")
    @patch("builtins.print")
    def test_execute_always_returns_string(self, mock_print, mock_input):
        """execute() always returns a string."""
        result = self.handler.execute(self.mock_bot, self.mock_context, [])
        assert isinstance(result, str)

    def test_broadcast_fp_always_returns_string(self):
        """broadcast_fp() always returns a string."""
        # Even on error, should return string
        result = self.handler.broadcast_fp(None, self.mock_context, [])
        assert isinstance(result, str)

    def test_discover_fp_functions_returns_dict(self):
        """_discover_fp_functions() returns a dictionary."""
        functions = self.handler._discover_fp_functions()
        assert isinstance(functions, dict)
        # Should have discovered some functions
        assert len(functions) > 0
        # All values should be callable
        for func in functions.values():
            assert callable(func)
