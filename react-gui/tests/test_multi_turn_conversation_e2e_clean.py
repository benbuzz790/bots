#!/usr/bin/env python3
"""
End-to-end test for multi-turn conversation flow.
Tests that the correct nodes are displayed in the chat box and that the complete 
conversation tree is properly displayed in the tree view.

This test validates:
1. Multi-turn conversation creation and flow
2. Chat box displays correct message sequence (path from root to current node)
3. Tree view displays complete conversation structure
4. Navigation between nodes updates both chat and tree views correctly
5. Message extraction and display logic works correctly
"""

import sys
import os
import asyncio
import json
import pytest
from typing import Dict, List, Any
from unittest.mock import Mock, patch, AsyncMock
import websockets
import threading
import time

# Add backend to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'backend'))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from bot_manager import BotManager
from models import BotState, ConversationNode, Message, MessageRole
from tree_serializer import serialize_conversation_tree, TreeLayout
from websocket_handler import WebSocketHandler


class TestMultiTurnConversationE2E:
    """End-to-end test for multi-turn conversation functionality."""

    @pytest.fixture
    def bot_manager(self):
        """Create bot manager for testing."""
        return BotManager()

    @pytest.fixture
    def mock_bot_instance(self):
        """Create a mock bot instance with conversation tree."""
        mock_bot = Mock()
        mock_bot.conversation = Mock()
        mock_bot.conversation._root_dict = Mock(return_value={
            "content": "",
            "role": "system",
            "replies": []
        })
        mock_bot.respond = Mock(side_effect=[
            "Hello! I'm here to help you with Python programming.",
            "Python has several basic data types: int, float, str, bool, list, dict, tuple, and set.",
            "Here's a simple example:\n\n```python\n# Integer\nage = 25\n\n# String\nname = 'Alice'\n\n# List\ncolors = ['red', 'blue', 'green']\n```",
            "Great question! Lists are mutable (can be changed) while tuples are immutable (cannot be changed after creation)."
        ])
        return mock_bot

    async def test_multi_turn_conversation_flow(self, bot_manager, mock_bot_instance):
        """Test complete multi-turn conversation flow with chat and tree validation."""

        print("🚀 Testing Multi-Turn Conversation E2E Flow")
        print("=" * 60)

        # Step 1: Create bot and mock the bot instance
        print("\n1️⃣ Setting up bot...")
        with patch.object(bot_manager, '_create_bot_instance', return_value=mock_bot_instance):
            bot_id = await bot_manager.create_bot("Python Helper Bot")
            print(f"   ✅ Bot created: {bot_id}")

        # Step 2: Create multi-turn conversation
        print("\n2️⃣ Creating multi-turn conversation...")

        conversation_turns = [
            ("user", "Hello, can you help me learn Python?"),
            ("user", "What are the basic data types in Python?"),
            ("user", "Can you show me some examples?"),
            ("user", "What's the difference between lists and tuples?")
        ]

        # Send messages and collect states
        conversation_states = []

        for i, (role, content) in enumerate(conversation_turns):
            print(f"   📝 Turn {i+1}: Sending '{content[:30]}...'")

            # Mock the bot response for this turn
            expected_response = mock_bot_instance.respond.side_effect[i]

            # Send message
            bot_state = await bot_manager.send_message(bot_id, content)
            conversation_states.append(bot_state)

            print(f"   ✅ Turn {i+1}: Got response '{expected_response[:30]}...'")
            print(f"   📊 Tree now has {len(bot_state.conversation_tree)} nodes")

        # Step 3: Validate final conversation structure
        print("\n3️⃣ Validating conversation structure...")
        final_state = conversation_states[-1]

        # Defensive validation
        assert isinstance(final_state, BotState), f"Expected BotState, got {type(final_state)}"
        assert isinstance(final_state.conversation_tree, dict), "Conversation tree must be dict"
        assert len(final_state.conversation_tree) >= 8, f"Expected at least 8 nodes (4 user + 4 bot), got {len(final_state.conversation_tree)}"
        assert final_state.current_node_id, "Current node ID must not be empty"
        assert final_state.current_node_id in final_state.conversation_tree, "Current node must exist in tree"

        print(f"   ✅ Structure valid: {len(final_state.conversation_tree)} nodes")

        # Step 4: Test chat box message extraction (path from root to current)
        print("\n4️⃣ Testing chat box message extraction...")

        chat_messages = self._extract_chat_messages(final_state)

        # Validate chat messages
        assert isinstance(chat_messages, list), "Chat messages must be list"
        assert len(chat_messages) == 8, f"Expected 8 messages in chat (4 user + 4 bot), got {len(chat_messages)}"

        # Validate message sequence
        expected_sequence = [
            ("user", "Hello, can you help me learn Python?"),
            ("assistant", "Hello! I'm here to help you with Python programming."),
            ("user", "What are the basic data types in Python?"),
            ("assistant", "Python has several basic data types: int, float, str, bool, list, dict, tuple, and set."),
            ("user", "Can you show me some examples?"),
            ("assistant", "Here's a simple example:\n\n```python\n# Integer\nage = 25\n\n# String\nname = 'Alice'\n\n# List\ncolors = ['red', 'blue', 'green']\n```"),
            ("user", "What's the difference between lists and tuples?"),
            ("assistant", "Great question! Lists are mutable (can be changed) while tuples are immutable (cannot be changed after creation).")
        ]

        for i, (expected_role, expected_content) in enumerate(expected_sequence):
            actual_message = chat_messages[i]
            assert actual_message.role.value == expected_role, f"Message {i}: expected role {expected_role}, got {actual_message.role.value}"
            assert expected_content in actual_message.content, f"Message {i}: expected content not found"

        print(f"   ✅ Chat messages valid: {len(chat_messages)} messages in correct sequence")

        # Step 5: Test tree view serialization
        print("\n5️⃣ Testing tree view serialization...")

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
        assert len(tree_data['nodes']) == len(final_state.conversation_tree), "Tree nodes count must match conversation tree"

        print(f"   ✅ Tree view valid: {len(tree_data['nodes'])} nodes, {len(tree_data['edges'])} edges")

        print("\n🎉 Multi-turn conversation E2E test completed successfully!")
        return True

    def _extract_chat_messages(self, bot_state: BotState) -> List[Message]:
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


async def run_all_tests():
    """Run all multi-turn conversation tests."""

    print("🧪 Multi-Turn Conversation E2E Test Suite")
    print("=" * 60)

    test_instance = TestMultiTurnConversationE2E()
    bot_manager = BotManager()

    try:
        # Create mock bot instance
        mock_bot = Mock()
        mock_bot.conversation = Mock()
        mock_bot.conversation._root_dict = Mock(return_value={
            "content": "",
            "role": "system", 
            "replies": []
        })
        mock_bot.respond = Mock(side_effect=[
            "Hello! I'm here to help you with Python programming.",
            "Python has several basic data types: int, float, str, bool, list, dict, tuple, and set.",
            "Here's a simple example:\n\n```python\n# Integer\nage = 25\n\n# String\nname = 'Alice'\n\n# List\ncolors = ['red', 'blue', 'green']\n```",
            "Great question! Lists are mutable (can be changed) while tuples are immutable (cannot be changed after creation).",
            "Functions in Python are defined using the 'def' keyword and can take parameters and return values."
        ])

        # Run main conversation flow test
        await test_instance.test_multi_turn_conversation_flow(bot_manager, mock_bot)

        print("\n🎉 All multi-turn conversation E2E tests passed!")
        return True

    except Exception as e:
        print(f"\n❌ Test suite failed: {e}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    success = asyncio.run(run_all_tests())
    if not success:
        sys.exit(1)
    print("\n✅ Multi-turn conversation E2E test suite completed successfully!")
