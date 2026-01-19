"""Integration tests for CLI color configuration."""

import json
import os
import tempfile
from unittest.mock import patch

from bots.dev.cli import CLIConfig, _init_colors
from bots.dev.cli_frontend import TerminalFrontend
from bots.utils.terminal_utils import ColorScheme


class TestCLIConfigColor:
    """Test CLI configuration color settings."""

    def test_cli_config_default_color(self):
        """Test that default color mode is 'auto'."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_config.json")
            config = CLIConfig()
            config.config_file = config_file
            assert config.color == "auto"

    def test_cli_config_save_color(self):
        """Test saving color configuration."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_config.json")
            config = CLIConfig()
            config.config_file = config_file
            config.color = "never"
            config.save_config()

            # Verify file was created and contains color setting
            assert os.path.exists(config_file)
            with open(config_file, "r") as f:
                data = json.load(f)
            assert data["color"] == "never"

    def test_cli_config_load_color(self):
        """Test loading color configuration from file."""
        with tempfile.TemporaryDirectory() as tmpdir:
            config_file = os.path.join(tmpdir, "test_config.json")

            # Create config file with color setting
            config_data = {"color": "always", "verbose": True}
            with open(config_file, "w") as f:
                json.dump(config_data, f)

            # Load config
            config = CLIConfig()
            config.config_file = config_file
            config.load_config()

            assert config.color == "always"

    def test_cli_config_color_modes(self):
        """Test all valid color modes."""
        valid_modes = ["auto", "always", "never"]
        for mode in valid_modes:
            config = CLIConfig()
            config.color = mode
            assert config.color == mode


class TestInitColors:
    """Test color initialization function."""

    def test_init_colors_auto(self):
        """Test initializing colors with auto mode."""
        _init_colors("auto")
        # Colors should be initialized (exact values depend on terminal)
        from bots.dev import cli

        assert hasattr(cli, "COLOR_USER")
        assert hasattr(cli, "COLOR_BOT")

    def test_init_colors_always(self):
        """Test initializing colors with always mode."""
        _init_colors("always")
        from bots.dev import cli

        # Colors should be ANSI codes
        assert cli.COLOR_USER == "\033[36m"
        assert cli.COLOR_BOT == "\033[95m"
        assert cli.COLOR_RESET == "\033[0m"

    def test_init_colors_never(self):
        """Test initializing colors with never mode."""
        _init_colors("never")
        from bots.dev import cli

        # Colors should be empty strings
        assert cli.COLOR_USER == ""
        assert cli.COLOR_BOT == ""
        assert cli.COLOR_RESET == ""


class TestTerminalFrontendColor:
    """Test TerminalFrontend color handling."""

    def test_terminal_frontend_with_color_auto(self):
        """Test TerminalFrontend with auto color mode."""
        config = CLIConfig()
        config.color = "auto"
        frontend = TerminalFrontend(config)

        assert hasattr(frontend, "colors")
        assert isinstance(frontend.colors, ColorScheme)

    def test_terminal_frontend_with_color_always(self):
        """Test TerminalFrontend with always color mode."""
        config = CLIConfig()
        config.color = "always"
        frontend = TerminalFrontend(config)

        assert frontend.colors.enabled is True
        assert frontend.colors.USER == "\033[36m"

    def test_terminal_frontend_with_color_never(self):
        """Test TerminalFrontend with never color mode."""
        config = CLIConfig()
        config.color = "never"
        frontend = TerminalFrontend(config)

        assert frontend.colors.enabled is False
        assert frontend.colors.USER == ""

    def test_terminal_frontend_display_with_colors(self):
        """Test that display methods use color scheme."""
        config = CLIConfig()
        config.color = "always"
        config.verbose = True
        frontend = TerminalFrontend(config)

        # Test that colors are used in display methods
        with patch("builtins.print") as mock_print:
            frontend.display_system("Test message")
            # Verify print was called (actual output testing is complex)
            assert mock_print.called

    def test_terminal_frontend_display_without_colors(self):
        """Test that display methods work without colors."""
        config = CLIConfig()
        config.color = "never"
        config.verbose = True
        frontend = TerminalFrontend(config)

        with patch("builtins.print") as mock_print:
            frontend.display_system("Test message")
            assert mock_print.called


class TestEnvironmentVariables:
    """Test environment variable handling."""

    @patch.dict(os.environ, {"NO_COLOR": "1"})
    def test_no_color_environment_variable(self):
        """Test that NO_COLOR environment variable is respected."""
        from bots.utils.terminal_utils import supports_color

        assert supports_color() is False

    @patch.dict(os.environ, {"FORCE_COLOR": "1"})
    def test_force_color_environment_variable(self):
        """Test that FORCE_COLOR environment variable is respected."""
        from bots.utils.terminal_utils import supports_color

        assert supports_color() is True

    @patch.dict(os.environ, {"NO_COLOR": "1", "FORCE_COLOR": "1"})
    def test_no_color_takes_precedence(self):
        """Test that NO_COLOR takes precedence over FORCE_COLOR."""
        from bots.utils.terminal_utils import supports_color

        # NO_COLOR should take precedence
        assert supports_color() is False


class TestBackwardCompatibility:
    """Test backward compatibility with existing code."""

    def test_color_constants_exist(self):
        """Test that color constants are still available."""
        from bots.dev import cli

        # All legacy color constants should exist
        assert hasattr(cli, "COLOR_USER")
        assert hasattr(cli, "COLOR_BOT")
        assert hasattr(cli, "COLOR_TOOL_NAME")
        assert hasattr(cli, "COLOR_TOOL_RESULT")
        assert hasattr(cli, "COLOR_METRICS")
        assert hasattr(cli, "COLOR_SYSTEM")
        assert hasattr(cli, "COLOR_ERROR")
        assert hasattr(cli, "COLOR_RESET")
        assert hasattr(cli, "COLOR_BOLD")
        assert hasattr(cli, "COLOR_DIM")
        assert hasattr(cli, "COLOR_ASSISTANT")
        assert hasattr(cli, "COLOR_TOOL_REQUEST")

    def test_color_constants_are_strings(self):
        """Test that color constants are strings."""
        from bots.dev import cli

        assert isinstance(cli.COLOR_USER, str)
        assert isinstance(cli.COLOR_BOT, str)
        assert isinstance(cli.COLOR_RESET, str)

    def test_cli_frontend_color_constants_exist(self):
        """Test that cli_frontend color constants exist."""
        from bots.dev import cli_frontend

        assert hasattr(cli_frontend, "COLOR_USER")
        assert hasattr(cli_frontend, "COLOR_BOT")
        assert hasattr(cli_frontend, "COLOR_RESET")


class TestColorSchemeIntegration:
    """Test integration of ColorScheme with CLI components."""

    def test_color_scheme_in_terminal_frontend(self):
        """Test that TerminalFrontend uses ColorScheme correctly."""
        config = CLIConfig()
        config.color = "always"
        frontend = TerminalFrontend(config)

        # Verify color scheme is properly initialized
        assert frontend.colors.USER == "\033[36m"
        assert frontend.colors.BOT == "\033[95m"
        assert frontend.colors.SYSTEM == "\033[2m\033[33m"
        assert frontend.colors.ERROR == "\033[31m"

    def test_color_scheme_updates_on_config_change(self):
        """Test that color scheme can be updated."""
        config = CLIConfig()
        config.color = "always"
        frontend = TerminalFrontend(config)

        # Initially enabled
        assert frontend.colors.enabled is True

        # Update config and recreate frontend
        config.color = "never"
        frontend = TerminalFrontend(config)

        # Now disabled
        assert frontend.colors.enabled is False
