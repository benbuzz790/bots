"""
Basic tests for the FastAPI backend implementation.
Tests defensive programming and core functionality.
"""

import pytest
import asyncio
import json
import sys
import os

# Add the current directory to Python path for imports
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from fastapi.testclient import TestClient
from fastapi.websockets import WebSocket

# Import the backend components (absolute imports for testing)
from backend.main import app
from models import MessageRole, create_message, create_conversation_node, create_tool_call
from backend.bot_manager import BotManager

class TestModels:
    """Test the Pydantic models and defensive validation."""

    def test_create_message_valid(self):
        """Test creating a valid message."""
        message = create_message("Hello world", MessageRole.USER)

        assert message.content == "Hello world"
        assert message.role == MessageRole.USER
        assert message.id
        assert message.timestamp
        assert message.tool_calls == []

    def test_create_message_invalid_content(self):
        """Test creating message with invalid content."""
        with pytest.raises(AssertionError, match="content must be str"):
            create_message(123, MessageRole.USER)

        with pytest.raises(AssertionError, match="content cannot be empty"):
            create_message("", MessageRole.USER)

        with pytest.raises(AssertionError, match="content cannot be empty"):
            create_message("   ", MessageRole.USER)

    def test_create_message_invalid_role(self):
        """Test creating message with invalid role."""
        with pytest.raises(AssertionError, match="role must be MessageRole"):
            create_message("Hello", "user")

    def test_create_conversation_node_valid(self):
        """Test creating a valid conversation node."""
        message = create_message("Test", MessageRole.USER)
        node = create_conversation_node(message)

        assert node.message == message
        assert node.parent is None
        assert node.children == []
        assert node.is_current is False
        assert node.id

    def test_create_conversation_node_with_parent(self):
        """Test creating conversation node with parent."""
        message = create_message("Test", MessageRole.USER)
        node = create_conversation_node(message, parent="parent-id", is_current=True)

        assert node.parent == "parent-id"
        assert node.is_current is True

    def test_create_tool_call_valid(self):
        """Test creating a valid tool call."""
        tool_call = create_tool_call("python_edit")

        assert tool_call.name == "python_edit"
        assert tool_call.status.value == "running"
        assert tool_call.result is None
        assert tool_call.error is None
        assert tool_call.id


class TestBotManager:
    """Test the bot manager functionality."""

    def test_create_bot(self):
        """Test creating a bot."""
        bot_id = bot_manager.create_bot("Test Bot")

        assert bot_id
        assert bot_id in bot_manager._bots
        assert bot_id in bot_manager._bot_states

        state = bot_manager.get_bot_state(bot_id)
        assert state.name == "Test Bot"
        assert state.is_connected is True
        assert state.is_thinking is False

        # Cleanup
        bot_manager.delete_bot(bot_id)

    def test_create_bot_invalid_name(self):
        """Test creating bot with invalid name."""
        with pytest.raises(AssertionError, match="name must be str"):
            bot_manager.create_bot(123)

        with pytest.raises(AssertionError, match="name cannot be empty"):
            bot_manager.create_bot("")

    def test_get_bot_nonexistent(self):
        """Test getting non-existent bot."""
        bot = bot_manager.get_bot("nonexistent")
        assert bot is None

        state = bot_manager.get_bot_state("nonexistent")
        assert state is None

    def test_delete_bot(self):
        """Test deleting a bot."""
        bot_id = bot_manager.create_bot("Delete Test")

        # Verify bot exists
        assert bot_manager.get_bot(bot_id) is not None

        # Delete bot
        deleted = bot_manager.delete_bot(bot_id)
        assert deleted is True

        # Verify bot is gone
        assert bot_manager.get_bot(bot_id) is None
        assert bot_manager.get_bot_state(bot_id) is None

        # Try deleting again
        deleted_again = bot_manager.delete_bot(bot_id)
        assert deleted_again is False

    def test_list_bots(self):
        """Test listing bots."""
        # Create some bots
        bot1_id = bot_manager.create_bot("Bot 1")
        bot2_id = bot_manager.create_bot("Bot 2")

        # List bots
        bots = bot_manager.list_bots()

        assert isinstance(bots, dict)
        assert bot1_id in bots
        assert bot2_id in bots
        assert bots[bot1_id] == "Bot 1"
        assert bots[bot2_id] == "Bot 2"

        # Cleanup
        bot_manager.delete_bot(bot1_id)
        bot_manager.delete_bot(bot2_id)

    def test_send_message(self):
        """Test sending a message to a bot."""
        bot_id = bot_manager.create_bot("Message Test Bot")

        # Send a simple message
        response = bot_manager.send_message(bot_id, "Hello bot!")

        assert response.role == MessageRole.ASSISTANT
        assert response.content
        assert isinstance(response.content, str)

        # Check conversation tree was updated
        state = bot_manager.get_bot_state(bot_id)
        assert len(state.conversation_tree) >= 3  # system + user + assistant

        # Cleanup
        bot_manager.delete_bot(bot_id)

    def test_send_message_invalid_inputs(self):
        """Test sending message with invalid inputs."""
        bot_id = bot_manager.create_bot("Invalid Test Bot")

        # Invalid bot_id type
        with pytest.raises(AssertionError, match="bot_id must be str"):
            bot_manager.send_message(123, "Hello")

        # Empty bot_id
        with pytest.raises(AssertionError, match="bot_id cannot be empty"):
            bot_manager.send_message("", "Hello")

        # Invalid content type
        with pytest.raises(AssertionError, match="content must be str"):
            bot_manager.send_message(bot_id, 123)

        # Empty content
        with pytest.raises(AssertionError, match="content cannot be empty"):
            bot_manager.send_message(bot_id, "")

        # Nonexistent bot
        with pytest.raises(ValueError, match="Bot nonexistent not found"):
            bot_manager.send_message("nonexistent", "Hello")

        # Cleanup
        bot_manager.delete_bot(bot_id)


class TestRESTAPI:
    """Test the REST API endpoints."""

    def setup_method(self):
        """Set up test client."""
        self.client = TestClient(app)

    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/api/health")

        assert response.status_code == 200
        data = response.json()

        assert data["status"] == "healthy"
        assert data["message"] == "Bot GUI backend is running"
        assert "bots_count" in data
        assert isinstance(data["bots_count"], int)

    def test_create_bot_endpoint(self):
        """Test bot creation endpoint."""
        response = self.client.post(
            "/api/bots/create",
            json={"name": "API Test Bot"}
        )

        assert response.status_code == 200
        data = response.json()

        assert "bot_id" in data
        assert data["name"] == "API Test Bot"
        assert data["message"] == "Bot created successfully"

        # Cleanup
        bot_id = data["bot_id"]
        bot_manager.delete_bot(bot_id)

    def test_get_bot_endpoint(self):
        """Test get bot endpoint."""
        # Create a bot first
        bot_id = bot_manager.create_bot("Get Test Bot")

        # Get the bot via API
        response = self.client.get(f"/api/bots/{bot_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["bot_id"] == bot_id
        assert data["name"] == "Get Test Bot"
        assert "conversation_tree" in data
        assert "current_node_id" in data
        assert "is_connected" in data
        assert "is_thinking" in data

        # Cleanup
        bot_manager.delete_bot(bot_id)

    def test_get_nonexistent_bot_endpoint(self):
        """Test getting non-existent bot."""
        response = self.client.get("/api/bots/nonexistent")

        assert response.status_code == 404
        data = response.json()
        assert "Bot nonexistent not found" in data["detail"]

    def test_delete_bot_endpoint(self):
        """Test delete bot endpoint."""
        # Create a bot first
        bot_id = bot_manager.create_bot("Delete Test Bot")

        # Delete via API
        response = self.client.delete(f"/api/bots/{bot_id}")

        assert response.status_code == 200
        data = response.json()

        assert data["bot_id"] == bot_id
        assert "deleted successfully" in data["message"]

        # Verify bot is gone
        assert bot_manager.get_bot(bot_id) is None

    def test_list_bots_endpoint(self):
        """Test list bots endpoint."""
        # Create some bots
        bot1_id = bot_manager.create_bot("List Bot 1")
        bot2_id = bot_manager.create_bot("List Bot 2")

        # List via API
        response = self.client.get("/api/bots")

        assert response.status_code == 200
        data = response.json()

        assert "bots" in data
        assert isinstance(data["bots"], dict)
        assert bot1_id in data["bots"]
        assert bot2_id in data["bots"]

        # Cleanup
        bot_manager.delete_bot(bot1_id)
        bot_manager.delete_bot(bot2_id)

    def test_root_endpoint(self):
        """Test root endpoint."""
        response = self.client.get("/")

        assert response.status_code == 200
        data = response.json()

        assert data["message"] == "Bot GUI Backend API"
        assert data["version"] == "1.0.0"
        assert data["docs"] == "/docs"
        assert data["health"] == "/api/health"


def run_tests():
    """Run all tests."""
    print("Running backend tests...")

    # Run pytest
    exit_code = pytest.main([
        __file__,
        "-v",
        "--tb=short"
    ])

    return exit_code == 0


if __name__ == "__main__":
    success = run_tests()
    if success:
        print("✅ All backend tests passed!")
    else:
        print("❌ Some backend tests failed!")
        exit(1)
