"""Integration tests for the complete navigation system.

Tests the full workflow from WebSocket events through backend processing
to frontend state updates, ensuring proper synchronization and error handling.
"""

import pytest
import asyncio
import json
from unittest.mock import Mock, AsyncMock, patch
from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket, WebSocketDisconnect

from backend.main import app
from models import BotState, ConversationNode, Message, MessageRole
from websocket_handler import WebSocketHandler
from bot_manager import BotManager


class TestNavigationIntegration:
    """Test complete navigation integration workflow."""

    def setup_method(self):
        """Set up integration test environment."""
        self.client = TestClient(app)
        self.bot_manager = BotManager()
        self.websocket_handler = WebSocketHandler(self.bot_manager)

    @pytest.mark.asyncio
    async def test_complete_navigation_workflow(self):
        """Test complete navigation from WebSocket to bot state update."""
        # Create bot and initial conversation
        bot_id = await self.bot_manager.create_bot("Integration Test Bot")
        initial_state = await self.bot_manager.send_message(bot_id, "Hello")

        # Verify initial state
        assert isinstance(initial_state, BotState)
        assert initial_state.id == bot_id
        assert len(initial_state.conversation_tree) >= 2

        # Mock WebSocket connection
        mock_websocket = AsyncMock(spec=WebSocket)

        # Test navigation via WebSocket
        navigate_event = {
            'type': 'navigate',
            'data': {
                'botId': bot_id,
                'direction': 'up'
            }
        }

        # Handle navigation event
        await self.websocket_handler.handle_message(mock_websocket, navigate_event)

        # Verify WebSocket response was sent
        mock_websocket.send_json.assert_called_once()
        response = mock_websocket.send_json.call_args[0][0]

        # Validate response structure
        assert response['type'] == 'navigation_response'
        assert 'data' in response
        assert 'botState' in response['data']

        bot_state_data = response['data']['botState']
        assert bot_state_data['id'] == bot_id
        assert 'conversationTree' in bot_state_data
        assert 'currentNodeId' in bot_state_data

        # Verify bot state actually changed
        updated_state = BotState(**bot_state_data)
        assert updated_state.current_node_id != initial_state.current_node_id

    @pytest.mark.asyncio
    async def test_websocket_connection_lifecycle(self):
        """Test WebSocket connection establishment and navigation."""
        with self.client.websocket_connect("/ws") as websocket:
            # Create bot via REST API first
            create_response = self.client.post("/api/bots/create", json={"name": "Test Bot"})
            assert create_response.status_code == 200
            bot_data = create_response.json()
            bot_id = bot_data['id']

            # Send initial message via WebSocket
            websocket.send_json({
                'type': 'send_message',
                'data': {
                    'botId': bot_id,
                    'content': 'Hello bot'
                }
            })

            # Receive bot response
            response = websocket.receive_json()
            assert response['type'] == 'bot_response'

            # Now test navigation
            websocket.send_json({
                'type': 'navigate',
                'data': {
                    'botId': bot_id,
                    'direction': 'up'
                }
            })

            # Receive navigation response
            nav_response = websocket.receive_json()
            assert nav_response['type'] in ['navigation_response', 'error']

    @pytest.mark.asyncio
    async def test_concurrent_navigation_safety(self):
        """Test that concurrent navigation operations are handled safely."""
        bot_id = await self.bot_manager.create_bot("Concurrent Test Bot")
        await self.bot_manager.send_message(bot_id, "Initial message")

        # Create multiple mock WebSocket connections
        websockets = [AsyncMock(spec=WebSocket) for _ in range(3)]

        # Define concurrent navigation operations
        async def navigate_operation(ws, direction):
            event = {
                'type': 'navigate',
                'data': {
                    'botId': bot_id,
                    'direction': direction
                }
            }
            try:
                await self.websocket_handler.handle_message(ws, event)
                return True
            except Exception as e:
                return e

        # Execute concurrent operations
        tasks = [
            navigate_operation(websockets[0], 'up'),
            navigate_operation(websockets[1], 'down'),
            navigate_operation(websockets[2], 'left')
        ]

        results = await asyncio.gather(*tasks, return_exceptions=True)

        # Verify all operations completed (some may fail due to navigation constraints)
        assert len(results) == 3
        for result in results:
            assert result is True or isinstance(result, Exception)

        # Verify at least one WebSocket got a response
        response_count = sum(1 for ws in websockets if ws.send_json.called)
        assert response_count >= 1

    @pytest.mark.asyncio
    async def test_slash_command_integration(self):
        """Test slash command processing through the complete pipeline."""
        bot_id = await self.bot_manager.create_bot("Slash Command Test Bot")
        await self.bot_manager.send_message(bot_id, "Setup message")

        mock_websocket = AsyncMock(spec=WebSocket)

        # Test various slash commands
        commands = [
            ('/up', 'up'),
            ('/down', 'down'),
            ('/left', 'left'),
            ('/right', 'right')
        ]

        for command, expected_direction in commands:
            mock_websocket.reset_mock()

            slash_event = {
                'type': 'slash_command',
                'data': {
                    'botId': bot_id,
                    'command': command
                }
            }

            await self.websocket_handler.handle_message(mock_websocket, slash_event)

            # Should have sent a response
            assert mock_websocket.send_json.called

            response = mock_websocket.send_json.call_args[0][0]
            # Response should be either navigation_response or error (if navigation not possible)
            assert response['type'] in ['navigation_response', 'error']

    @pytest.mark.asyncio
    async def test_click_navigation_integration(self):
        """Test click-to-navigate functionality."""
        bot_id = await self.bot_manager.create_bot("Click Navigation Test Bot")
        initial_state = await self.bot_manager.send_message(bot_id, "Create conversation tree")

        # Get a node ID from the conversation tree
        tree = initial_state.conversation_tree
        target_node_id = None
        for node_id, node in tree.items():
            if node_id != initial_state.current_node_id:
                target_node_id = node_id
                break

        assert target_node_id is not None, "Need at least 2 nodes for click navigation test"

        mock_websocket = AsyncMock(spec=WebSocket)

        # Simulate click navigation
        click_event = {
            'type': 'navigate_to_node',
            'data': {
                'botId': bot_id,
                'nodeId': target_node_id
            }
        }

        await self.websocket_handler.handle_message(mock_websocket, click_event)

        # Verify response
        mock_websocket.send_json.assert_called_once()
        response = mock_websocket.send_json.call_args[0][0]

        assert response['type'] == 'navigation_response'
        updated_state = BotState(**response['data']['botState'])
        assert updated_state.current_node_id == target_node_id

    def test_tree_serialization_consistency(self):
        """Test that tree serialization remains consistent across operations."""
        # Create mock bot with complex conversation structure
        mock_bot = Mock()

        # Create branching conversation: root -> [child1, child2] -> grandchild
        root = Mock()
        root.content = "Root message"
        root.role = "user"
        root.parent = None

        child1 = Mock()
        child1.content = "Child 1 response"
        child1.role = "assistant"
        child1.parent = root

        child2 = Mock()
        child2.content = "Child 2 response"
        child2.role = "assistant"
        child2.parent = root

        grandchild = Mock()
        grandchild.content = "Grandchild message"
        grandchild.role = "user"
        grandchild.parent = child1
        grandchild.replies = []

        root.replies = [child1, child2]
        child1.replies = [grandchild]
        child2.replies = []

        mock_bot.conversation = grandchild

        # Serialize tree multiple times and verify consistency
        serializer = self.bot_manager.tree_serializer

        tree1 = serializer.convert_bot_conversation(mock_bot)
        tree2 = serializer.convert_bot_conversation(mock_bot)

        # Verify structural consistency
        assert len(tree1) == len(tree2), "Tree size should be consistent"

        # Verify content consistency
        contents1 = {node.message.content for node in tree1.values()}
        contents2 = {node.message.content for node in tree2.values()}
        assert contents1 == contents2, "Tree content should be consistent"

        # Verify relationship consistency
        for node_id, node in tree1.items():
            corresponding_node = None
            for other_id, other_node in tree2.items():
                if other_node.message.content == node.message.content:
                    corresponding_node = other_node
                    break

            assert corresponding_node is not None, f"Node {node.message.content} not found in second tree"
            assert len(node.children) == len(corresponding_node.children), "Child count should match"

    @pytest.mark.asyncio
    async def test_error_propagation_and_recovery(self):
        """Test error handling and recovery across the integration."""
        bot_id = await self.bot_manager.create_bot("Error Test Bot")

        mock_websocket = AsyncMock(spec=WebSocket)

        # Test navigation error (try to go up from root)
        # First, navigate to root
        root_event = {
            'type': 'navigate',
            'data': {
                'botId': bot_id,
                'direction': 'up'  # This should eventually fail when at root
            }
        }

        # Keep navigating up until we get an error
        max_attempts = 10
        error_received = False

        for _ in range(max_attempts):
            mock_websocket.reset_mock()
            await self.websocket_handler.handle_message(mock_websocket, root_event)

            if mock_websocket.send_json.called:
                response = mock_websocket.send_json.call_args[0][0]
                if response['type'] == 'error':
                    error_received = True
                    assert 'Cannot navigate up' in response['data']['message']
                    break

        assert error_received, "Should have received navigation error"

        # Test recovery - navigation in valid direction should work
        mock_websocket.reset_mock()
        recovery_event = {
            'type': 'navigate',
            'data': {
                'botId': bot_id,
                'direction': 'down'
            }
        }

        await self.websocket_handler.handle_message(mock_websocket, recovery_event)

        # Should get successful response or different error (not the same error)
        assert mock_websocket.send_json.called
        response = mock_websocket.send_json.call_args[0][0]

        if response['type'] == 'error':
            # Different error is acceptable (e.g., "Cannot navigate down from leaf")
            assert 'Cannot navigate up' not in response['data']['message']
        else:
            # Successful navigation is also acceptable
            assert response['type'] == 'navigation_response'

    @pytest.mark.asyncio
    async def test_state_synchronization_across_connections(self):
        """Test that bot state changes are properly synchronized."""
        bot_id = await self.bot_manager.create_bot("Sync Test Bot")
        initial_state = await self.bot_manager.send_message(bot_id, "Initial message")

        # Simulate multiple WebSocket connections to the same bot
        websocket1 = AsyncMock(spec=WebSocket)
        websocket2 = AsyncMock(spec=WebSocket)

        # Connection 1 navigates
        nav_event = {
            'type': 'navigate',
            'data': {
                'botId': bot_id,
                'direction': 'up'
            }
        }

        await self.websocket_handler.handle_message(websocket1, nav_event)

        # Both connections should be able to get current state
        state_request = {
            'type': 'get_bot_state',
            'data': {
                'botId': bot_id
            }
        }

        await self.websocket_handler.handle_message(websocket1, state_request)
        await self.websocket_handler.handle_message(websocket2, state_request)

        # Both should receive the same updated state
        assert websocket1.send_json.call_count >= 2  # Navigation response + state response
        assert websocket2.send_json.call_count >= 1  # State response

        # Get the state responses (last calls)
        state1_response = websocket1.send_json.call_args_list[-1][0][0]
        state2_response = websocket2.send_json.call_args[0][0]

        # Both should have the same current node
        if state1_response['type'] == 'bot_state' and state2_response['type'] == 'bot_state':
            state1_data = state1_response['data']['botState']
            state2_data = state2_response['data']['botState']
            assert state1_data['currentNodeId'] == state2_data['currentNodeId']

    @pytest.mark.asyncio
    async def test_defensive_validation_integration(self):
        """Test defensive validation across the entire integration."""
        mock_websocket = AsyncMock(spec=WebSocket)

        # Test invalid event types
        invalid_events = [
            {'type': 'invalid_type', 'data': {}},
            {'invalid_structure': True},
            {'type': 'navigate', 'data': {'invalid': 'data'}},
            {'type': 'navigate', 'data': {'botId': '', 'direction': 'up'}},
            {'type': 'navigate', 'data': {'botId': 'valid', 'direction': 'invalid'}},
        ]

        for invalid_event in invalid_events:
            mock_websocket.reset_mock()

            # Should handle gracefully and send error response
            await self.websocket_handler.handle_message(mock_websocket, invalid_event)

            # Should have sent an error response
            assert mock_websocket.send_json.called
            response = mock_websocket.send_json.call_args[0][0]
            assert response['type'] == 'error'
            assert 'message' in response['data']

    def test_performance_under_load(self):
        """Test navigation performance with multiple rapid operations."""
        import time

        bot_id = "perf-test-bot"
        mock_bot = Mock()

        # Create simple conversation structure
        root = Mock()
        root.content = "Root"
        root.role = "user"
        root.parent = None
        root.replies = []

        child = Mock()
        child.content = "Child"
        child.role = "assistant"
        child.parent = root
        child.replies = []

        root.replies = [child]
        mock_bot.conversation = child

        self.bot_manager._bots[bot_id] = mock_bot

        # Perform rapid navigation operations
        start_time = time.time()
        operations = 100

        for i in range(operations):
            try:
                # Alternate between up and down navigation
                direction = 'up' if i % 2 == 0 else 'down'
                self.bot_manager.navigator.navigate(bot_id, direction)
            except ValueError:
                # Navigation errors are expected and acceptable
                pass

        end_time = time.time()
        duration = end_time - start_time

        # Should complete within reasonable time (adjust threshold as needed)
        assert duration < 1.0, f"Navigation operations took too long: {duration}s"

        # Operations per second should be reasonable
        ops_per_second = operations / duration
        assert ops_per_second > 50, f"Navigation too slow: {ops_per_second} ops/sec"


if __name__ == "__main__":
    pytest.main([__file__, "-v", "-s"])
