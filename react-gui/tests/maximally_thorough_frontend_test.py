#!/usr/bin/env python3
"""
Maximally Thorough Frontend Test

Tests the "conversationTree must be an object" error and validates
the complete conversation cycle with tool usage.
"""

import asyncio
import json
import requests
import websockets
from typing import Any

BACKEND_URL = "http://127.0.0.1:8000"
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

async def test_conversation_tree_structure():
    """Test the conversation tree structure thoroughly."""
    print("🚀 Testing ConversationTree Structure")
    print("=" * 50)

    # Step 1: Create bot
    print("1. Creating bot...")
    response = requests.post(f"{BACKEND_URL}/api/bots/create", json={"name": "Test Bot"})
    if response.status_code != 200:
        print(f"❌ Failed to create bot: {response.status_code}")
        print(f"Response content: {response.text}")
        print(f"Response headers: {response.headers}")
        return False

    bot_data = response.json()
    bot_id = bot_data.get("bot_id")
    print(f"✅ Bot created: {bot_id}")

    # Step 2: Connect WebSocket
    print("2. Connecting to WebSocket...")
    try:
        websocket = await websockets.connect(WEBSOCKET_URL)
        print("✅ WebSocket connected")
    except Exception as e:
        print(f"❌ WebSocket connection failed: {e}")
        return False

    # Step 3: Send message that triggers tool usage
    print("3. Sending message with tool usage...")
    message = {
        "type": "send_message",
        "data": {
            "botId": bot_id,
            "content": "Please create a Python file called test.py with a hello world function"
        }
    }

    try:
        await websocket.send(json.dumps(message))
        print("✅ Message sent")

        # Step 4: Wait for and validate responses (handle multiple responses)
        print("4. Waiting for bot responses...")
        bot_response_received = False
        response_count = 0
        max_responses = 10  # Prevent infinite loop

        while not bot_response_received and response_count < max_responses:
            try:
                response_raw = await asyncio.wait_for(websocket.recv(), timeout=30.0)
                response = json.loads(response_raw)
                response_count += 1

                response_type = response.get('type')
                print(f"✅ Response {response_count} received: {response_type}")

                if response_type == "bot_thinking":
                    print("   🤔 Bot is thinking...")
                    continue
                elif response_type == "tool_update":
                    print("   🔧 Tool execution update...")
                    continue
                elif response_type == "bot_response":
                    print("   💬 Bot response received!")
                    bot_response_received = True

                    # Step 5: THE CRITICAL TEST - Validate conversationTree
                    if "data" in response:
                        data = response["data"]

                        if "conversationTree" in data:
                            tree = data["conversationTree"]

                            # This is the key validation that was failing
                            if not isinstance(tree, dict):
                                print(f"❌ FOUND THE ERROR: conversationTree must be an object, got {type(tree)}")
                                print(f"   Actual value: {str(tree)[:200]}...")
                                print(f"   Response keys: {list(data.keys())}")
                                await websocket.close()
                                return False
                            else:
                                print(f"✅ conversationTree is valid object with {len(tree)} nodes")

                                # Validate each node
                                for node_id, node in tree.items():
                                    if not isinstance(node, dict):
                                        print(f"❌ Node {node_id} is not an object: {type(node)}")
                                        await websocket.close()
                                        return False

                                    required_fields = ['id', 'message', 'parent', 'children', 'is_current']
                                    for field in required_fields:
                                        if field not in node:
                                            print(f"❌ Node {node_id} missing field: {field}")
                                            await websocket.close()
                                            return False

                                print(f"✅ All {len(tree)} nodes have valid structure")
                        else:
                            print("⚠️  No conversationTree in response")
                            print(f"   Available keys: {list(data.keys())}")
                    else:
                        print("⚠️  No data in bot_response")
                        print(f"   Response structure: {response}")
                else:
                    print(f"⚠️  Unexpected response type: {response_type}")

            except asyncio.TimeoutError:
                print(f"❌ Timeout waiting for response {response_count + 1}")
                break

        if not bot_response_received:
            print(f"❌ Never received bot_response after {response_count} responses")
            await websocket.close()
            return False

        await websocket.close()
        return True

    except Exception as e:
        print(f"❌ Error during message handling: {e}")
        await websocket.close()
        return False

async def main():
    """Run the test."""
    success = await test_conversation_tree_structure()

    if success:
        print("\n🎉 Test completed successfully!")
        print("ConversationTree structure is valid.")
        return 0
    else:
        print("\n❌ Test failed!")
        print("Found issues with conversationTree structure.")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)