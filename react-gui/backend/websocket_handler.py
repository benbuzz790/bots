"""
WebSocket handler for real-time communication with React frontend.
Implements the WebSocketHandler class from architecture.md with defensive programming.
"""
import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

try:
    from .models import (
        SendMessageEvent, GetBotStateEvent, BotResponseEvent,
        ToolUpdateEvent, ErrorEvent, MessageRole
    )
    from .bot_manager import BotManager
except ImportError:
    from models import (
        SendMessageEvent, GetBotStateEvent, BotResponseEvent,
        ToolUpdateEvent, ErrorEvent, MessageRole
    )
    from bot_manager import BotManager


logging.basicConfig(level=logging.INFO, format='%(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.info("Attempting to import bots framework...")

class WebSocketHandler:
    """Handles WebSocket connections and message routing with defensive validation."""

    def __init__(self, bot_manager: BotManager):
        """Initialize WebSocket handler."""
        assert isinstance(bot_manager, BotManager), f"Expected BotManager, got {type(bot_manager)}"
        self.bot_manager = bot_manager
        self.connections: Dict[str, WebSocket] = {}

    def _convert_bot_state_for_frontend(self, bot_state_dict: Dict[str, Any]) -> Dict[str, Any]:
        """Convert bot state field names from snake_case to camelCase for frontend."""
        field_mapping = {
            'conversation_tree': 'conversationTree',
            'current_node_id': 'currentNodeId',
            'is_connected': 'isConnected',
            'is_thinking': 'isThinking',
            'react_flow_data': 'reactFlowData'
        }

        converted = {}
        for key, value in bot_state_dict.items():
            new_key = field_mapping.get(key, key)

            # Special handling for conversation_tree - convert nested ConversationNode objects
            if key == 'conversation_tree' and isinstance(value, dict):
                converted_tree = {}
                for node_id, node in value.items():
                    if hasattr(node, 'dict'):
                        # Pydantic model - convert to dict
                        node_dict = node.dict()
                    elif isinstance(node, dict):
                        # Already a dict
                        node_dict = node
                    else:
                        # Fallback
                        node_dict = node

                    # Convert node field names from snake_case to camelCase
                    converted_node = {}
                    node_field_mapping = {
                        'is_current': 'isCurrent',
                        'tool_calls': 'toolCalls'
                    }

                    for node_key, node_value in node_dict.items():
                        converted_node[node_field_mapping.get(node_key, node_key)] = node_value

                    converted_tree[node_id] = converted_node
                converted[new_key] = converted_tree
            else:
                converted[new_key] = value

        return converted

    async def handle_connection(self, websocket: WebSocket):
        """Handle new WebSocket connection."""
        assert isinstance(websocket, WebSocket), f"Expected WebSocket, got {type(websocket)}"
        await websocket.accept()
        connection_id = str(uuid.uuid4())
        self.connections[connection_id] = websocket

        try:
            while True:
                data = await websocket.receive_json()
                await self.handle_message(websocket, data)
        except WebSocketDisconnect:
            if connection_id in self.connections:
                del self.connections[connection_id]
            logger.info(f"WebSocket connection {connection_id} disconnected")

    async def handle_message(self, websocket: WebSocket, data: dict):
        """Process incoming WebSocket message."""
        assert isinstance(data, dict), f"data must be dict, got {type(data)}"
        assert 'type' in data, "data must have 'type' field"

        message_type = data['type']
        message_data = data.get('data', {})

        try:
            if message_type == 'send_message':
                await self._handle_send_message(websocket, message_data)
            elif message_type == 'get_bot_state':
                await self._handle_get_bot_state(websocket, message_data)
            else:
                await self._send_error(websocket, f"Unknown message type: {message_type}")
        except Exception as e:
            logger.error(f"Error handling message: {e}")
            await self._send_error(websocket, str(e))

    async def _handle_send_message(self, websocket: WebSocket, data: dict):
        """Handle send_message event."""
        assert 'botId' in data, "data must have 'botId' field"
        assert 'content' in data, "data must have 'content' field"

        bot_id = data['botId']
        content = data['content']

        # Send thinking indicator
        await websocket.send_json({
            'type': 'bot_thinking',
            'data': {'botId': bot_id, 'thinking': True}
        })

        try:
            # Get bot response
            bot_state = await self.bot_manager.send_message(bot_id, content)

            # Convert bot state to frontend format (this handles all field conversions)
            converted_bot_state = self._convert_bot_state_for_frontend(bot_state.dict())

            # Send response with properly converted data
            await websocket.send_json({
                'type': 'bot_response',
                'data': {
                    'botId': bot_id,
                    **converted_bot_state  # Spread the converted fields directly
                }
            })
        except Exception as e:
            await self._send_error(websocket, f"Error sending message: {str(e)}")

    async def _handle_get_bot_state(self, websocket: WebSocket, data: dict):
        """Handle get_bot_state event."""
        assert 'botId' in data, "data must have 'botId' field"

        bot_id = data['botId']

        try:
            bot_state = await self.bot_manager.get_bot_state(bot_id)

            # Convert bot state to frontend format
            converted_bot_state = self._convert_bot_state_for_frontend(bot_state.dict())

            await websocket.send_json({
                'type': 'bot_state',
                'data': {
                    'botId': bot_id,
                    **converted_bot_state  # Spread the converted fields directly
                }
            })
        except Exception as e:
            await self._send_error(websocket, f"Error getting bot state: {str(e)}")

    async def _send_error(self, websocket: WebSocket, message: str):
        """Send error message to client."""
        await websocket.send_json({
            'type': 'error',
            'data': {'message': message}
        })

    async def handle_event(self, websocket: WebSocket, event):
        """Handle WebSocket event - compatibility method for tests."""
        if hasattr(event, 'model_dump'):
            # Pydantic v2 model
            data = event.model_dump()
        elif hasattr(event, 'dict'):
            # Pydantic v1 model (fallback)
            data = event.dict()
        elif hasattr(event, 'type') and hasattr(event, 'data'):
            # Object with type and data attributes
            data = {'type': event.type, 'data': event.data}
        else:
            # Assume it's already a dict
            data = event

        await self.handle_message(websocket, data)