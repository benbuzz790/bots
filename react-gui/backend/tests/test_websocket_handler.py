"""Tests for WebSocket handler with comprehensive defensive validation."""

import pytest
import uuid
import json
from unittest.mock import Mock, patch, AsyncMock
import sys
import os
sys.path.append(os.path.join(os.path.dirname(__file__), '..'))

from websocket_handler import WebSocketHandler
from bot_manager import BotManager
from models import BotState
from .conftest import (
    assert_bot_state_valid,
    VALID_BOT_NAME, VALID_MESSAGE_CONTENT,
    INVALID_EMPTY_STRING, INVALID_WHITESPACE_STRING,
    INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST
)


class TestWebSocketHandler:
    """Test WebSocket handler functionality."""

    @pytest.fixture
    def mock_bot_manager(self):
        """Create a mock bot manager."""
        manager = Mock(spec=BotManager)
        manager.send_message = AsyncMock()
        manager.get_bot_state = AsyncMock()
        manager.list_bots = AsyncMock(return_value={})
        return manager

    @pytest.fixture
    def mock_websocket(self):
        """Create a mock WebSocket connection."""
        websocket = Mock()
        websocket.send_json = AsyncMock()
        websocket.receive_json = AsyncMock()
        return websocket

    @pytest.fixture
    def handler(self, mock_bot_manager):
        """Create WebSocket handler with mock bot manager."""
        return WebSocketHandler(mock_bot_manager)

    @pytest.mark.asyncio
    async def test_websocket_handler_initialization(self, mock_bot_manager):
        """Test WebSocket handler initialization."""
        handler = WebSocketHandler(mock_bot_manager)

        assert handler.bot_manager is mock_bot_manager
        assert hasattr(handler, 'connections')

    @pytest.mark.asyncio
    async def test_handle_send_message_event(self, handler, mock_websocket):
        """Test handling send message events."""
        # Mock bot manager response
        mock_bot_state = Mock(spec=BotState)
        handler.bot_manager.send_message.return_value = mock_bot_state

        event_data = {
            'type': 'send_message',
            'data': {
                'botId': str(uuid.uuid4()),
                'content': VALID_MESSAGE_CONTENT
            }
        }

        await handler.handle_message(mock_websocket, event_data)

        # Verify bot manager was called
        handler.bot_manager.send_message.assert_called_once()

        # Verify response was sent
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_handle_get_bot_state_event(self, handler, mock_websocket):
        """Test handling get bot state events."""
        # Mock bot manager response
        mock_bot_state = Mock(spec=BotState)
        handler.bot_manager.get_bot_state.return_value = mock_bot_state

        event_data = {
            'type': 'get_bot_state',
            'data': {
                'botId': str(uuid.uuid4())
            }
        }

        await handler.handle_message(mock_websocket, event_data)

        # Verify bot manager was called
        handler.bot_manager.get_bot_state.assert_called_once()

        # Verify response was sent
        mock_websocket.send_json.assert_called()

    @pytest.mark.asyncio
    async def test_handle_invalid_event_type(self, handler, mock_websocket):
        """Test handling invalid event types."""
        event_data = {
            'type': 'invalid_event',
            'data': {}
        }

        await handler.handle_message(mock_websocket, event_data)

        # Verify error response was sent
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args['type'] == 'error'

    @pytest.mark.asyncio
    async def test_handle_event_with_missing_data(self, handler, mock_websocket):
        """Test handling events with missing required data."""
        event_data = {
            'type': 'send_message',
            'data': {
                'botId': str(uuid.uuid4())
                # Missing 'content' field
            }
        }

        await handler.handle_message(mock_websocket, event_data)

        # Verify error response was sent
        mock_websocket.send_json.assert_called()
        call_args = mock_websocket.send_json.call_args[0][0]
        assert call_args['type'] == 'error'
