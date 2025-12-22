"""Tests for CLI frontend abstraction.

NOTE: These tests are skipped when running with pytest-xdist because patching
builtins.input causes worker processes to crash. See TEST_PATCHING_HARD_WALL.md
for details.
"""

import sys
from unittest.mock import MagicMock, patch

import pytest

from bots.dev.cli_frontend import CLIFrontend, TerminalFrontend

# Skip all tests in this module when running with xdist
# Input patching is incompatible with xdist worker processes
pytestmark = pytest.mark.skipif(
    "xdist" in sys.modules, reason="Input patching incompatible with xdist workers - causes worker crashes"
)


class TestCLIFrontend:
    """Test the abstract CLIFrontend interface."""

    def test_is_abstract(self):
        """CLIFrontend cannot be instantiated directly."""
        with pytest.raises(TypeError):
            CLIFrontend()


class TestTerminalFrontend:
    """Test the TerminalFrontend implementation."""

    def setup_method(self):
        """Set up test fixtures."""
        # Create a mock config
        self.mock_config = MagicMock()
        self.mock_config.width = 80
        self.mock_config.indent = 4
        self.mock_config.verbose = False
        self.frontend = TerminalFrontend(self.mock_config)

    def test_initialization(self):
        """Frontend initializes with config."""
        assert self.frontend.config == self.mock_config

    @patch("builtins.print")
    def test_display_message_user(self, mock_print):
        """Display user message with correct formatting."""
        self.frontend.display_message("user", "Hello, bot!")
        # Verify print was called
        assert mock_print.called

    @patch("builtins.print")
    def test_display_message_assistant(self, mock_print):
        """Display assistant message with correct formatting."""
        self.frontend.display_message("assistant", "Hello, user!")
        # Verify print was called
        assert mock_print.called

    @patch("builtins.print")
    def test_display_system(self, mock_print):
        """Display system message."""
        self.frontend.display_system("System notification")
        # Verify print was called
        assert mock_print.called

    @patch("builtins.print")
    def test_display_error(self, mock_print):
        """Display error message."""
        self.frontend.display_error("Error occurred")
        # Verify print was called
        assert mock_print.called

    @patch("builtins.print")
    def test_display_metrics(self, mock_print):
        """Display metrics when verbose is on."""
        self.mock_config.verbose = True
        metrics = {"input_tokens": 100, "output_tokens": 50, "cost": 0.01, "duration": 1.5}
        self.frontend.display_metrics(metrics)
        # Verify print was called
        assert mock_print.called

    @patch("builtins.print")
    def test_display_metrics_not_verbose(self, mock_print):
        """Don't display metrics when verbose is off."""
        self.mock_config.verbose = False
        metrics = {"input_tokens": 100}
        self.frontend.display_metrics(metrics)
        # Should not print when not verbose
        assert not mock_print.called

    @patch("builtins.print")
    def test_display_tool_call(self, mock_print):
        """Display tool call."""
        self.frontend.display_tool_call("python_edit", {"file": "test.py"})
        # Verify print was called
        assert mock_print.called

    @patch("builtins.print")
    def test_display_tool_result(self, mock_print):
        """Display tool result."""
        self.frontend.display_tool_result("python_edit", "File edited successfully")
        # Verify print was called
        assert mock_print.called

    @patch("builtins.input", return_value="test input")
    def test_get_user_input(self, mock_input):
        """Get user input."""
        result = self.frontend.get_user_input(">>> ")
        assert result == "test input"
        assert mock_input.called
