"""
Shared utilities for CLI operations.
This module contains utility functions and constants used across CLI handlers.
"""

import platform
import sys
from typing import List

from bots.foundation.base import ConversationNode

# Platform-specific imports
if platform.system() == "Windows":
    import msvcrt
else:
    import select
    import termios
    import tty
# Color constants - TODO: Make these configurable (issue #166)
COLOR_USER = "\033[36m"  # Cyan (not dim)
COLOR_BOT = "\033[95m"  # Light Pink/Magenta
COLOR_TOOL_NAME = "\033[2m\033[33m"  # Dim Yellow
COLOR_TOOL_RESULT = "\033[2m\033[32m"  # Dim Green
COLOR_METRICS = "\033[2m\033[37m"  # Very Dim Gray
COLOR_SYSTEM = "\033[2m\033[33m"  # Dim Yellow
COLOR_ERROR = "\033[31m"  # Red
COLOR_RESET = "\033[0m"  # Reset
COLOR_BOLD = "\033[1m"  # Bold
COLOR_DIM = "\033[2m"  # Dim
# Legacy colors for compatibility
COLOR_ASSISTANT = COLOR_BOT
COLOR_TOOL_REQUEST = "\033[34m"  # Blue


class EscapeException(Exception):
    """Exception raised when user presses ESC to cancel input."""

    pass


def input_with_esc(prompt: str = "") -> str:
    """
    Get user input with ESC key support to cancel/interrupt.
    Args:
        prompt: The prompt string to display
    Returns:
        The user's input string
    Raises:
        EscapeException: If user presses ESC key
    """
    if platform.system() == "Windows":
        # Windows implementation
        print(prompt, end="", flush=True)
        chars = []
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\x1b":  # ESC key
                    print()  # New line
                    raise EscapeException("Input cancelled by ESC key")
                elif char == b"\r":  # Enter key
                    print()  # New line
                    return "".join(chars)
                elif char == b"\x08":  # Backspace
                    if chars:
                        chars.pop()
                        # Erase character on screen
                        print("\b \b", end="", flush=True)
                elif char == b"\x03":  # Ctrl+C
                    print()
                    raise KeyboardInterrupt()
                else:
                    try:
                        decoded = char.decode("utf-8")
                        chars.append(decoded)
                        print(decoded, end="", flush=True)
                    except UnicodeDecodeError:
                        pass
    else:
        # Unix/Linux/Mac implementation
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            print(prompt, end="", flush=True)
            chars = []
            while True:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)
                    if char == "\x1b":  # ESC key
                        print("\r\n", end="", flush=True)
                        raise EscapeException("Input cancelled by ESC key")
                    elif char == "\r" or char == "\n":  # Enter key
                        print("\r\n", end="", flush=True)
                        return "".join(chars)
                    elif char == "\x7f":  # Backspace/Delete
                        if chars:
                            chars.pop()
                            print("\b \b", end="", flush=True)
                    elif char == "\x03":  # Ctrl+C
                        print("\r\n", end="", flush=True)
                        raise KeyboardInterrupt()
                    elif ord(char) >= 32:  # Printable characters
                        chars.append(char)
                        print(char, end="", flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def find_leaves(node: ConversationNode) -> List[ConversationNode]:
    """Recursively find all leaf nodes from a given node.
    Args:
        node: The starting conversation node
    Returns:
        List of leaf nodes (nodes with no replies)
    """
    leaves = []

    def dfs(current_node):
        if not current_node.replies:  # This is a leaf
            leaves.append(current_node)
        else:
            for reply in current_node.replies:
                dfs(reply)

    dfs(node)
    return leaves


def check_for_interrupt() -> bool:
    """Check if user pressed Escape without blocking execution."""
    if platform.system() == "Windows":
        if msvcrt.kbhit():
            key = msvcrt.getch()
            return key == b"\x1b"  # ESC key
        return False
    else:
        if select.select([sys.stdin], [], [], 0.0)[0]:
            key = sys.stdin.read(1)
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)
            return key == "\x1b"  # ESC key
        return False


def setup_raw_mode():
    """Set up terminal for raw input mode on Unix systems."""
    if platform.system() != "Windows":
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return old_settings


def restore_terminal(old_settings):
    """Restore terminal settings on Unix systems."""
    if platform.system() != "Windows" and old_settings is not None:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
