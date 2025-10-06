"""
Debug test file to isolate CLI wizard test issues.
Building up complexity step by step.
"""

import pytest
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import bots.dev.cli as cli_module
from bots.testing.mock_bot import MockBot




pytestmark = pytest.mark.e2e

class TestWizardDebug(unittest.TestCase):
    """Incrementally test CLI wizard functionality to isolate issues."""

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_01_simple_chat_and_exit(self, mock_input, mock_bot_class):
        """Test 1: Just chat once and exit."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Hello!")
        mock_bot_class.return_value = mock_bot

        mock_input.side_effect = [
            "Hello bot",
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 1 output:\n{output}")

        self.assertIn("Hello!", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_02_fp_command_then_exit(self, mock_input, mock_bot_class):
        """Test 2: Type /fp command, see the menu, then type an invalid choice to exit."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Hello!")
        mock_bot_class.return_value = mock_bot

        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "invalid",  # Invalid FP selection - should show error and return to main loop
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 2 output:\n{output}")

        self.assertIn("Available functional prompts", output)
        self.assertIn("Invalid selection", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_03_fp_single_prompt(self, mock_input, mock_bot_class):
        """Test 3: Select single_prompt and provide a prompt."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Analysis complete")
        mock_bot_class.return_value = mock_bot

        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "11",  # Select single_prompt (it's #11 in alphabetical order!)
            "Analyze this code",  # The prompt parameter
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 3 output:\n{output}")

        self.assertIn("single_prompt", output)
        self.assertIn("Executing single_prompt", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_04_fp_single_prompt_no_initial_chat(self, mock_input, mock_bot_class):
        """Test 4: Go straight to /fp without initial chat."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Analysis complete")
        mock_bot_class.return_value = mock_bot

        mock_input.side_effect = [
            "/fp",
            "11",  # Select single_prompt (it's #11 in alphabetical order!)
            "Analyze this code",  # The prompt parameter
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 4 output:\n{output}")

        self.assertIn("single_prompt", output)
        self.assertIn("Executing single_prompt", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_05_fp_single_prompt_no_redirect(self, mock_input, mock_bot_class):
        """Test 5: Same as test 4 but without redirect_stdout to see the actual error."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Analysis complete")
        mock_bot_class.return_value = mock_bot

        mock_input.side_effect = [
            "/fp",
            "11",  # Select single_prompt (it's #11 in alphabetical order!)
            "Analyze this code",  # The prompt parameter
            "/exit",
        ]

        # Don't redirect stdout - let errors print normally
        with self.assertRaises(SystemExit):
            cli_module.main("")


if __name__ == "__main__":
    unittest.main()
