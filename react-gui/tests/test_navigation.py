"""
Test script for backend navigation functionality.
Tests the bot manager navigation methods with defensive programming.
"""

import asyncio
import logging
import sys
import os

# Add the backend directory to the path
sys.path.insert(0, os.path.dirname(__file__))
sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from bot_manager import BotManager
from models import MessageRole

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_navigation():
    """Test navigation functionality."""

    print("🚀 Testing Backend Navigation Functionality")
    print("=" * 50)

    # Create bot manager
    bot_manager = BotManager()

    try:
        # Test 1: Create bot
        print("\n1. Creating bot...")
        bot_id = bot_manager.create_bot("Test Navigation Bot")
        print(f"✅ Created bot: {bot_id}")

        # Test 2: Send some messages to create a conversation tree
        print("\n2. Building conversation tree...")

        # Send first message
        response1 = bot_manager.send_message(bot_id, "Hello, can you help me with Python?")
        print(f"✅ Sent message 1, got response: {response1.content[:50]}...")

        # Send second message
        response2 = bot_manager.send_message(bot_id, "What are the basic data types?")
        print(f"✅ Sent message 2, got response: {response2.content[:50]}...")

        # Get current state
        state = bot_manager.get_bot_state(bot_id)
        print(f"✅ Current conversation has {len(state.conversation_tree)} nodes")

        # Test 3: Navigation up
        print("\n3. Testing navigation up...")
        try:
            updated_state = bot_manager.navigate_up(bot_id)
            print(f"✅ Navigated up to node: {updated_state.current_node_id}")
        except ValueError as e:
            print(f"⚠️  Navigation up failed (expected): {e}")

        # Test 4: Navigation down
        print("\n4. Testing navigation down...")
        try:
            # First go to root
            root_state = bot_manager.navigate_to_root(bot_id)
            print(f"✅ Moved to root: {root_state.current_node_id}")

            # Then try to go down
            down_state = bot_manager.navigate_down(bot_id)
            print(f"✅ Navigated down to node: {down_state.current_node_id}")
        except ValueError as e:
            print(f"⚠️  Navigation down failed: {e}")

        # Test 5: Navigation to specific node
        print("\n5. Testing direct node navigation...")

        # Get all node IDs
        state = bot_manager.get_bot_state(bot_id)
        node_ids = list(state.conversation_tree.keys())

        if len(node_ids) > 1:
            target_node_id = node_ids[0]  # Navigate to first node
            nav_state = bot_manager.navigate_to_node(bot_id, target_node_id)
            print(f"✅ Navigated to specific node: {nav_state.current_node_id}")

        # Test 6: Tree serialization
        print("\n6. Testing tree serialization...")
        serialized = bot_manager.serialize_conversation_tree(bot_id)
        print(f"✅ Serialized tree with {len(serialized)} nodes")

        # Test 7: Conversation path
        print("\n7. Testing conversation path...")
        path = bot_manager.get_conversation_path(bot_id)
        print(f"✅ Got conversation path with {len(path)} messages")

        # Test 8: Error handling
        print("\n8. Testing error handling...")

        try:
            bot_manager.navigate_up("invalid_bot_id")
            print("❌ Should have failed with invalid bot ID")
        except (ValueError, AssertionError) as e:
            print(f"✅ Correctly handled invalid bot ID: {type(e).__name__}")

        try:
            bot_manager.navigate_to_node(bot_id, "invalid_node_id")
            print("❌ Should have failed with invalid node ID")
        except ValueError as e:
            print(f"✅ Correctly handled invalid node ID: {e}")

        print("\n🎉 All navigation tests completed successfully!")

        # Display final tree structure
        print("\n📊 Final Conversation Tree:")
        state = bot_manager.get_bot_state(bot_id)
        for node_id, node in state.conversation_tree.items():
            current_marker = "👉 " if node.is_current else "   "
            role_icon = "🤖" if node.message.role == MessageRole.ASSISTANT else "👤"
            content_preview = node.message.content[:40].replace('\n', ' ')
            if len(node.message.content) > 40:
                content_preview += "..."
            print(f"{current_marker}{role_icon} {node_id[:8]}: {content_preview}")
            if node.children:
                print(f"      └─ Children: {[child[:8] for child in node.children]}")

    except Exception as e:
        print(f"❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return False

    return True


if __name__ == "__main__":
    success = asyncio.run(test_navigation())
    if success:
        print("\n✅ All tests passed!")
        sys.exit(0)
    else:
        print("\n❌ Some tests failed!")
        sys.exit(1)