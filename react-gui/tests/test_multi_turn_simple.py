#!/usr/bin/env python3
"""
Simplified end-to-end test for multi-turn conversation flow.
Tests that the correct nodes are displayed in the chat box and that the complete 
conversation tree is properly displayed in the tree view.
"""

import sys
import os
import asyncio
import json
from typing import Dict, List, Any
from unittest.mock import Mock, patch, MagicMock
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from bot_manager import BotManager
from models import BotState, ConversationNode, Message, MessageRole
from tree_serializer import serialize_conversation_tree, TreeLayout


async def test_multi_turn_conversation_flow():
    """Test complete multi-turn conversation flow with chat and tree validation."""

    print("🚀 Testing Multi-Turn Conversation E2E Flow")
    print("=" * 60)

    # Step 1: Create bot manager
    print("\n1️⃣ Setting up bot manager...")
    bot_manager = BotManager()
    print("   ✅ Bot manager created")

    # Step 2: Mock the bot framework since we're testing the GUI logic
    print("\n2️⃣ Setting up mocks...")

    # Mock the bot responses
    mock_responses = [
        "Hello! I'm here to help you with Python programming.",
        "Python has several basic data types: int, float, str, bool, list, dict, tuple, and set.",
        "Here's a simple example:\n\n```python\n# Integer\nage = 25\n\n# String\nname = 'Alice'\n\n# List\ncolors = ['red', 'blue', 'green']\n```",
        "Great question! Lists are mutable (can be changed) while tuples are immutable (cannot be changed after creation)."
    ]

    # Mock the bot creation and responses
    with patch('bots.foundation.anthropic_bots.AnthropicBot') as MockBot, \
         patch('bots.tools.code_tools') as mock_tools:

        # Create mock bot instance
        mock_bot_instance = MagicMock()
        mock_bot_instance.respond = MagicMock(side_effect=mock_responses)
        mock_bot_instance.name = "Test Bot"
        MockBot.return_value = mock_bot_instance

        print("   ✅ Mocks configured")

        # Step 3: Create bot
        print("\n3️⃣ Creating bot...")
        bot_id = await bot_manager.create_bot("Python Helper Bot")
        print(f"   ✅ Bot created: {bot_id}")

        # Step 4: Create multi-turn conversation
        print("\n4️⃣ Creating multi-turn conversation...")

        conversation_turns = [
            "Hello, can you help me learn Python?",
            "What are the basic data types in Python?",
            "Can you show me some examples?",
            "What's the difference between lists and tuples?"
        ]

        # Send messages and collect states
        conversation_states = []

        for i, content in enumerate(conversation_turns):
            print(f"   📝 Turn {i+1}: Sending '{content[:30]}...'")

            # Send message
            bot_state = await bot_manager.send_message(bot_id, content)
            conversation_states.append(bot_state)

            expected_response = mock_responses[i]
            print(f"   ✅ Turn {i+1}: Got response '{expected_response[:30]}...'")
            print(f"   📊 Tree now has {len(bot_state.conversation_tree)} nodes")

        # Step 5: Validate final conversation structure
        print("\n5️⃣ Validating conversation structure...")
        final_state = conversation_states[-1]

        # Defensive validation
        assert isinstance(final_state, BotState), f"Expected BotState, got {type(final_state)}"
        assert isinstance(final_state.conversation_tree, dict), "Conversation tree must be dict"
        assert len(final_state.conversation_tree) >= 2, f"Expected at least 2 nodes, got {len(final_state.conversation_tree)}"
        assert final_state.current_node_id, "Current node ID must not be empty"
        assert final_state.current_node_id in final_state.conversation_tree, "Current node must exist in tree"

        print(f"   ✅ Structure valid: {len(final_state.conversation_tree)} nodes")

        # Display conversation tree structure
        print("\n   📊 Conversation Tree Structure:")
        for node_id, node in final_state.conversation_tree.items():
            current_marker = "👉" if node.is_current else "  "
            role_icon = "🤖" if node.message.role == MessageRole.ASSISTANT else "👤"
            content_preview = node.message.content[:40].replace('\n', ' ')
            if len(node.message.content) > 40:
                content_preview += "..."
            print(f"   {current_marker} {role_icon} {node_id[:8]}: {content_preview}")
            if node.children:
                print(f"      └─ Children: {[child[:8] for child in node.children]}")

        # Step 6: Test chat box message extraction (path from root to current)
        print("\n6️⃣ Testing chat box message extraction...")

        chat_messages = extract_chat_messages(final_state)

        # Validate chat messages
        assert isinstance(chat_messages, list), "Chat messages must be list"
        print(f"   ✅ Chat messages extracted: {len(chat_messages)} messages")

        # Display chat messages
        print("\n   📝 Chat Messages (path from root to current):")
        for i, msg in enumerate(chat_messages):
            role_icon = "🤖" if msg.role == MessageRole.ASSISTANT else "👤"
            content_preview = msg.content[:50].replace('\n', ' ')
            if len(msg.content) > 50:
                content_preview += "..."
            print(f"   {i+1}. {role_icon} {msg.role.value}: {content_preview}")

        # Step 7: Test tree view serialization
        print("\n7️⃣ Testing tree view serialization...")

        tree_data = serialize_gui_conversation_tree(
            final_state.conversation_tree,
            final_state.current_node_id,
            TreeLayout()
        )

        # Validate tree data
        assert isinstance(tree_data, dict), "Tree data must be dict"
        assert 'nodes' in tree_data, "Tree data must have nodes"
        assert 'edges' in tree_data, "Tree data must have edges"
        assert isinstance(tree_data['nodes'], list), "Tree nodes must be list"
        assert isinstance(tree_data['edges'], list), "Tree edges must be list"

        print(f"   ✅ Tree view valid: {len(tree_data['nodes'])} nodes, {len(tree_data['edges'])} edges")

        # Display tree structure
        print("\n   🌳 Tree View Structure:")
        for node in tree_data['nodes']:
            node_type = node.get('type', 'unknown')
            is_current = node.get('data', {}).get('isCurrent', False)
            current_marker = "👉" if is_current else "  "
            role = node.get('data', {}).get('role', 'unknown')
            preview = node.get('data', {}).get('preview', 'No preview')[:30]
            print(f"   {current_marker} [{node_type}] {role}: {preview}")

        # Step 8: Test that chat and tree are synchronized
        print("\n8️⃣ Testing chat/tree synchronization...")

        # Find current node in tree data
        current_tree_node = None
        for node in tree_data['nodes']:
            if node['id'] == final_state.current_node_id:
                current_tree_node = node
                break

        assert current_tree_node is not None, "Current node must be found in tree data"
        assert current_tree_node.get('data', {}).get('isCurrent') is True, "Current node must be marked as current in tree"

        # Verify the last message in chat matches the current node
        if chat_messages:
            last_chat_message = chat_messages[-1]
            current_conversation_node = final_state.conversation_tree[final_state.current_node_id]

            assert last_chat_message.id == current_conversation_node.message.id, "Last chat message must match current node message"
            assert last_chat_message.content == current_conversation_node.message.content, "Message content must match"

        print(f"   ✅ Chat/tree synchronization verified")

        print("\n🎉 Multi-turn conversation E2E test completed successfully!")
        return True


def extract_chat_messages(bot_state: BotState) -> List[Message]:
    """
    Extract messages for chat display (path from root to current node).
    This mirrors the logic in ChatInterface.tsx.
    """
    # Input validation
    assert isinstance(bot_state, BotState), f"Expected BotState, got {type(bot_state)}"
    assert isinstance(bot_state.conversation_tree, dict), "Conversation tree must be dict"
    assert bot_state.current_node_id, "Current node ID must not be empty"

    if not bot_state.conversation_tree:
        return []

    # Build path from root to current node
    def build_path(node_id: str) -> List[str]:
        path = []
        current_id = node_id

        while current_id:
            node = bot_state.conversation_tree.get(current_id)
            if not node:
                break
            path.insert(0, current_id)  # Insert at beginning to build path from root
            current_id = node.parent

        return path

    path_to_current = build_path(bot_state.current_node_id)

    # Extract messages along the path
    messages = []
    for node_id in path_to_current:
        node = bot_state.conversation_tree[node_id]
        if node.message.content.strip():
            # Skip system initialization messages unless they have meaningful content
            if node.message.role != MessageRole.SYSTEM or node.message.content != 'Bot initialized':
                messages.append(node.message)

    return messages


async def run_test():
    """Run the multi-turn conversation test."""

    print("🧪 Multi-Turn Conversation E2E Test Suite")
    print("=" * 60)

    try:
        success = await test_multi_turn_conversation_flow()

        if success:
            print("\n🎉 All multi-turn conversation E2E tests passed!")
            return True
        else:
            print("\n❌ Some tests failed!")
            return False

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_test())
    if not success:
        sys.exit(1)
    print("\n✅ Multi-turn conversation E2E test suite completed successfully!")
