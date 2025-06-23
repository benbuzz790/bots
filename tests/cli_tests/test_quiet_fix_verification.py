import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import bots.dev.cli as cli_module


class TestQuietModeFix(unittest.TestCase):
    def setUp(self):
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot

    @patch("bots.flows.functional_prompts.chain")
    def test_quiet_mode_fix_verified(self, mock_chain):
        test_response = "Message should appear once in quiet mode"

        def mock_chain_with_callback(bot, prompts, callback=None):
            responses = [test_response]
            nodes = [self.mock_bot.conversation]
            if callback:
                callback(responses, nodes)
            return responses, nodes

        mock_chain.side_effect = mock_chain_with_callback
        cli = cli_module.CLI()
        cli.context = self.context
        cli.context.config.verbose = False
        with StringIO() as buf, redirect_stdout(buf):
            cli._handle_chat(self.mock_bot, "Test input")
            output = buf.getvalue()
        response_count = output.count(test_response)
        print(f"Quiet mode - Output: {repr(output)}")
        print(f"Quiet mode - Count: {response_count} (should be 1)")
        self.assertEqual(response_count, 1, f"Fix verified: message appears {response_count} time(s)")


if __name__ == "__main__":
    unittest.main()
