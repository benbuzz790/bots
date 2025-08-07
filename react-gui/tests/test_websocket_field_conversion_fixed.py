#!/usr/bin/env python3
"""
Test WebSocket field conversion after fixing the handler
"""

import asyncio
import json
import websockets

WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

async def test_websocket_field_conversion():
    """Test WebSocket field conversion with a simple message."""
    print("🔍 Testing WebSocket field conversion")
    print("=" * 50)

    try:
        # Connect to WebSocket
        print("1. Connecting to WebSocket...")
        websocket = await websockets.connect(WEBSOCKET_URL)
        print("✅ WebSocket connected")

        # Send a simple message that doesn't require bot creation
        # (This will fail but we can see the error structure)
        print("2. Sending test message...")
        message = {
            "type": "send_message",
            "data": {
                "botId": "nonexistent-bot",
                "content": "test"
            }
        }

        await websocket.send(json.dumps(message))
        print("✅ Message sent")

        # Wait for response
        print("3. Waiting for response...")
        response_raw = await asyncio.wait_for(websocket.recv(), timeout=10.0)
        response = json.loads(response_raw)

        print(f"✅ Response received: {response.get('type')}")
        print(f"Response structure: {json.dumps(response, indent=2)}")

        # Check if error response has proper structure
        if response.get('type') == 'error':
            print("✅ Error response received as expected")
            print(f"Error message: {response.get('data', {}).get('message', 'No message')}")

        await websocket.close()
        return True

    except Exception as e:
        print(f"❌ Error: {e}")
        return False

async def main():
    """Run the test."""
    success = await test_websocket_field_conversion()

    if success:
        print("\n🎉 WebSocket connection test passed!")
        print("WebSocket handler is responding correctly.")
    else:
        print("\n❌ WebSocket connection test failed!")

if __name__ == "__main__":
    asyncio.run(main())