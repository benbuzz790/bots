"""Frontend abstraction for CLI interactions.
This module provides an abstract interface for CLI frontends, enabling
multiple presentation layers (terminal, GUI, web) to share the same
business logic and command handlers.
"""

from abc import ABC, abstractmethod
from typing import Any, Dict, Optional

# Color constants
COLOR_USER = "\033[36m"  # Cyan
COLOR_BOT = "\033[95m"  # Light Pink/Magenta
COLOR_TOOL_NAME = "\033[2m\033[33m"  # Dim Yellow
COLOR_TOOL_RESULT = "\033[2m\033[32m"  # Dim Green
COLOR_METRICS = "\033[2m\033[37m"  # Very Dim Gray
COLOR_SYSTEM = "\033[2m\033[33m"  # Dim Yellow
COLOR_ERROR = "\033[31m"  # Red
COLOR_RESET = "\033[0m"  # Reset
COLOR_BOLD = "\033[1m"  # Bold
COLOR_DIM = "\033[2m"  # Dim


class CLIFrontend(ABC):
    """Abstract base class for CLI frontends.
    Defines the interface that all frontends must implement. This enables
    multiple presentation layers (terminal, GUI, web, plugins) to work
    with the same command handlers and business logic.
    """

    @abstractmethod
    def display_message(self, role: str, content: str) -> None:
        """Display a conversation message.
        Args:
            role: The role of the message sender ('user', 'assistant', etc.)
            content: The message content to display
        """
        pass

    @abstractmethod
    def display_system(self, message: str) -> None:
        """Display a system message.
        Args:
            message: The system message to display
        """
        pass

    @abstractmethod
    def display_error(self, message: str) -> None:
        """Display an error message.
        Args:
            message: The error message to display
        """
        pass

    @abstractmethod
    def display_metrics(self, metrics: Dict[str, Any]) -> None:
        """Display API usage metrics.
        Args:
            metrics: Dictionary containing metrics data (tokens, cost, duration, etc.)
        """
        pass

    @abstractmethod
    def display_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """Display a tool being called.
        Args:
            name: Name of the tool being called
            args: Arguments passed to the tool
        """
        pass

    @abstractmethod
    def display_tool_result(self, name: str, result: str) -> None:
        """Display a tool execution result.
        Args:
            name: Name of the tool that was executed
            result: Result returned by the tool
        """
        pass

    @abstractmethod
    def get_user_input(self, prompt: str = ">>> ") -> str:
        """Get single-line input from user.
        Args:
            prompt: The prompt to display to the user
        Returns:
            The user's input as a string
        """
        pass

    @abstractmethod
    def get_multiline_input(self, prompt: str) -> str:
        """Get multi-line input from user.
        Args:
            prompt: The prompt to display to the user
        Returns:
            The user's multi-line input as a string
        """
        pass

    @abstractmethod
    def confirm(self, question: str) -> bool:
        """Ask user for yes/no confirmation.
        Args:
            question: The question to ask the user
        Returns:
            True if user confirms, False otherwise
        """
        pass


class TerminalFrontend(CLIFrontend):
    """Terminal-based frontend implementation.
    Implements the CLI frontend interface for terminal/console display,
    using ANSI color codes and standard input/output.
    """

    def __init__(self, config):
        """Initialize the terminal frontend.
        Args:
            config: CLIConfig instance with display settings
        """
        self.config = config

    def display_message(self, role: str, content: str) -> None:
        """Display a conversation message with role-appropriate formatting."""
        color = COLOR_USER if role == "user" else COLOR_BOT
        self._pretty(content, role, color)

    def display_system(self, message: str) -> None:
        """Display a system message."""
        self._pretty(message, "system", COLOR_SYSTEM)

    def display_error(self, message: str) -> None:
        """Display an error message."""
        self._pretty(message, "error", COLOR_ERROR)

    def display_metrics(self, metrics: Dict[str, Any]) -> None:
        """Display API usage metrics if verbose mode is on."""
        if not self.config.verbose:
            return
        # Format metrics
        total_tokens = metrics.get("input_tokens", 0) + metrics.get("output_tokens", 0)
        cost = metrics.get("cost", 0)
        duration = metrics.get("duration", 0)
        if total_tokens == 0 and cost == 0:
            return
        metrics_str = f"{total_tokens:,} | ${cost:.4f} | {duration:.2f}s"
        # Add session totals if available
        if "session_tokens" in metrics and "session_cost" in metrics:
            session_tokens = metrics["session_tokens"]
            session_cost = metrics["session_cost"]
            metrics_str += f"\n{session_tokens:,} | ${session_cost:.4f}"
        self._pretty(metrics_str, "metrics", COLOR_METRICS, newline_after_name=True)

    def display_tool_call(self, name: str, args: Dict[str, Any]) -> None:
        """Display a tool being called."""
        formatted_args = self._format_tool_data(args, color=COLOR_TOOL_NAME)
        self._pretty(formatted_args, name, COLOR_TOOL_NAME)

    def display_tool_result(self, name: str, result: str) -> None:
        """Display a tool execution result."""
        self._pretty(result, f"{name} result", COLOR_TOOL_RESULT)

    def get_user_input(self, prompt: str = ">>> ") -> str:
        """Get single-line input from user."""
        return input(f"{COLOR_USER}{prompt}{COLOR_RESET}").strip()

    def get_multiline_input(self, prompt: str) -> str:
        """Get multi-line input from user (until empty line)."""
        print(f"{COLOR_USER}{prompt}{COLOR_RESET}")
        lines = []
        while True:
            line = input()
            if not line:
                break
            lines.append(line)
        return "\n".join(lines)

    def confirm(self, question: str) -> bool:
        """Ask user for yes/no confirmation."""
        response = input(f"{COLOR_SYSTEM}{question} (y/n): {COLOR_RESET}").strip().lower()
        return response in ("y", "yes")

    def _pretty(
        self,
        string: str,
        name: Optional[str] = None,
        color: str = COLOR_RESET,
        newline_after_name: bool = False,
    ) -> None:
        """Print a string nicely formatted with color."""
        import textwrap

        print()
        if name is not None:
            if newline_after_name:
                prefix = f"{color}{COLOR_BOLD}{name}:{COLOR_RESET}\n{' ' * self.config.indent}{color}"
            else:
                prefix = f"{color}{COLOR_BOLD}{name}: {COLOR_RESET}{color}"
        else:
            prefix = color
        if not isinstance(string, str):
            string = str(string)
        # Safeguard: truncate very long strings
        max_length = 50000
        if len(string) > max_length:
            string = string[:max_length] + "\n... (output truncated)"
        # Quick path for simple strings
        if len(string) < 1000 and "\n" not in string:
            print(prefix + string + COLOR_RESET)
            print()
            return
        lines = string.split("\n")
        formatted_lines = []
        # Limit number of lines
        max_lines = 1000
        if len(lines) > max_lines:
            lines = lines[:max_lines]
            lines.append("... (output truncated)")
        for i, line in enumerate(lines):
            # Skip wrapping for very long lines
            if len(line) > 10000:
                if i == 0:
                    formatted_lines.append(prefix + line[:10000] + "... (line truncated)" + COLOR_RESET)
                else:
                    formatted_lines.append(
                        " " * self.config.indent + color + line[:10000] + "... (line truncated)" + COLOR_RESET
                    )
                continue
            if i == 0:
                initial_line = prefix + line + COLOR_RESET
                try:
                    wrapped = textwrap.wrap(
                        initial_line,
                        width=self.config.width,
                        subsequent_indent=" " * self.config.indent,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                except Exception:
                    wrapped = [initial_line]
            else:
                try:
                    wrapped = textwrap.wrap(
                        color + line + COLOR_RESET,
                        width=self.config.width,
                        initial_indent=" " * self.config.indent,
                        subsequent_indent=" " * self.config.indent,
                        break_long_words=True,
                        break_on_hyphens=False,
                    )
                except Exception:
                    wrapped = [" " * self.config.indent + color + line + COLOR_RESET]
            if wrapped:
                formatted_lines.extend(wrapped)
            else:
                formatted_lines.append(" " * self.config.indent if i > 0 else prefix + COLOR_RESET)
        for line in formatted_lines:
            print(line)
        print()

    def _format_tool_data(self, data: dict, indent: int = 4, color: str = COLOR_RESET) -> str:
        """Format tool arguments or results in a clean, minimal way."""
        if not data:
            return "(empty)"
        # Special case: single input - just show the value without the key
        if len(data) == 1:
            key, value = next(iter(data.items()))
            if isinstance(value, str):
                return "\n" + value
            elif isinstance(value, dict):
                return "\n" + self._format_tool_data(value, indent, color)
            else:
                return "\n" + str(value)
        # Multiple inputs - show key: value pairs
        lines = []
        for key, value in data.items():
            # Strip underscores from parameter names
            display_key = key.replace("_", " ")
            bold_key = f"{color}{COLOR_BOLD}{display_key}{COLOR_RESET}{color}:"
            if isinstance(value, dict):
                # Nested dict
                nested = self._format_tool_data(value, indent, color)
                lines.append(bold_key)
                for nested_line in nested.split("\n"):
                    if nested_line:
                        lines.append(" " * indent + nested_line)
            elif isinstance(value, str):
                # String value
                if "\n" in value:
                    lines.append(bold_key)
                    for line in value.split("\n"):
                        lines.append(" " * indent + line)
                else:
                    lines.append(f"{bold_key} {value}")
            elif isinstance(value, (list, tuple)):
                lines.append(f"{bold_key} {value}")
            else:
                lines.append(f"{bold_key} {value}")
        return "\n" + "\n".join(lines)
