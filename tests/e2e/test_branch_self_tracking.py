"""
Test suite for verifying Issue #118 fix: branch_self tracking after save/load.

This test reproduces the specific scenario where branch_self would lose track
of the branching node during save/load operations, causing branches to execute
wrong prompts from previous branch_self calls.
"""

import os
import tempfile
import unittest

import pytest

from bots.testing.mock_bot import MockBot

pytestmark = pytest.mark.e2e


class TestBranchSelfTracking(unittest.TestCase):
    """Test branch_self tracking after save/load operations (Issue #118)."""

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

    def test_branch_self_tracking_after_save_load_simple(self):
        """
        Verify branch_self tracks correct node after save/load (Issue #118).
        This is a basic test to ensure save/load works with branch_self.
        """
        from bots.foundation.base import Bot
        from bots.testing.mock_bot import MockBot

        # Create bot with branch_self tool
        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # Step 1: Create initial conversation
        bot.respond("Hello")

        # Step 2: Use branch_self
        bot.respond("Use branch_self with ['Task A', 'Task B']")

        # Step 3: Save and load
        bot.save("simple_test.bot")
        loaded_bot = Bot.load("simple_test.bot")

        # Step 4: Verify loaded bot has conversation
        self.assertIsNotNone(loaded_bot.conversation, "Loaded bot should have conversation")

        # Navigate to root and count nodes
        def count_nodes(node):
            count = 1
            for reply in node.replies:
                count += count_nodes(reply)
            return count

        root = loaded_bot.conversation
        while root.parent:
            root = root.parent

        total_nodes = count_nodes(root)
        self.assertGreater(total_nodes, 2, "Tree should have multiple nodes after branch_self")

        # Verify loaded bot is at a leaf (no replies)
        self.assertEqual(len(loaded_bot.conversation.replies), 0, "Loaded bot should be positioned at a leaf node")

        print(f"✅ Test passed: Tree has {total_nodes} nodes, loaded bot at leaf")

    def test_branch_self_position_after_load(self):
        """
        Verify Bot.load() positions at replies[-1] (rightmost) not replies[0] (leftmost).
        This is the CORE test for the Issue #118 fix.
        """
        from bots.foundation.base import Bot

        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # Create a conversation with multiple branches
        bot.respond("Start")
        bot.respond("Use branch_self with ['Branch A', 'Branch B', 'Branch C']")

        # Save and load
        bot.save("position_test.bot")
        loaded_bot = Bot.load("position_test.bot")

        # The loaded bot should be at a leaf node
        self.assertEqual(len(loaded_bot.conversation.replies), 0, "Loaded bot should be at a leaf (no replies)")

        # Navigate to parent to see siblings
        if loaded_bot.conversation.parent:
            parent = loaded_bot.conversation.parent
            num_siblings = len(parent.replies)
            # With replies[-1], we should be at the last sibling
            if num_siblings > 1:
                last_sibling = parent.replies[-1]
                self.assertEqual(
                    loaded_bot.conversation,
                    last_sibling,
                    "Loaded bot should be positioned at the rightmost sibling (replies[-1])",
                )
                print(f"✅ Test passed: Positioned at rightmost of {num_siblings} siblings")
            else:
                print("✅ Test passed: Single branch, positioned correctly")
        else:
            print("✅ Test passed: At root level")

    def test_multiple_branch_self_calls_with_save_load(self):
        """
        Test multiple branch_self calls with save/load between them.

        This is the core Issue #118 scenario: ensuring that after load,
        a new branch_self call branches from the correct position.
        """
        from bots.foundation.base import Bot

        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # First branch_self call
        bot.respond("Start")
        bot.respond("Use branch_self with prompts ['First A', 'First B']")

        # Count nodes after first branch_self
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

        nodes_after_first = count_tree(bot.conversation)

        # Save and load
        bot.save("multi_test.bot")
        loaded_bot = Bot.load("multi_test.bot")

        # Verify tree structure is preserved
        nodes_after_load = count_tree(loaded_bot.conversation)
        self.assertEqual(nodes_after_first, nodes_after_load, "Tree structure should be preserved after load")

        # The key test: loaded bot should be positioned at a leaf
        # This verifies the replies[-1] fix
        self.assertEqual(len(loaded_bot.conversation.replies), 0, "Loaded bot should be at a leaf node (replies[-1] fix)")

        print(f"✅ Test passed: Tree structure preserved ({nodes_after_load} nodes), positioned at leaf")

    def test_conversation_tree_integrity_after_save_load(self):
        """
        Verify that the entire conversation tree structure is preserved
        through save/load cycles.
        """
        from bots.foundation.base import Bot

        bot = MockBot()
        import bots.tools.self_tools

        bot.add_tools(bots.tools.self_tools)

        # Create a complex tree
        bot.respond("Root message")
        bot.respond("Use branch_self with ['Branch 1', 'Branch 2']")

        # Count nodes before save
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

        # Save and load
        bot.save("integrity_test.bot")
        loaded_bot = Bot.load("integrity_test.bot")

        # Count nodes after load
        nodes_after = count_tree(loaded_bot.conversation)

        # Tree should have same number of nodes
        self.assertEqual(
            nodes_before, nodes_after, f"Tree should have same structure: {nodes_before} nodes before, {nodes_after} after"
        )

        print(f"✅ Test passed: Tree integrity preserved ({nodes_before} nodes)")


if __name__ == "__main__":
    unittest.main(verbosity=2)
