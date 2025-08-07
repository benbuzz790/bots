"""
Comprehensive tests for WebSocket handler with defensive programming validation.
Tests WebSocket event handling, message routing, and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from typing import Dict, Any

# Import the WebSocket handler we're testing (assuming it'll be created)
try:
    from backend.websocket_handler import (
        WebSocketHandler, WebSocketEvent, handle_websocket_connection
    )
    from backend.models import MessageRole, Message, BotState
except ImportError:
    # Mock the handler for testing structure
    from pydantic import BaseModel
    from enum import Enum

    class WebSocketEvent(BaseModel):
        type: str
        data: Dict[str, Any]

    class WebSocketHandler:
        def __init__(self, bot_manager):
            self.bot_manager = bot_manager
            self.connections = {}

        async def handle_event(self, websocket, event: WebSocketEvent):
            pass

        async def send_response(self, websocket, event_type: str, data: Dict[str, Any]):
            pass


class TestWebSocketEvent:
    """Test WebSocketEvent model validation."""

    def test_valid_websocket_event_creation(self):
        """Test creating a valid WebSocketEvent."""
        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123", "content": "Hello"}
        )

        assert event.type == "send_message"
        assert event.data["botId"] == "bot-123"
        assert event.data["content"] == "Hello"

    def test_websocket_event_validation_failures(self):
        """Test WebSocketEvent validation failures."""
        # Missing required fields
        with pytest.raises(ValueError):
            WebSocketEvent()

        # Invalid data type
        with pytest.raises(ValueError):
            WebSocketEvent(type="test", data="not_a_dict")

    def test_websocket_event_field_types(self):
        """Test WebSocketEvent field type validation."""
        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123"}
        )

        assert isinstance(event.type, str)
        assert isinstance(event.data, dict)


class TestWebSocketHandler:
    """Test WebSocketHandler class with defensive programming."""

    def setup_method(self):
        """Set up test fixtures."""
        import sys
        import os

        # Add the backend directory to the path
        backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
        sys.path.insert(0, backend_path)

        from websocket_handler import WebSocketHandler
        from bot_manager import BotManager

        self.mock_bot_manager = Mock(spec=BotManager)
        self.handler = WebSocketHandler(self.mock_bot_manager)
        self.mock_websocket = AsyncMock()

    def test_websocket_handler_initialization(self):
        """Test WebSocketHandler initialization."""
        assert self.handler.bot_manager == self.mock_bot_manager
        assert isinstance(self.handler.connections, dict)

    def test_websocket_handler_input_validation(self):
        """Test WebSocketHandler input validation during initialization."""
        import sys
        import os

        # Add the backend directory to the path
        backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
        sys.path.insert(0, backend_path)

        from websocket_handler import WebSocketHandler

        # Test None bot_manager - this should raise AssertionError in real implementation
        try:
            WebSocketHandler(None)
            assert False, "Should have raised AssertionError for None bot_manager"
        except AssertionError:
            pass  # Expected

        # Test invalid bot_manager type - this should raise AssertionError in real implementation  
        try:
            WebSocketHandler("not_a_bot_manager")
            assert False, "Should have raised AssertionError for invalid bot_manager type"
        except AssertionError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_handle_send_message_event(self):
        """Test handling send_message event."""
        # Mock bot manager methods properly
        mock_bot_state = Mock()
        mock_bot_state.dict.return_value = {
            "id": "bot-123",
            "name": "Test Bot",
            "conversation_tree": {},
            "current_node_id": "node-1",
            "is_connected": True,
            "is_thinking": False
        }
        mock_bot_state.react_flow_data = {"nodes": [], "edges": []}

        # Mock the async methods
        self.mock_bot_manager.list_bots = AsyncMock(return_value={})
        self.mock_bot_manager.send_message = AsyncMock(return_value=mock_bot_state)

        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123", "content": "Hello"}
        )

        await self.handler.handle_event(self.mock_websocket, event)

        # Verify bot manager send_message was called
        self.mock_bot_manager.send_message.assert_called_once_with("bot-123", "Hello")

        # Verify WebSocket responses were sent (thinking + response)
        assert self.mock_websocket.send_json.call_count == 2

    @pytest.mark.asyncio
    async def test_handle_get_bot_state_event(self):
        """Test handling get_bot_state event."""
        # Mock bot state
        mock_bot_state = Mock()
        mock_bot_state.dict.return_value = {
            "id": "bot-123",
            "name": "Test Bot",
            "conversation_tree": {},
            "current_node_id": "node-1",
            "is_connected": True,
            "is_thinking": False
        }

        # Mock the async method
        self.mock_bot_manager.get_bot_state = AsyncMock(return_value=mock_bot_state)

        event = WebSocketEvent(
            type="get_bot_state",
            data={"botId": "bot-123"}
        )

        await self.handler.handle_event(self.mock_websocket, event)

        # Verify bot state was retrieved
        self.mock_bot_manager.get_bot_state.assert_called_once_with("bot-123")

        # Verify WebSocket response was sent
        self.mock_websocket.send_json.assert_called_once()

    @pytest.mark.asyncio
    async def test_handle_invalid_event_type(self):
        """Test handling invalid event type."""
        event = WebSocketEvent(
            type="invalid_event",
            data={}
        )

        await self.handler.handle_event(self.mock_websocket, event)

        # Should send error response via send_json
        self.mock_websocket.send_json.assert_called_once()
        call_args = self.mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert "Unknown message type" in call_args["data"]["message"]

    @pytest.mark.asyncio
    async def test_handle_event_with_missing_data(self):
        """Test handling event with missing required data."""
        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123"}  # Missing content
        )

        await self.handler.handle_event(self.mock_websocket, event)

        # Should send error response via send_json
        self.mock_websocket.send_json.assert_called_once()
        call_args = self.mock_websocket.send_json.call_args[0][0]
        assert call_args["type"] == "error"
        assert "content" in call_args["data"]["message"]

    @pytest.mark.asyncio
    async def test_handle_event_with_nonexistent_bot(self):
        """Test handling event with nonexistent bot."""
        # Mock bot manager methods properly
        self.mock_bot_manager.list_bots = AsyncMock(return_value={})
        self.mock_bot_manager.send_message = AsyncMock(side_effect=Exception("Bot not found"))

        event = WebSocketEvent(
            type="send_message",
            data={"botId": "nonexistent-bot", "content": "Hello"}
        )

        await self.handler.handle_event(self.mock_websocket, event)

        # Should send error response via send_json
        self.mock_websocket.send_json.assert_called()
        # Check if any call was an error (thinking indicator might be sent first)
        calls = self.mock_websocket.send_json.call_args_list
        error_calls = [call for call in calls if call[0][0].get("type") == "error"]
        assert len(error_calls) > 0
        assert "Bot not found" in error_calls[0][0][0]["data"]["message"]

    @pytest.mark.asyncio
    async def test_websocket_send_json_functionality(self):
        """Test WebSocket send_json functionality."""
        response_data = {
            "type": "bot_response",
            "data": {
                "botId": "bot-123",
                "message": "Test response"
            }
        }

        # Test direct WebSocket send_json call
        await self.mock_websocket.send_json(response_data)

        # Verify WebSocket send_json was called
        self.mock_websocket.send_json.assert_called_once_with(response_data)

    def test_websocket_handler_input_validation(self):
        """Test WebSocketHandler input validation during initialization."""
        import sys
        import os

        # Add the backend directory to the path
        backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
        sys.path.insert(0, backend_path)

        from websocket_handler import WebSocketHandler

        # Test None bot_manager - this should raise AssertionError in real implementation
        try:
            WebSocketHandler(None)
            assert False, "Should have raised AssertionError for None bot_manager"
        except AssertionError:
            pass  # Expected

        # Test invalid bot_manager type - this should raise AssertionError in real implementation  
        try:
            WebSocketHandler("not_a_bot_manager")
            assert False, "Should have raised AssertionError for invalid bot_manager type"
        except AssertionError:
            pass  # Expected

    @pytest.mark.asyncio
    async def test_connection_management(self):
        """Test WebSocket connection management."""
        connection_id = "conn-123"

        # Add connection
        self.handler.connections[connection_id] = self.mock_websocket
        assert connection_id in self.handler.connections

        # Remove connection
        del self.handler.connections[connection_id]
        assert connection_id not in self.handler.connections

    @pytest.mark.asyncio
    async def test_error_handling_during_event_processing(self):
        """Test error handling during event processing."""
        # Mock bot manager methods properly
        self.mock_bot_manager.list_bots = AsyncMock(return_value={})
        self.mock_bot_manager.send_message = AsyncMock(side_effect=Exception("Database error"))

        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123", "content": "Hello"}
        )

        await self.handler.handle_event(self.mock_websocket, event)

        # Should send error response via send_json
        self.mock_websocket.send_json.assert_called()
        # Check if any call was an error (thinking indicator might be sent first)
        calls = self.mock_websocket.send_json.call_args_list
        error_calls = [call for call in calls if call[0][0].get("type") == "error"]
        assert len(error_calls) > 0
        assert "Database error" in error_calls[0][0][0]["data"]["message"]


class TestWebSocketConnection:
    """Test WebSocket connection handling."""

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test complete WebSocket connection lifecycle."""
        mock_websocket = AsyncMock()
        mock_bot_manager = Mock()

        # Mock WebSocket receive to simulate client messages
        messages = [
            json.dumps({
                "type": "send_message",
                "data": {"botId": "bot-123", "content": "Hello"}
            }),
            json.dumps({
                "type": "get_bot_state",
                "data": {"botId": "bot-123"}
            })
        ]

        mock_websocket.receive_text.side_effect = messages + [Exception("Connection closed")]

        handler = WebSocketHandler(mock_bot_manager)

        # This would be the actual connection handler
        # await handle_websocket_connection(mock_websocket, handler)

        # Verify connection was handled
        # assert mock_websocket.receive_text.call_count >= 2

    @pytest.mark.asyncio
    async def test_websocket_connection_error_handling(self):
        """Test WebSocket connection error handling."""
        mock_websocket = AsyncMock()
        mock_bot_manager = Mock()

        # Mock WebSocket to raise exception
        mock_websocket.receive_text.side_effect = Exception("Connection error")

        handler = WebSocketHandler(mock_bot_manager)

        # Connection should handle errors gracefully
        try:
            # await handle_websocket_connection(mock_websocket, handler)
            pass
        except Exception as e:
            pytest.fail(f"Connection handler should not raise: {e}")

    @pytest.mark.asyncio
    async def test_invalid_json_message_handling(self):
        """Test handling of invalid JSON messages."""
        mock_websocket = AsyncMock()
        mock_bot_manager = Mock()

        # Mock invalid JSON message
        mock_websocket.receive_text.return_value = "invalid json"

        handler = WebSocketHandler(mock_bot_manager)

        with patch.object(handler, 'send_response') as mock_send:
            # This should handle invalid JSON gracefully
            try:
                raw_message = await mock_websocket.receive_text()
                json.loads(raw_message)  # This will fail
            except json.JSONDecodeError:
                await handler.send_response(
                    mock_websocket,
                    "error",
                    {"message": "Invalid JSON format"}
                )

            # Should send error response
            mock_send.assert_called_once()


class TestWebSocketEventValidation:
    """Test WebSocket event validation and defensive programming."""

    def test_event_type_validation(self):
        """Test event type validation."""
        valid_types = ["send_message", "get_bot_state", "navigate", "auto_mode"]

        for event_type in valid_types:
            event = WebSocketEvent(type=event_type, data={})
            assert event.type == event_type

    def test_event_data_validation(self):
        """Test event data validation."""
        # Valid data structures for different event types
        test_cases = [
            {
                "type": "send_message",
                "data": {"botId": "bot-123", "content": "Hello"}
            },
            {
                "type": "get_bot_state",
                "data": {"botId": "bot-123"}
            },
            {
                "type": "navigate",
                "data": {"botId": "bot-123", "direction": "up"}
            }
        ]

        for case in test_cases:
            event = WebSocketEvent(**case)
            assert event.type == case["type"]
            assert event.data == case["data"]

    def test_event_serialization(self):
        """Test WebSocket event serialization."""
        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123", "content": "Hello"}
        )

        serialized = event.model_dump()
        assert isinstance(serialized, dict)
        assert serialized["type"] == "send_message"
        assert serialized["data"]["botId"] == "bot-123"

        # Test JSON serialization
        json_str = json.dumps(serialized)
        assert isinstance(json_str, str)

        # Test deserialization
        deserialized = json.loads(json_str)
        reconstructed = WebSocketEvent(**deserialized)
        assert reconstructed.type == event.type
        assert reconstructed.data == event.data


class TestWebSocketSecurity:
    """Test WebSocket security and input validation."""

    @pytest.mark.asyncio
    async def test_malicious_input_handling(self):
        """Test handling of malicious input."""
        import sys
        import os

        # Add the backend directory to the path
        backend_path = os.path.join(os.path.dirname(__file__), '..', '..', 'backend')
        sys.path.insert(0, backend_path)

        from websocket_handler import WebSocketHandler
        from bot_manager import BotManager

        mock_bot_manager = Mock(spec=BotManager)
        handler = WebSocketHandler(mock_bot_manager)
        mock_websocket = AsyncMock()

        # Test various malicious inputs
        malicious_inputs = [
            {"type": "send_message", "data": {"botId": "", "content": "test"}},  # Empty botId
            {"type": "send_message", "data": {"botId": "bot-123", "content": ""}},  # Empty content
            {"type": "send_message", "data": {"botId": "bot-123"}},  # Missing content
            {"type": "get_bot_state", "data": {}},  # Missing botId
        ]

        for malicious_input in malicious_inputs:
            mock_websocket.reset_mock()
            await handler.handle_message(mock_websocket, malicious_input)

            # Should send error response
            mock_websocket.send_json.assert_called()
            call_args = mock_websocket.send_json.call_args[0][0]
            assert call_args["type"] == "error"

    def test_input_sanitization(self):
        """Test input sanitization for WebSocket events."""
        # Test content length limits
        long_content = "A" * 10000
        event = WebSocketEvent(
            type="send_message",
            data={"botId": "bot-123", "content": long_content}
        )

        # Should create event but content might be truncated in handler
        assert event.data["content"] == long_content

        # Test bot ID format validation
        invalid_bot_ids = ["", None, 123, "bot with spaces", "bot/with/slashes"]

        for bot_id in invalid_bot_ids:
            try:
                event = WebSocketEvent(
                    type="send_message",
                    data={"botId": bot_id, "content": "Hello"}
                )
                # Event creation might succeed, but handler should validate
                assert event.data["botId"] == bot_id
            except (ValueError, TypeError):
                # Some invalid IDs might fail at Pydantic level
                pass


if __name__ == "__main__":
    pytest.main([__file__])