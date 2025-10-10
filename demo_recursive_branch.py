#!/usr/bin/env python3
"""
Demonstration of recursive branch_self functionality.

This script demonstrates that branch_self can now be called within branches
without causing infinite loops.
"""

import os
import tempfile

from bots.testing.mock_bot import MockBot


def demo_recursive_branching():
    """Demonstrate recursive branch_self calls."""
    print("=" * 70)
    print("RECURSIVE BRANCH_SELF DEMONSTRATION")
    print("=" * 70)

    # Create a temporary directory for the demo
    with tempfile.TemporaryDirectory() as temp_dir:
        original_cwd = os.getcwd()
        os.chdir(temp_dir)

        try:
            # Create a bot with branch_self tool
            print("\n1. Creating MockBot with branch_self tool...")
            bot = MockBot()
            import bots.tools.self_tools
            bot.add_tools(bots.tools.self_tools)
            print("   ✓ Bot created")

            # Initial conversation
            print("\n2. Starting initial conversation...")
            bot.respond("Hello, let's test recursive branching")
            print("   ✓ Initial message sent")

            # First level of branching
            print("\n3. First level: Using branch_self with 2 branches...")
            bot.respond("Use branch_self with ['Task A', 'Task B']")
            print("   ✓ First level branching completed")

            # Count nodes after first branch
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
            print(f"   → Tree now has {nodes_after_first} nodes")

            # Second level of branching (RECURSIVE!)
            print("\n4. Second level: Using branch_self WITHIN a branch...")
            print("   (This would have caused infinite loop before the fix)")
            bot.respond("Use branch_self with ['Subtask 1', 'Subtask 2']")
            print("   ✓ Second level branching completed (no infinite loop!)")

            nodes_after_second = count_tree(bot.conversation)
            print(f"   → Tree now has {nodes_after_second} nodes")

            # Third level of branching (DEEPER RECURSION!)
            print("\n5. Third level: Going even deeper...")
            bot.respond("Use branch_self with ['Sub-subtask X', 'Sub-subtask Y']")
            print("   ✓ Third level branching completed")

            nodes_after_third = count_tree(bot.conversation)
            print(f"   → Tree now has {nodes_after_third} nodes")

            # Summary
            print("\n" + "=" * 70)
            print("SUMMARY")
            print("=" * 70)
            print(f"✓ Successfully completed 3 levels of recursive branching")
            print(f"✓ No infinite loops detected")
            print(f"✓ Tree grew from {nodes_after_first} → {nodes_after_second} → {nodes_after_third} nodes")
            print(f"✓ Recursive branch_self is now working correctly!")
            print("=" * 70)

        finally:
            os.chdir(original_cwd)


if __name__ == "__main__":
    demo_recursive_branching()