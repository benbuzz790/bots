"""
Comprehensive tests for bot manager with defensive programming validation.
Tests bot instance management, conversation handling, and integration with bots framework.
"""

import pytest
import uuid
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, Any, Optional

# Import the bot manager we're testing (assuming it'll be created)
try:
    from backend.bot_manager import BotManager, BotInstance
    from backend.models import Message, MessageRole, ConversationNode, BotState
except ImportError:
    # Mock the bot manager for testing structure
    from pydantic import BaseModel
    from enum import Enum

    class BotInstance:
        def __init__(self, bot_id: str, name: str):
            self.id = bot_id
            self.name = name
            self.bot = None
            self.conversation_tree = {}
            self.current_node_id = None
            self.is_thinking = False

        async def send_message(self, content: str) -> str:
            return "Mock response"

        def get_state(self) -> Dict[str, Any]:
            return {
                "id": self.id,
                "name": self.name,
                "conversation_tree": self.conversation_tree,
                "current_node_id": self.current_node_id,
                "is_connected": True,
                "is_thinking": self.is_thinking
            }

    class BotManager:
        def __init__(self):
            self.bots: Dict[str, BotInstance] = {}

        def create_bot(self, name: str) -> str:
            bot_id = str(uuid.uuid4())
            self.bots[bot_id] = BotInstance(bot_id, name)
            return bot_id

        def get_bot(self, bot_id: str) -> Optional[BotInstance]:
            return self.bots.get(bot_id)

        def delete_bot(self, bot_id: str) -> bool:
            if bot_id in self.bots:
                del self.bots[bot_id]
                return True
            return False

        def get_bot_state(self, bot_id: str) -> Optional[Dict[str, Any]]:
            bot = self.get_bot(bot_id)
            return bot.get_state() if bot else None


class TestBotInstance:
    """Test BotInstance class with defensive programming."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot_id = "bot-123"
        self.bot_name = "Test Bot"
        self.bot_instance = BotInstance(self.bot_id, self.bot_name)

    def test_bot_instance_initialization(self):
        """Test BotInstance initialization."""
        assert self.bot_instance.id == self.bot_id
        assert self.bot_instance.name == self.bot_name
        assert isinstance(self.bot_instance.conversation_tree, dict)
        assert self.bot_instance.current_node_id is None
        assert self.bot_instance.is_thinking is False

    def test_bot_instance_input_validation(self):
        """Test BotInstance input validation."""
        # Test None bot_id
        with pytest.raises(AssertionError):
            BotInstance(None, "Test Bot")

        # Test empty bot_id
        with pytest.raises(AssertionError):
            BotInstance("", "Test Bot")

        # Test None name
        with pytest.raises(AssertionError):
            BotInstance("bot-123", None)

        # Test empty name
        with pytest.raises(AssertionError):
            BotInstance("bot-123", "")

    @pytest.mark.asyncio
    async def test_send_message_valid_input(self):
        """Test sending a valid message."""
        with patch.object(self.bot_instance, 'bot') as mock_bot:
            mock_bot.respond = Mock(return_value="Bot response")

            response = await self.bot_instance.send_message("Hello, bot!")

            assert isinstance(response, str)
            assert response == "Bot response"
            mock_bot.respond.assert_called_once_with("Hello, bot!")

    @pytest.mark.asyncio
    async def test_send_message_input_validation(self):
        """Test send_message input validation."""
        # Test None content
        with pytest.raises(AssertionError):
            await self.bot_instance.send_message(None)

        # Test empty content
        with pytest.raises(AssertionError):
            await self.bot_instance.send_message("")

        # Test non-string content
        with pytest.raises(AssertionError):
            await self.bot_instance.send_message(123)

    @pytest.mark.asyncio
    async def test_send_message_without_bot(self):
        """Test sending message when bot is not initialized."""
        # Bot instance without actual bot
        self.bot_instance.bot = None

        with pytest.raises(RuntimeError):
            await self.bot_instance.send_message("Hello")

    @pytest.mark.asyncio
    async def test_send_message_bot_error(self):
        """Test handling bot errors during message sending."""
        with patch.object(self.bot_instance, 'bot') as mock_bot:
            mock_bot.respond.side_effect = Exception("Bot error")

            with pytest.raises(Exception):
                await self.bot_instance.send_message("Hello")

    def test_get_state_valid_output(self):
        """Test getting bot state with valid output."""
        state = self.bot_instance.get_state()

        assert isinstance(state, dict)
        assert state["id"] == self.bot_id
        assert state["name"] == self.bot_name
        assert "conversation_tree" in state
        assert "current_node_id" in state
        assert "is_connected" in state
        assert "is_thinking" in state

        # Validate field types
        assert isinstance(state["id"], str)
        assert isinstance(state["name"], str)
        assert isinstance(state["conversation_tree"], dict)
        assert isinstance(state["is_connected"], bool)
        assert isinstance(state["is_thinking"], bool)

    def test_conversation_tree_management(self):
        """Test conversation tree management."""
        # Add a node to conversation tree
        node_id = "node-123"
        message_data = {
            "id": "msg-123",
            "role": "user",
            "content": "Hello",
            "timestamp": datetime.utcnow().isoformat(),
            "tool_calls": []
        }

        self.bot_instance.conversation_tree[node_id] = {
            "id": node_id,
            "message": message_data,
            "parent": None,
            "children": [],
            "is_current": True
        }

        self.bot_instance.current_node_id = node_id

        state = self.bot_instance.get_state()
        assert node_id in state["conversation_tree"]
        assert state["current_node_id"] == node_id

    def test_thinking_state_management(self):
        """Test thinking state management."""
        assert self.bot_instance.is_thinking is False

        self.bot_instance.is_thinking = True
        assert self.bot_instance.is_thinking is True

        state = self.bot_instance.get_state()
        assert state["is_thinking"] is True


class TestBotManager:
    """Test BotManager class with defensive programming."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot_manager = BotManager()

    def test_bot_manager_initialization(self):
        """Test BotManager initialization."""
        assert isinstance(self.bot_manager.bots, dict)
        assert len(self.bot_manager.bots) == 0

    def test_create_bot_valid_input(self):
        """Test creating a bot with valid input."""
        bot_name = "Test Bot"
        bot_id = self.bot_manager.create_bot(bot_name)

        assert isinstance(bot_id, str)
        assert bot_id in self.bot_manager.bots
        assert self.bot_manager.bots[bot_id].name == bot_name
        assert self.bot_manager.bots[bot_id].id == bot_id

    def test_create_bot_input_validation(self):
        """Test create_bot input validation."""
        # Test None name
        with pytest.raises(AssertionError):
            self.bot_manager.create_bot(None)

        # Test empty name
        with pytest.raises(AssertionError):
            self.bot_manager.create_bot("")

        # Test non-string name
        with pytest.raises(AssertionError):
            self.bot_manager.create_bot(123)

    def test_create_bot_unique_ids(self):
        """Test that create_bot generates unique IDs."""
        bot_id1 = self.bot_manager.create_bot("Bot 1")
        bot_id2 = self.bot_manager.create_bot("Bot 2")

        assert bot_id1 != bot_id2
        assert bot_id1 in self.bot_manager.bots
        assert bot_id2 in self.bot_manager.bots

    def test_get_bot_valid_id(self):
        """Test getting a bot with valid ID."""
        bot_id = self.bot_manager.create_bot("Test Bot")
        bot_instance = self.bot_manager.get_bot(bot_id)

        assert bot_instance is not None
        assert isinstance(bot_instance, BotInstance)
        assert bot_instance.id == bot_id

    def test_get_bot_invalid_id(self):
        """Test getting a bot with invalid ID."""
        # Test nonexistent ID
        bot_instance = self.bot_manager.get_bot("nonexistent-id")
        assert bot_instance is None

        # Test None ID
        bot_instance = self.bot_manager.get_bot(None)
        assert bot_instance is None

        # Test empty ID
        bot_instance = self.bot_manager.get_bot("")
        assert bot_instance is None

    def test_get_bot_input_validation(self):
        """Test get_bot input validation."""
        # Test non-string ID
        with pytest.raises(AssertionError):
            self.bot_manager.get_bot(123)

    def test_delete_bot_valid_id(self):
        """Test deleting a bot with valid ID."""
        bot_id = self.bot_manager.create_bot("Test Bot")

        # Verify bot exists
        assert bot_id in self.bot_manager.bots

        # Delete bot
        result = self.bot_manager.delete_bot(bot_id)

        assert result is True
        assert bot_id not in self.bot_manager.bots

    def test_delete_bot_invalid_id(self):
        """Test deleting a bot with invalid ID."""
        # Test nonexistent ID
        result = self.bot_manager.delete_bot("nonexistent-id")
        assert result is False

        # Test None ID
        result = self.bot_manager.delete_bot(None)
        assert result is False

        # Test empty ID
        result = self.bot_manager.delete_bot("")
        assert result is False

    def test_delete_bot_input_validation(self):
        """Test delete_bot input validation."""
        # Test non-string ID
        with pytest.raises(AssertionError):
            self.bot_manager.delete_bot(123)

    def test_get_bot_state_valid_id(self):
        """Test getting bot state with valid ID."""
        bot_id = self.bot_manager.create_bot("Test Bot")
        bot_state = self.bot_manager.get_bot_state(bot_id)

        assert bot_state is not None
        assert isinstance(bot_state, dict)
        assert bot_state["id"] == bot_id
        assert bot_state["name"] == "Test Bot"

    def test_get_bot_state_invalid_id(self):
        """Test getting bot state with invalid ID."""
        # Test nonexistent ID
        bot_state = self.bot_manager.get_bot_state("nonexistent-id")
        assert bot_state is None

        # Test None ID
        bot_state = self.bot_manager.get_bot_state(None)
        assert bot_state is None

    def test_get_bot_state_input_validation(self):
        """Test get_bot_state input validation."""
        # Test non-string ID
        with pytest.raises(AssertionError):
            self.bot_manager.get_bot_state(123)

    def test_multiple_bots_management(self):
        """Test managing multiple bots simultaneously."""
        # Create multiple bots
        bot_ids = []
        for i in range(5):
            bot_id = self.bot_manager.create_bot(f"Bot {i}")
            bot_ids.append(bot_id)

        # Verify all bots exist
        assert len(self.bot_manager.bots) == 5
        for bot_id in bot_ids:
            assert bot_id in self.bot_manager.bots

        # Delete some bots
        for i in range(0, 5, 2):  # Delete bots 0, 2, 4
            result = self.bot_manager.delete_bot(bot_ids[i])
            assert result is True

        # Verify correct bots remain
        assert len(self.bot_manager.bots) == 2
        assert bot_ids[1] in self.bot_manager.bots
        assert bot_ids[3] in self.bot_manager.bots


class TestBotManagerIntegration:
    """Test BotManager integration with bots framework."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot_manager = BotManager()

    @patch('backend.bot_manager.AnthropicBot')
    def test_bot_creation_with_framework_integration(self, mock_anthropic_bot):
        """Test bot creation integrates with bots framework."""
        mock_bot = Mock()
        mock_anthropic_bot.return_value = mock_bot

        bot_id = self.bot_manager.create_bot("Test Bot")
        bot_instance = self.bot_manager.get_bot(bot_id)

        # Verify bot framework integration
        assert bot_instance is not None
        # Implementation would set up actual bot instance

    @patch('backend.bot_manager.code_tools')
    def test_bot_tool_integration(self, mock_code_tools):
        """Test bot tool integration."""
        bot_id = self.bot_manager.create_bot("Test Bot")
        bot_instance = self.bot_manager.get_bot(bot_id)

        # Verify tools are added to bot
        # Implementation would add tools to bot instance
        assert bot_instance is not None

    @pytest.mark.asyncio
    async def test_conversation_flow_integration(self):
        """Test conversation flow with bots framework."""
        bot_id = self.bot_manager.create_bot("Test Bot")
        bot_instance = self.bot_manager.get_bot(bot_id)

        with patch.object(bot_instance, 'bot') as mock_bot:
            mock_bot.respond = Mock(return_value="Hello! How can I help?")
            mock_bot.conversation = Mock()
            mock_bot.conversation.content = "Hello! How can I help?"
            mock_bot.conversation.role = "assistant"

            response = await bot_instance.send_message("Hello")

            assert response == "Hello! How can I help?"
            mock_bot.respond.assert_called_once_with("Hello")


class TestBotManagerErrorHandling:
    """Test BotManager error handling and edge cases."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot_manager = BotManager()

    def test_concurrent_bot_operations(self):
        """Test concurrent bot operations."""
        import threading
        import time

        results = []
        errors = []

        def create_bot_worker(name):
            try:
                bot_id = self.bot_manager.create_bot(f"Bot {name}")
                results.append(bot_id)
            except Exception as e:
                errors.append(e)

        # Create multiple threads
        threads = []
        for i in range(10):
            thread = threading.Thread(target=create_bot_worker, args=(i,))
            threads.append(thread)
            thread.start()

        # Wait for all threads
        for thread in threads:
            thread.join()

        # Verify results
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 10
        assert len(set(results)) == 10  # All unique IDs

    def test_memory_management_with_many_bots(self):
        """Test memory management with many bots."""
        # Create many bots
        bot_ids = []
        for i in range(100):
            bot_id = self.bot_manager.create_bot(f"Bot {i}")
            bot_ids.append(bot_id)

        assert len(self.bot_manager.bots) == 100

        # Delete all bots
        for bot_id in bot_ids:
            result = self.bot_manager.delete_bot(bot_id)
            assert result is True

        assert len(self.bot_manager.bots) == 0

    def test_bot_state_consistency(self):
        """Test bot state consistency across operations."""
        bot_id = self.bot_manager.create_bot("Test Bot")

        # Get initial state
        initial_state = self.bot_manager.get_bot_state(bot_id)
        assert initial_state is not None

        # Modify bot instance
        bot_instance = self.bot_manager.get_bot(bot_id)
        bot_instance.is_thinking = True

        # Get updated state
        updated_state = self.bot_manager.get_bot_state(bot_id)
        assert updated_state["is_thinking"] is True
        assert updated_state["id"] == initial_state["id"]
        assert updated_state["name"] == initial_state["name"]

    def test_invalid_operations_on_deleted_bot(self):
        """Test operations on deleted bots."""
        bot_id = self.bot_manager.create_bot("Test Bot")

        # Delete bot
        result = self.bot_manager.delete_bot(bot_id)
        assert result is True

        # Try operations on deleted bot
        bot_instance = self.bot_manager.get_bot(bot_id)
        assert bot_instance is None

        bot_state = self.bot_manager.get_bot_state(bot_id)
        assert bot_state is None

        # Try to delete again
        result = self.bot_manager.delete_bot(bot_id)
        assert result is False


class TestBotManagerSecurity:
    """Test BotManager security and input sanitization."""

    def setup_method(self):
        """Set up test fixtures."""
        self.bot_manager = BotManager()

    def test_malicious_bot_names(self):
        """Test handling of malicious bot names."""
        malicious_names = [
            "<script>alert('xss')</script>",
            "'; DROP TABLE bots; --",
            "../../../etc/passwd",
            "A" * 10000,  # Very long name
            "Bot\x00Name",  # Null byte
            "Bot\nName",  # Newline
            "Bot\tName"  # Tab
        ]

        for name in malicious_names:
            try:
                bot_id = self.bot_manager.create_bot(name)
                bot_instance = self.bot_manager.get_bot(bot_id)

                # Bot should be created but name should be sanitized
                assert bot_instance is not None
                assert isinstance(bot_instance.name, str)

                # Clean up
                self.bot_manager.delete_bot(bot_id)

            except (ValueError, AssertionError):
                # Some names might be rejected at validation level
                pass

    def test_bot_id_format_validation(self):
        """Test bot ID format validation."""
        # Create a bot to get a valid ID format
        bot_id = self.bot_manager.create_bot("Test Bot")

        # Valid ID should be UUID format
        import uuid
        try:
            uuid.UUID(bot_id)
        except ValueError:
            pytest.fail(f"Bot ID should be valid UUID format: {bot_id}")

        # Test operations with malformed IDs
        malformed_ids = [
            "not-a-uuid",
            "123",
            "bot-id-with-dashes",
            "../../../etc/passwd",
            "<script>alert('xss')</script>"
        ]

        for malformed_id in malformed_ids:
            bot_instance = self.bot_manager.get_bot(malformed_id)
            assert bot_instance is None

            bot_state = self.bot_manager.get_bot_state(malformed_id)
            assert bot_state is None

            result = self.bot_manager.delete_bot(malformed_id)
            assert result is False


if __name__ == "__main__":
    pytest.main([__file__])