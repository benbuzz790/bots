#!/usr/bin/env python3
"""
Test to examine the bot's internal conversation structure vs GUI conversion.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from bot_manager import BotManager

async def test_conversion_theory():
    """Test the bot's internal structure vs GUI conversion."""
    print("🔍 Testing Conversion Theory")
    print("=" * 60)

    # Create bot manager and bot
    bot_manager = BotManager()
    bot_id = await bot_manager.create_bot("Test Bot")

    # Send a few messages to build conversation history
    print("📤 Building conversation history...")
    await bot_manager.send_message(bot_id, "First message")
    await bot_manager.send_message(bot_id, "Second message") 
    bot_state = await bot_manager.send_message(bot_id, "Third message")

    # Get the actual bot object
    bot = await bot_manager.get_bot(bot_id)

    print(f"\n🤖 Bot Internal Structure Analysis:")
    print(f"   Bot conversation current node: {bot.conversation}")
    print(f"   Current node role: {getattr(bot.conversation, 'role', 'no role')}")
    print(f"   Current node content: {getattr(bot.conversation, 'content', 'no content')[:50]}...")

    # Walk up the conversation tree to see full history
    print(f"\n📜 Full Conversation History (walking up from current):")
    current = bot.conversation
    depth = 0
    nodes_found = []

    while current and depth < 20:  # Prevent infinite loops
        role = getattr(current, 'role', 'no role')
        content = getattr(current, 'content', 'no content')
        content_preview = content[:50] + "..." if len(content) > 50 else content

        print(f"   Depth {depth}: Role={role}, Content='{content_preview}'")
        nodes_found.append((role, content))

        # Try to go to parent
        if hasattr(current, 'parent'):
            current = current.parent
        else:
            print(f"   No parent attribute found at depth {depth}")
            break
        depth += 1

    print(f"\n📊 Internal Structure Summary:")
    print(f"   Total nodes found walking up: {len(nodes_found)}")
    print(f"   Expected nodes: 6 (3 user + 3 assistant)")

    # Now test the root finding
    print(f"\n🌳 Root Finding Test:")
    if hasattr(bot.conversation, '_find_root'):
        root = bot.conversation._find_root()
        print(f"   Root node: {root}")
        print(f"   Root role: {getattr(root, 'role', 'no role')}")
        print(f"   Root content: {getattr(root, 'content', 'no content')[:50]}...")
        print(f"   Root is empty: {root._is_empty() if hasattr(root, '_is_empty') else 'no _is_empty method'}")
    else:
        print(f"   No _find_root method available")

    # Compare with GUI conversion result
    print(f"\n🔄 GUI Conversion Result:")
    print(f"   Converted tree size: {len(bot_state.conversation_tree)}")
    print(f"   GUI thinks current node is: {bot_state.current_node_id}")

    # Show what the GUI actually converted
    for node_id, node in bot_state.conversation_tree.items():
        print(f"   GUI Node {node_id[:8]}...")
        print(f"     Role: {node.message.role}")
        print(f"     Content: {node.message.content[:50]}...")

    print("=" * 60)

    # Determine if theory is correct
    internal_nodes = len(nodes_found)
    gui_nodes = len(bot_state.conversation_tree)

    if internal_nodes > gui_nodes:
        print("✅ THEORY CONFIRMED: Bot has more conversation history than GUI is converting")
        print(f"   Bot internal: {internal_nodes} nodes")
        print(f"   GUI converted: {gui_nodes} nodes")
        return True
    else:
        print("❌ THEORY REJECTED: Bot and GUI have same amount of data")
        print(f"   Bot internal: {internal_nodes} nodes") 
        print(f"   GUI converted: {gui_nodes} nodes")
        return False

if __name__ == "__main__":
    try:
        theory_confirmed = asyncio.run(test_conversion_theory())
        sys.exit(0 if theory_confirmed else 1)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)