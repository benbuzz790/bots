"""
Simple WebSocket handler for the React GUI with defensive programming.
"""

import json
import logging
import uuid
from typing import Dict, Any, Optional
from fastapi import WebSocket, WebSocketDisconnect

from bot_manager import get_bot_manager

logger = logging.getLogger(__name__)

async def websocket_endpoint(websocket: WebSocket, bot_manager_instance):
    """Simple WebSocket endpoint for chat with defensive programming."""
    # Input validation
    assert isinstance(websocket, WebSocket), f"websocket must be WebSocket, got {type(websocket)}"
    assert bot_manager_instance is not None, "bot_manager_instance cannot be None"

    await websocket.accept()
    connection_id = str(uuid.uuid4())

    logger.info(f"WebSocket connection established: {connection_id}")

    try:
        while True:
            # Receive message
            data = await websocket.receive_json()

            # Input validation
            assert isinstance(data, dict), f"data must be dict, got {type(data)}"
            assert 'type' in data, "data must have 'type' field"

            logger.info(f"Received: {data}")

            # Handle different message types
            message_type = data.get('type')
            message_data = data.get('data', {})

            # Validate message_data
            assert isinstance(message_data, dict), f"message_data must be dict, got {type(message_data)}"

            if message_type == 'create_bot':
                # Create new bot
                name = message_data.get('name', 'Demo Bot')
                assert isinstance(name, str), f"name must be str, got {type(name)}"
                assert name.strip(), "name cannot be empty"

                try:
                    bot_id = await bot_manager_instance.create_bot(name.strip())
                    assert isinstance(bot_id, str), f"bot_id must be str, got {type(bot_id)}"
                    assert bot_id, "bot_id cannot be empty"

                    response = {
                        'type': 'bot_created',
                        'data': {'botId': bot_id}
                    }

                    await websocket.send_json(response)
                    logger.info(f"Created bot: {bot_id}")

                except Exception as e:
                    logger.error(f"Error creating bot: {e}")
                    await websocket.send_json({
                        'type': 'error',
                        'data': {'message': f"Failed to create bot: {str(e)}"}
                    })

            elif message_type == 'send_message':
                # Send message to bot
                bot_id = message_data.get('botId')
                content = message_data.get('content')

                # Input validation
                assert isinstance(bot_id, str), f"botId must be str, got {type(bot_id)}"
                assert isinstance(content, str), f"content must be str, got {type(content)}"
                assert bot_id.strip(), "botId cannot be empty"
                assert content.strip(), "content cannot be empty"

                try:
                    # Send thinking indicator
                    await websocket.send_json({
                        'type': 'bot_thinking',
                        'data': {'botId': bot_id, 'thinking': True}
                    })

                    # Get bot response
                    bot_state = await bot_manager_instance.send_message(bot_id, content.strip())

                    # Validate bot_state
                    assert bot_state is not None, "bot_state cannot be None"
                    assert hasattr(bot_state, 'id'), "bot_state must have id attribute"
                    assert hasattr(bot_state, 'name'), "bot_state must have name attribute"

                    # Get conversation tree
                    conversation_tree = await bot_manager_instance.serialize_conversation_tree(bot_id)
                    assert isinstance(conversation_tree, dict), f"conversation_tree must be dict, got {type(conversation_tree)}"

                    response_data = {
                        'type': 'bot_response',
                        'data': {
                            'botId': bot_id,
                            'botState': {
                                'id': bot_state.id,
                                'name': bot_state.name,
                                'conversation_tree': conversation_tree,
                                'current_node_id': bot_state.current_node_id,
                                'is_connected': bot_state.is_connected,
                                'is_thinking': False
                            }
                        }
                    }

                    await websocket.send_json(response_data)
                    logger.info(f"Sent message response for bot: {bot_id}")

                except Exception as e:
                    logger.error(f"Error sending message: {e}")
                    await websocket.send_json({
                        'type': 'error',
                        'data': {'message': f"Failed to send message: {str(e)}"}
                    })

            elif message_type == 'navigate':
                # Navigate conversation tree
                bot_id = message_data.get('botId')
                direction = message_data.get('direction')

                # Input validation
                assert isinstance(bot_id, str), f"botId must be str, got {type(bot_id)}"
                assert isinstance(direction, str), f"direction must be str, got {type(direction)}"
                assert bot_id.strip(), "botId cannot be empty"
                assert direction.strip(), "direction cannot be empty"
                assert direction in ['up', 'down', 'left', 'right'], f"Invalid direction: {direction}"

                try:
                    bot_state = await bot_manager_instance.navigate(bot_id, direction)

                    # Validate bot_state
                    assert bot_state is not None, "bot_state cannot be None"

                    # Get conversation tree
                    conversation_tree = await bot_manager_instance.serialize_conversation_tree(bot_id)
                    assert isinstance(conversation_tree, dict), f"conversation_tree must be dict, got {type(conversation_tree)}"

                    response_data = {
                        'type': 'navigation_response',
                        'data': {
                            'botId': bot_id,
                            'botState': {
                                'id': bot_state.id,
                                'name': bot_state.name,
                                'conversation_tree': conversation_tree,
                                'current_node_id': bot_state.current_node_id,
                                'is_connected': bot_state.is_connected,
                                'is_thinking': False
                            }
                        }
                    }

                    await websocket.send_json(response_data)
                    logger.info(f"Navigation response sent for bot: {bot_id}, direction: {direction}")

                except Exception as e:
                    logger.error(f"Error navigating: {e}")
                    await websocket.send_json({
                        'type': 'error',
                        'data': {'message': f"Failed to navigate: {str(e)}"}
                    })

            else:
                # Unknown message type
                logger.warning(f"Unknown message type: {message_type}")
                await websocket.send_json({
                    'type': 'error',
                    'data': {'message': f'Unknown message type: {message_type}'}
                })

    except WebSocketDisconnect:
        logger.info(f"WebSocket disconnected: {connection_id}")
    except AssertionError as e:
        logger.error(f"Validation error: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'data': {'message': f"Validation error: {str(e)}"}
            })
        except:
            pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
        try:
            await websocket.send_json({
                'type': 'error',
                'data': {'message': f"Server error: {str(e)}"}
            })
        except:
            pass