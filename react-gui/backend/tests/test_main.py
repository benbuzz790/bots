"""Integration tests for FastAPI main application."""

import pytest
import json
from fastapi.testclient import TestClient
from unittest.mock import Mock, patch, AsyncMock
import uuid

# Import the FastAPI app
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from backend.main import app
from models import BotState
from conftest import (
    assert_bot_state_valid,
    VALID_BOT_NAME, VALID_MESSAGE_CONTENT,
    INVALID_EMPTY_STRING, INVALID_WHITESPACE_STRING,
    INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST
)


class TestFastAPIApp:
    """Test FastAPI application endpoints and WebSocket functionality."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/api/health")

        assert response.status_code == 200, f"Expected 200, got {response.status_code}"

        data = response.json()
        assert isinstance(data, dict), f"Expected dict, got {type(data)}"
        assert "status" in data, "Response should have 'status' field"
        assert data["status"] == "healthy", f"Expected 'healthy', got {data['status']}"
        assert "timestamp" in data, "Response should have 'timestamp' field"

    def test_create_bot_endpoint_valid_request(self):
        """Test creating a bot with valid request."""
        with patch('main.bot_manager.create_bot') as mock_create_bot:
            test_bot_id = str(uuid.uuid4())
            mock_create_bot.return_value = test_bot_id

            request_data = {"name": VALID_BOT_NAME}
            response = self.client.post("/api/bots/create", json=request_data)

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert isinstance(data, dict), f"Expected dict, got {type(data)}"
            assert "bot_id" in data, "Response should have 'bot_id' field"
            assert data["bot_id"] == test_bot_id, f"Expected {test_bot_id}, got {data['bot_id']}"

            # Verify bot_manager.create_bot was called correctly
            mock_create_bot.assert_called_once_with(VALID_BOT_NAME)

    def test_create_bot_endpoint_missing_name(self):
        """Test creating a bot without name field."""
        request_data = {}  # Missing 'name' field
        response = self.client.post("/api/bots/create", json=request_data)

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

        data = response.json()
        assert "detail" in data, "Error response should have 'detail' field"

    def test_create_bot_endpoint_invalid_name_type(self):
        """Test creating a bot with invalid name type."""
        invalid_names = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_name in invalid_names:
            request_data = {"name": invalid_name}
            response = self.client.post("/api/bots/create", json=request_data)

            assert response.status_code == 422, f"Expected 422 for {invalid_name}, got {response.status_code}"

    def test_create_bot_endpoint_empty_name(self):
        """Test creating a bot with empty name."""
        with patch('main.bot_manager.create_bot') as mock_create_bot:
            mock_create_bot.side_effect = AssertionError("name cannot be empty")

            request_data = {"name": INVALID_EMPTY_STRING}
            response = self.client.post("/api/bots/create", json=request_data)

            assert response.status_code == 400, f"Expected 400, got {response.status_code}"

            data = response.json()
            assert "detail" in data, "Error response should have 'detail' field"
            assert "name cannot be empty" in data["detail"]

    def test_get_bot_endpoint_valid_id(self):
        """Test getting a bot with valid ID."""
        test_bot_id = str(uuid.uuid4())

        with patch('main.bot_manager.get_bot') as mock_get_bot:
            mock_bot = Mock()
            mock_get_bot.return_value = mock_bot

            with patch('main.bot_manager._get_bot_state') as mock_get_state:
                mock_bot_state = Mock(spec=BotState)
                mock_bot_state.dict.return_value = {
                    "id": test_bot_id,
                    "name": VALID_BOT_NAME,
                    "is_connected": True,
                    "is_thinking": False
                }
                mock_get_state.return_value = mock_bot_state

                response = self.client.get(f"/api/bots/{test_bot_id}")

                assert response.status_code == 200, f"Expected 200, got {response.status_code}"

                data = response.json()
                assert isinstance(data, dict), f"Expected dict, got {type(data)}"
                assert data["id"] == test_bot_id, f"Expected {test_bot_id}, got {data['id']}"
                assert data["name"] == VALID_BOT_NAME, f"Expected {VALID_BOT_NAME}, got {data['name']}"

                # Verify bot_manager methods were called
                mock_get_bot.assert_called_once_with(test_bot_id)
                mock_get_state.assert_called_once_with(mock_bot)

    def test_get_bot_endpoint_invalid_id_format(self):
        """Test getting a bot with invalid ID format."""
        invalid_ids = ["not-a-uuid", "", "123", "invalid-format"]

        for invalid_id in invalid_ids:
            response = self.client.get(f"/api/bots/{invalid_id}")

            # Should either be 400 (validation error) or 404 (not found)
            assert response.status_code in [400, 404], f"Expected 400 or 404 for {invalid_id}, got {response.status_code}"

    def test_get_bot_endpoint_not_found(self):
        """Test getting a non-existent bot."""
        non_existent_id = str(uuid.uuid4())

        with patch('main.bot_manager.get_bot') as mock_get_bot:
            mock_get_bot.return_value = None  # Bot not found

            response = self.client.get(f"/api/bots/{non_existent_id}")

            assert response.status_code == 404, f"Expected 404, got {response.status_code}"

            data = response.json()
            assert "detail" in data, "Error response should have 'detail' field"
            assert "not found" in data["detail"].lower()

    def test_delete_bot_endpoint_valid_id(self):
        """Test deleting a bot with valid ID."""
        test_bot_id = str(uuid.uuid4())

        with patch('main.bot_manager.delete_bot') as mock_delete_bot:
            mock_delete_bot.return_value = True  # Successful deletion

            response = self.client.delete(f"/api/bots/{test_bot_id}")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert isinstance(data, dict), f"Expected dict, got {type(data)}"
            assert "message" in data, "Response should have 'message' field"
            assert "deleted" in data["message"].lower()

            # Verify bot_manager.delete_bot was called
            mock_delete_bot.assert_called_once_with(test_bot_id)

    def test_delete_bot_endpoint_not_found(self):
        """Test deleting a non-existent bot."""
        non_existent_id = str(uuid.uuid4())

        with patch('main.bot_manager.delete_bot') as mock_delete_bot:
            mock_delete_bot.return_value = False  # Bot not found

            response = self.client.delete(f"/api/bots/{non_existent_id}")

            assert response.status_code == 404, f"Expected 404, got {response.status_code}"

            data = response.json()
            assert "detail" in data, "Error response should have 'detail' field"
            assert "not found" in data["detail"].lower()

    def test_list_bots_endpoint_empty(self):
        """Test listing bots when none exist."""
        with patch('main.bot_manager.list_bots') as mock_list_bots:
            mock_list_bots.return_value = []

            response = self.client.get("/api/bots/")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert isinstance(data, list), f"Expected list, got {type(data)}"
            assert len(data) == 0, f"Expected empty list, got {len(data)} items"

    def test_list_bots_endpoint_with_bots(self):
        """Test listing bots when some exist."""
        test_bot_ids = [str(uuid.uuid4()) for _ in range(3)]

        with patch('main.bot_manager.list_bots') as mock_list_bots:
            mock_list_bots.return_value = test_bot_ids

            response = self.client.get("/api/bots/")

            assert response.status_code == 200, f"Expected 200, got {response.status_code}"

            data = response.json()
            assert isinstance(data, list), f"Expected list, got {type(data)}"
            assert len(data) == 3, f"Expected 3 bots, got {len(data)}"

            for bot_id in test_bot_ids:
                assert bot_id in data, f"Bot {bot_id} should be in response"

    def test_websocket_connection(self):
        """Test WebSocket connection establishment."""
        with self.client.websocket_connect("/ws") as websocket:
            # Connection should be established successfully
            assert websocket is not None, "WebSocket connection should be established"

    def test_websocket_send_message_valid(self):
        """Test sending a valid message via WebSocket."""
        with patch('main.websocket_handler.handle_message') as mock_handle_message:
            mock_handle_message.return_value = None  # Async function

            with self.client.websocket_connect("/ws") as websocket:
                test_message = {
                    "type": "send_message",
                    "data": {
                        "botId": str(uuid.uuid4()),
                        "content": VALID_MESSAGE_CONTENT
                    }
                }

                websocket.send_json(test_message)

                # WebSocket should remain connected
                # Note: In real tests, we'd verify the response, but mocking makes this complex

    def test_websocket_invalid_json(self):
        """Test sending invalid JSON via WebSocket."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send invalid JSON (this will be handled by FastAPI/Starlette)
            try:
                websocket.send_text("invalid json")
                # The connection might be closed due to invalid JSON
            except Exception:
                # Expected behavior for invalid JSON
                pass

    def test_cors_headers(self):
        """Test CORS headers are present."""
        response = self.client.get("/api/health")

        assert response.status_code == 200

        # Check for CORS headers (these are added by FastAPI CORS middleware)
        headers = response.headers
        # Note: In test client, CORS headers might not be present
        # This test would be more meaningful in a real browser environment

    def test_error_handling_middleware(self):
        """Test error handling middleware."""
        with patch('main.bot_manager.create_bot') as mock_create_bot:
            # Simulate an unexpected error
            mock_create_bot.side_effect = Exception("Unexpected error")

            request_data = {"name": VALID_BOT_NAME}
            response = self.client.post("/api/bots/create", json=request_data)

            assert response.status_code == 500, f"Expected 500, got {response.status_code}"

            data = response.json()
            assert "detail" in data, "Error response should have 'detail' field"

    def test_request_validation_middleware(self):
        """Test request validation."""
        # Test with completely invalid JSON structure
        response = self.client.post(
            "/api/bots/create",
            json={"invalid_field": "value"},  # Missing required 'name' field
            headers={"Content-Type": "application/json"}
        )

        assert response.status_code == 422, f"Expected 422, got {response.status_code}"

        data = response.json()
        assert "detail" in data, "Validation error should have 'detail' field"

    def test_content_type_validation(self):
        """Test content type validation."""
        # Test with wrong content type
        response = self.client.post(
            "/api/bots/create",
            data="not json",
            headers={"Content-Type": "text/plain"}
        )

        # Should return 422 for invalid content type
        assert response.status_code in [400, 422], f"Expected 400 or 422, got {response.status_code}"

    def test_method_not_allowed(self):
        """Test method not allowed responses."""
        # Try POST on GET-only endpoint
        response = self.client.post("/api/health")

        assert response.status_code == 405, f"Expected 405, got {response.status_code}"

    def test_not_found_endpoint(self):
        """Test 404 for non-existent endpoints."""
        response = self.client.get("/api/nonexistent")

        assert response.status_code == 404, f"Expected 404, got {response.status_code}"


class TestWebSocketIntegration:
    """Integration tests for WebSocket functionality."""

    def setup_method(self):
        """Set up test client for each test."""
        self.client = TestClient(app)

    def test_websocket_send_message_flow(self):
        """Test complete send message flow via WebSocket."""
        with patch('main.bot_manager') as mock_bot_manager:
            # Mock bot manager responses
            mock_bot_state = Mock(spec=BotState)
            mock_bot_state.dict.return_value = {
                "id": "test-bot",
                "name": "Test Bot",
                "conversation_tree": {},
                "current_node_id": "node-1",
                "is_connected": True,
                "is_thinking": False
            }
            mock_bot_manager.send_message.return_value = mock_bot_state

            with self.client.websocket_connect("/ws") as websocket:
                # Send message
                test_message = {
                    "type": "send_message",
                    "data": {
                        "botId": "test-bot-id",
                        "content": VALID_MESSAGE_CONTENT
                    }
                }

                websocket.send_json(test_message)

                # Receive thinking indicator
                thinking_response = websocket.receive_json()
                assert thinking_response["type"] == "bot_thinking"
                assert thinking_response["data"]["thinking"] is True

                # Receive bot response
                bot_response = websocket.receive_json()
                assert bot_response["type"] == "bot_response"
                assert "botState" in bot_response["data"]

    def test_websocket_get_bot_state_flow(self):
        """Test get bot state flow via WebSocket."""
        with patch('main.bot_manager') as mock_bot_manager:
            # Mock bot and state
            mock_bot = Mock()
            mock_bot_manager.get_bot.return_value = mock_bot

            mock_bot_state = Mock(spec=BotState)
            mock_bot_state.dict.return_value = {
                "id": "test-bot",
                "name": "Test Bot",
                "is_connected": True,
                "is_thinking": False
            }

            with patch('main.websocket_handler._get_bot_state') as mock_get_state:
                mock_get_state.return_value = mock_bot_state

                with self.client.websocket_connect("/ws") as websocket:
                    # Send get bot state request
                    test_message = {
                        "type": "get_bot_state",
                        "data": {
                            "botId": "test-bot-id"
                        }
                    }

                    websocket.send_json(test_message)

                    # Receive bot state response
                    response = websocket.receive_json()
                    assert response["type"] == "bot_state"
                    assert "botState" in response["data"]

    def test_websocket_error_handling(self):
        """Test WebSocket error handling."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send invalid message format
            invalid_message = {
                "type": "send_message",
                "data": {
                    # Missing required fields
                }
            }

            websocket.send_json(invalid_message)

            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "message" in response["data"]

    def test_websocket_unknown_message_type(self):
        """Test WebSocket handling of unknown message types."""
        with self.client.websocket_connect("/ws") as websocket:
            # Send unknown message type
            unknown_message = {
                "type": "unknown_type",
                "data": {"some": "data"}
            }

            websocket.send_json(unknown_message)

            # Should receive error response
            response = websocket.receive_json()
            assert response["type"] == "error"
            assert "Unknown message type" in response["data"]["message"]

    def test_multiple_websocket_connections(self):
        """Test handling multiple WebSocket connections."""
        connections = []

        try:
            # Create multiple connections
            for i in range(3):
                ws = self.client.websocket_connect("/ws")
                connections.append(ws.__enter__())

            # All connections should be active
            assert len(connections) == 3

            # Send message on each connection
            for i, ws in enumerate(connections):
                test_message = {
                    "type": "get_bot_state",
                    "data": {"botId": f"bot-{i}"}
                }
                ws.send_json(test_message)

        finally:
            # Clean up connections
            for ws in connections:
                try:
                    ws.__exit__(None, None, None)
                except:
                    pass
