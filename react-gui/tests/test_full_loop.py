#!/usr/bin/env python3
"""
Full loop test for React GUI - tests the complete user workflow.
Simulates: Bot creation -> WebSocket connection -> Message sending -> Response handling
"""

import asyncio
import json
import requests
import websockets
import time
from typing import Dict, Any, Optional


class FullLoopTester:
    def __init__(self, backend_url="http://localhost:8000", ws_url="ws://localhost:8000/ws"):
        self.backend_url = backend_url
        self.ws_url = ws_url
        self.bot_id = None
        self.received_messages = []

    def test_1_backend_health(self) -> bool:
        """Test 1: Backend health check."""
        print("🔍 Test 1: Backend Health Check")
        try:
            response = requests.get(f"{self.backend_url}/api/health", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Backend healthy - {data.get('bots_count', 0)} bots active")
                return True
            else:
                print(f"   ❌ Health check failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Health check error: {e}")
            return False

    def test_2_bot_creation(self) -> bool:
        """Test 2: Bot creation via REST API."""
        print("🔍 Test 2: Bot Creation")
        try:
            response = requests.post(
                f"{self.backend_url}/api/bots/create",
                json={"name": "Full Loop Test Bot"},
                timeout=10
            )
            if response.status_code == 200:
                data = response.json()
                self.bot_id = data.get("bot_id")
                print(f"   ✅ Bot created: {self.bot_id}")
                print(f"   ✅ Bot name: {data.get('name')}")
                return True
            else:
                print(f"   ❌ Bot creation failed: {response.status_code}")
                print(f"   ❌ Response: {response.text}")
                return False
        except Exception as e:
            print(f"   ❌ Bot creation error: {e}")
            return False

    def test_3_bot_retrieval(self) -> bool:
        """Test 3: Bot state retrieval via REST API."""
        print("🔍 Test 3: Bot State Retrieval")
        if not self.bot_id:
            print("   ❌ No bot ID available")
            return False

        try:
            response = requests.get(f"{self.backend_url}/api/bots/{self.bot_id}", timeout=5)
            if response.status_code == 200:
                data = response.json()
                print(f"   ✅ Bot retrieved: {data.get('name')}")
                print(f"   ✅ Bot connected: {data.get('is_connected')}")
                return True
            else:
                print(f"   ❌ Bot retrieval failed: {response.status_code}")
                return False
        except Exception as e:
            print(f"   ❌ Bot retrieval error: {e}")
            return False

    async def test_4_websocket_full_flow(self) -> bool:
        """Test 4: Complete WebSocket message flow."""
        print("🔍 Test 4: WebSocket Full Message Flow")
        if not self.bot_id:
            print("   ❌ No bot ID available")
            return False

        try:
            async with websockets.connect(self.ws_url) as websocket:
                print("   ✅ WebSocket connected")

                # Send test message
                test_message = "Hello! This is a full loop test message."
                message = {
                    "type": "send_message",
                    "data": {
                        "botId": self.bot_id,
                        "content": test_message
                    }
                }
                await websocket.send(json.dumps(message))
                print(f"   ✅ Message sent: '{test_message}'")

                # Collect responses for up to 15 seconds
                responses = []
                start_time = time.time()
                
                while time.time() - start_time < 15:
                    try:
                        response = await asyncio.wait_for(websocket.recv(), timeout=2)
                        data = json.loads(response)
                        responses.append(data)
                        print(f"   📨 Received: {data.get('type', 'unknown')}")
                        
                        # Check if we got a complete bot response
                        if data.get('type') == 'bot_response':
                            bot_state = data.get('data', {}).get('botState', {})
                            if bot_state:
                                print(f"   ✅ Bot response received")
                                print(f"   ✅ Bot state valid: {bool(bot_state.get('id'))}")
                                print(f"   ✅ Conversation tree: {len(bot_state.get('conversationTree', {}))}")
                                return True
                                
                    except asyncio.TimeoutError:
                        continue
                    except Exception as e:
                        print(f"   ⚠️  Response parsing error: {e}")
                        continue

                print(f"   ❌ No complete bot response received in 15 seconds")
                print(f"   📊 Total responses: {len(responses)}")
                return False

        except Exception as e:
            print(f"   ❌ WebSocket test error: {e}")
            return False

    async def run_full_loop_test(self):
        """Run complete full loop test."""
        print("🚀 Starting Full Loop Test - Complete User Workflow")
        print("=" * 60)

        tests = [
            ("Backend Health", self.test_1_backend_health),
            ("Bot Creation", self.test_2_bot_creation),
            ("Bot Retrieval", self.test_3_bot_retrieval),
            ("WebSocket Flow", self.test_4_websocket_full_flow),
        ]

        passed = 0
        total = len(tests)

        for test_name, test_func in tests:
            if asyncio.iscoroutinefunction(test_func):
                result = await test_func()
            else:
                result = test_func()
            
            if result:
                passed += 1
            print()  # Empty line between tests

        print("=" * 60)
        print(f"🏁 Full Loop Test Complete: {passed}/{total} tests passed")
        
        if passed == total:
            print("🎉 ALL TESTS PASSED - System is fully functional!")
        else:
            print("❌ Some tests failed - Check the output above")
        
        return passed == total


if __name__ == "__main__":
    tester = FullLoopTester()
    success = asyncio.run(tester.run_full_loop_test())
    exit(0 if success else 1)
