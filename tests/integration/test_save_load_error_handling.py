"""
Test for bot save/load issues (WO-TBD):
1. Ensure error messages during load don't print excessive source code
2. Ensure verbose mode shows tool requests/results after load
"""

import os
import sys
import tempfile
import unittest
from io import StringIO

from bots.dev.cli_modules.callbacks import RealTimeDisplayCallbacks
from bots.dev.cli_modules.context import CLIContext
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines


class TestSaveLoadErrorHandling(unittest.TestCase):
    """Test that save/load error handling is reasonable and doesn't spam console."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def tearDown(self):
        """Clean up test environment."""
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_successful_load_produces_no_excessive_output(self):
        """Test that successful bot load doesn't produce excessive console output.

        This test ensures that when a bot is loaded successfully, there's no
        warning spam or debug output that would clutter the CLI.
        """
        # Create and save a bot
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        from bots.tools.code_tools import view_dir

        bot.add_tools(view_dir)

        save_path = os.path.join(self.temp_dir, "test_bot.bot")
        bot.save(save_path)

        # Capture stdout/stderr during load
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured = StringIO()

        try:
            sys.stdout = captured
            sys.stderr = captured
            Bot.load(save_path)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        output = captured.getvalue()

        # Successful load should produce minimal or no output
        self.assertLess(
            len(output),
            500,
            f"Successful load produced excessive output ({len(output)} chars):\n{output[:200]}",
        )

        # Should not contain error patterns
        self.assertNotIn("Full stack trace:", output)
        self.assertNotIn("Source context (lines", output)
        self.assertNotIn("Warning: Failed to load module", output)

    def test_verbose_callbacks_work_after_load(self):
        """Test that verbose mode properly shows tool execution after bot load.

        This test verifies that when a bot is loaded and callbacks are attached,
        the verbose mode properly displays tool requests and results.
        """
        # Create and save a bot
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        from bots.tools.code_tools import view_dir

        bot.add_tools(view_dir)

        save_path = os.path.join(self.temp_dir, "test_bot.bot")
        bot.save(save_path)

        # Load the bot
        loaded_bot = Bot.load(save_path)

        # Set up CLI context with verbose mode
        context = CLIContext()
        context.config.verbose = True
        context.bot_instance = loaded_bot

        # Attach callbacks
        loaded_bot.callbacks = RealTimeDisplayCallbacks(context)

        # Verify callbacks are attached and verbose is enabled
        self.assertIsNotNone(loaded_bot.callbacks)
        self.assertTrue(context.config.verbose)

        # Test that callbacks produce output when triggered
        captured = StringIO()
        old_stdout = sys.stdout

        try:
            sys.stdout = captured

            # Simulate tool execution callbacks
            loaded_bot.callbacks.on_tool_start(
                "view_dir", metadata={"tool_args": {"start_path": ".", "target_extensions": ["py"]}}
            )
            loaded_bot.callbacks.on_tool_complete("view_dir", "Test result")

        finally:
            sys.stdout = old_stdout

        callback_output = captured.getvalue()

        # Callbacks should produce output in verbose mode
        self.assertGreater(
            len(callback_output),
            20,
            f"Verbose callbacks should produce output, got: {repr(callback_output)}",
        )

        # Should contain tool-related output
        # Note: The exact format may vary, but there should be visible output
        self.assertTrue(len(callback_output.strip()) > 0, "Callbacks should produce visible output in verbose mode")

    def test_code_hash_mismatch_warning_is_concise(self):
        """Test that code hash mismatch warnings are concise, not verbose.

        When a module's code has changed, the warning should be brief and
        not include the entire source code.
        """
        # Create and save a bot
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        from bots.tools.code_tools import view_dir

        bot.add_tools(view_dir)

        save_path = os.path.join(self.temp_dir, "test_bot.bot")
        bot.save(save_path)

        # Modify the saved file to trigger code hash mismatch
        import json

        with open(save_path, "r") as f:
            data = json.load(f)

        # Change the code hash to force mismatch

        # Ensure modules exist
        assert "tool_handler" in data, "tool_handler missing from saved data"
        assert "modules" in data["tool_handler"], "modules missing from tool_handler"
        assert len(data["tool_handler"]["modules"]) > 0, "No modules found in tool_handler"

        # Get the first module and mutate its hash
        first_module = next(iter(data["tool_handler"]["modules"].values()))
        first_module["code_hash"] = "intentionally_wrong_hash"

        with open(save_path, "w") as f:
            json.dump(data, f)

        # Capture output during load
        old_stdout = sys.stdout
        old_stderr = sys.stderr
        captured = StringIO()

        try:
            sys.stdout = captured
            sys.stderr = captured
            Bot.load(save_path)
        finally:
            sys.stdout = old_stdout
            sys.stderr = old_stderr

        output = captured.getvalue()

        # Warning should be concise (< 500 chars for a single module warning)
        self.assertLess(
            len(output),
            500,
            f"Code hash mismatch warning too verbose ({len(output)} chars):\n{output[:300]}",
        )

        # Should contain the expected warning
        self.assertIn("Warning: Code hash mismatch", output)

        # Should NOT contain excessive detail
        self.assertNotIn("Full stack trace:", output)
        self.assertNotIn("Source context (lines", output)

    def test_tool_handler_bot_reference_preserved_after_load(self):
        """Test that tool_handler.bot reference is properly set after bot load.

        This test ensures that the circular reference between bot and tool_handler
        is maintained after loading, which is critical for callbacks to work.

        Regression test for: Verbose mode not showing tool requests/results after load
        Root cause: tool_handler.bot was None after load, preventing callback invocation
        """
        # Create and save a bot with tools
        bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE37_SONNET_20250219, max_tokens=1000)

        from bots.tools.code_tools import view_dir

        bot.add_tools(view_dir)

        # Verify reference exists before save
        self.assertTrue(hasattr(bot.tool_handler, "bot"))
        self.assertIs(bot.tool_handler.bot, bot)

        # Save the bot
        save_path = os.path.join(self.temp_dir, "test_bot.bot")
        bot.save(save_path)

        # Load the bot
        loaded_bot = Bot.load(save_path)

        # Verify reference is restored after load
        self.assertTrue(hasattr(loaded_bot.tool_handler, "bot"), "tool_handler.bot attribute should exist after load")
        self.assertIsNotNone(loaded_bot.tool_handler.bot, "tool_handler.bot should not be None after load")
        self.assertIs(
            loaded_bot.tool_handler.bot,
            loaded_bot,
            "tool_handler.bot should reference the loaded bot instance",
        )


if __name__ == "__main__":
    unittest.main()
