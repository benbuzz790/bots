#!/usr/bin/env python3
"""
Test WebSocket response flow - check if frontend receives and processes responses.
"""

import asyncio
import json
import requests
import websockets
import time


async def test_websocket_response_flow():
    """Test the complete WebSocket response flow."""
    print("🔍 Testing WebSocket Response Flow")
    print("=" * 50)
    
    # Step 1: Create a bot
    print("1️⃣ Creating bot via REST API...")
    try:
        response = requests.post(
            "http://localhost:8000/api/bots/create",
            json={"name": "Response Test Bot"},
            timeout=10
        )
        if response.status_code != 200:
            print(f"❌ Bot creation failed: {response.status_code}")
            return False
        
        bot_data = response.json()
        bot_id = bot_data["bot_id"]
        print(f"✅ Bot created: {bot_id}")
    except Exception as e:
        print(f"❌ Bot creation error: {e}")
        return False
    
    # Step 2: Connect to WebSocket and send message
    print("2️⃣ Testing WebSocket message flow...")
    try:
        async with websockets.connect("ws://localhost:8000/ws") as websocket:
            print("✅ WebSocket connected")
            
            # Send message
            message = {
                "type": "send_message",
                "data": {
                    "botId": bot_id,
                    "content": "Test message for response analysis"
                }
            }
            await websocket.send(json.dumps(message))
            print("✅ Message sent")
            
            # Collect all responses
            responses = []
            start_time = time.time()
            
            while time.time() - start_time < 10:  # Wait up to 10 seconds
                try:
                    response = await asyncio.wait_for(websocket.recv(), timeout=2)
                    data = json.loads(response)
                    responses.append(data)
                    print(f"📨 Response {len(responses)}: {data.get('type', 'unknown')}")
                    
                    # Analyze bot_response in detail
                    if data.get('type') == 'bot_response':
                        bot_state = data.get('data', {}).get('botState', {})
                        print(f"   🔍 Bot state keys: {list(bot_state.keys())}")
                        print(f"   🔍 Conversation tree size: {len(bot_state.get('conversationTree', {}))}")
                        print(f"   🔍 Current node: {bot_state.get('currentNodeId', 'none')}")
                        print(f"   🔍 Is thinking: {bot_state.get('isThinking', 'unknown')}")
                        
                except asyncio.TimeoutError:
                    continue
                except Exception as e:
                    print(f"⚠️  Response error: {e}")
                    continue
            
            print(f"📊 Total responses received: {len(responses)}")
            return len(responses) > 0
            
    except Exception as e:
        print(f"❌ WebSocket test error: {e}")
        return False


if __name__ == "__main__":
    success = asyncio.run(test_websocket_response_flow())
    if success:
        print("🎉 WebSocket responses are working!")
    else:
        print("❌ WebSocket response issues detected")
    exit(0 if success else 1)
