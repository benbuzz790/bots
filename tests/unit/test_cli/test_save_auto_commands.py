import os
import tempfile
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

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

    @patch("builtins.input")
    @patch("bots.dev.cli.check_for_interrupt")
    def test_auto_command_stops_when_no_tools_used(self, mock_check_interrupt, mock_input):
        """Test /auto command stops when bot doesn't use tools."""
        # Mock that interrupt is never pressed
        mock_check_interrupt.return_value = False

        mock_input.side_effect = ["Hello bot", "/auto", "/exit"]  # Initial chat  # Start autonomous mode

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nAuto command stops output:\n{output}")

        # The bot responds without using tools, so /auto completes immediately
        # Check that bot responded to the /auto command
        self.assertIn("I'm ready to help", output)

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
        self.assertIn("user", output.lower())  # User message should be present


if __name__ == "__main__":
    unittest.main()
