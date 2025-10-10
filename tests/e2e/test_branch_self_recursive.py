"""
Test suite for verifying recursive branch_self functionality.

This test ensures that branch_self can be called within branches created by branch_self
without causing infinite loops.
"""

import os
import tempfile
import unittest

import pytest

from bots.testing.mock_bot import MockBot

pytestmark = pytest.mark.e2e


class TestBranchSelfRecursive(unittest.TestCase):
    """Test recursive branch_self calls."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_single_level_recursion(self):
        """
    Test that branch_self can be called once within a branch.
    This is the simplest recursive case.
    """
        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # Initial conversation
        bot.respond("Start")

        # First level branch_self
        bot.respond("Use branch_self with ['Task A', 'Task B']")

        # Count nodes before second branch_self
        def count_tree(node):
            root = node
            while root.parent:
                root = root.parent

            def count_recursive(n):
                count = 1
                for reply in n.replies:
                    count += count_recursive(reply)
                return count

            return count_recursive(root)

        nodes_before = count_tree(bot.conversation)

        # Second level branch_self (within a branch)
        # This should NOT cause infinite loop
        bot.respond("Use branch_self with ['Subtask 1', 'Subtask 2']")

        nodes_after = count_tree(bot.conversation)

        # Verify that nodes were added (not stuck in loop)
        self.assertGreater(nodes_after, nodes_before, "Second branch_self should add nodes")

        print(f"✅ Test passed: Single level recursion works ({nodes_before} -> {nodes_after} nodes)")

    def test_two_level_recursion(self):
        """
    Test that branch_self can be called twice within nested branches.
    This tests deeper recursion.
    """
        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # Initial conversation
        bot.respond("Start")

        # First level
        bot.respond("Use branch_self with ['Level1-A', 'Level1-B']")

        # Second level
        bot.respond("Use branch_self with ['Level2-A', 'Level2-B']")

        # Third level (this is the critical test)
        bot.respond("Use branch_self with ['Level3-A', 'Level3-B']")

        # If we got here without hanging, the test passed
        def count_tree(node):
            root = node
            while root.parent:
                root = root.parent

            def count_recursive(n):
                count = 1
                for reply in n.replies:
                    count += count_recursive(reply)
                return count

            return count_recursive(root)

        total_nodes = count_tree(bot.conversation)

        # With 3 levels of branching (2 branches each), we should have many nodes
        self.assertGreater(total_nodes, 5, "Three levels of branching should create multiple nodes")

        print(f"✅ Test passed: Two level recursion works ({total_nodes} nodes)")

    def test_recursive_branching_no_infinite_loop(self):
        """
    Test that recursive branching completes in reasonable time.
    This is a timeout test to ensure no infinite loops.
    """
        import signal

        # Set a timeout to catch infinite loops
        def timeout_handler(signum, frame):
            raise TimeoutError("Test took too long - likely infinite loop")

        # Use alarm on Unix systems, or just rely on test framework timeout
        try:
            signal.signal(signal.SIGALRM, timeout_handler)
            signal.alarm(30)  # 30 second timeout
        except (AttributeError, ValueError):
            # Windows doesn't have SIGALRM, skip timeout setup
            pass

        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        try:
            # Initial conversation
            bot.respond("Start")

            # Nested branch_self calls
            bot.respond("Use branch_self with ['A', 'B']")
            bot.respond("Use branch_self with ['C', 'D']")

            # If we reach here, no infinite loop occurred
            try:
                signal.alarm(0)  # Cancel alarm
            except (AttributeError, ValueError):
                pass

            print("✅ Test passed: No infinite loop detected")

        except TimeoutError:
            self.fail("Recursive branching caused infinite loop (timeout)")

    def test_branch_positioning_after_recursive_load(self):
        """
    Test that after loading in a branch, the conversation is positioned
    at the tagged node, not at replies[-1].
    """
        from bots.foundation.base import Bot

        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # Create initial state
        bot.respond("Start")
        bot.respond("Use branch_self with ['Branch A', 'Branch B']")

        # Get the current node count
        def count_tree(node):
            root = node
            while root.parent:
                root = root.parent

            def count_recursive(n):
                count = 1
                for reply in n.replies:
                    count += count_recursive(reply)
                return count

            return count_recursive(root)

        nodes_before = count_tree(bot.conversation)

        # Save and load to simulate what happens in branch_self
        bot.save("test_positioning.bot")
        loaded_bot = Bot.load("test_positioning.bot")

        # The loaded bot should be at a leaf node (replies[-1] behavior)
        self.assertEqual(
            len(loaded_bot.conversation.replies),
            0,
            "Loaded bot should be at a leaf node",
        )

        # Now use branch_self again - this should work without infinite loop
        loaded_bot.respond("Use branch_self with ['Sub A', 'Sub B']")

        nodes_after = count_tree(loaded_bot.conversation)

        # Verify nodes were added
        self.assertGreater(
            nodes_after, nodes_before, "Recursive branch_self should add nodes"
        )

        print(
            f"✅ Test passed: Branch positioning correct ({nodes_before} -> {nodes_after} nodes)"
        )


if __name__ == "__main__":
    unittest.main(verbosity=2)
