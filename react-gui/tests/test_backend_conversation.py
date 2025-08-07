#!/usr/bin/env python3
"""
Test script to directly test backend conversation handling and see debug logs.
"""

import asyncio
import sys
import os

# Add the backend directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'backend'))

from bot_manager import BotManager

async def test_conversation_building():
    """Test conversation building and see debug logs."""
    print("🚀 Testing Backend Conversation Building")
    print("=" * 60)

    # Create bot manager
    bot_manager = BotManager()

    # Create a bot
    print("📝 Creating bot...")
    bot_id = await bot_manager.create_bot("Test Bot")
    print(f"✅ Created bot: {bot_id}")

    # Send first message
    print("\n📤 Sending first message...")
    bot_state1 = await bot_manager.send_message(bot_id, "Hello, this is my first message!")
    print(f"✅ First response received")
    print(f"   Conversation tree size: {len(bot_state1.conversation_tree)}")
    print(f"   Current node: {bot_state1.current_node_id}")

    # Send second message
    print("\n📤 Sending second message...")
    bot_state2 = await bot_manager.send_message(bot_id, "This is my second message. Can you help me?")
    print(f"✅ Second response received")
    print(f"   Conversation tree size: {len(bot_state2.conversation_tree)}")
    print(f"   Current node: {bot_state2.current_node_id}")

    # Send third message
    print("\n📤 Sending third message...")
    bot_state3 = await bot_manager.send_message(bot_id, "And this is my third message for testing.")
    print(f"✅ Third response received")
    print(f"   Conversation tree size: {len(bot_state3.conversation_tree)}")
    print(f"   Current node: {bot_state3.current_node_id}")

    # Analyze the final conversation tree
    print(f"\n🔍 Final Conversation Analysis:")
    print(f"   Total nodes: {len(bot_state3.conversation_tree)}")

    for node_id, node in bot_state3.conversation_tree.items():
        print(f"   Node {node_id[:8]}...")
        print(f"     Role: {node.message.role}")
        print(f"     Content: {node.message.content[:50]}...")
        print(f"     Parent: {node.parent[:8] + '...' if node.parent else 'None'}")
        print(f"     Children: {[c[:8] + '...' for c in node.children]}")
        print(f"     Is Current: {node.is_current}")
        print()

    print("=" * 60)
    print("✅ Backend conversation test completed")

    return len(bot_state3.conversation_tree)

if __name__ == "__main__":
    try:
        result = asyncio.run(test_conversation_building())
        print(f"\n🏁 Test completed - final tree had {result} nodes")
        if result < 6:  # Should have at least 6 nodes (3 user + 3 assistant)
            print("⚠️  Warning: Expected more nodes in conversation tree")
            sys.exit(1)
        else:
            print("✅ Conversation tree looks good!")
            sys.exit(0)
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)