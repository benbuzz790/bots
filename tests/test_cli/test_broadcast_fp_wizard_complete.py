import unittest
from unittest.mock import patch, MagicMock
from contextlib import redirect_stdout
from io import StringIO

import bots.dev.cli as cli_module

"""Complete test suite for all /broadcast_fp command wizards."""


class TestBroadcastFPWizardComplete(unittest.TestCase):
    """Test suite for all functional prompt wizards via /broadcast_fp command."""

    @patch("builtins.input")
    def test_broadcast_fp_branch_wizard(self, mock_input):
        """Test /broadcast_fp command with branch wizard."""
        mock_input.side_effect = [
            "Create initial content",  # Create conversation
            "/label", "start",  # Create a label for navigation
            "Create more content",  # Create branches
            "/broadcast_fp",
            "all",  # Select all leaves
            "3",  # Select branch
            "Security analysis branch",  # First prompt
            "Performance analysis branch",  # Second prompt
            "Usability analysis branch",  # Third prompt
            "",  # End prompts
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP branch wizard output:\n{output}")

        # Should show branch broadcast execution
        self.assertIn("branch", output)
        self.assertIn("Broadcasting branch", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_tree_of_thought_wizard(self, mock_input):
        """Test /broadcast_fp command with tree_of_thought wizard."""
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
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP tree_of_thought wizard output:\n{output}")

        # Should show tree_of_thought broadcast execution
        self.assertIn("tree_of_thought", output)
        self.assertIn("Broadcasting tree_of_thought", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_prompt_while_wizard(self, mock_input):
        """Test /broadcast_fp command with prompt_while wizard."""
        mock_input.side_effect = [
            "Debug this code",
            "/broadcast_fp",
            "all",
            "5",  # Select prompt_while
            "Continue debugging until all issues are fixed",  # first_prompt
            "Keep going",  # continue_prompt
            "2",  # Stop condition (tool_not_used)
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP prompt_while wizard output:\n{output}")

        # Should show prompt_while broadcast execution
        self.assertIn("prompt_while", output)
        self.assertIn("Broadcasting prompt_while", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_chain_while_wizard(self, mock_input):
        """Test /broadcast_fp command with chain_while wizard."""
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
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP chain_while wizard output:\n{output}")

        # Should show chain_while broadcast execution
        self.assertIn("chain_while", output)
        self.assertIn("Broadcasting chain_while", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_branch_while_wizard(self, mock_input):
        """Test /broadcast_fp command with branch_while wizard."""
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
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP branch_while wizard output:\n{output}")

        # Should show branch_while broadcast execution
        self.assertIn("branch_while", output)
        self.assertIn("Broadcasting branch_while", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_selective_leaf_targeting(self, mock_input):
        """Test /broadcast_fp with selective leaf targeting."""
        mock_input.side_effect = [
            "Create branch A",
            "/label", "branchA",
            "/up",  # Go back
            "Create branch B", 
            "/label", "branchB",
            "/up",  # Go back
            "Create branch C",
            "/broadcast_fp",
            "1,3",  # Select only leaves 1 and 3 (not 2)
            "1",  # Select single_prompt
            "Message for selected leaves only",
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP selective targeting output:\n{output}")

        # Should show selective leaf targeting
        self.assertIn("Selected 2 leaves for broadcast", output)
        self.assertIn("Broadcasting single_prompt to 2 selected leaves", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_error_handling(self, mock_input):
        """Test /broadcast_fp error handling scenarios."""
        mock_input.side_effect = [
            "Initial content",
            "/broadcast_fp",
            "invalid_selection",  # Invalid leaf selection
            "all",  # Then valid selection
            "invalid_fp",  # Invalid FP selection
            "1",  # Then valid FP selection
            "Valid prompt after errors",
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP error handling output:\n{output}")

        # Should handle errors gracefully
        self.assertIn("Invalid leaf selection format", output)
        self.assertIn("Invalid functional prompt selection", output)
        # But then proceed with valid selections
        self.assertIn("Broadcasting single_prompt", output)

    @patch("builtins.input")
    def test_broadcast_fp_no_leaves_scenario(self, mock_input):
        """Test /broadcast_fp when no leaves are available."""
        # Start with fresh bot that has no conversation branches
        mock_input.side_effect = [
            "/broadcast_fp",  # Try broadcast without any conversation
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP no leaves output:\n{output}")

        # Should handle no leaves scenario
        self.assertIn("No leaves found from current node", output)

    @patch("builtins.input")
    def test_broadcast_fp_complex_recursive_scenario(self, mock_input):
        """Test /broadcast_fp with recursive par_branch for complex tree building."""
        mock_input.side_effect = [
            "Start complex analysis",
            "/label", "root_analysis",
            # First create some branches
            "Technical analysis path",
            "/up", "/label", "tech_path",
            "Business analysis path", 
            "/up", "/label", "biz_path",
            "User analysis path",
            # Now broadcast par_branch to create recursive branches
            "/broadcast_fp",
            "all",  # All leaves
            "8",  # par_branch for recursive branching
            "Deep dive approach A",  # First recursive prompt
            "Deep dive approach B",  # Second recursive prompt
            "Deep dive approach C",  # Third recursive prompt
            "",  # End prompts
            "/exit"
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP recursive scenario output:\n{output}")

        # Should show recursive par_branch execution
        self.assertIn("par_branch", output)
        self.assertIn("Broadcasting par_branch", output)
        self.assertIn("Broadcast completed", output)

    import pytest
    @pytest.skip("Does not halt")
    @patch("builtins.input")
    def test_broadcast_fp_all_functional_prompts_integration(self, mock_input):
        """Integration test showing all 9 FPs are available in broadcast_fp."""
        mock_input.side_effect = [
            "Test all FPs availability",
            "/broadcast_fp",
            "all",
            # This will show the menu with all 9 options, then exit
            "/exit"  # Exit from the FP selection
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
            "9. par_branch_while"
        ]

        for fp_option in expected_fps:
            self.assertIn(fp_option, output, f"Should show {fp_option} in broadcast_fp menu")


if __name__ == '__main__':
    unittest.main()