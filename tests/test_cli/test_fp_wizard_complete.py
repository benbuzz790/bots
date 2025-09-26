import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import bots.dev.cli as cli_module

"""Complete test suite for all /fp command wizards."""


class TestFPWizardComplete(unittest.TestCase):
    """Test suite for all functional prompt wizards via /fp command."""

    @patch("builtins.input")
    def test_fp_single_prompt_wizard(self, mock_input):
        """Test /fp command with single_prompt wizard."""
        mock_input.side_effect = [
            "Hello bot",  # Initial chat
            "/fp",
            "1",  # Select single_prompt
            "Analyze this code structure",  # The prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP single_prompt wizard output:\n{output}")

        # Should show single_prompt execution
        self.assertIn("single_prompt", output)
        self.assertIn("Collecting parameters for single_prompt", output)
        self.assertIn("Executing single_prompt", output)

    @patch("builtins.input")
    def test_fp_branch_wizard(self, mock_input):
        """Test /fp command with branch wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "3",  # Select branch
            "Analyze from security perspective",  # First prompt
            "Analyze from performance perspective",  # Second prompt
            "Analyze from maintainability perspective",  # Third prompt
            "",  # End prompts
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP branch wizard output:\n{output}")

        # Should show branch execution
        self.assertIn("branch", output)
        self.assertIn("Collecting parameters for branch", output)
        self.assertIn("Executing branch", output)

    @patch("builtins.input")
    def test_fp_tree_of_thought_wizard(self, mock_input):
        """Test /fp command with tree_of_thought wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "4",  # Select tree_of_thought
            "Analyze technical feasibility",  # First prompt
            "Analyze business impact",  # Second prompt
            "Analyze user experience",  # Third prompt
            "",  # End prompts
            "1",  # Select concatenate recombinator
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP tree_of_thought wizard output:\n{output}")

        # Should show tree_of_thought execution
        self.assertIn("tree_of_thought", output)
        self.assertIn("Collecting parameters for tree_of_thought", output)
        self.assertIn("Executing tree_of_thought", output)

    @patch("builtins.input")
    def test_fp_prompt_while_wizard(self, mock_input):
        """Test /fp command with prompt_while wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "5",  # Select prompt_while
            "Debug this code and fix all issues",  # first_prompt
            "Continue debugging if needed",  # continue_prompt
            "2",  # Stop condition (tool_not_used)
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP prompt_while wizard output:\n{output}")

        # Should show prompt_while execution
        self.assertIn("prompt_while", output)
        self.assertIn("Collecting parameters for prompt_while", output)
        self.assertIn("Executing prompt_while", output)

    @patch("builtins.input")
    def test_fp_chain_while_wizard(self, mock_input):
        """Test /fp command with chain_while wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "6",  # Select chain_while
            "First, analyze the problem",  # First prompt
            "Then, propose solutions",  # Second prompt
            "Finally, implement the best solution",  # Third prompt
            "",  # End prompts
            "2",  # Stop condition (tool_not_used)
            "continue with this step",  # continue_prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP chain_while wizard output:\n{output}")

        # Should show chain_while execution
        self.assertIn("chain_while", output)
        self.assertIn("Collecting parameters for chain_while", output)
        self.assertIn("Executing chain_while", output)

    @patch("builtins.input")
    def test_fp_branch_while_wizard(self, mock_input):
        """Test /fp command with branch_while wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "7",  # Select branch_while
            "Optimize function A until perfect",  # First prompt
            "Optimize function B until perfect",  # Second prompt
            "Optimize function C until perfect",  # Third prompt
            "",  # End prompts
            "3",  # Stop condition (said_DONE)
            "keep optimizing",  # continue_prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP branch_while wizard output:\n{output}")

        # Should show branch_while execution
        self.assertIn("branch_while", output)
        self.assertIn("Collecting parameters for branch_while", output)
        self.assertIn("Executing branch_while", output)

    @patch("builtins.input")
    def test_fp_par_branch_wizard(self, mock_input):
        """Test /fp command with par_branch wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "8",  # Select par_branch
            "Parallel analysis approach A",  # First prompt
            "Parallel analysis approach B",  # Second prompt
            "Parallel analysis approach C",  # Third prompt
            "",  # End prompts
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP par_branch wizard output:\n{output}")

        # Should show par_branch execution
        self.assertIn("par_branch", output)
        self.assertIn("Collecting parameters for par_branch", output)
        self.assertIn("Executing par_branch", output)

    @patch("builtins.input")
    def test_fp_par_branch_while_wizard(self, mock_input):
        """Test /fp command with par_branch_while wizard."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "9",  # Select par_branch_while
            "Parallel optimization task A",  # First prompt
            "Parallel optimization task B",  # Second prompt
            "",  # End prompts
            "2",  # Stop condition (tool_not_used)
            "continue optimization",  # continue_prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP par_branch_while wizard output:\n{output}")

        # Should show par_branch_while execution
        self.assertIn("par_branch_while", output)
        self.assertIn("Collecting parameters for par_branch_while", output)
        self.assertIn("Executing par_branch_while", output)

    @patch("builtins.input")
    def test_fp_wizard_parameter_validation(self, mock_input):
        """Test /fp wizard parameter validation and error handling."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "invalid_choice",  # Invalid selection first
            "1",  # Then valid selection
            "Valid prompt after invalid choice",
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP wizard validation output:\n{output}")

        # Should handle invalid selection gracefully
        self.assertIn("Invalid selection", output)
        # But then proceed with valid selection
        self.assertIn("single_prompt", output)

    @patch("builtins.input")
    def test_fp_wizard_by_name_selection(self, mock_input):
        """Test /fp wizard selection by name instead of number."""
        mock_input.side_effect = [
            "Hello bot",
            "/fp",
            "chain",  # Select by name instead of number
            "First step",
            "Second step",
            "",  # End prompts
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nFP wizard by name output:\n{output}")

        # Should work with name selection
        self.assertIn("chain", output)
        self.assertIn("Collecting parameters for chain", output)


if __name__ == "__main__":
    unittest.main()
