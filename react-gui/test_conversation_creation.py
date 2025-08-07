#!/usr/bin/env python3
"""
Test script to verify conversation tree creation and field conversion.
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
from websocket_handler import WebSocketHandler
from models import BotState, ConversationNode, Message, MessageRole

async def test_conversation_creation():
    """Test conversation tree creation step by step."""
    print("🧪 Testing Conversation Tree Creation")
    print("=" * 50)

    # Test 1: Create BotManager and bot
    print("1. Creating bot...")
    bot_manager = BotManager()
    bot_id = bot_manager.create_bot("Test Bot")
    print(f"   ✅ Bot created: {bot_id}")

    # Test 2: Check initial state
    print("2. Checking initial bot state...")
    initial_state = await bot_manager.get_bot_state(bot_id)
    print(f"   ✅ Initial conversation tree: {len(initial_state.conversation_tree)} nodes")
    print(f"   ✅ Initial current node: {initial_state.current_node_id}")

    # Test 3: Send first message
    print("3. Sending first message...")
    bot_state_1 = await bot_manager.send_message(bot_id, "Hello, this is my first message!")
    print(f"   ✅ After first message: {len(bot_state_1.conversation_tree)} nodes")
    print(f"   ✅ Current node: {bot_state_1.current_node_id}")

    # Examine the conversation tree structure
    if bot_state_1.conversation_tree:
        print("   📋 Conversation tree structure:")
        for node_id, node in bot_state_1.conversation_tree.items():
            print(f"      Node {node_id}:")
            print(f"        - Role: {node.message.role}")
            print(f"        - Content: {node.message.content[:50]}...")
            print(f"        - Parent: {node.parent}")
            print(f"        - Children: {node.children}")
            print(f"        - Is Current: {node.is_current}")

    # Test 4: Send second message
    print("\n4. Sending second message...")
    bot_state_2 = await bot_manager.send_message(bot_id, "This is my second message!")
    print(f"   ✅ After second message: {len(bot_state_2.conversation_tree)} nodes")
    print(f"   ✅ Current node: {bot_state_2.current_node_id}")

    # Test 5: Test WebSocket field conversion
    print("\n5. Testing WebSocket field conversion...")
    ws_handler = WebSocketHandler(bot_manager)

    # Convert to frontend format
    bot_state_dict = bot_state_2.dict()
    print(f"   📋 Original fields: {list(bot_state_dict.keys())}")

    converted = ws_handler._convert_bot_state_for_frontend(bot_state_dict)
    print(f"   📋 Converted fields: {list(converted.keys())}")

    # Test the exact WebSocket response format
    websocket_response = {
        'type': 'bot_response',
        'data': {
            'botId': bot_id,
            **converted
        }
    }

    response_data = websocket_response['data']

    # Validate the response matches what the frontend test expects
    print("\n6. Validating frontend compatibility...")

    if 'conversationTree' in response_data:
        tree = response_data['conversationTree']
        if isinstance(tree, dict):
            print(f"   ✅ conversationTree is valid object with {len(tree)} nodes")

            # Check each node structure
            for node_id, node in tree.items():
                if not isinstance(node, dict):
                    print(f"   ❌ Node {node_id} is not an object: {type(node)}")
                    return False

                # The frontend test checks for these specific fields
                required_fields = ['id', 'message', 'parent', 'children', 'isCurrent']
                missing_fields = []
                for field in required_fields:
                    if field not in node:
                        missing_fields.append(field)

                if missing_fields:
                    print(f"   ❌ Node {node_id} missing fields: {missing_fields}")
                    print(f"   Available fields: {list(node.keys())}")
                    return False
                else:
                    print(f"   ✅ Node {node_id} has all required camelCase fields")
        else:
            print(f"   ❌ conversationTree is not an object: {type(tree)}")
            return False
    else:
        print("   ❌ No conversationTree in response")
        return False

    # Test 7: JSON serialization (what actually gets sent over WebSocket)
    print("\n7. Testing JSON serialization...")
    try:
        import json
        json_str = json.dumps(websocket_response)
        parsed_back = json.loads(json_str)
        print("   ✅ WebSocket response can be JSON serialized and parsed")

        # Verify structure after JSON round-trip
        tree_after_json = parsed_back['data']['conversationTree']
        if isinstance(tree_after_json, dict) and len(tree_after_json) > 0:
            print(f"   ✅ conversationTree survives JSON round-trip with {len(tree_after_json)} nodes")
        else:
            print(f"   ❌ conversationTree corrupted after JSON: {type(tree_after_json)}")
            return False

    except Exception as e:
        print(f"   ❌ JSON serialization failed: {e}")
        return False

    print("\n🎉 All conversation creation tests passed!")
    print("The backend should now properly create and convert conversation trees.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_conversation_creation())
    exit(0 if success else 1)