#!/usr/bin/env python3
"""
Simple automated test for the React GUI chat functionality.
Tests both REST API and WebSocket communication.
"""

import asyncio
import json
import requests
import websockets
from typing import Dict, Any


class ChatTester:
    def __init__(self, backend_url="http://localhost:8000", ws_url="ws://localhost:8000/ws"):
        self.backend_url = backend_url
        self.ws_url = ws_url
        self.bot_id = None

    def test_backend_health(self) -> bool:
        """Test if backend is running and healthy."""
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                print("✅ Backend health check passed")
                return True
            else:
                print(f"❌ Backend health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"❌ Backend health check failed: {e}")
            return False

    def test_bot_creation(self) -> bool:
        """Test bot creation via REST API."""
        try:
            response = requests.post(
                f"{self.backend_url}/api/bots/create",
                json={"name": "Test Bot"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.bot_id = data.get("bot_id")
                print(f"✅ Bot created successfully: {self.bot_id}")
                return True
            else:
                print(f"❌ Bot creation failed: {response.status_code} - {response.text}")
                return False
        except Exception as e:
            print(f"❌ Bot creation failed: {e}")
            return False

    async def test_websocket_communication(self) -> bool:
        """Test WebSocket message sending."""
        if not self.bot_id:
            print("❌ No bot ID available for WebSocket test")
            return False

        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("✅ WebSocket connected")

                # Send a test message
                message = {
                    "type": "send_message",
                    "data": {
                        "botId": self.bot_id,
                        "content": "Hello, test message!"
                    }
                }
                await websocket.send(json.dumps(message))
                print("✅ Test message sent")

                # Wait for response (with timeout)
                response = await asyncio.wait_for(websocket.recv(), timeout=10)
                data = json.loads(response)
                print(f"✅ Received response: {data.get('type', 'unknown')}")
                return True

        except Exception as e:
            print(f"❌ WebSocket test failed: {e}")
            return False

    async def run_all_tests(self):
        """Run all tests in sequence."""
        print("🧪 Starting automated chat functionality tests...\n")

        tests_passed = 0
        total_tests = 3

        if self.test_backend_health():
            tests_passed += 1
        if self.test_bot_creation():
            tests_passed += 1
        if await self.test_websocket_communication():
            tests_passed += 1

        print(f"\n🏁 Tests completed: {tests_passed}/{total_tests} passed")
        return tests_passed == total_tests


if __name__ == "__main__":
    tester = ChatTester()
    success = asyncio.run(tester.run_all_tests())
    exit(0 if success else 1)
