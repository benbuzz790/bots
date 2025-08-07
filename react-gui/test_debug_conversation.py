#!/usr/bin/env python3
"""
Debug test to trace exactly what happens during conversation tree creation.
"""

import asyncio
import sys
import os
from typing import Dict, Any
from unittest.mock import MagicMock
from datetime import datetime
import uuid

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Mock the bots framework
class MockBot:
    def __init__(self):
        self.name = "Mock Bot"
        self.conversation_history = []

    def add_tools(self, tools):
        pass

    def respond(self, message: str) -> str:
        self.conversation_history.append(("user", message))
        response = f"Mock response to: {message}"
        self.conversation_history.append(("assistant", response))
        return response

# Create comprehensive mock modules
mock_tools = MagicMock()
mock_anthropic_bots = MagicMock()
mock_anthropic_bots.AnthropicBot = MockBot
mock_foundation = MagicMock()
mock_foundation.anthropic_bots = mock_anthropic_bots
mock_bots = MagicMock()
mock_bots.foundation = mock_foundation
mock_bots.tools = mock_tools
mock_bots.tools.code_tools = mock_tools

# Install the mocks
sys.modules['bots'] = mock_bots
sys.modules['bots.foundation'] = mock_foundation
sys.modules['bots.foundation.anthropic_bots'] = mock_anthropic_bots
sys.modules['bots.tools'] = mock_tools
sys.modules['bots.tools.code_tools'] = mock_tools

# Now import our backend modules
from bot_manager import BotManager
from models import BotState, ConversationNode, Message, MessageRole

async def debug_conversation_creation():
    """Debug conversation tree creation step by step."""
    print("🔍 Debug: Conversation Tree Creation")
    print("=" * 50)

    # Create BotManager and bot
    bot_manager = BotManager()
    bot_id = bot_manager.create_bot("Debug Bot")
    print(f"✅ Bot created: {bot_id}")

    # Check internal state before message
    print(f"\n📋 Before message:")
    print(f"   _conversation_trees[{bot_id}]: {len(bot_manager._conversation_trees[bot_id])} items")
    print(f"   _current_node_ids[{bot_id}]: {bot_manager._current_node_ids[bot_id]}")

    # Manually trace through send_message logic
    print(f"\n🔍 Tracing send_message logic...")
    content = "Hello, debug message!"

    # Get bot and call respond
    bot = bot_manager._bots[bot_id]
    response = bot.respond(content.strip())
    print(f"   Bot response: {response}")

    # Get existing conversation tree
    conversation_tree = bot_manager._conversation_trees[bot_id].copy()
    current_node_id = bot_manager._current_node_ids[bot_id]
    print(f"   Existing tree size: {len(conversation_tree)}")
    print(f"   Current node ID: {current_node_id}")

    # Generate new node IDs
    user_msg_id = str(uuid.uuid4())
    bot_msg_id = str(uuid.uuid4())
    print(f"   Generated user_msg_id: {user_msg_id}")
    print(f"   Generated bot_msg_id: {bot_msg_id}")

    # Create user message
    user_message = Message(
        id=user_msg_id,
        role=MessageRole.USER,
        content=content.strip(),
        timestamp=datetime.utcnow().isoformat(),
        tool_calls=[]
    )
    print(f"   Created user message: {user_message.id}")

    # Create user node
    user_node = ConversationNode(
        id=user_msg_id,
        message=user_message,
        parent=current_node_id,
        children=[bot_msg_id],
        is_current=False
    )
    print(f"   Created user node: {user_node.id}")

    # Create bot message
    bot_message = Message(
        id=bot_msg_id,
        role=MessageRole.ASSISTANT,
        content=response,
        timestamp=datetime.utcnow().isoformat(),
        tool_calls=[]
    )
    print(f"   Created bot message: {bot_message.id}")

    # Create bot node
    bot_node = ConversationNode(
        id=bot_msg_id,
        message=bot_message,
        parent=user_msg_id,
        children=[],
        is_current=True
    )
    print(f"   Created bot node: {bot_node.id}")

    # Add nodes to tree
    conversation_tree[user_msg_id] = user_node
    conversation_tree[bot_msg_id] = bot_node
    print(f"   Added nodes to tree. New size: {len(conversation_tree)}")

    # Update stored state
    bot_manager._conversation_trees[bot_id] = conversation_tree
    bot_manager._current_node_ids[bot_id] = bot_msg_id
    print(f"   Updated stored state")

    # Create BotState manually to debug
    print(f"\n🔍 Creating BotState...")
    try:
        bot_state = BotState(
            id=bot_id,
            name=bot_manager._bot_metadata[bot_id]['name'],
            conversation_tree=conversation_tree,
            current_node_id=bot_msg_id,
            is_connected=True,
            is_thinking=False
        )
        print(f"   ✅ BotState created successfully")
        print(f"   BotState.conversation_tree type: {type(bot_state.conversation_tree)}")
        print(f"   BotState.conversation_tree size: {len(bot_state.conversation_tree)}")

        # Check the actual content
        for node_id, node in bot_state.conversation_tree.items():
            print(f"      Node {node_id}: {type(node)} - {node.message.role} - {node.message.content[:30]}...")

    except Exception as e:
        print(f"   ❌ BotState creation failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Now test the actual send_message method
    print(f"\n🔍 Testing actual send_message method...")
    try:
        actual_bot_state = await bot_manager.send_message(bot_id, "Second message")
        print(f"   ✅ send_message completed")
        print(f"   Actual conversation_tree size: {len(actual_bot_state.conversation_tree)}")
        print(f"   Actual current_node_id: {actual_bot_state.current_node_id}")

        # Check if the tree has the expected structure
        if len(actual_bot_state.conversation_tree) > 0:
            print(f"   📋 Conversation tree contents:")
            for node_id, node in actual_bot_state.conversation_tree.items():
                print(f"      {node_id}: {node.message.role} - '{node.message.content[:30]}...'")
                print(f"         Parent: {node.parent}, Children: {node.children}, Current: {node.is_current}")
        else:
            print(f"   ❌ Conversation tree is empty!")
            return False

    except Exception as e:
        print(f"   ❌ send_message failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print(f"\n🎉 Debug completed successfully!")
    return True

if __name__ == "__main__":
    success = asyncio.run(debug_conversation_creation())
    exit(0 if success else 1)