import unittest
import datetime as DT
import os
import sys
import traceback
import concurrent
from unittest.mock import patch, MagicMock
from io import StringIO
from contextlib import redirect_stdout
import bots.dev.cli as cli_module
import bots.dev.auto_terminal as auto_terminal_module
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot
import tempfile
from datetime import datetime
"""Unit tests for the CLI module.
This test suite verifies the functionality of the new CLI interface,
focusing on file operations, conversation navigation, and command handling.
Tests are designed to run against real APIs without mocking core functionality,
except for input/output operations.
"""
class DetailedTestCase(unittest.TestCase):
    """Base test class with enhanced assertion capabilities."""
    def normalize_text(self, text: str) -> str:
        """Normalize text for flexible comparison.
        Standardizes text format by removing common variations in syntax and formatting
        to enable more robust text comparisons.
        Parameters:
            text (str): The text to normalize
        Returns:
            str: The normalized text with special characters removed and standardized spacing
        """
        text = str(text).lower()
        text = text.replace('"', '').replace("'", '')
        text = text.replace('{', '').replace('}', '')
        text = text.replace('[', '').replace(']', '')
        text = text.replace(':', '').replace(',', '')
        return ' '.join(text.split())
    def assertContainsNormalized(self, haystack: str, needle: str, msg: str = None) -> None:
        """Assert that needle exists in haystack after normalization.
        Performs a contains assertion after normalizing both strings to handle
        variations in formatting, whitespace, and special characters.
        Parameters:
            haystack (str): The larger text to search within
            needle (str): The text to search for
            msg (str): Optional custom error message
        Raises: 
            AssertionError: If normalized needle is not found in normalized haystack
        """
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(
            normalized_needle in normalized_haystack,
            msg or f'Expected to find "{needle}" in text (after normalization).\nGot:\n{haystack}'
        )
    def assertEqualWithDetails(self, first: object, second: object, msg: str = None) -> None:
        """Detailed assertion with local variable context on failure.
        Enhanced version of assertEqual that provides detailed context including
        local variables and stack trace on assertion failure.
        Parameters:
            first (object): First value to compare
            second (object): Second value to compare
            msg (str): Optional custom error message
        Raises:
            AssertionError: If values are not equal, with detailed context
        """
        try:
            self.assertEqual(first, second, msg)
        except AssertionError as e:
            exc_type, exc_value, exc_traceback = sys.exc_info()
            frame = exc_traceback.tb_frame.f_back
            if frame:
                local_vars = frame.f_locals.copy()
                local_vars.pop('self', None)
                error_message = f'\nAssertion Error: {str(e)}\n'
                error_message += '\nLocal variables:\n'
                for key, value in local_vars.items():
                    error_message += f'{key} = {repr(value)}\n'
                error_message += '\nTraceback:\n'
                error_message += ''.join(traceback.format_tb(exc_traceback))
            else:
                error_message = f'\nAssertion Error: {str(e)}\n'
                error_message += 'Unable to retrieve local variables.\n'
                error_message += '\nTraceback:\n'
                error_message += ''.join(traceback.format_tb(exc_traceback))
            raise AssertionError(error_message)
class TestCLIBasics(DetailedTestCase):
    """Test suite for basic CLI functionality."""
    @patch('builtins.input')
    def test_help_command(self, mock_input: MagicMock) -> None:
        """Test the /help command displays help information."""
        mock_input.side_effect = ['/help', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main()
            output = buf.getvalue()
            print(f'\nHelp output:\n{output}')
        self.assertContainsNormalized(output, 'Available commands')
        self.assertContainsNormalized(output, '/fp: Execute functional prompts')
        self.assertContainsNormalized(output, '/config: Show or modify CLI configuration')
    @patch('builtins.input')
    def test_verbose_quiet_commands(self, mock_input: MagicMock) -> None:
        """Test verbose and quiet mode commands."""
        mock_input.side_effect = ['/verbose', '/quiet', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main()
            output = buf.getvalue()
            print(f'\nVerbose/Quiet output:\n{output}')
        self.assertContainsNormalized(output, 'Tool output enabled')
        self.assertContainsNormalized(output, 'Tool output disabled')
    @patch('builtins.input')
    def test_config_command(self, mock_input: MagicMock) -> None:
        """Test the /config command shows current configuration."""
        mock_input.side_effect = ['/config', '/exit']
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main()
            output = buf.getvalue()
            print(f'\nConfig output:\n{output}')
        self.assertContainsNormalized(output, 'Current configuration')
        self.assertContainsNormalized(output, 'verbose:')
        self.assertContainsNormalized(output, 'width:')
        self.assertContainsNormalized(output, 'indent:')
if __name__ == '__main__':
    # Clean up any config files before running tests
    if os.path.exists('cli_config.json'):
        os.remove('cli_config.json')
    unittest.main()
