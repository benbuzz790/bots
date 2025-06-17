"""Python File Writer Bot factory and configuration module.
This module provides a factory function and configuration for creating
specialized bot instances that write and test Python code. It encapsulates
bot initialization, tool configuration, and system message setup in a
reusable way.
Module Attributes:
    BOT_NAME (str): Name identifier for the bot instance ('Codey')
    BOT_ROLE (str): Role identifier for the bot ('File Writer')
    BOT_SAVE_PATH (str): Path where bot state is saved
    SYSTEM_MESSAGE (str): Configured system message for bot initialization
Tool Dependencies:
    - code_tools: For code manipulation operations
    - terminal_tools: For system operations
    - python_editing_tools: For Python-specific file operations
Use when you need to:
- Generate new Python files with corresponding tests
- Modify existing Python files while maintaining test coverage
- Ensure code changes meet specific requirements through testing
The bot's primary responsibilities include:
- Writing code based on specified requirements with type hints and docstrings
- Creating corresponding test files with appropriate test coverage
- Ensuring requirements are met through automated testing
- Using available tools flexibly for file manipulation
Note:
    This bot maintains state and saves it to disk. Each initialization will
    create a new state file at BOT_SAVE_PATH. The bot uses the Anthropic API
    and standard rate limits apply.
Performance Considerations:
    The bot maintains conversation history which can grow over time. For
    long-running sessions, consider creating new instances periodically to
    manage memory usage.
Example:
    >>> from bots.botlib.build_py_file_bot import create_file_writer_bot
    >>> bot = create_file_writer_bot()
    >>> bot.respond("Create a new utility function in utils.py")
Example:
    >>> (in terminal) python botlib/build_py_file_bot.py
    >>> from bots import load
    >>> bot = load('botlib/Codey@8Feb2025.bot')
"""

import textwrap
from typing import Final

import bots
from bots.foundation.base import Bot

# System message defining the bot's personality and operational guidelines
SYSTEM_MESSAGE: str = textwrap.dedent(
    """
    ## About you
    - You are a diligent coder named Codey.
    - You write code carefully, gathering necessary context, and ensuring
      requirements are both clearly delivered to you and met by your code.
    - Your goal is to implement a file to certain requirements, and to prove
      that those requirements are met with a separate test file.
    ## Tool Guidance
    You use your tools flexibly but precisely, for instance, using powershell
    if you do not have a necessary tool to modify a file.
    """
)
BOT_NAME: Final[str] = "Codey"
BOT_ROLE: Final[str] = "File Writer"
BOT_SAVE_PATH: Final[str] = "botlib/Codey@27May2025"


def create_file_writer_bot(autosave: bool = False) -> Bot:
    """Factory function that creates and configures a specialized Python
    file writer bot.
    Use when you need to create a new bot instance for writing and testing
    Python files. This factory function handles all aspects of bot
    configuration including:
    - Initializing the Anthropic bot with name and role
    - Setting up the system message for code writing behavior
    - Adding required tool sets (code, terminal, and Python editing tools)
    - Saving initial bot state
    - Configuring autosave behavior
    Args:
        autosave (bool, optional): Whether to enable automatic state saving.
            Defaults to False.
    Returns:
        Bot: Fully configured file writer bot instance with all necessary
            tools and settings. The returned bot is ready to handle Python
            file creation and testing tasks.
    Raises:
        ValueError: If required environment variables for API access are not
            set
        IOError: If unable to save initial bot state to disk
        ImportError: If required tool modules are not available
    Example:
        >>> bot = create_file_writer_bot(autosave=True)
        >>> bot.respond("Create a new class in models.py")
        >>> # Bot will create the file with proper documentation and tests
    """
    bot = bots.AnthropicBot(name=BOT_NAME, role=BOT_ROLE, autosave=autosave)
    bot.set_system_message(SYSTEM_MESSAGE)
    # Add required tool sets
    bot.add_tools(bots.tools.code_tools)
    bot.add_tools(bots.tools.terminal_tools)
    bot.add_tools(bots.tools.python_edit)
    # Save initial state
    bot.save(BOT_SAVE_PATH)
    return bot


if __name__ == "__main__":
    create_file_writer_bot()
