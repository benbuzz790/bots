import json
import os
import shutil
import sys
import tempfile
import unittest
from unittest.mock import patch

import pytest

import bots.tools.python_editing_tools as python_editing_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines

"""Test suite for AnthropicBot save and load functionality.

This module contains comprehensive tests for verifying the persistence
and restoration capabilities of AnthropicBot instances. It tests:

- Basic bot attribute persistence (name, model, settings)
- Conversation history preservation
- Tool configuration and execution state
- Custom attribute handling
- Error cases and edge conditions
- Working directory independence
- Multiple save/load cycles

The test suite ensures that bots can be properly serialized and
deserialized while maintaining their complete state and functionality.
"""


def simple_addition(x, y) -> str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))


class TestSaveLoadAnthropic(unittest.TestCase):
    """Test suite for AnthropicBot save and load functionality.

    This test suite verifies the complete serialization and deserialization
    capabilities of AnthropicBot instances. It ensures that all bot state
    is properly preserved across save/load operations.

    Attributes:
        temp_dir (str): Temporary directory path for test file operations
        bot (AnthropicBot): Test bot instance with Claude 3.5 Sonnet configuration

    Test Categories:
        - Basic Persistence: Core bot attribute preservation
        - Conversation: Chat history and structure preservation
        - Tools: Tool configuration and execution state
        - Custom State: User-defined attribute handling
        - Error Handling: Corrupt files and edge cases
        - Directory Handling: Path resolution and working directory
    """

    def setUp(self) -> "TestSaveLoadAnthropic":
        """Set up test environment before each test.

        Creates a temporary directory and initializes a test AnthropicBot instance
        with Claude 3.5 Sonnet configuration.

        Args:
            self: Test class instance

        Returns:
            TestSaveLoadAnthropic: Self reference for method chaining

        Note:
            The temporary directory is created using tempfile.mkdtemp()
            and will be cleaned up in tearDown().
        """
        self.temp_dir = tempfile.mkdtemp()
        self.bot = AnthropicBot(
            name="TestClaude",
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=1000,
            temperature=0,
        )
        self.bot.system_message = (
            "You are in a test environment. When asked to use tools, use them immediately "
            "without asking for clarification or reflecting on the request. Execute tool calls directly."
        )
        return self

    def tearDown(self) -> None:
        """Clean up test environment after each test.

        Removes the temporary directory and all its contents created during setUp.
        Also cleans up any .bot files that might have been created in the current directory.
        Handles cleanup errors gracefully with warning messages.

        Args:
            self: Test class instance

        Returns:
            None

        Note:
            Uses shutil.rmtree with ignore_errors=True for robust cleanup
        """
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up {self.temp_dir}: {e}")
