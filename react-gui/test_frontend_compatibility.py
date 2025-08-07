#!/usr/bin/env python3
"""
Test that simulates the exact frontend test scenario to verify the fix.
"""

import asyncio
import json
import sys
import os
from typing import Dict, Any
from unittest.mock import MagicMock, AsyncMock

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
        response = f"I'll help you create that Python file. Let me use the code editor tool to create test.py with a hello world function."
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

# Mock WebSocket for testing
class MockWebSocket:
    def __init__(self):
        self.sent_messages = []

    async def send_json(self, data):
        self.sent_messages.append(data)
        print(f"📤 WebSocket sent: {data['type']}")

async def test_frontend_compatibility():
    """Test the exact scenario from the frontend test."""
    print("🚀 Testing Frontend Compatibility")
    print("Simulating: maximally_thorough_frontend_test.py")
    print("=" * 60)

    # Step 1: Create bot (simulates REST API call)
    print("1. Creating bot...")
    bot_manager = BotManager()
    bot_id = bot_manager.create_bot("Test Bot")
    print(f"✅ Bot created: {bot_id}")

    # Step 2: Create WebSocket handler
    print("2. Setting up WebSocket handler...")
    ws_handler = WebSocketHandler(bot_manager)
    mock_websocket = MockWebSocket()
    print("✅ WebSocket handler ready")

    # Step 3: Send the exact message from the frontend test
    print("3. Sending message with tool usage...")
    message_data = {
        "botId": bot_id,
        "content": "Please create a Python file called test.py with a hello world function"
    }

    # Simulate the WebSocket message handling
    await ws_handler._handle_send_message(mock_websocket, message_data)
    print(f"✅ Message processed, {len(mock_websocket.sent_messages)} responses sent")

    # Step 4: Analyze the responses (simulates frontend receiving messages)
    print("4. Analyzing WebSocket responses...")

    bot_response_received = False
    for i, response in enumerate(mock_websocket.sent_messages):
        response_type = response.get('type')
        print(f"   Response {i+1}: {response_type}")

        if response_type == "bot_thinking":
            print("      🤔 Bot is thinking...")
        elif response_type == "bot_response":
            print("      💬 Bot response received!")
            bot_response_received = True

            # Step 5: THE CRITICAL TEST - Validate conversationTree
            # This is the exact validation from the frontend test
            if "data" in response:
                data = response["data"]

                if "conversationTree" in data:
                    tree = data["conversationTree"]

                    # This is the key validation that was failing
                    if not isinstance(tree, dict):
                        print(f"      ❌ FOUND THE ERROR: conversationTree must be an object, got {type(tree)}")
                        print(f"         Actual value: {str(tree)[:200]}...")
                        print(f"         Response keys: {list(data.keys())}")
                        return False
                    else:
                        print(f"      ✅ conversationTree is valid object with {len(tree)} nodes")

                        # Validate each node (exact same validation as frontend test)
                        for node_id, node in tree.items():
                            if not isinstance(node, dict):
                                print(f"      ❌ Node {node_id} is not an object: {type(node)}")
                                return False

                            # Frontend test checks for these fields (note: camelCase!)
                            required_fields = ['id', 'message', 'parent', 'children', 'isCurrent']
                            for field in required_fields:
                                if field not in node:
                                    print(f"      ❌ Node {node_id} missing field: {field}")
                                    print(f"         Available fields: {list(node.keys())}")
                                    return False

                        print(f"      ✅ All {len(tree)} nodes have valid structure")
                else:
                    print("      ⚠️  No conversationTree in response")
                    print(f"         Available keys: {list(data.keys())}")
                    return False
            else:
                print("      ⚠️  No data in bot_response")
                print(f"         Response structure: {response}")
                return False

    if not bot_response_received:
        print("   ❌ Never received bot_response")
        return False

    # Step 6: Test JSON serialization (what actually goes over the wire)
    print("5. Testing JSON serialization...")
    for response in mock_websocket.sent_messages:
        if response.get('type') == 'bot_response':
            try:
                json_str = json.dumps(response)
                parsed_back = json.loads(json_str)

                # Verify the structure survives JSON round-trip
                tree = parsed_back['data']['conversationTree']
                if isinstance(tree, dict) and len(tree) > 0:
                    print(f"   ✅ JSON serialization works, {len(tree)} nodes preserved")
                else:
                    print(f"   ❌ JSON serialization corrupted tree: {type(tree)}")
                    return False
            except Exception as e:
                print(f"   ❌ JSON serialization failed: {e}")
                return False

    print("\n🎉 Frontend compatibility test PASSED!")
    print("The 'conversationTree must be an object' error is FIXED!")
    print("\nKey fixes applied:")
    print("✅ BotState creation uses camelCase aliases")
    print("✅ WebSocket handler properly converts field names")
    print("✅ Conversation tree nodes have camelCase fields")
    print("✅ JSON serialization preserves structure")
    return True

if __name__ == "__main__":
    success = asyncio.run(test_frontend_compatibility())
    exit(0 if success else 1)