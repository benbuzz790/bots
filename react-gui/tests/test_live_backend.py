#!/usr/bin/env python3
"""
Live integration test for the running React GUI backend.
Tests actual API endpoints against the live server.
"""

import requests
import json
import time
import websocket
import threading
from typing import Dict, Any, List

# Configuration
BACKEND_URL = "http://127.0.0.1:8000"
WEBSOCKET_URL = "ws://127.0.0.1:8000/ws"

class LiveBackendTest:
    """Test the live backend server."""

    def __init__(self):
        self.test_results = []

    def log_result(self, test_name: str, success: bool, message: str = ""):
        """Log test result."""
        status = "✅ PASS" if success else "❌ FAIL"
        result = f"{status} {test_name}"
        if message:
            result += f": {message}"
        print(result)
        self.test_results.append({
            "test": test_name,
            "success": success,
            "message": message
        })

    def test_health_endpoint(self) -> bool:
        """Test the health check endpoint."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/health", timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("status") == "healthy":
                    self.log_result("Health Check", True, f"Backend healthy with {data.get('bots_count', 0)} bots")
                    return True
                else:
                    self.log_result("Health Check", False, f"Unexpected status: {data.get('status')}")
                    return False
            else:
                self.log_result("Health Check", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("Health Check", False, f"Exception: {e}")
            return False

    def test_create_bot(self) -> str:
        """Test bot creation endpoint."""
        try:
            payload = {"name": "Test Bot"}
            response = requests.post(f"{BACKEND_URL}/api/bots/create", 
                                   json=payload, timeout=10)

            if response.status_code == 200:
                data = response.json()
                bot_id = data.get("bot_id")
                if bot_id:
                    self.log_result("Create Bot", True, f"Created bot {bot_id}")
                    return bot_id
                else:
                    self.log_result("Create Bot", False, "No bot_id in response")
                    return None
            else:
                self.log_result("Create Bot", False, f"HTTP {response.status_code}: {response.text}")
                return None

        except Exception as e:
            self.log_result("Create Bot", False, f"Exception: {e}")
            return None

    def test_get_bot(self, bot_id: str) -> bool:
        """Test get bot endpoint."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/bots/{bot_id}", timeout=5)

            if response.status_code == 200:
                data = response.json()
                if data.get("id") == bot_id:
                    self.log_result("Get Bot", True, f"Retrieved bot {bot_id}")
                    return True
                else:
                    self.log_result("Get Bot", False, f"Bot ID mismatch: {data.get('id')} != {bot_id}")
                    return False
            else:
                self.log_result("Get Bot", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("Get Bot", False, f"Exception: {e}")
            return False

    def test_list_bots(self) -> bool:
        """Test list bots endpoint."""
        try:
            response = requests.get(f"{BACKEND_URL}/api/bots", timeout=5)

            if response.status_code == 200:
                data = response.json()
                if isinstance(data, dict):
                    bot_count = len(data)
                    self.log_result("List Bots", True, f"Found {bot_count} bots")
                    return True
                else:
                    self.log_result("List Bots", False, f"Unexpected response type: {type(data)}")
                    return False
            else:
                self.log_result("List Bots", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("List Bots", False, f"Exception: {e}")
            return False

    def test_websocket_connection(self) -> bool:
        """Test WebSocket connection."""
        try:
            connection_id = "test-connection-123"
            ws_url = f"{WEBSOCKET_URL}/{connection_id}"

            # Simple connection test
            ws = websocket.create_connection(ws_url, timeout=5)

            # Send a simple message
            test_message = {
                "type": "get_bot_state",
                "data": {"botId": "test"}
            }
            ws.send(json.dumps(test_message))

            # Try to receive a response (with timeout)
            ws.settimeout(3)
            try:
                response = ws.recv()
                response_data = json.loads(response)
                ws.close()

                self.log_result("WebSocket Connection", True, "Connected and received response")
                return True
            except websocket.WebSocketTimeoutException:
                ws.close()
                self.log_result("WebSocket Connection", True, "Connected (timeout on response is OK)")
                return True

        except Exception as e:
            self.log_result("WebSocket Connection", False, f"Exception: {e}")
            return False

    def test_delete_bot(self, bot_id: str) -> bool:
        """Test delete bot endpoint."""
        try:
            response = requests.delete(f"{BACKEND_URL}/api/bots/{bot_id}", timeout=5)

            if response.status_code == 200:
                self.log_result("Delete Bot", True, f"Deleted bot {bot_id}")
                return True
            else:
                self.log_result("Delete Bot", False, f"HTTP {response.status_code}")
                return False

        except Exception as e:
            self.log_result("Delete Bot", False, f"Exception: {e}")
            return False

    def run_all_tests(self) -> Dict[str, Any]:
        """Run all tests and return results."""
        print("🚀 Starting Live Backend Integration Tests")
        print("=" * 50)

        # Test 1: Health check
        if not self.test_health_endpoint():
            print("❌ Backend not healthy, stopping tests")
            return self.get_summary()

        # Test 2: Create bot
        bot_id = self.test_create_bot()
        if not bot_id:
            print("❌ Cannot create bot, stopping tests")
            return self.get_summary()

        # Test 3: Get bot
        self.test_get_bot(bot_id)

        # Test 4: List bots
        self.test_list_bots()

        # Test 5: WebSocket connection
        self.test_websocket_connection()

        # Test 6: Delete bot (cleanup)
        self.test_delete_bot(bot_id)

        return self.get_summary()

    def get_summary(self) -> Dict[str, Any]:
        """Get test summary."""
        total = len(self.test_results)
        passed = sum(1 for r in self.test_results if r["success"])
        failed = total - passed

        print("\n" + "=" * 50)
        print(f"📊 Test Summary: {passed}/{total} passed, {failed} failed")

        if failed > 0:
            print("\n❌ Failed Tests:")
            for result in self.test_results:
                if not result["success"]:
                    print(f"  - {result['test']}: {result['message']}")

        return {
            "total": total,
            "passed": passed,
            "failed": failed,
            "success_rate": passed / total if total > 0 else 0,
            "results": self.test_results
        }

def main():
    """Run the live backend tests."""
    tester = LiveBackendTest()
    summary = tester.run_all_tests()

    # Exit with appropriate code
    exit_code = 0 if summary["failed"] == 0 else 1
    return exit_code

if __name__ == "__main__":
    exit_code = main()
    exit(exit_code)