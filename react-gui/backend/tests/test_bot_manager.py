"""Tests for BotManager service with comprehensive defensive validation."""

import pytest
import uuid
import sys
import os
from unittest.mock import Mock, patch, AsyncMock
import asyncio

sys.path.append(os.path.join(os.path.dirname(__file__), '..'))
from bot_manager import BotManager
from models import BotState, MessageRole
from conftest import (
    assert_bot_state_valid,
    VALID_BOT_NAME, VALID_MESSAGE_CONTENT,
    INVALID_EMPTY_STRING, INVALID_WHITESPACE_STRING,
    INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST
)


class TestBotManager:
    """Test BotManager service functionality."""

    @pytest.mark.asyncio
    async def test_create_bot_valid_name(self):
        """Test creating a bot with valid name."""
        manager = BotManager()

        with patch('bot_manager.AnthropicBot') as mock_bot_class:
            mock_bot = Mock()
            mock_bot.add_tools = Mock()
            mock_bot_class.return_value = mock_bot

            bot_id = await manager.create_bot(VALID_BOT_NAME)

            # Validate return value
            assert isinstance(bot_id, str), f"Expected string bot_id, got {type(bot_id)}"
            assert len(bot_id) > 0, "Bot ID cannot be empty"
            assert bot_id in manager._bots, f"Bot {bot_id} not found in manager"
            assert bot_id in manager._conversation_trees, f"Conversation tree for {bot_id} not found"

            # Verify bot was created and configured
            mock_bot_class.assert_called_once()
            mock_bot.add_tools.assert_called_once()

    @pytest.mark.asyncio
    async def test_create_bot_invalid_name_type(self):
        """Test creating a bot with invalid name type."""
        manager = BotManager()

        # Test with non-string types
        invalid_names = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_name in invalid_names:
            with pytest.raises(AssertionError, match="name must be str"):
                await manager.create_bot(invalid_name)

    @pytest.mark.asyncio
    async def test_create_bot_empty_name(self):
        """Test creating a bot with empty name."""
        manager = BotManager()

        # Test with empty and whitespace names
        invalid_names = [INVALID_EMPTY_STRING, INVALID_WHITESPACE_STRING]

        for invalid_name in invalid_names:
            with pytest.raises(AssertionError, match="name cannot be empty"):
                await manager.create_bot(invalid_name)

    @pytest.mark.asyncio
    async def test_send_message_valid_inputs(self, mock_bot):
        """Test sending a message with valid inputs."""
        manager = BotManager()
        bot_id = str(uuid.uuid4())
        manager._bots[bot_id] = mock_bot
        manager._conversation_trees[bot_id] = {}

        # Mock the conversation conversion methods
        with patch.object(manager, '_convert_bot_conversation') as mock_convert:
            with patch.object(manager, '_find_current_node') as mock_find_current:
                mock_convert.return_value = {}
                mock_find_current.return_value = str(uuid.uuid4())

                bot_state = await manager.send_message(bot_id, VALID_MESSAGE_CONTENT)

                # Validate return value
                assert_bot_state_valid(bot_state)
                assert bot_state.id == bot_id
                assert bot_state.is_connected is True
                assert bot_state.is_thinking is False

                # Verify bot.respond was called
                mock_bot.respond.assert_called_once_with(VALID_MESSAGE_CONTENT)

    @pytest.mark.asyncio
    async def test_send_message_invalid_bot_id_type(self):
        """Test sending a message with invalid bot_id type."""
        manager = BotManager()

        invalid_bot_ids = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_bot_id in invalid_bot_ids:
            with pytest.raises(AssertionError, match="bot_id must be str"):
                await manager.send_message(invalid_bot_id, VALID_MESSAGE_CONTENT)

    @pytest.mark.asyncio
    async def test_send_message_invalid_content_type(self):
        """Test sending a message with invalid content type."""
        manager = BotManager()
        bot_id = str(uuid.uuid4())

        invalid_contents = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_content in invalid_contents:
            with pytest.raises(AssertionError, match="content must be str"):
                await manager.send_message(bot_id, invalid_content)

    @pytest.mark.asyncio
    async def test_send_message_bot_not_found(self):
        """Test sending a message to non-existent bot."""
        manager = BotManager()
        non_existent_bot_id = str(uuid.uuid4())

        with pytest.raises(AssertionError, match=f"Bot {non_existent_bot_id} not found"):
            await manager.send_message(non_existent_bot_id, VALID_MESSAGE_CONTENT)

    @pytest.mark.asyncio
    async def test_send_message_empty_content(self, mock_bot):
        """Test sending a message with empty content."""
        manager = BotManager()
        bot_id = str(uuid.uuid4())
        manager._bots[bot_id] = mock_bot

        invalid_contents = [INVALID_EMPTY_STRING, INVALID_WHITESPACE_STRING]

        for invalid_content in invalid_contents:
            with pytest.raises(AssertionError, match="content cannot be empty"):
                await manager.send_message(bot_id, invalid_content)

    @pytest.mark.asyncio
    async def test_get_bot_valid_id(self, mock_bot):
        """Test getting a bot with valid ID."""
        manager = BotManager()
        bot_id = str(uuid.uuid4())
        manager._bots[bot_id] = mock_bot

        retrieved_bot = await manager.get_bot(bot_id)

        assert retrieved_bot is mock_bot, "Retrieved bot should match stored bot"

    @pytest.mark.asyncio
    async def test_get_bot_invalid_id_type(self):
        """Test getting a bot with invalid ID type."""
        manager = BotManager()

        invalid_bot_ids = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_bot_id in invalid_bot_ids:
            with pytest.raises(AssertionError, match="bot_id must be string"):
                await manager.get_bot(invalid_bot_id)

    @pytest.mark.asyncio
    async def test_get_bot_empty_id(self):
        """Test getting a bot with empty ID."""
        manager = BotManager()

        with pytest.raises(AssertionError, match="bot_id cannot be empty"):
            await manager.get_bot(INVALID_EMPTY_STRING)

    @pytest.mark.asyncio
    async def test_get_bot_not_found(self):
        """Test getting a non-existent bot."""
        manager = BotManager()
        non_existent_bot_id = str(uuid.uuid4())

        retrieved_bot = await manager.get_bot(non_existent_bot_id)

        assert retrieved_bot is None, "Non-existent bot should return None"

    @pytest.mark.asyncio
    async def test_delete_bot_valid_id(self, mock_bot):
        """Test deleting a bot with valid ID."""
        manager = BotManager()
        bot_id = str(uuid.uuid4())
        manager._bots[bot_id] = mock_bot
        manager._conversation_trees[bot_id] = {}

        success = await manager.delete_bot(bot_id)

        assert success is True, "Delete should return True for existing bot"
        assert bot_id not in manager._bots, "Bot should be removed from _bots"
        assert bot_id not in manager._conversation_trees, "Conversation tree should be removed"

    @pytest.mark.asyncio
    async def test_delete_bot_invalid_id_type(self):
        """Test deleting a bot with invalid ID type."""
        manager = BotManager()

        invalid_bot_ids = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_bot_id in invalid_bot_ids:
            with pytest.raises(AssertionError, match="bot_id must be string"):
                await manager.delete_bot(invalid_bot_id)

    @pytest.mark.asyncio
    async def test_delete_bot_empty_id(self):
        """Test deleting a bot with empty ID."""
        manager = BotManager()

        with pytest.raises(AssertionError, match="bot_id cannot be empty"):
            await manager.delete_bot(INVALID_EMPTY_STRING)

    @pytest.mark.asyncio
    async def test_delete_bot_not_found(self):
        """Test deleting a non-existent bot."""
        manager = BotManager()
        non_existent_bot_id = str(uuid.uuid4())

        success = await manager.delete_bot(non_existent_bot_id)

        assert success is False, "Delete should return False for non-existent bot"

    def test_convert_bot_conversation_valid_bot(self, mock_bot):
        """Test converting bot conversation to our format."""
        manager = BotManager()

        # Set up mock conversation structure
        mock_node = Mock()
        mock_node.content = "Test message"
        mock_node.role = "user"
        mock_node.parent = None
        mock_node.replies = []
        mock_node.tool_calls = []
        mock_bot.conversation = mock_node

        with patch.object(manager, '_convert_node_recursive') as mock_convert_recursive:
            mock_convert_recursive.return_value = ({}, str(uuid.uuid4()))

            result = manager._convert_bot_conversation(mock_bot)

            assert isinstance(result, dict), f"Expected dict, got {type(result)}"
            mock_convert_recursive.assert_called_once()

    def test_convert_bot_conversation_invalid_bot_type(self):
        """Test converting bot conversation with invalid bot type."""
        manager = BotManager()

        invalid_bots = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_bot in invalid_bots:
            with pytest.raises(AssertionError, match="bot must have conversation attribute"):
                manager._convert_bot_conversation(invalid_bot)

    def test_find_current_node_valid_bot(self, mock_bot):
        """Test finding current node in bot conversation."""
        manager = BotManager()

        # Mock bot conversation
        mock_bot.conversation = Mock()

        with patch.object(manager, '_find_current_node_recursive') as mock_find_recursive:
            expected_node_id = str(uuid.uuid4())
            mock_find_recursive.return_value = expected_node_id

            result = manager._find_current_node(mock_bot)

            assert result == expected_node_id, f"Expected {expected_node_id}, got {result}"
            mock_find_recursive.assert_called_once_with(mock_bot.conversation)

    def test_find_current_node_invalid_bot_type(self):
        """Test finding current node with invalid bot type."""
        manager = BotManager()

        invalid_bots = [INVALID_NON_STRING, INVALID_NONE, INVALID_DICT, INVALID_LIST]

        for invalid_bot in invalid_bots:
            with pytest.raises(AssertionError, match="bot must have conversation attribute"):
                manager._find_current_node(invalid_bot)

    @pytest.mark.asyncio
    async def test_list_bots_empty(self):
        """Test listing bots when none exist."""
        manager = BotManager()

        bots = await manager.list_bots()

        assert isinstance(bots, list), f"Expected list, got {type(bots)}"
        assert len(bots) == 0, "Empty manager should return empty list"

    @pytest.mark.asyncio
    async def test_list_bots_with_bots(self, mock_bot):
        """Test listing bots when some exist."""
        manager = BotManager()
        bot_id1 = str(uuid.uuid4())
        bot_id2 = str(uuid.uuid4())
        manager._bots[bot_id1] = mock_bot
        manager._bots[bot_id2] = mock_bot

        bots = await manager.list_bots()

        assert isinstance(bots, list), f"Expected list, got {type(bots)}"
        assert len(bots) == 2, f"Expected 2 bots, got {len(bots)}"
        assert bot_id1 in bots, f"Bot {bot_id1} should be in list"
        assert bot_id2 in bots, f"Bot {bot_id2} should be in list"

    @pytest.mark.asyncio
    async def test_concurrent_bot_operations(self, mock_bot):
        """Test concurrent bot operations for thread safety."""
        manager = BotManager()

        # Create multiple bots concurrently
        async def create_bot_task(name):
            return await manager.create_bot(f"{name}")

        tasks = [create_bot_task(f"Bot {i}") for i in range(5)]
        bot_ids = await asyncio.gather(*tasks)

        # Verify all bots were created
        assert len(bot_ids) == 5, f"Expected 5 bot IDs, got {len(bot_ids)}"
        assert len(set(bot_ids)) == 5, "All bot IDs should be unique"

        for bot_id in bot_ids:
            assert bot_id in manager._bots, f"Bot {bot_id} should exist"
            assert bot_id in manager._conversation_trees, f"Conversation tree for {bot_id} should exist"

    @pytest.mark.asyncio
    async def test_bot_manager_state_consistency(self, mock_bot):
        """Test that BotManager maintains consistent state."""
        manager = BotManager()

        # Create a bot
        bot_id = await manager.create_bot(VALID_BOT_NAME)

        # Verify initial state
        assert len(manager._bots) == 1, "Should have 1 bot"
        assert len(manager._conversation_trees) == 1, "Should have 1 conversation tree"

        # Delete the bot
        success = await manager.delete_bot(bot_id)
        assert success is True, "Delete should succeed"

        # Verify final state
        assert len(manager._bots) == 0, "Should have 0 bots after deletion"
        assert len(manager._conversation_trees) == 0, "Should have 0 conversation trees after deletion"

    @pytest.mark.asyncio
    async def test_error_handling_during_bot_creation(self):
        """Test error handling when bot creation fails."""
        manager = BotManager()

        with patch('bot_manager.AnthropicBot') as mock_bot_class:
            # Make bot creation fail
            mock_bot_class.side_effect = Exception("Bot creation failed")

            with pytest.raises(Exception, match="Bot creation failed"):
                await manager.create_bot(VALID_BOT_NAME)

            # Verify no partial state was left behind
            assert len(manager._bots) == 0, "No bots should exist after failed creation"
            assert len(manager._conversation_trees) == 0, "No conversation trees should exist after failed creation"
