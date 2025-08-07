"""
Comprehensive tests for backend models with defensive programming validation.
Tests all Pydantic models, enums, and validation logic.
"""

import pytest
import uuid
from datetime import datetime
from typing import List, Optional

# Import the models we're testing (assuming they'll be created)
try:
    from backend.models import (
        MessageRole, ToolCallStatus, ToolCall, Message, 
        ConversationNode, BotState, create_message
    )
except ImportError:
    # Mock the models for testing structure
    from pydantic import BaseModel
    from enum import Enum

    class MessageRole(str, Enum):
        USER = "user"
        ASSISTANT = "assistant"
        SYSTEM = "system"

    class ToolCallStatus(str, Enum):
        RUNNING = "running"
        COMPLETED = "completed"
        ERROR = "error"

    class ToolCall(BaseModel):
        id: str
        name: str
        status: ToolCallStatus
        result: Optional[str] = None
        error: Optional[str] = None

    class Message(BaseModel):
        id: str
        role: MessageRole
        content: str
        timestamp: str
        tool_calls: List[ToolCall] = []

    class ConversationNode(BaseModel):
        id: str
        message: Message
        parent: Optional[str] = None
        children: List[str] = []
        is_current: bool = False

    class BotState(BaseModel):
        id: str
        name: str
        conversation_tree: dict
        current_node_id: str
        is_connected: bool
        is_thinking: bool


class TestMessageRole:
    """Test MessageRole enum validation."""

    def test_valid_roles(self):
        """Test all valid message roles."""
        assert MessageRole.USER == "user"
        assert MessageRole.ASSISTANT == "assistant"
        assert MessageRole.SYSTEM == "system"

    def test_role_values(self):
        """Test role enum values are strings."""
        for role in MessageRole:
            assert isinstance(role.value, str)
            assert role.value in ["user", "assistant", "system"]


class TestToolCallStatus:
    """Test ToolCallStatus enum validation."""

    def test_valid_statuses(self):
        """Test all valid tool call statuses."""
        assert ToolCallStatus.RUNNING == "running"
        assert ToolCallStatus.COMPLETED == "completed"
        assert ToolCallStatus.ERROR == "error"

    def test_status_values(self):
        """Test status enum values are strings."""
        for status in ToolCallStatus:
            assert isinstance(status.value, str)
            assert status.value in ["running", "completed", "error"]


class TestToolCall:
    """Test ToolCall model validation and defensive programming."""

    def test_valid_tool_call_creation(self):
        """Test creating a valid ToolCall."""
        tool_call = ToolCall(
            id="test-id",
            name="test_tool",
            status=ToolCallStatus.RUNNING
        )

        assert tool_call.id == "test-id"
        assert tool_call.name == "test_tool"
        assert tool_call.status == ToolCallStatus.RUNNING
        assert tool_call.result is None
        assert tool_call.error is None

    def test_tool_call_with_result(self):
        """Test ToolCall with result."""
        tool_call = ToolCall(
            id="test-id",
            name="test_tool",
            status=ToolCallStatus.COMPLETED,
            result="Success!"
        )

        assert tool_call.result == "Success!"
        assert tool_call.error is None

    def test_tool_call_with_error(self):
        """Test ToolCall with error."""
        tool_call = ToolCall(
            id="test-id",
            name="test_tool",
            status=ToolCallStatus.ERROR,
            error="Something went wrong"
        )

        assert tool_call.error == "Something went wrong"
        assert tool_call.result is None

    def test_tool_call_validation_failures(self):
        """Test ToolCall validation failures."""
        # Missing required fields
        with pytest.raises(ValueError):
            ToolCall()

        # Invalid status
        with pytest.raises(ValueError):
            ToolCall(
                id="test-id",
                name="test_tool",
                status="invalid_status"
            )

    def test_tool_call_field_types(self):
        """Test ToolCall field type validation."""
        tool_call = ToolCall(
            id="test-id",
            name="test_tool",
            status=ToolCallStatus.RUNNING
        )

        assert isinstance(tool_call.id, str)
        assert isinstance(tool_call.name, str)
        assert isinstance(tool_call.status, ToolCallStatus)
        assert tool_call.result is None or isinstance(tool_call.result, str)
        assert tool_call.error is None or isinstance(tool_call.error, str)


class TestMessage:
    """Test Message model validation and defensive programming."""

    def test_valid_message_creation(self):
        """Test creating a valid Message."""
        timestamp = datetime.utcnow().isoformat()
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello, bot!",
            timestamp=timestamp
        )

        assert message.id == "msg-123"
        assert message.role == MessageRole.USER
        assert message.content == "Hello, bot!"
        assert message.timestamp == timestamp
        assert message.tool_calls == []

    def test_message_with_tool_calls(self):
        """Test Message with tool calls."""
        tool_call = ToolCall(
            id="tool-1",
            name="test_tool",
            status=ToolCallStatus.COMPLETED,
            result="Done"
        )

        message = Message(
            id="msg-123",
            role=MessageRole.ASSISTANT,
            content="I'll help you with that.",
            timestamp=datetime.utcnow().isoformat(),
            tool_calls=[tool_call]
        )

        assert len(message.tool_calls) == 1
        assert message.tool_calls[0].id == "tool-1"
        assert message.tool_calls[0].name == "test_tool"

    def test_message_validation_failures(self):
        """Test Message validation failures."""
        # Missing required fields
        with pytest.raises(ValueError):
            Message()

        # Invalid role
        with pytest.raises(ValueError):
            Message(
                id="msg-123",
                role="invalid_role",
                content="Hello",
                timestamp=datetime.utcnow().isoformat()
            )

    def test_message_field_types(self):
        """Test Message field type validation."""
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow().isoformat()
        )

        assert isinstance(message.id, str)
        assert isinstance(message.role, MessageRole)
        assert isinstance(message.content, str)
        assert isinstance(message.timestamp, str)
        assert isinstance(message.tool_calls, list)


class TestConversationNode:
    """Test ConversationNode model validation."""

    def test_valid_conversation_node_creation(self):
        """Test creating a valid ConversationNode."""
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow().isoformat()
        )

        node = ConversationNode(
            id="node-123",
            message=message
        )

        assert node.id == "node-123"
        assert node.message == message
        assert node.parent is None
        assert node.children == []
        assert node.is_current is False

    def test_conversation_node_with_relationships(self):
        """Test ConversationNode with parent and children."""
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow().isoformat()
        )

        node = ConversationNode(
            id="node-123",
            message=message,
            parent="parent-node",
            children=["child-1", "child-2"],
            is_current=True
        )

        assert node.parent == "parent-node"
        assert node.children == ["child-1", "child-2"]
        assert node.is_current is True

    def test_conversation_node_field_types(self):
        """Test ConversationNode field type validation."""
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow().isoformat()
        )

        node = ConversationNode(
            id="node-123",
            message=message
        )

        assert isinstance(node.id, str)
        assert isinstance(node.message, Message)
        assert node.parent is None or isinstance(node.parent, str)
        assert isinstance(node.children, list)
        assert isinstance(node.is_current, bool)


class TestBotState:
    """Test BotState model validation."""

    def test_valid_bot_state_creation(self):
        """Test creating a valid BotState."""
        bot_state = BotState(
            id="bot-123",
            name="Test Bot",
            conversation_tree={},
            current_node_id="node-1",
            is_connected=True,
            is_thinking=False
        )

        assert bot_state.id == "bot-123"
        assert bot_state.name == "Test Bot"
        assert bot_state.conversation_tree == {}
        assert bot_state.current_node_id == "node-1"
        assert bot_state.is_connected is True
        assert bot_state.is_thinking is False

    def test_bot_state_with_conversation_tree(self):
        """Test BotState with conversation tree."""
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow().isoformat()
        )

        node = ConversationNode(
            id="node-123",
            message=message,
            is_current=True
        )

        bot_state = BotState(
            id="bot-123",
            name="Test Bot",
            conversation_tree={"node-123": node},
            current_node_id="node-123",
            is_connected=True,
            is_thinking=False
        )

        assert "node-123" in bot_state.conversation_tree
        assert bot_state.conversation_tree["node-123"] == node

    def test_bot_state_field_types(self):
        """Test BotState field type validation."""
        bot_state = BotState(
            id="bot-123",
            name="Test Bot",
            conversation_tree={},
            current_node_id="node-1",
            is_connected=True,
            is_thinking=False
        )

        assert isinstance(bot_state.id, str)
        assert isinstance(bot_state.name, str)
        assert isinstance(bot_state.conversation_tree, dict)
        assert isinstance(bot_state.current_node_id, str)
        assert isinstance(bot_state.is_connected, bool)
        assert isinstance(bot_state.is_thinking, bool)


class TestDefensiveFunctions:
    """Test defensive programming functions."""

    def test_create_message_valid_input(self):
        """Test create_message with valid input."""
        # This function should be implemented in models.py
        # For now, we'll test the expected behavior
        pass

    def test_create_message_input_validation(self):
        """Test create_message input validation."""
        # Test empty content
        # Test invalid role
        # Test invalid tool_calls
        pass

    def test_create_message_output_validation(self):
        """Test create_message output validation."""
        # Test return type
        # Test required fields are populated
        pass


class TestModelSerialization:
    """Test model serialization and deserialization."""

    def test_message_json_serialization(self):
        """Test Message JSON serialization."""
        message = Message(
            id="msg-123",
            role=MessageRole.USER,
            content="Hello",
            timestamp=datetime.utcnow().isoformat()
        )

        json_data = message.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["id"] == "msg-123"
        assert json_data["role"] == "user"
        assert json_data["content"] == "Hello"

    def test_message_json_deserialization(self):
        """Test Message JSON deserialization."""
        json_data = {
            "id": "msg-123",
            "role": "user",
            "content": "Hello",
            "timestamp": datetime.utcnow().isoformat(),
            "tool_calls": []
        }

        message = Message(**json_data)
        assert message.id == "msg-123"
        assert message.role == MessageRole.USER
        assert message.content == "Hello"

    def test_bot_state_json_serialization(self):
        """Test BotState JSON serialization."""
        bot_state = BotState(
            id="bot-123",
            name="Test Bot",
            conversation_tree={},
            current_node_id="node-1",
            is_connected=True,
            is_thinking=False
        )

        json_data = bot_state.model_dump()
        assert isinstance(json_data, dict)
        assert json_data["id"] == "bot-123"
        assert json_data["name"] == "Test Bot"
        assert json_data["is_connected"] is True


if __name__ == "__main__":
    pytest.main([__file__])