"""Tests for CLI frontend abstraction."""

from unittest.mock import MagicMock, patch

import pytest

from bots.dev.cli_frontend import CLIFrontend, TerminalFrontend


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

    @patch("builtins.input", side_effect=["line 1", "line 2", ""])
    def test_get_multiline_input(self, mock_input):
        """Get multiline input."""
        result = self.frontend.get_multiline_input("Enter text:")
        # Should collect lines until empty line
        assert "line 1" in result
        assert "line 2" in result

    @patch("builtins.input", return_value="y")
    def test_confirm_yes(self, mock_input):
        """Confirm returns True for yes."""
        result = self.frontend.confirm("Continue?")
        assert result is True

    @patch("builtins.input", return_value="n")
    def test_confirm_no(self, mock_input):
        """Confirm returns False for no."""
        result = self.frontend.confirm("Continue?")
        assert result is False

    @patch("builtins.input", return_value="yes")
    def test_confirm_yes_variants(self, mock_input):
        """Confirm accepts yes variants."""
        result = self.frontend.confirm("Continue?")
        assert result is True

    @patch("builtins.input", return_value="invalid")
    def test_confirm_invalid_defaults_no(self, mock_input):
        """Confirm defaults to False for invalid input."""
        result = self.frontend.confirm("Continue?")
        assert result is False


class TestMockFrontend:
    """Test that a mock frontend can be created for testing handlers."""

    def test_mock_frontend_creation(self):
        """Can create a mock frontend for handler testing."""
        mock_frontend = MagicMock(spec=CLIFrontend)
        # Verify it has the required methods
        assert hasattr(mock_frontend, "display_message")
        assert hasattr(mock_frontend, "display_system")
        assert hasattr(mock_frontend, "display_error")
        assert hasattr(mock_frontend, "get_user_input")
