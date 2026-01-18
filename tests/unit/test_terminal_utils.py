"""Tests for terminal capability detection and color configuration."""

import os
from unittest.mock import MagicMock, patch

from bots.utils.terminal_utils import (
    ColorScheme,
    TerminalCapabilities,
    create_color_scheme,
    detect_terminal_type,
    get_terminal_width,
    supports_color,
)


class TestTerminalCapabilities:
    """Test terminal capability detection."""

    def test_supports_color_force_never(self):
        """Test that force='never' disables colors."""
        caps = TerminalCapabilities()
        assert caps.supports_color(force="never") is False

    def test_supports_color_force_always(self):
        """Test that force='always' enables colors."""
        caps = TerminalCapabilities()
        assert caps.supports_color(force="always") is True

    @patch.dict(os.environ, {"NO_COLOR": "1"})
    def test_supports_color_no_color_env(self):
        """Test that NO_COLOR environment variable disables colors."""
        caps = TerminalCapabilities()
        assert caps.supports_color() is False

    @patch.dict(os.environ, {"FORCE_COLOR": "1"})
    def test_supports_color_force_color_env(self):
        """Test that FORCE_COLOR environment variable enables colors."""
        caps = TerminalCapabilities()
        # Should return True even if not a tty
        assert caps.supports_color() is True

    @patch.dict(os.environ, {"TERM": "dumb"})
    def test_supports_color_dumb_terminal(self):
        """Test that dumb terminal disables colors."""
        caps = TerminalCapabilities()
        with patch("sys.stdout.isatty", return_value=True):
            assert caps.supports_color() is False

    @patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True)
    def test_supports_color_with_term(self):
        """Test color support with TERM set and isatty."""
        caps = TerminalCapabilities()
        with patch("sys.stdout.isatty", return_value=True):
            assert caps.supports_color() is True

    def test_supports_color_not_tty(self):
        """Test that non-tty output disables colors."""
        caps = TerminalCapabilities()
        with patch("sys.stdout.isatty", return_value=False):
            with patch.dict(os.environ, {}, clear=True):
                assert caps.supports_color() is False

    def test_get_terminal_width_default(self):
        """Test terminal width with default fallback."""
        caps = TerminalCapabilities()
        width = caps.get_terminal_width(default=100)
        assert isinstance(width, int)
        assert width > 0

    def test_get_terminal_width_cached(self):
        """Test that terminal width is cached."""
        caps = TerminalCapabilities()
        width1 = caps.get_terminal_width()
        width2 = caps.get_terminal_width()
        assert width1 == width2

    @patch.dict(os.environ, {"TERM_PROGRAM": "vscode"})
    def test_detect_terminal_type_vscode(self):
        """Test detection of VS Code terminal."""
        caps = TerminalCapabilities()
        assert caps.detect_terminal_type() == "vscode"

    @patch.dict(os.environ, {"TERM": "xterm-256color"}, clear=True)
    def test_detect_terminal_type_term(self):
        """Test detection from TERM variable."""
        caps = TerminalCapabilities()
        assert caps.detect_terminal_type() == "xterm-256color"

    @patch("sys.platform", "win32")
    @patch.dict(os.environ, {}, clear=True)
    def test_detect_terminal_type_windows(self):
        """Test detection on Windows."""
        caps = TerminalCapabilities()
        assert caps.detect_terminal_type() == "windows"


class TestColorScheme:
    """Test color scheme management."""

    def test_color_scheme_enabled(self):
        """Test color scheme with colors enabled."""
        scheme = ColorScheme(enabled=True)
        assert scheme.enabled is True
        assert scheme.USER == "\033[36m"
        assert scheme.BOT == "\033[95m"
        assert scheme.ERROR == "\033[31m"
        assert scheme.RESET == "\033[0m"

    def test_color_scheme_disabled(self):
        """Test color scheme with colors disabled."""
        scheme = ColorScheme(enabled=False)
        assert scheme.enabled is False
        assert scheme.USER == ""
        assert scheme.BOT == ""
        assert scheme.ERROR == ""
        assert scheme.RESET == ""

    def test_color_scheme_enable(self):
        """Test enabling colors on a disabled scheme."""
        scheme = ColorScheme(enabled=False)
        assert scheme.USER == ""
        scheme.enable()
        assert scheme.enabled is True
        assert scheme.USER == "\033[36m"

    def test_color_scheme_disable(self):
        """Test disabling colors on an enabled scheme."""
        scheme = ColorScheme(enabled=True)
        assert scheme.USER == "\033[36m"
        scheme.disable()
        assert scheme.enabled is False
        assert scheme.USER == ""

    def test_color_scheme_legacy_compatibility(self):
        """Test that legacy color names are available."""
        scheme = ColorScheme(enabled=True)
        assert scheme.ASSISTANT == scheme.BOT
        assert scheme.TOOL_REQUEST == "\033[34m"


class TestModuleFunctions:
    """Test module-level convenience functions."""

    def test_supports_color_function(self):
        """Test supports_color convenience function."""
        result = supports_color(force="always")
        assert result is True

    def test_get_terminal_width_function(self):
        """Test get_terminal_width convenience function."""
        width = get_terminal_width(default=120)
        assert isinstance(width, int)
        assert width > 0

    def test_detect_terminal_type_function(self):
        """Test detect_terminal_type convenience function."""
        term_type = detect_terminal_type()
        assert isinstance(term_type, str)

    def test_create_color_scheme_auto(self):
        """Test creating color scheme with auto detection."""
        scheme = create_color_scheme(force=None)
        assert isinstance(scheme, ColorScheme)

    def test_create_color_scheme_always(self):
        """Test creating color scheme with force=always."""
        scheme = create_color_scheme(force="always")
        assert scheme.enabled is True
        assert scheme.USER == "\033[36m"

    def test_create_color_scheme_never(self):
        """Test creating color scheme with force=never."""
        scheme = create_color_scheme(force="never")
        assert scheme.enabled is False
        assert scheme.USER == ""


class TestWindowsSupport:
    """Test Windows-specific terminal support."""

    @patch("sys.platform", "win32")
    @patch.dict(os.environ, {"WT_SESSION": "some-session-id"})
    def test_windows_terminal_support(self):
        """Test Windows Terminal detection."""
        caps = TerminalCapabilities()
        with patch("sys.stdout.isatty", return_value=True):
            assert caps.supports_color() is True

    @patch("sys.platform", "win32")
    @patch.dict(os.environ, {"TERM_PROGRAM": "vscode"})
    def test_vscode_on_windows_support(self):
        """Test VS Code terminal on Windows."""
        caps = TerminalCapabilities()
        with patch("sys.stdout.isatty", return_value=True):
            assert caps.supports_color() is True


class TestEdgeCases:
    """Test edge cases and error handling."""

    def test_terminal_width_exception_handling(self):
        """Test that terminal width handles exceptions gracefully."""
        caps = TerminalCapabilities()
        with patch("shutil.get_terminal_size", side_effect=Exception("Test error")):
            width = caps.get_terminal_width(default=80)
            assert width == 80

    def test_color_scheme_all_colors_defined(self):
        """Test that all expected color attributes are defined."""
        scheme = ColorScheme(enabled=True)
        expected_attrs = [
            "USER",
            "BOT",
            "TOOL_NAME",
            "TOOL_RESULT",
            "METRICS",
            "SYSTEM",
            "ERROR",
            "RESET",
            "BOLD",
            "DIM",
            "ASSISTANT",
            "TOOL_REQUEST",
        ]
        for attr in expected_attrs:
            assert hasattr(scheme, attr), f"Missing attribute: {attr}"
            assert isinstance(getattr(scheme, attr), str)

    def test_supports_color_no_isatty_attribute(self):
        """Test handling when stdout has no isatty attribute."""
        caps = TerminalCapabilities()
        mock_stdout = MagicMock(spec=[])  # No isatty attribute
        with patch("sys.stdout", mock_stdout):
            with patch.dict(os.environ, {}, clear=True):
                assert caps.supports_color() is False
