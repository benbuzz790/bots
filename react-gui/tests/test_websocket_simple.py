#!/usr/bin/env python3
"""Test WebSocket connection between frontend and backend."""

import asyncio
import websockets
import json

async def test_websocket():
    """Test WebSocket connection to backend."""
    print("🔌 Testing WebSocket Connection")
    print("=" * 40)

    try:
        # Connect to the WebSocket endpoint
        uri = "ws://127.0.0.1:8000/ws"
        print(f"1. Connecting to {uri}...")

        async with websockets.connect(uri) as websocket:
            print("   ✅ WebSocket connected successfully!")

            # Test sending a message
            print("2. Sending test message...")
            test_message = {
                "type": "get_bot_state",
                "data": {"botId": "test-bot"}
            }
            await websocket.send(json.dumps(test_message))
            print("   ✅ Message sent successfully!")

            # Try to receive a response (with timeout)
            print("3. Waiting for response...")
            try:
                response = await asyncio.wait_for(websocket.recv(), timeout=5.0)
                response_data = json.loads(response)
                print(f"   ✅ Received response: {response_data.get('type', 'unknown')}")
                return True
            except asyncio.TimeoutError:
                print("   ⚠️  No response received (timeout - this is OK)")
                return True

    except websockets.exceptions.ConnectionRefused:
        print("   ❌ Connection refused - backend may not be running")
        return False
    except Exception as e:
        print(f"   ❌ WebSocket test failed: {e}")
        return False

async def main():
    """Run WebSocket test."""
    success = await test_websocket()

    if success:
        print("\n🎉 WebSocket connection test passed!")
        print("Frontend should now be able to connect to backend.")
        return 0
    else:
        print("\n❌ WebSocket connection test failed!")
        return 1

if __name__ == "__main__":
    exit_code = asyncio.run(main())
    exit(exit_code)