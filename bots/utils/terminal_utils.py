"""Terminal capability detection and color configuration utilities.

This module provides utilities for detecting terminal capabilities and
managing color output across different terminal environments.

Standards supported:
- NO_COLOR: https://no-color.org/
- FORCE_COLOR: Common in CI/CD environments
- GNU conventions: --color=auto|always|never
"""

import os
import sys
from typing import Optional


class TerminalCapabilities:
    """Detects and manages terminal capabilities."""

    def __init__(self):
        """Initialize terminal capability detection."""
        self._color_support = None
        self._width = None

    def supports_color(self, force: Optional[str] = None) -> bool:
        """Detect if terminal supports color output.

        Args:
            force: Override detection with 'always', 'never', or 'auto'

        Returns:
            True if colors should be used, False otherwise
        """
        # Handle forced color mode
        if force == "never":
            return False
        if force == "always":
            return True

        # Respect NO_COLOR standard (https://no-color.org/)
        if os.getenv("NO_COLOR"):
            return False

        # Force color if requested (common in CI/CD)
        if os.getenv("FORCE_COLOR"):
            return True

        # Check if output is to a terminal
        if not hasattr(sys.stdout, "isatty") or not sys.stdout.isatty():
            return False

        # Check TERM environment variable
        term = os.getenv("TERM", "")
        if term == "dumb":
            return False

        # Windows-specific checks
        if sys.platform == "win32":
            # Windows 10+ supports ANSI colors
            # Check for Windows Terminal, VS Code, or modern console
            wt_session = os.getenv("WT_SESSION")
            term_program = os.getenv("TERM_PROGRAM")
            if wt_session or term_program in ("vscode", "Windows Terminal"):
                return True
            # Try to enable ANSI support on Windows
            try:
                import ctypes

                kernel32 = ctypes.windll.kernel32
                # Enable ANSI escape sequence processing
                kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
                return True
            except Exception:
                # Fall back to no color on older Windows
                return False

        # Unix-like systems: if we have a TERM and isatty, assume color support
        return bool(term)

    def get_terminal_width(self, default: int = 160) -> int:
        """Get terminal width in characters.

        Args:
            default: Default width if detection fails

        Returns:
            Terminal width in characters
        """
        if self._width is not None:
            return self._width

        # Try to get terminal size
        try:
            import shutil

            size = shutil.get_terminal_size(fallback=(default, 24))
            self._width = size.columns
            return self._width
        except Exception:
            self._width = default
            return default

    def detect_terminal_type(self) -> str:
        """Detect the type of terminal being used.

        Returns:
            String identifying terminal type (e.g., 'xterm', 'windows', 'vscode')
        """
        # Check for specific terminal programs
        term_program = os.getenv("TERM_PROGRAM", "")
        if term_program:
            return term_program.lower()

        # Check TERM variable
        term = os.getenv("TERM", "")
        if term:
            return term.lower()

        # Platform fallback
        if sys.platform == "win32":
            return "windows"

        return "unknown"


class ColorScheme:
    """Manages color codes for terminal output."""

    def __init__(self, enabled: bool = True):
        """Initialize color scheme.

        Args:
            enabled: Whether colors are enabled
        """
        self.enabled = enabled
        self._init_colors()

    def _init_colors(self):
        """Initialize color codes based on enabled state."""
        if self.enabled:
            # Standard ANSI colors
            self.USER = "\033[36m"  # Cyan
            self.BOT = "\033[95m"  # Light Pink/Magenta
            self.TOOL_NAME = "\033[2m\033[33m"  # Dim Yellow
            self.TOOL_RESULT = "\033[2m\033[32m"  # Dim Green
            self.METRICS = "\033[2m\033[37m"  # Very Dim Gray
            self.SYSTEM = "\033[2m\033[33m"  # Dim Yellow
            self.ERROR = "\033[31m"  # Red
            self.RESET = "\033[0m"  # Reset
            self.BOLD = "\033[1m"  # Bold
            self.DIM = "\033[2m"  # Dim

            # Legacy compatibility
            self.ASSISTANT = self.BOT
            self.TOOL_REQUEST = "\033[34m"  # Blue
        else:
            # No colors - all empty strings
            self.USER = ""
            self.BOT = ""
            self.TOOL_NAME = ""
            self.TOOL_RESULT = ""
            self.METRICS = ""
            self.SYSTEM = ""
            self.ERROR = ""
            self.RESET = ""
            self.BOLD = ""
            self.DIM = ""
            self.ASSISTANT = ""
            self.TOOL_REQUEST = ""

    def enable(self):
        """Enable colors."""
        self.enabled = True
        self._init_colors()

    def disable(self):
        """Disable colors."""
        self.enabled = False
        self._init_colors()


# Global terminal capabilities instance
_terminal_capabilities = TerminalCapabilities()


def supports_color(force: Optional[str] = None) -> bool:
    """Check if terminal supports color output.

    Args:
        force: Override detection with 'always', 'never', or 'auto'

    Returns:
        True if colors should be used, False otherwise
    """
    return _terminal_capabilities.supports_color(force)


def get_terminal_width(default: int = 160) -> int:
    """Get terminal width in characters.

    Args:
        default: Default width if detection fails

    Returns:
        Terminal width in characters
    """
    return _terminal_capabilities.get_terminal_width(default)


def detect_terminal_type() -> str:
    """Detect the type of terminal being used.

    Returns:
        String identifying terminal type
    """
    return _terminal_capabilities.detect_terminal_type()


def create_color_scheme(force: Optional[str] = None) -> ColorScheme:
    """Create a color scheme based on terminal capabilities.

    Args:
        force: Override detection with 'always', 'never', or 'auto'

    Returns:
        ColorScheme instance with appropriate colors
    """
    enabled = supports_color(force)
    return ColorScheme(enabled)
