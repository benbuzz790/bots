import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import bots.dev.cli as cli_module


class TestQuietModeDuplicate(unittest.TestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.content = "Test response from bot"
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot
        self.context.config.verbose = False

    @patch("bots.flows.functional_prompts.chain")
    def test_quiet_mode_shows_message_once_after_fix(self, mock_chain):
        """Test that quiet mode shows message only once after the fix."""
        test_response = "Bot response should appear once in quiet mode"

        def mock_chain_with_callback(bot, prompts, callback=None):
            responses = [test_response]
            nodes = [self.mock_bot.conversation]
            if callback:
                callback(responses, nodes)
            return (responses, nodes)

        mock_chain.side_effect = mock_chain_with_callback
        cli = cli_module.CLI()
        cli.context = self.context
        cli.context.config.verbose = False  # Quiet mode
        with StringIO() as buf, redirect_stdout(buf):
            cli._handle_chat(self.mock_bot, "Test input")
            output = buf.getvalue()
        response_count = output.count(test_response)
        print(f"Quiet mode output: {repr(output)}")
        print(f"Quiet mode count: {response_count}")
        # After fix, message should appear only once in quiet mode
        self.assertEqual(response_count, 1, f"In quiet mode, message should appear once but appears {response_count} times")

    @patch("bots.flows.functional_prompts.chain")
    def test_verbose_mode_shows_message_once_after_fix(self, mock_chain):
        """Test that verbose mode still shows message only once after the fix."""
        test_response = "Bot response should appear once in verbose mode"

        def mock_chain_with_callback(bot, prompts, callback=None):
            responses = [test_response]
            nodes = [self.mock_bot.conversation]
            if callback:
                callback(responses, nodes)
            return (responses, nodes)

        mock_chain.side_effect = mock_chain_with_callback
        cli = cli_module.CLI()
        cli.context = self.context
        cli.context.config.verbose = True  # Verbose mode
        with StringIO() as buf, redirect_stdout(buf):
            cli._handle_chat(self.mock_bot, "Test input")
            output = buf.getvalue()
        response_count = output.count(test_response)
        print(f"Verbose mode output: {repr(output)}")
        print(f"Verbose mode count: {response_count}")
        # Verbose mode should still show message only once
        self.assertEqual(response_count, 1, f"In verbose mode, message should appear once but appears {response_count} times")

    @patch("bots.flows.functional_prompts.chain")
    def test_quiet_mode_with_tools_shows_tool_summary(self, mock_chain):
        """Test that quiet mode shows tool usage summary correctly."""
        test_response = "Bot used tools to complete the task"

        def mock_chain_with_callback(bot, prompts, callback=None):
            responses = [test_response]
            nodes = [self.mock_bot.conversation]
            if callback:
                callback(responses, nodes)
            return (responses, nodes)

        mock_chain.side_effect = mock_chain_with_callback
        # Add mock tool usage to the conversation node (new callback system expects this)
        self.mock_bot.conversation.tool_calls = [{"function": {"name": "test_tool"}}]
        # Also keep the old format for backward compatibility if needed
        self.mock_bot.tool_handler.requests = [{"function": {"name": "test_tool"}}]
        self.mock_bot.tool_handler.tool_name_and_input = MagicMock(return_value=("test_tool", {}))
        cli = cli_module.CLI()
        cli.context = self.context
        cli.context.config.verbose = False  # Quiet mode
        with StringIO() as buf, redirect_stdout(buf):
            cli._handle_chat(self.mock_bot, "Test input")
            output = buf.getvalue()
        response_count = output.count(test_response)
        tool_summary_present = "Used tools:" in output
        print(f"Quiet mode with tools output: {repr(output)}")
        print(f"Response count: {response_count}")
        print(f"Tool summary present: {tool_summary_present}")
        # Message should appear once, and tool summary should be present
        self.assertEqual(response_count, 1, f"Message should appear once but appears {response_count} times")
        self.assertTrue(tool_summary_present, "Tool usage summary should be present in quiet mode")

    @patch("bots.flows.functional_prompts.chain")
    def test_verbose_mode_with_tools_shows_full_details(self, mock_chain):
        """Test that verbose mode shows full tool details correctly."""
        test_response = "Bot used tools in verbose mode"

        def mock_chain_with_callback(bot, prompts, callback=None):
            responses = [test_response]
            nodes = [self.mock_bot.conversation]
            if callback:
                callback(responses, nodes)
            return (responses, nodes)

        mock_chain.side_effect = mock_chain_with_callback
        # Add mock tool usage
        self.mock_bot.tool_handler.requests = [{"function": {"name": "test_tool"}}]
        self.mock_bot.tool_handler.results = [{"result": "test_result"}]
        cli = cli_module.CLI()
        cli.context = self.context
        cli.context.config.verbose = True  # Verbose mode
        with StringIO() as buf, redirect_stdout(buf):
            cli._handle_chat(self.mock_bot, "Test input")
            output = buf.getvalue()
        response_count = output.count(test_response)
        tool_requests_present = "Tool Requests" in output
        print(f"Verbose mode with tools output: {repr(output)}")
        print(f"Response count: {response_count}")
        print(f"Tool requests section present: {tool_requests_present}")
        # Message should appear once, and detailed tool info should be present
        self.assertEqual(response_count, 1, f"Message should appear once but appears {response_count} times")
        self.assertTrue(tool_requests_present, "Detailed tool information should be present in verbose mode")


if __name__ == "__main__":
    unittest.main()
