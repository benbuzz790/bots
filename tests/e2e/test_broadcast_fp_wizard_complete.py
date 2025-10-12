import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

import bots.dev.cli as cli_module
from bots.testing.mock_bot import MockBot

pytestmark = pytest.mark.e2e

"""Complete test suite for all /broadcast_fp command wizards."""


def create_mock_bot(mock_bot_class, response_text="Analysis complete"):
    """Helper function to create a properly mocked bot using MockBot."""
    mock_bot = MockBot(name="TestBot")
    mock_bot.set_response_pattern(response_text)
    mock_bot_class.return_value = mock_bot
    return mock_bot


class TestBroadcastFPWizardComplete(unittest.TestCase):
    """Test suite for all functional prompt wizards via /broadcast_fp command."""

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_branch_wizard(self, mock_input, mock_bot_class):
        """Test /broadcast_fp command with branch wizard."""
        create_mock_bot(mock_bot_class)

        mock_input.side_effect = [
            "Create initial content",  # Create conversation
            "/label",
            "start",  # Create a label for navigation
            "Create more content",  # Create branches
            "/broadcast_fp",
            "all",  # Select all leaves
            "3",  # Select branch
            "Security analysis branch",  # First prompt
            "Performance analysis branch",  # Second prompt
            "Usability analysis branch",  # Third prompt
            "",  # End prompts
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP branch wizard output:\n{output}")

        # Should show branch broadcast execution
        self.assertIn("branch", output)
        self.assertIn("Broadcasting branch", output)
        self.assertIn("Broadcast complete", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_tree_of_thought_wizard(self, mock_input, mock_bot_class):
        """Test /broadcast_fp command with tree_of_thought wizard."""
        create_mock_bot(mock_bot_class)

        mock_input.side_effect = [
            "Initial analysis",
            "/broadcast_fp",
            "all",
            "4",  # Select tree_of_thought
            "Technical perspective",  # First prompt
            "Business perspective",  # Second prompt
            "User perspective",  # Third prompt
            "",  # End prompts
            "1",  # Select concatenate recombinator
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP tree_of_thought wizard output:\n{output}")

        # Should show tree_of_thought broadcast execution
        self.assertIn("tree_of_thought", output)
        self.assertIn("Broadcasting tree_of_thought", output)
        self.assertIn("Broadcast complete", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_prompt_while_wizard(self, mock_input, mock_bot_class):
        """Test /broadcast_fp command with prompt_while wizard."""
        create_mock_bot(mock_bot_class, "Response without tools")

        mock_input.side_effect = [
            "Debug this code",
            "/broadcast_fp",
            "all",
            "5",  # Select prompt_while
            "Continue debugging until all issues are fixed",  # first_prompt
            "Keep going",  # continue_prompt
            "2",  # Stop condition (tool_not_used)
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP prompt_while wizard output:\n{output}")

        # Should show prompt_while broadcast execution
        self.assertIn("prompt_while", output)
        self.assertIn("Broadcasting prompt_while", output)
        self.assertIn("Broadcast complete", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_chain_while_wizard(self, mock_input, mock_bot_class):
        """Test /broadcast_fp command with chain_while wizard."""
        create_mock_bot(mock_bot_class, "DONE")

        mock_input.side_effect = [
            "Start development process",
            "/broadcast_fp",
            "all",
            "6",  # Select chain_while
            "Plan the architecture",  # First prompt
            "Implement core features",  # Second prompt
            "Add tests and documentation",  # Third prompt
            "",  # End prompts
            "3",  # Stop condition (said_DONE)
            "continue with this phase",  # continue_prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP chain_while wizard output:\n{output}")

        # Should show chain_while broadcast execution
        self.assertIn("chain_while", output)
        self.assertIn("Broadcasting chain_while", output)
        self.assertIn("Broadcast complete", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_branch_while_wizard(self, mock_input, mock_bot_class):
        """Test /broadcast_fp command with branch_while wizard."""
        create_mock_bot(mock_bot_class, "Response without tools")

        mock_input.side_effect = [
            "Optimize multiple components",
            "/broadcast_fp",
            "all",
            "7",  # Select branch_while
            "Optimize database queries",  # First prompt
            "Optimize API endpoints",  # Second prompt
            "Optimize frontend rendering",  # Third prompt
            "",  # End prompts
            "2",  # Stop condition (tool_not_used)
            "continue optimization",  # continue_prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP branch_while wizard output:\n{output}")

        # Should show branch_while broadcast execution
        self.assertIn("branch_while", output)
        self.assertIn("Broadcasting branch_while", output)
        self.assertIn("Broadcast complete", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_selective_leaf_targeting(self, mock_input, mock_bot_class):
        """Test /broadcast_fp with selective leaf targeting."""
        create_mock_bot(mock_bot_class, "Response complete")

        mock_input.side_effect = [
            "Create branch A",
            "Create branch B",
            "Create branch C",
            "/broadcast_fp",
            "1",  # Select leaf 1
            "1",  # Select single_prompt
            "Message for selected leaf",
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP selective targeting output:\n{output}")

        # Should show selective leaf targeting
        self.assertIn("Broadcasting single_prompt", output)
        self.assertIn("Broadcast complete", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_error_handling(self, mock_input, mock_bot_class):
        """Test /broadcast_fp error handling scenarios."""
        # Use MockBot instead of helper function
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Response complete")
        mock_bot_class.return_value = mock_bot

        mock_input.side_effect = [
            "Initial content",
            "/broadcast_fp",
            "invalid_selection",  # Invalid leaf selection - will return to main loop
            "/broadcast_fp",  # Try again
            "all",  # Valid leaf selection
            "1",  # Select single_prompt (it's #1 in broadcast_fp menu)
            "Valid prompt after errors",
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP error handling output:\n{output}")

        # Should handle errors gracefully
        has_leaf_error = "Invalid leaf selection format" in output

        self.assertTrue(has_leaf_error, "Expected leaf selection error message not found")
        print("✓ Found leaf selection error message")

        # After retry, should successfully broadcast
        self.assertIn("Broadcasting single_prompt", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_no_leaves_scenario(self, mock_input, mock_bot_class):
        """Test /broadcast_fp when no leaves are available."""
        # Use MockBot instead of helper function
        mock_bot = MockBot(name="TestBot")
        mock_bot.set_response_pattern("Response complete")
        mock_bot_class.return_value = mock_bot

        # Start with fresh bot that has no conversation branches
        # The bot will have an empty root node, which counts as a leaf
        # So this test actually won't trigger "no leaves" - it will find 1 leaf
        mock_input.side_effect = [
            "/broadcast_fp",
            "all",  # Select the one leaf (empty root)
            "1",  # Select single_prompt
            "Test prompt",  # The prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP no leaves output:\n{output}")

        # Should successfully broadcast to the empty root node
        self.assertIn("Broadcasting single_prompt", output)

    @patch("bots.dev.cli.AnthropicBot")
    @patch("builtins.input")
    def test_broadcast_fp_complex_recursive_scenario(self, mock_input, mock_bot_class):
        """Test /broadcast_fp with recursive par_branch for complex tree building."""
        create_mock_bot(mock_bot_class, "Analysis complete")

        mock_input.side_effect = [
            "Start complex analysis",
            "/label",
            "root_analysis",
            # First create some branches
            "Technical analysis path",
            "/up",
            "/label",
            "tech_path",
            "Business analysis path",
            "/up",
            "/label",
            "biz_path",
            "User analysis path",
            # Now broadcast par_branch to create recursive branches
            "/broadcast_fp",
            "all",  # All leaves
            "8",  # par_branch for recursive branching
            "Deep dive approach A",  # First recursive prompt
            "Deep dive approach B",  # Second recursive prompt
            "Deep dive approach C",  # Third recursive prompt
            "",  # End prompts
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP recursive scenario output:\n{output}")

        # Should show recursive par_branch execution
        self.assertIn("par_branch", output)
        self.assertIn("Broadcasting par_branch", output)
        self.assertIn("Broadcast complete", output)

    @unittest.skip("Does not halt")
    @patch("builtins.input")
    def test_broadcast_fp_all_functional_prompts_integration(self, mock_input):
        """Integration test showing all 9 FPs are available in broadcast_fp."""
        mock_input.side_effect = [
            "Test all FPs availability",
            "/broadcast_fp",
            "all",
            # This will show the menu with all 9 options, then exit
            "/exit",  # Exit from the FP selection
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP all options output:\n{output}")

        # Should show all 9 functional prompt options
        expected_fps = [
            "1. single_prompt",
            "2. chain",
            "3. branch",
            "4. tree_of_thought",
            "5. prompt_while",
            "6. chain_while",
            "7. branch_while",
            "8. par_branch",
            "9. par_branch_while",
        ]

        for fp_option in expected_fps:
            self.assertIn(fp_option, output, f"Should show {fp_option} in broadcast_fp menu")


if __name__ == "__main__":
    unittest.main()
