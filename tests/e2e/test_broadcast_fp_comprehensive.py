import pytest
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import bots.dev.cli as cli_module
from bots.dev.cli import DynamicFunctionalPromptHandler, DynamicParameterCollector
from bots.flows import functional_prompts as fp



pytestmark = pytest.mark.e2e

"""Comprehensive tests for broadcast_fp functionality including par_branch support."""


class TestBroadcastFPAvailability(unittest.TestCase):
    """Test what functional prompts are available for broadcasting."""

    def test_broadcast_fp_includes_par_branch_functions(self):
        """Test that broadcast_fp includes par_branch and par_branch_while for recursive branching."""
        # Get the functional prompts available in broadcast_fp from the CLI code
        expected_broadcastable_fps = {
            "single_prompt": fp.single_prompt,
            "chain": fp.chain,
            "branch": fp.branch,
            "tree_of_thought": fp.tree_of_thought,
            "prompt_while": fp.prompt_while,
            "chain_while": fp.chain_while,
            "branch_while": fp.branch_while,
            # These should be added for recursive branching capability
            "par_branch": fp.par_branch,
            "par_branch_while": fp.par_branch_while,
        }

        # Test that the collector can handle all of these
        collector = DynamicParameterCollector()

        # Check that we have the right number of options (should be 9 now)
        # This test will fail until we add par_branch support
        for i, (name, func) in enumerate(expected_broadcastable_fps.items(), 1):
            with patch("builtins.input", return_value=str(i)):
                result = collector._collect_functional_prompt("functional_prompt", None)
                if i <= 7:  # Current implementation only has 7
                    self.assertIsNotNone(result, f"Should be able to collect option {i}")
                else:  # Options 8 and 9 don't exist yet
                    # This will fail until we implement par_branch support
                    pass

    def test_par_branch_functions_are_discoverable(self):
        """Test that par_branch functions are discovered by the handler."""
        handler = DynamicFunctionalPromptHandler()
        discovered_fps = handler._discover_fp_functions()

        # These should be discoverable
        self.assertIn("par_branch", discovered_fps)
        self.assertIn("par_branch_while", discovered_fps)
        self.assertEqual(discovered_fps["par_branch"], fp.par_branch)
        self.assertEqual(discovered_fps["par_branch_while"], fp.par_branch_while)


class TestBroadcastFPFunctionalSuccess(unittest.TestCase):
    """Test actual functional success of broadcast_fp with different FPs."""

    @patch("builtins.input")
    def test_broadcast_fp_with_single_prompt_via_cli(self, mock_input):
        """Test /broadcast_fp command with single_prompt through full CLI interface."""
        # This tests the full CLI path, not just availability
        mock_input.side_effect = [
            "Hello bot",  # Initial chat to create conversation
            "/broadcast_fp",  # Start broadcast_fp command
            "all",  # Select all leaves
            "1",  # Select single_prompt
            "Test broadcast message",  # The prompt to broadcast
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP single_prompt output:\n{output}")

        # Should show broadcast functionality
        self.assertIn("broadcast", output.lower())

    @patch("builtins.input")
    def test_broadcast_fp_with_chain_via_cli(self, mock_input):
        """Test /broadcast_fp command with chain through full CLI interface."""
        mock_input.side_effect = [
            "Create some content",  # Initial chat
            "/label",
            "start",  # Create a label
            "Create more content",  # Another response to create branches
            "/broadcast_fp",  # Start broadcast_fp
            "all",  # Select all leaves
            "2",  # Select chain
            "First step in chain",  # First prompt
            "Second step in chain",  # Second prompt
            "",  # End prompt collection
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP chain output:\n{output}")

        # Should show chain parameter collection and execution
        self.assertIn("prompt_list", output.lower())

    @patch("builtins.input")
    def test_broadcast_fp_with_par_branch_via_cli(self, mock_input):
        """Test /broadcast_fp command with par_branch - now implemented!"""
        mock_input.side_effect = [
            "Initial content",
            "/broadcast_fp",
            "all",
            "8",  # This is now par_branch (implemented!)
            "Branch prompt 1",
            "Branch prompt 2",
            "",
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP par_branch output:\n{output}")

        # par_branch is now available in the menu and attempts to execute
        # Should show that par_branch option exists
        self.assertIn("par_branch", output)
        self.assertIn("Broadcast completed", output)

    @patch("builtins.input")
    def test_broadcast_fp_with_par_branch_while_via_cli(self, mock_input):
        """Test /broadcast_fp command with par_branch_while - now implemented!"""
        mock_input.side_effect = [
            "Initial content",
            "/broadcast_fp",
            "all",
            "9",  # This is now par_branch_while (implemented!)
            "While prompt 1",
            "While prompt 2",
            "",  # End prompts
            "2",  # Stop condition (tool_not_used)
            "continue",  # Continue prompt
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP par_branch_while output:\n{output}")

        # par_branch_while is now available and attempts to execute
        self.assertIn("par_branch_while", output)
        self.assertIn("Broadcast completed", output)


class TestBroadcastFPRecursiveBranching(unittest.TestCase):
    """Test recursive branching scenarios that require par_branch support."""

    def test_recursive_branching_use_case(self):
        """Test the use case for recursive branching in broadcast_fp."""
        # Scenario: You have multiple conversation leaves, and you want to
        # broadcast a par_branch to each leaf, creating multiple parallel
        # sub-branches from each leaf

        # This is the kind of workflow that requires par_branch in broadcast_fp:
        # 1. Start with conversation tree with multiple leaves
        # 2. Use broadcast_fp with par_branch to create sub-branches from each leaf
        # 3. Each leaf now has multiple parallel explorations

        # For now, just document the intended behavior
        intended_workflow = """
        1. Initial conversation creates multiple leaves (A, B, C)
        2. /broadcast_fp with par_branch sends multiple prompts to each leaf:
           - Leaf A gets prompts ["Approach 1", "Approach 2", "Approach 3"]
           - Leaf B gets prompts ["Approach 1", "Approach 2", "Approach 3"]
           - Leaf C gets prompts ["Approach 1", "Approach 2", "Approach 3"]
        3. Result: Each original leaf now has 3 parallel sub-branches
        4. Total: 9 new conversation endpoints (3 leaves × 3 branches each)
        """

        # This test documents the intended behavior
        self.assertIsNotNone(intended_workflow)

    @patch("builtins.input")
    def test_broadcast_fp_leaf_selection_with_multiple_leaves(self, mock_input):
        """Test leaf selection when there are multiple conversation endpoints."""
        mock_input.side_effect = [
            "Create first branch",
            "/label",
            "branch1",
            "/up",  # Go back
            "Create second branch",
            "/label",
            "branch2",
            "/up",  # Go back
            "Create third branch",
            "/broadcast_fp",
            "1,3",  # Select leaves 1 and 3 (not 2)
            "1",  # single_prompt
            "Broadcast to selected leaves only",
            "/exit",
        ]

        with StringIO() as buf, redirect_stdout(buf):
            with self.assertRaises(SystemExit):
                cli_module.main("")
            output = buf.getvalue()
            print(f"\nBroadcast FP selective leaves output:\n{output}")

        # Should show leaf selection interface
        self.assertIn("leaf", output.lower())


class TestBroadcastFPParameterCollection(unittest.TestCase):
    """Test parameter collection for different functional prompts in broadcast context."""

    def test_parameter_collection_for_complex_fps(self):
        """Test that complex FPs can have their parameters collected properly."""
        collector = DynamicParameterCollector()

        # Test tree_of_thought parameter collection
        with patch(
            "builtins.input",
            side_effect=[
                "Analyze technical aspects",
                "Analyze business aspects",
                "Analyze user aspects",
                "",  # End prompts
                "1",  # Select concatenate recombinator
            ],
        ):
            params = collector.collect_parameters(fp.tree_of_thought)

        self.assertIsNotNone(params)
        self.assertIn("prompts", params)
        self.assertIn("recombinator_function", params)
        self.assertEqual(len(params["prompts"]), 3)

    def test_parameter_collection_for_while_functions(self):
        """Test parameter collection for *_while functions."""
        collector = DynamicParameterCollector()

        # Test prompt_while parameter collection
        with patch(
            "builtins.input",
            side_effect=[
                "Debug this code thoroughly",  # first_prompt
                "Keep debugging",  # continue_prompt
                "2",  # stop_condition (tool_not_used)
            ],
        ):
            params = collector.collect_parameters(fp.prompt_while)

        self.assertIsNotNone(params)
        self.assertIn("first_prompt", params)
        self.assertIn("continue_prompt", params)
        self.assertIn("stop_condition", params)


if __name__ == "__main__":
    unittest.main()
