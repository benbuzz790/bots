import inspect
import os
import sys
import traceback
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import MagicMock, patch

import bots.dev.cli as cli_module
import bots.flows.functional_prompts as fp

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
        text = text.replace('"', "").replace("'", "")
        text = text.replace("{", "").replace("}", "")
        text = text.replace("[", "").replace("]", "")
        text = text.replace(":", "").replace(",", "")
        return " ".join(text.split())

    def assertContainsNormalized(self, haystack: str, needle: str, msg: str | None = None) -> None:
        """Assert that needle exists in haystack after normalization.
        Performs a contains assertion after normalizing both strings to handle
        variations in formatting, whitespace, and special characters.
        Parameters:
            haystack (str): The larger text to search within
            needle (str): The text to search for
            msg (str | None): Optional custom error message
        Raises:
            AssertionError: If normalized needle is not found in normalized haystack
        """
        normalized_haystack = self.normalize_text(haystack)
        normalized_needle = self.normalize_text(needle)
        self.assertTrue(
            normalized_needle in normalized_haystack,
            msg or f'Expected to find "{needle}" in text (after normalization).\nGot:\n{haystack}',
        )

    def assertEqualWithDetails(self, first: object, second: object, msg: str | None = None) -> None:
        """Detailed assertion with local variable context on failure.
        Enhanced version of assertEqual that provides detailed context including
        local variables and stack trace on assertion failure.
        Parameters:
            first (object): First value to compare
            second (object): Second value to compare
            msg (str | None): Optional custom error message
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
                local_vars.pop("self", None)
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "\nLocal variables:\n"
                for key, value in local_vars.items():
                    error_message += f"{key} = {repr(value)}\n"
                error_message += "\nTraceback:\n"
                error_message += "".join(traceback.format_tb(exc_traceback))
            else:
                error_message = f"\nAssertion Error: {str(e)}\n"
                error_message += "Unable to retrieve local variables.\n"
                error_message += "\nTraceback:\n"
                error_message += "".join(traceback.format_tb(exc_traceback))
            raise AssertionError(error_message)


class TestCLIBasics(DetailedTestCase):
    """Test suite for basic CLI functionality."""

    @patch("builtins.input")
    def test_help_command(self, mock_input: MagicMock) -> None:
        """Test the /help command displays help information."""
        mock_input.side_effect = ["/help", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nHelp output:\n{output}")
        self.assertContainsNormalized(output, "Available commands")
        self.assertContainsNormalized(output, "/fp: Execute functional prompts")
        self.assertContainsNormalized(output, "/config: Show or modify CLI configuration")

    @patch("builtins.input")
    def test_verbose_quiet_commands(self, mock_input: MagicMock) -> None:
        """Test verbose and quiet mode commands."""
        mock_input.side_effect = ["/quiet", "/verbose", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nVerbose/Quiet output:\n{output}")
        self.assertContainsNormalized(output, "Tool output enabled")
        self.assertContainsNormalized(output, "Tool output disabled")

    @patch("builtins.input")
    def test_config_command(self, mock_input: MagicMock) -> None:
        """Test the /config command shows current configuration."""
        mock_input.side_effect = ["/config", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nConfig output:\n{output}")
        self.assertContainsNormalized(output, "Current configuration")
        self.assertContainsNormalized(output, "verbose:")
        self.assertContainsNormalized(output, "width:")
        self.assertContainsNormalized(output, "indent:")


class TestConversationNavigation(DetailedTestCase):
    """Test suite for conversation navigation commands."""

    @patch("builtins.input")
    def test_root_command(self, mock_input: MagicMock) -> None:
        """Test the /root command moves to conversation root."""
        mock_input.side_effect = ["Hello bot", "/root", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nRoot command output:\n{output}")
        self.assertContainsNormalized(output, "Moved to root of conversation tree")

    @patch("builtins.input")
    def test_up_command_at_root(self, mock_input: MagicMock) -> None:
        """Test /up command when already at root."""
        mock_input.side_effect = ["/up", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nUp at root output:\n{output}")
        self.assertContainsNormalized(output, "At root - can't go up")

    @patch("builtins.input")
    def test_down_command_at_leaf(self, mock_input: MagicMock) -> None:
        """Test /down command when at leaf node."""
        mock_input.side_effect = ["/down", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nDown at leaf output:\n{output}")
        self.assertContainsNormalized(output, "At leaf - can't go down")


class TestLabelingSystem(DetailedTestCase):
    """Test suite for conversation labeling functionality."""

    @patch("builtins.input")
    def test_label_and_goto(self, mock_input: MagicMock) -> None:
        """Test labeling a node and navigating to it."""
        mock_input.side_effect = [
            "Write a simple function",
            "/label",
            "test_function",
            "Write another function",
            "/goto",
            "test_function",
            "/exit",
        ]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nLabel and goto output:\n{output}")
        self.assertContainsNormalized(output, "Saved current node with label: test_function")
        self.assertContainsNormalized(output, "Moved to node labeled: test_function")

    @patch("builtins.input")
    def test_goto_nonexistent_label(self, mock_input: MagicMock) -> None:
        """Test error handling for /goto with invalid labels."""
        mock_input.side_effect = [
            "Write a function",
            "/goto",
            "nonexistent_label",
            "/exit",
        ]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nGoto nonexistent output:\n{output}")
        self.assertContainsNormalized(output, "No node found with label: nonexistent_label")

    @patch("builtins.input")
    def test_showlabels_empty(self, mock_input: MagicMock) -> None:
        """Test the /showlabels command when no labels exist."""
        mock_input.side_effect = ["/showlabels", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nShowlabels empty output:\n{output}")
        self.assertContainsNormalized(output, "No labels saved")

    @patch("builtins.input")
    def test_showlabels_with_labels(self, mock_input: MagicMock) -> None:
        """Test the /showlabels command with existing labels."""
        mock_input.side_effect = [
            "Write a fibonacci function",
            "/label",
            "fibonacci_func",
            "Write a sorting algorithm",
            "/label",
            "sort_algo",
            "/showlabels",
            "/exit",
        ]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nShowlabels with labels output:\n{output}")
        self.assertContainsNormalized(output, "Saved labels:")
        self.assertContainsNormalized(output, "fibonacci_func")
        self.assertContainsNormalized(output, "sort_algo")


class TestFunctionalPrompts(DetailedTestCase):
    """Test suite for functional prompt functionality."""

    @patch("builtins.input")
    def test_fp_command_basic(self, mock_input: MagicMock) -> None:
        """Test basic /fp command functionality."""
        # Mock the wizard interaction for a simple chain
        mock_input.side_effect = [
            "/fp",
            "1",  # Select chain
            "Analyze this problem",  # First prompt
            "Propose a solution",  # Second prompt
            "",  # End prompts
            "/exit",
        ]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP command output:\n{output}")
        self.assertContainsNormalized(output, "Available functional prompts")
        self.assertContainsNormalized(output, "chain")

    @patch("builtins.input")
    def test_fp_command_invalid_selection(self, mock_input: MagicMock) -> None:
        """Test /fp command with invalid selection."""
        mock_input.side_effect = ["/fp", "invalid_choice", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP invalid selection output:\n{output}")
        self.assertContainsNormalized(output, "Invalid selection")


class TestErrorHandling(DetailedTestCase):
    """Test suite for error handling and recovery."""

    @patch("builtins.input")
    def test_invalid_command(self, mock_input: MagicMock) -> None:
        """Test handling of invalid commands."""
        mock_input.side_effect = ["/invalid_command", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nInvalid command output:\n{output}")
        self.assertContainsNormalized(output, "Unrecognized command")

    @patch("builtins.input")
    def test_keyboard_interrupt_handling(self, mock_input: MagicMock) -> None:
        """Test that KeyboardInterrupt is handled gracefully."""
        mock_input.side_effect = [KeyboardInterrupt(), "/exit"]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nKeyboard interrupt output:\n{output}")
        self.assertContainsNormalized(output, "Use /exit to quit")


class TestConfigManagement(DetailedTestCase):
    """Test suite for configuration management."""

    @patch("builtins.input")
    def test_config_set_verbose(self, mock_input: MagicMock) -> None:
        """Test setting verbose configuration."""
        mock_input.side_effect = ["/config set verbose false", "/config", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nConfig set verbose output:\n{output}")
        self.assertContainsNormalized(output, "Set verbose to False")

    @patch("builtins.input")
    def test_config_set_width(self, mock_input: MagicMock) -> None:
        """Test setting width configuration."""
        mock_input.side_effect = ["/config set width 80", "/config", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nConfig set width output:\n{output}")
        self.assertContainsNormalized(output, "Set width to 80")

    @patch("builtins.input")
    def test_config_invalid_setting(self, mock_input: MagicMock) -> None:
        """Test setting invalid configuration."""
        mock_input.side_effect = ["/config set invalid_setting value", "/exit"]
        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nConfig invalid setting output:\n{output}")
        self.assertContainsNormalized(output, "Unknown setting: invalid_setting")


class TestWhileFunctionsInCLI(DetailedTestCase):
    """Test the *_while functions work correctly within CLI context."""

    def setUp(self):
        """Set up test fixtures."""
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.content = "Test response"
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.mock_bot.tool_handler.clear = MagicMock()
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot


class TestFunctionalPromptUsability(DetailedTestCase):
    """
    Test suite demonstrating the usability assessment of functional prompts in CLI.

    This class validates which functional prompts are:
    - ✅ Fully usable through CLI parameter collection
    - ⚠️ Partially usable with limitations
    - ❌ Not usable due to parameter collection issues
    """

    def setUp(self):
        """Set up test fixtures for parameter collection testing."""
        self.collector = cli_module.DynamicParameterCollector()
        self.handler = cli_module.DynamicFunctionalPromptHandler()

        # Set up mock bot for tests that need it
        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.content = "Test response"
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.mock_bot.tool_handler.clear = MagicMock()
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot

    def test_fully_usable_chain_function(self):
        """✅ Demonstrate that chain() is fully usable through CLI."""
        # Test parameter collection for chain function
        with patch(
            "builtins.input",
            side_effect=[
                "Analyze the problem step by step",
                "Propose three different solutions",
                "Evaluate each solution for feasibility",
                "",  # End prompt collection
            ],
        ):
            collected = self.collector.collect_parameters(fp.chain)

        # Should successfully collect all required parameters
        self.assertIsNotNone(collected)
        self.assertIn("prompt_list", collected)
        self.assertEqual(len(collected["prompt_list"]), 3)
        self.assertEqual(collected["prompt_list"][0], "Analyze the problem step by step")

        # Verify callback handling
        self.assertIn("_callback_type", collected)
        self.assertEqual(collected["_callback_type"], "list")

    def test_fully_usable_branch_function(self):
        """✅ Demonstrate that branch() is fully usable through CLI."""
        with patch(
            "builtins.input",
            side_effect=[
                "Analyze from security perspective",
                "Analyze from performance perspective",
                "Analyze from maintainability perspective",
                "",
            ],
        ):
            collected = self.collector.collect_parameters(fp.branch)

        self.assertIsNotNone(collected)
        self.assertIn("prompt_list", collected)
        self.assertEqual(len(collected["prompt_list"]), 3)

    def test_fully_usable_prompt_while_function(self):
        """✅ Demonstrate that prompt_while() is fully usable through CLI."""
        with patch(
            "builtins.input",
            side_effect=[
                "Debug this code and fix all issues",  # first_prompt
                "Continue debugging if needed",  # continue_prompt
                "2",  # stop_condition choice (tool_not_used)
            ],
        ):
            collected = self.collector.collect_parameters(fp.prompt_while)

        self.assertIsNotNone(collected)
        self.assertIn("first_prompt", collected)
        self.assertIn("continue_prompt", collected)
        self.assertIn("stop_condition", collected)
        self.assertEqual(collected["first_prompt"], "Debug this code and fix all issues")

    def test_partially_usable_tree_of_thought_function(self):
        """⚠️ Demonstrate that tree_of_thought() is partially usable with limitations."""
        with patch(
            "builtins.input",
            side_effect=[
                "Analyze technical feasibility",
                "Analyze business impact",
                "Analyze user experience impact",
                "",  # End prompts
                "1",  # recombinator choice (concatenate)
            ],
        ):
            collected = self.collector.collect_parameters(fp.tree_of_thought)

        # Should collect parameters but with limitations
        self.assertIsNotNone(collected)
        self.assertIn("prompts", collected)
        self.assertIn("recombinator_function", collected)

        # Verify special callback handling for tree_of_thought
        self.assertEqual(collected["_callback_type"], "single")

        # Verify recombinator is limited to predefined options
        from bots.flows.recombinators import recombinators

        self.assertEqual(collected["recombinator_function"], recombinators.concatenate)

    def test_non_usable_prompt_for_function(self):
        """❌ Demonstrate that prompt_for() is not usable due to unimplemented handlers."""
        # Test that items parameter handler is not implemented
        items_result = self.collector._collect_items("items", inspect.Parameter.empty)
        self.assertIsNone(items_result)

        # Test that dynamic_prompt parameter handler is not implemented
        dynamic_prompt_result = self.collector._collect_dynamic_prompt("dynamic_prompt", inspect.Parameter.empty)
        self.assertIsNone(dynamic_prompt_result)

        # Full parameter collection should fail
        with patch("builtins.input", side_effect=["y"]):  # should_branch = True
            collected = self.collector.collect_parameters(fp.prompt_for)

        # Should return None due to missing required parameters
        self.assertIsNone(collected)

    def test_non_usable_par_dispatch_function_signature(self):
        """❌ Demonstrate par_dispatch() is not usable due to complex parameter requirements."""
        sig = inspect.signature(fp.par_dispatch)
        params = list(sig.parameters.keys())

        # Has parameters that require complex input CLI can't handle
        self.assertIn("bot_list", params)  # List of Bot instances
        self.assertIn("functional_prompt", params)  # Function reference

        # Has **kwargs which can't be collected
        sig_str = str(sig)
        self.assertIn("**kwargs", sig_str)

    def test_function_discovery_completeness(self):
        """Test that function discovery finds expected functions correctly."""
        discovered = self.handler.fp_functions

        # Verify fully usable functions are discovered
        fully_usable = [
            "chain",
            "branch",
            "prompt_while",
            "chain_while",
            "tree_of_thought",
            "par_branch",
            "par_branch_while",
            "broadcast_to_leaves",
            "broadcast_fp",
        ]
        for func_name in fully_usable:
            self.assertIn(
                func_name,
                discovered,
                f"Fully usable function '{func_name}' should be discovered",
            )

    def test_parameter_handler_coverage(self):
        """Test that parameter handlers exist for expected parameter types."""
        handlers = self.collector.param_handlers

        # Verify handlers exist for common parameter types
        expected_handlers = [
            "prompt_list",
            "prompts",
            "prompt",
            "first_prompt",
            "stop_condition",
            "continue_prompt",
            "recombinator_function",
            "should_branch",
            "skip",
            "items",
            "dynamic_prompt",
        ]

        for handler_name in expected_handlers:
            self.assertIn(handler_name, handlers, f"Handler for '{handler_name}' should exist")

    def test_condition_options_available(self):
        """Test that predefined stop conditions are available."""
        conditions = self.collector.conditions

        # Verify expected conditions are available
        expected_conditions = ["1", "2", "3"]  # tool_used, tool_not_used, said_DONE
        for key in expected_conditions:
            self.assertIn(key, conditions)

        # Verify condition functions are callable
        for key, (name, func) in conditions.items():
            self.assertTrue(callable(func), f"Condition '{name}' should be callable")

    def test_recombinator_options_available(self):
        """Test that predefined recombinator functions are available."""
        # Test recombinator collection
        with patch("builtins.input", return_value="1"):
            result = self.collector._collect_recombinator("recombinator_function", inspect.Parameter.empty)

        # Should return a valid recombinator function
        self.assertIsNotNone(result)
        self.assertTrue(callable(result))

        # Test invalid selection defaults to concatenate
        with patch("builtins.input", return_value="invalid"):
            result = self.collector._collect_recombinator("recombinator_function", inspect.Parameter.empty)

        from bots.flows.recombinators import recombinators

        self.assertEqual(result, recombinators.concatenate)

    @patch("builtins.input")
    def test_end_to_end_fp_command_with_chain(self, mock_input):
        """✅ Demonstrate successful end-to-end /fp command with chain function."""
        mock_input.side_effect = [
            "/fp",
            "chain",  # Select chain function by name
            "First, understand the requirements",
            "Then, design the architecture",
            "Finally, implement the solution",
            "",  # End prompt collection
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()

        # Should show successful parameter collection and execution
        self.assertContainsNormalized(output, "Available functional prompts")
        self.assertContainsNormalized(output, "Collecting parameters for chain")
        self.assertContainsNormalized(output, "Executing chain")

    def test_chain_while_with_multiple_prompts(self):
        """Test chain_while processes multiple prompts sequentially."""
        from bots.flows.functional_prompts import chain_while

        # Mock bot responses
        responses = ["Response 1", "Response 2", "Response 3"]
        self.mock_bot.respond.side_effect = responses

        # Create a stop condition that stops immediately
        def stop_immediately(bot):
            return True

        prompts = ["Prompt 1", "Prompt 2", "Prompt 3"]
        # Test chain_while
        result_responses, result_nodes = chain_while(self.mock_bot, prompts, stop_condition=stop_immediately)
        # Verify all prompts were processed
        self.assertEqual(len(result_responses), 3)
        self.assertEqual(self.mock_bot.respond.call_count, 3)
        # Verify prompts were called in order
        call_args = [call[0][0] for call in self.mock_bot.respond.call_args_list]
        self.assertEqual(call_args, prompts)

    def test_while_functions_empty_prompt_list(self):
        """Test *_while functions handle empty prompt lists gracefully."""
        from bots.flows.functional_prompts import chain_while

        def stop_immediately(bot):
            return True

        # Test chain_while with empty list
        responses, nodes = chain_while(self.mock_bot, [], stop_condition=stop_immediately)
        self.assertEqual(len(responses), 0)
        self.assertEqual(len(nodes), 0)
        # Verify bot.respond was never called
        self.mock_bot.respond.assert_not_called()

    def test_cli_callback_function_creation(self):
        """Test that CLI callback function works correctly."""
        # Test the CLICallbacks class method
        callback = self.context.callbacks.get_standard_callback()
        # Mock tool data
        self.mock_bot.tool_handler.requests = [{"tool": "test", "args": {}}]
        self.mock_bot.tool_handler.results = [{"output": "test result"}]
        self.context.config.verbose = True
        # Test callback execution (should not raise exceptions)
        try:
            callback(["test response"], [self.mock_bot.conversation])
        except Exception as e:
            self.fail(f"Callback raised an exception: {e}")


class TestAutoCommand(DetailedTestCase):
    """Test suite for the /auto command functionality."""

    def setUp(self):
        """Set up test fixtures for auto command tests."""
        from unittest.mock import MagicMock

        self.mock_bot = MagicMock()
        self.mock_bot.name = "TestBot"
        self.mock_bot.conversation = MagicMock()
        self.mock_bot.conversation.content = "Test response"
        self.mock_bot.tool_handler = MagicMock()
        self.mock_bot.tool_handler.requests = []
        self.mock_bot.tool_handler.results = []
        self.mock_bot.tool_handler.clear = MagicMock()
        self.context = cli_module.CLIContext()
        self.context.bot_instance = self.mock_bot


if __name__ == "__main__":
    # Clean up any config files before running tests
    if os.path.exists("cli_config.json"):
        os.remove("cli_config.json")
    unittest.main()
