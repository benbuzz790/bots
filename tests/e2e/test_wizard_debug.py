"""
Debug test file to isolate CLI wizard test issues.
Building up complexity step by step.
"""

import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

import bots.dev.cli as cli_module
from bots.testing.mock_bot import MockBot

pytestmark = pytest.mark.e2e


class TestWizardDebug:
    """Incrementally test CLI wizard functionality to isolate issues."""

    @patch("bots.dev.cli.AnthropicBot")
    def test_01_simple_chat_and_exit(self, mock_bot_class, monkeypatch):
        """Test 1: Just chat once and exit."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Hello!")
        mock_bot_class.return_value = mock_bot

        inputs = iter(["Hello bot", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs, "/exit"))

        with StringIO() as buf, redirect_stdout(buf):
            with pytest.raises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 1 output:\n{output}")

        assert "Hello!" in output

    @patch("bots.dev.cli.AnthropicBot")
    def test_02_fp_command_then_exit(self, mock_bot_class, monkeypatch):
        """Test 2: Type /fp command, see the menu, then type an invalid choice to exit."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Hello!")
        mock_bot_class.return_value = mock_bot

        inputs = iter(["Hello bot", "/fp", "invalid", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs, "/exit"))

        with StringIO() as buf, redirect_stdout(buf):
            with pytest.raises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 2 output:\n{output}")

        assert "Available functional prompts" in output
        assert "Invalid selection" in output

    @patch("bots.dev.cli.AnthropicBot")
    def test_03_fp_single_prompt(self, mock_bot_class, monkeypatch):
        """Test 3: Select single_prompt and provide a prompt."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Analysis complete")
        mock_bot_class.return_value = mock_bot

        # Mock both input() and input_with_esc()
        # input() is used for: main loop, fp selection
        # input_with_esc() is used for: parameter collection
        main_inputs = iter(["Hello bot", "/fp", "11", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(main_inputs, "/exit"))

        param_inputs = iter(["Analyze this code"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(param_inputs, ""))

        with StringIO() as buf, redirect_stdout(buf):
            with pytest.raises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 3 output:\n{output}")

        assert "single_prompt" in output
        assert "Executing single_prompt" in output

    @patch("bots.dev.cli.AnthropicBot")
    def test_04_fp_single_prompt_no_initial_chat(self, mock_bot_class, monkeypatch):
        """Test 4: Go straight to /fp without initial chat."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Analysis complete")
        mock_bot_class.return_value = mock_bot

        # Mock both input() and input_with_esc()
        main_inputs = iter(["/fp", "11", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(main_inputs, "/exit"))

        param_inputs = iter(["Analyze this code"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(param_inputs, ""))

        with StringIO() as buf, redirect_stdout(buf):
            with pytest.raises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nTest 4 output:\n{output}")

        assert "single_prompt" in output
        assert "Executing single_prompt" in output

    @patch("bots.dev.cli.AnthropicBot")
    def test_05_fp_single_prompt_no_redirect(self, mock_bot_class, monkeypatch):
        """Test 5: Same as test 4 but without redirect_stdout to see the actual error."""
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Analysis complete")
        mock_bot_class.return_value = mock_bot

        # Mock both input() and input_with_esc()
        main_inputs = iter(["/fp", "11", "/exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(main_inputs, "/exit"))

        param_inputs = iter(["Analyze this code"])
        monkeypatch.setattr("bots.dev.cli.input_with_esc", lambda _: next(param_inputs, ""))

        # Don't redirect stdout - let errors print normally
        with pytest.raises(SystemExit):
            cli_module.main("")


if __name__ == "__main__":
    unittest.main()
