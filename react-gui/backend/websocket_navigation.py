"""
Navigation handlers for WebSocket events.
Implements tree navigation functionality with defensive programming.
"""

import logging
from typing import Dict

from .models import NavigateEvent, NavigateToNodeEvent, SlashCommandEvent
from .bot_manager import bot_manager

logger = logging.getLogger(__name__)


class NavigationHandler:
    """Handles navigation-related WebSocket events."""

    def __init__(self, connection_manager):
        """Initialize navigation handler."""
        self.manager = connection_manager

    async def handle_navigate(self, connection_id: str, event_data: dict) -> None:
        """
        Handle navigation event with defensive validation.

        Args:
            connection_id: Connection identifier
            event_data: Event data
        """
        # Input validation
        assert isinstance(connection_id, str), f"connection_id must be str, got {type(connection_id)}"
        assert isinstance(event_data, dict), f"event_data must be dict, got {type(event_data)}"

        try:
            # Validate event data
            event = NavigateEvent(type="navigate", data=event_data)

            # Get bot ID
            bot_id = event_data.get('botId')
            if not bot_id:
                bot_id = self.manager.get_bot_id(connection_id)

            if not bot_id:
                await self.manager.send_error(connection_id, "No bot available")
                return

            direction = event_data['direction'].strip().lower()

            # Perform navigation based on direction
            try:
                if direction == 'up':
                    updated_state = bot_manager.navigate_up(bot_id)
                elif direction == 'down':
                    updated_state = bot_manager.navigate_down(bot_id)
                elif direction == 'left':
                    updated_state = bot_manager.navigate_left(bot_id)
                elif direction == 'right':
                    updated_state = bot_manager.navigate_right(bot_id)
                elif direction == 'root':
                    updated_state = bot_manager.navigate_to_root(bot_id)
                else:
                    await self.manager.send_error(connection_id, f"Invalid direction: {direction}")
                    return

                # Send updated bot state
                await self.manager.send_bot_state(connection_id, bot_id)

                logger.info(f"Bot {bot_id} navigated {direction} for connection {connection_id}")

            except ValueError as e:
                # Navigation not possible (e.g., already at root, no children, etc.)
                await self.manager.send_error(connection_id, str(e))
                logger.warning(f"Navigation {direction} failed for bot {bot_id}: {e}")

        except Exception as e:
            logger.error(f"Error handling navigate: {e}")
            await self.manager.send_error(connection_id, f"Navigation failed: {str(e)}")

    async def handle_navigate_to_node(self, connection_id: str, event_data: dict) -> None:
        """
        Handle navigate to node event (click-to-navigate) with defensive validation.

        Args:
            connection_id: Connection identifier
            event_data: Event data
        """
        # Input validation
        assert isinstance(connection_id, str), f"connection_id must be str, got {type(connection_id)}"
        assert isinstance(event_data, dict), f"event_data must be dict, got {type(event_data)}"

        try:
            # Validate event data
            event = NavigateToNodeEvent(type="navigate_to_node", data=event_data)

            # Get bot ID
            bot_id = event_data.get('botId')
            if not bot_id:
                bot_id = self.manager.get_bot_id(connection_id)

            if not bot_id:
                await self.manager.send_error(connection_id, "No bot available")
                return

            node_id = event_data['nodeId'].strip()

            # Perform navigation to specific node
            try:
                updated_state = bot_manager.navigate_to_node(bot_id, node_id)

                # Send updated bot state
                await self.manager.send_bot_state(connection_id, bot_id)

                logger.info(f"Bot {bot_id} navigated to node {node_id} for connection {connection_id}")

            except ValueError as e:
                # Node not found or navigation not possible
                await self.manager.send_error(connection_id, str(e))
                logger.warning(f"Navigation to node {node_id} failed for bot {bot_id}: {e}")

        except Exception as e:
            logger.error(f"Error handling navigate_to_node: {e}")
            await self.manager.send_error(connection_id, f"Node navigation failed: {str(e)}")

    async def handle_slash_command(self, connection_id: str, event_data: dict) -> None:
        """
        Handle slash command event with defensive validation.

        Args:
            connection_id: Connection identifier
            event_data: Event data
        """
        # Input validation
        assert isinstance(connection_id, str), f"connection_id must be str, got {type(connection_id)}"
        assert isinstance(event_data, dict), f"event_data must be dict, got {type(event_data)}"

        try:
            # Validate event data
            event = SlashCommandEvent(type="slash_command", data=event_data)

            # Get bot ID
            bot_id = event_data.get('botId')
            if not bot_id:
                bot_id = self.manager.get_bot_id(connection_id)

            if not bot_id:
                await self.manager.send_error(connection_id, "No bot available")
                return

            command = event_data['command'].strip()

            # Parse command
            parts = command.split()
            cmd = parts[0].lower()

            try:
                # Handle different slash commands
                if cmd == '/up':
                    updated_state = bot_manager.navigate_up(bot_id)
                    await self.manager.send_bot_state(connection_id, bot_id)
                    await self._send_system_message(connection_id, "Moved up in conversation tree")

                elif cmd == '/down':
                    updated_state = bot_manager.navigate_down(bot_id)
                    await self.manager.send_bot_state(connection_id, bot_id)
                    await self._send_system_message(connection_id, "Moved down in conversation tree")

                elif cmd == '/left':
                    updated_state = bot_manager.navigate_left(bot_id)
                    await self.manager.send_bot_state(connection_id, bot_id)
                    await self._send_system_message(connection_id, "Moved left to sibling")

                elif cmd == '/right':
                    updated_state = bot_manager.navigate_right(bot_id)
                    await self.manager.send_bot_state(connection_id, bot_id)
                    await self._send_system_message(connection_id, "Moved right to sibling")

                elif cmd == '/root':
                    updated_state = bot_manager.navigate_to_root(bot_id)
                    await self.manager.send_bot_state(connection_id, bot_id)
                    await self._send_system_message(connection_id, "Moved to root of conversation tree")

                elif cmd == '/help':
                    help_text = """Available Commands:

/help - Show this help
/up - Move up in conversation tree  
/down - Move down in conversation tree
/left - Move to left sibling
/right - Move to right sibling
/root - Move to root of conversation

Navigation: Use commands to move through the conversation tree.
The tree view shows your current position.

Type normally to chat with the bot."""
                    await self._send_system_message(connection_id, help_text)

                else:
                    await self._send_system_message(connection_id, f"Unknown command: {cmd}. Type /help for available commands.")

                logger.info(f"Processed slash command {cmd} for bot {bot_id} from connection {connection_id}")

            except ValueError as e:
                # Command execution failed (e.g., navigation not possible)
                await self._send_system_message(connection_id, str(e))
                logger.warning(f"Slash command {cmd} failed for bot {bot_id}: {e}")

        except Exception as e:
            logger.error(f"Error handling slash_command: {e}")
            await self.manager.send_error(connection_id, f"Command failed: {str(e)}")

    async def _send_system_message(self, connection_id: str, message: str) -> None:
        """
        Send a system message to the client.

        Args:
            connection_id: Connection identifier
            message: System message content
        """
        # Input validation
        assert isinstance(connection_id, str), f"connection_id must be str, got {type(connection_id)}"
        assert isinstance(message, str), f"message must be str, got {type(message)}"
        assert connection_id.strip(), "connection_id cannot be empty"
        assert message.strip(), "message cannot be empty"

        try:
            system_event = {
                'type': 'system_message',
                'data': {
                    'message': message.strip()
                }
            }

            await self.manager.send_personal_message(system_event, connection_id)

        except Exception as e:
            logger.error(f"Failed to send system message: {e}")