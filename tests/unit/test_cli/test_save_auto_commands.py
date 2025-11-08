import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

import bots.dev.cli as cli_module

"""Tests for /save and /auto commands."""


class TestSaveCommand(unittest.TestCase):
    """Test suite for /save command functionality."""

    def setUp(self):
        """Set up test fixtures."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test fixtures."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    @patch("builtins.input")
    def test_save_command_success(self, mock_input):
        """Test successful /save command."""
        mock_input.side_effect = [
            "Hello bot",  # Initial chat to create some conversation
            "/save",
            "test_bot",  # Filename
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nSave command success output:\n{output}")

        # Should show successful save
        self.assertIn("Bot saved to test_bot.bot", output)
        # File should exist
        self.assertTrue(os.path.exists("test_bot.bot"))

    @patch("builtins.input")
    def test_save_command_cancelled(self, mock_input):
        """Test /save command when user cancels."""
        mock_input.side_effect = ["Hello bot", "/save", "", "/exit"]  # Empty filename cancels

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nSave command cancelled output:\n{output}")

        # Should show cancellation message
        self.assertIn("Save cancelled - no filename provided", output)

    @patch("builtins.input")
    def test_save_command_auto_extension(self, mock_input):
        """Test /save command automatically adds .bot extension."""
        mock_input.side_effect = ["Hello bot", "/save", "my_bot", "/exit"]  # No extension

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nSave command auto extension output:\n{output}")

        # Should show .bot extension was added
        self.assertIn("Bot saved to my_bot.bot", output)
        self.assertTrue(os.path.exists("my_bot.bot"))


class TestAutoCommand(unittest.TestCase):
    """Test suite for /auto command functionality."""

    def test_auto_command_stops_when_no_tools_used(self):
        """Test that /auto command stops when bot doesn't use tools"""
        with tempfile.NamedTemporaryFile(mode="w", suffix=".bot", delete=False) as f:
            bot_file = f.name

        try:
            # Create a bot and save it
            bot = AnthropicBot(model="claude-3-5-sonnet-20241022")
            bot.save(bot_file)

            # Simulate CLI with /auto command
            # The bot will respond without using tools, so /auto should complete
            with patch("sys.stdin", StringIO("Hello\n/auto\n/exit\n")):
                buf = StringIO()
                with redirect_stdout(buf):
                    with self.assertRaises(SystemExit):
                        cli_module.main("")
                output = buf.getvalue()
                print(f"\nAuto command stops output:\n{output}")

            # The bot responds without using tools, so /auto completes immediately
            # Check that:
            # 1. Bot responded (check for bot name in output)
            self.assertTrue("Claude:" in output or "Bot:" in output, "Bot should have responded to the message")
            # 2. /auto command was executed and bot responded to "ok" prompt
            # The output contains ANSI codes, so check for the pattern with color codes
            self.assertTrue("You:" in output and "ok" in output, "Auto command should show 'You: ok' prompt")
            # 3. Bot provided a second response after the auto command
            # Count occurrences of "Claude:" - should be at least 2 (initial + auto response)
            claude_count = output.count("Claude:")
            self.assertGreaterEqual(claude_count, 2, "Bot should respond at least twice (initial + auto)")
            # 4. No error messages
            self.assertNotIn("error", output.lower())
            self.assertNotIn("exception", output.lower())

        finally:
            # Clean up
            if os.path.exists(bot_file):
                os.remove(bot_file)

    @patch("builtins.input")
    @patch("bots.dev.cli.check_for_interrupt")
    def test_auto_command_interrupted_by_user(self, mock_check_interrupt, mock_input):
        """Test /auto command when user interrupts with ESC."""
        # Mock that interrupt is pressed immediately
        mock_check_interrupt.return_value = True

        mock_input.side_effect = ["Hello bot", "/auto", "/exit"]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nAuto command interrupted output:\n{output}")

        # Should show interruption message
        self.assertIn("Autonomous execution interrupted by user", output)

    @pytest.mark.serial
    @patch("builtins.input")
    def test_auto_command_error_handling(self, mock_input):
        """Test /auto command error handling."""
        mock_input.side_effect = ["/auto", "/exit"]  # Try auto without any conversation context

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nAuto command error output:\n{output}")

        # Should handle the case gracefully - /auto returns a message which gets displayed
        # The command completes without crashing
        self.assertIn("you:", output.lower())  # User prompt should be present


if __name__ == "__main__":
    unittest.main()
