#!/usr/bin/env python3
"""
Test script to verify the backend can handle bot creation and WebSocket communication
with proper field conversion, using mocked bots to avoid framework dependencies.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
from unittest.mock import MagicMock

# Add the backend directory to Python path
backend_dir = os.path.join(os.path.dirname(__file__), 'backend')
sys.path.insert(0, backend_dir)

# Mock the bots framework to avoid import errors
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
from models import BotState

async def test_mock_backend():
    """Test the backend with mocked bots."""
    print("🚀 Testing Backend with Mock Bots")
    print("=" * 50)

    # Test 1: Create BotManager
    print("1. Creating BotManager...")
    bot_manager = BotManager()
    print("   ✅ BotManager created successfully")

    # Test 2: Create a bot
    print("2. Creating a bot...")
    try:
        bot_id = bot_manager.create_bot("Test Bot")
        print(f"   ✅ Bot created successfully: {bot_id}")
    except Exception as e:
        print(f"   ❌ Bot creation failed: {e}")
        return False

    # Test 3: Send a message
    print("3. Sending a message...")
    try:
        bot_state = await bot_manager.send_message(bot_id, "Hello, test message!")
        print(f"   ✅ Message sent successfully")
        print(f"   ✅ Bot state type: {type(bot_state)}")
        print(f"   ✅ Conversation tree type: {type(bot_state.conversation_tree)}")
        print(f"   ✅ Conversation tree has {len(bot_state.conversation_tree)} nodes")
    except Exception as e:
        print(f"   ❌ Message sending failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 4: Test WebSocket handler field conversion
    print("4. Testing WebSocket handler...")
    try:
        ws_handler = WebSocketHandler(bot_manager)

        # Test the conversion function
        bot_state_dict = bot_state.dict()
        converted = ws_handler._convert_bot_state_for_frontend(bot_state_dict)

        # Check for proper field conversion
        if 'conversationTree' in converted and isinstance(converted['conversationTree'], dict):
            print("   ✅ WebSocket handler converts conversationTree correctly")
        else:
            print(f"   ❌ WebSocket handler conversion failed: {type(converted.get('conversationTree'))}")
            return False

        if 'currentNodeId' in converted:
            print("   ✅ WebSocket handler converts currentNodeId correctly")
        else:
            print("   ❌ WebSocket handler missing currentNodeId")
            return False

        if 'isConnected' in converted and 'isThinking' in converted:
            print("   ✅ WebSocket handler converts boolean fields correctly")
        else:
            print("   ❌ WebSocket handler missing boolean fields")
            return False

    except Exception as e:
        print(f"   ❌ WebSocket handler test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    # Test 5: Simulate the exact WebSocket response format
    print("5. Testing WebSocket response format...")
    try:
        # This simulates what _handle_send_message does
        converted_bot_state = ws_handler._convert_bot_state_for_frontend(bot_state.dict())

        websocket_response = {
            'type': 'bot_response',
            'data': {
                'botId': bot_id,
                **converted_bot_state  # Spread the converted fields directly
            }
        }

        response_data = websocket_response['data']

        # This is the exact check that was failing in the frontend test
        if 'conversationTree' in response_data:
            tree = response_data['conversationTree']
            if isinstance(tree, dict):
                print(f"   ✅ conversationTree is valid object with {len(tree)} nodes")

                # Validate each node structure
                for node_id, node in tree.items():
                    if not isinstance(node, dict):
                        print(f"   ❌ Node {node_id} is not an object: {type(node)}")
                        return False

                    # Check for required fields (these should be camelCase now)
                    required_fields = ['id', 'message', 'parent', 'children', 'isCurrent']
                    for field in required_fields:
                        if field not in node:
                            print(f"   ❌ Node {node_id} missing field: {field}")
                            print(f"   Available fields: {list(node.keys())}")
                            return False

                print(f"   ✅ All {len(tree)} nodes have valid camelCase structure")
            else:
                print(f"   ❌ conversationTree is not an object: {type(tree)}")
                return False
        else:
            print("   ❌ No conversationTree in response")
            print(f"   Available keys: {list(response_data.keys())}")
            return False

    except Exception as e:
        print(f"   ❌ WebSocket response format test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

    print("\n🎉 All backend tests passed!")
    print("The field conversion fixes should resolve the frontend error.")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_mock_backend())
    exit(0 if success else 1)