#!/usr/bin/env python3
"""
Test the corrected BotManager behavior for multi-turn conversations.
This test validates that the conversation tree properly accumulates and 
that chat/tree synchronization works correctly.
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

from bot_manager_corrected import BotManager
from models import BotState, ConversationNode, Message, MessageRole
from tree_serializer import serialize_conversation_tree, TreeLayout


async def test_corrected_multi_turn_conversation():
    """Test the corrected multi-turn conversation behavior."""

    print("🔧 Testing CORRECTED Multi-Turn Conversation Behavior")
    print("=" * 70)

    # Step 1: Create bot manager
    print("\n1️⃣ Setting up corrected bot manager...")
    bot_manager = BotManager()
    print("   ✅ Corrected bot manager created")

    # Step 2: Mock the bot framework
    print("\n2️⃣ Setting up mocks...")

    mock_responses = [
        "Hello! I'm here to help you with Python programming.",
        "Python has several basic data types: int, float, str, bool, list, dict, tuple, and set.",
        "Here's a simple example:\n\n```python\n# Integer\nage = 25\n\n# String\nname = 'Alice'\n\n# List\ncolors = ['red', 'blue', 'green']\n```",
        "Great question! Lists are mutable (can be changed) while tuples are immutable (cannot be changed after creation)."
    ]

    with patch('bots.foundation.anthropic_bots.AnthropicBot') as MockBot, \
         patch('bots.tools.code_tools') as mock_tools:

        mock_bot_instance = MagicMock()
        mock_bot_instance.respond = MagicMock(side_effect=mock_responses)
        mock_bot_instance.name = "Test Bot"
        MockBot.return_value = mock_bot_instance

        print("   ✅ Mocks configured")

        # Step 3: Create bot
        print("\n3️⃣ Creating bot...")
        bot_id = await bot_manager.create_bot("Python Helper Bot")
        print(f"   ✅ Bot created: {bot_id}")

        # Step 4: Send multiple messages and verify accumulation
        print("\n4️⃣ Testing conversation accumulation...")

        conversation_turns = [
            "Hello, can you help me learn Python?",
            "What are the basic data types in Python?",
            "Can you show me some examples?",
            "What's the difference between lists and tuples?"
        ]

        conversation_states = []

        for i, content in enumerate(conversation_turns):
            print(f"   📝 Turn {i+1}: Sending '{content[:30]}...'")

            bot_state = await bot_manager.send_message(bot_id, content)
            conversation_states.append(bot_state)

            expected_response = mock_responses[i]
            print(f"   ✅ Turn {i+1}: Got response '{expected_response[:30]}...'")
            print(f"   📊 Tree now has {len(bot_state.conversation_tree)} nodes")

            # CRITICAL TEST: Verify tree is accumulating, not replacing
            expected_node_count = (i + 1) * 2  # Each turn adds user + bot message
            assert len(bot_state.conversation_tree) == expected_node_count, \
                f"Turn {i+1}: Expected {expected_node_count} nodes, got {len(bot_state.conversation_tree)}"

            print(f"   ✅ Accumulation verified: {expected_node_count} nodes as expected")

        # Step 5: Validate final conversation structure
        print("\n5️⃣ Validating final conversation structure...")
        final_state = conversation_states[-1]

        assert isinstance(final_state, BotState), f"Expected BotState, got {type(final_state)}"
        assert len(final_state.conversation_tree) == 8, f"Expected 8 nodes total, got {len(final_state.conversation_tree)}"
        assert final_state.current_node_id, "Current node ID must not be empty"
        assert final_state.current_node_id in final_state.conversation_tree, "Current node must exist in tree"

        print(f"   ✅ Final structure valid: {len(final_state.conversation_tree)} nodes")

        # Display conversation tree structure
        print("\n   📊 Final Conversation Tree Structure:")
        for node_id, node in final_state.conversation_tree.items():
            current_marker = "👉" if node.is_current else "  "
            role_icon = "🤖" if node.message.role == MessageRole.ASSISTANT else "👤"
            content_preview = node.message.content[:40].replace('\n', ' ')
            if len(node.message.content) > 40:
                content_preview += "..."
            parent_info = f" (parent: {node.parent[:8] if node.parent else 'None'})"
            children_info = f" (children: {len(node.children)})"
            print(f"   {current_marker} {role_icon} {node_id[:8]}: {content_preview}{parent_info}{children_info}")

        # Step 6: Test chat message extraction with full conversation
        print("\n6️⃣ Testing chat message extraction...")

        chat_messages = bot_manager.get_conversation_path(bot_id)

        assert isinstance(chat_messages, list), "Chat messages must be list"
        assert len(chat_messages) == 8, f"Expected 8 chat messages, got {len(chat_messages)}"

        print(f"   ✅ Chat messages extracted: {len(chat_messages)} messages")

        # Validate message sequence
        expected_sequence = [
            ("user", "Hello, can you help me learn Python?"),
            ("assistant", "Hello! I'm here to help you with Python programming."),
            ("user", "What are the basic data types in Python?"),
            ("assistant", "Python has several basic data types"),
            ("user", "Can you show me some examples?"),
            ("assistant", "Here's a simple example"),
            ("user", "What's the difference between lists and tuples?"),
            ("assistant", "Great question! Lists are mutable")
        ]

        print("\n   📝 Chat Message Sequence:")
        for i, (expected_role, expected_content_start) in enumerate(expected_sequence):
            actual_message = chat_messages[i]
            role_icon = "🤖" if actual_message.role == MessageRole.ASSISTANT else "👤"
            content_preview = actual_message.content[:50].replace('\n', ' ')
            if len(actual_message.content) > 50:
                content_preview += "..."

            assert actual_message.role.value == expected_role, \
                f"Message {i+1}: expected role {expected_role}, got {actual_message.role.value}"
            assert expected_content_start in actual_message.content, \
                f"Message {i+1}: expected content '{expected_content_start}' not found"

            print(f"   {i+1}. {role_icon} {actual_message.role.value}: {content_preview}")

        print("   ✅ All messages in correct sequence")

        # Step 7: Test tree view serialization
        print("\n7️⃣ Testing tree view serialization...")

        tree_data = bot_manager.serialize_conversation_tree(bot_id)

        assert isinstance(tree_data, dict), "Tree data must be dict"
        assert 'nodes' in tree_data, "Tree data must have nodes"
        assert 'edges' in tree_data, "Tree data must have edges"
        assert len(tree_data['nodes']) == 8, f"Expected 8 tree nodes, got {len(tree_data['nodes'])}"
        assert len(tree_data['edges']) == 7, f"Expected 7 tree edges, got {len(tree_data['edges'])}"

        print(f"   ✅ Tree view valid: {len(tree_data['nodes'])} nodes, {len(tree_data['edges'])} edges")

        # Step 8: Test chat/tree synchronization
        print("\n8️⃣ Testing chat/tree synchronization...")

        # Find current node in tree data
        current_tree_node = None
        for node in tree_data['nodes']:
            if node['id'] == final_state.current_node_id:
                current_tree_node = node
                break

        assert current_tree_node is not None, "Current node must be found in tree data"
        assert current_tree_node.get('data', {}).get('isCurrent') is True, \
            "Current node must be marked as current in tree"

        print("   ✅ Current node found and marked correctly in tree data")

        # Verify the last message in chat matches the current node
        last_chat_message = chat_messages[-1]
        current_conversation_node = final_state.conversation_tree[final_state.current_node_id]

        assert last_chat_message.id == current_conversation_node.message.id, \
            "Last chat message must match current node message"
        assert last_chat_message.content == current_conversation_node.message.content, \
            "Message content must match"

        print("   ✅ Chat/tree synchronization verified")

        # Step 9: Test navigation
        print("\n9️⃣ Testing navigation...")

        # Navigate to root
        root_state = await bot_manager.navigate_to_root(bot_id)
        root_chat_messages = bot_manager.get_conversation_path(bot_id)

        assert len(root_chat_messages) == 1, f"Expected 1 message at root, got {len(root_chat_messages)}"
        assert root_chat_messages[0].role == MessageRole.USER, "Root message should be user message"
        assert "Hello, can you help me learn Python?" in root_chat_messages[0].content, \
            "Root message should be first user message"

        print(f"   ✅ Navigation to root: chat shows {len(root_chat_messages)} message")

        # Navigate down
        down_state = await bot_manager.navigate(bot_id, "down")
        down_chat_messages = bot_manager.get_conversation_path(bot_id)

        assert len(down_chat_messages) == 2, f"Expected 2 messages after down, got {len(down_chat_messages)}"

        print(f"   ✅ Navigation down: chat shows {len(down_chat_messages)} messages")

        # Navigate back to end
        end_state = await bot_manager.navigate_to_node(bot_id, final_state.current_node_id)
        end_chat_messages = bot_manager.get_conversation_path(bot_id)

        assert len(end_chat_messages) == 8, f"Expected 8 messages at end, got {len(end_chat_messages)}"

        print(f"   ✅ Navigation to end: chat shows {len(end_chat_messages)} messages")

        print("\n🎉 ALL CORRECTED BEHAVIOR TESTS PASSED!")
        print("\n📋 Summary of Fixes Validated:")
        print("   ✅ Conversation tree properly accumulates (8 nodes instead of 2)")
        print("   ✅ Current node ID is tracked correctly (no more hardcoded 'test_node')")
        print("   ✅ Chat message extraction shows full conversation path")
        print("   ✅ Tree view serialization includes all nodes with correct relationships")
        print("   ✅ Navigation updates both chat and tree views correctly")
        print("   ✅ Chat/tree synchronization works perfectly")

        return True


async def run_corrected_test():
    """Run the corrected behavior test."""

    print("🧪 Corrected Multi-Turn Conversation Test Suite")
    print("=" * 70)

    try:
        success = await test_corrected_multi_turn_conversation()

        if success:
            print("\n🎉 All corrected behavior tests passed!")
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
    success = asyncio.run(run_corrected_test())
    if not success:
        sys.exit(1)
    print("\n✅ Corrected behavior test suite completed successfully!")
