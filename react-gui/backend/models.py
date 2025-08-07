"""
Pydantic models for the React GUI backend.
Implements the data structures defined in architecture.md with defensive validation.
"""

from __future__ import annotations

import uuid
from datetime import datetime
from enum import Enum
from typing import Dict, List, Optional, Any
from pydantic import BaseModel, Field, field_validator


class MessageRole(str, Enum):
    """Message role enumeration."""
    USER = "user"
    ASSISTANT = "assistant"
    SYSTEM = "system"


class ToolCallStatus(str, Enum):
    """Tool call status enumeration."""
    RUNNING = "running"
    COMPLETED = "completed"
    ERROR = "error"


class ToolCall(BaseModel):
    """Represents a tool call with status and results."""
    id: str = Field(..., description="Unique identifier for the tool call")
    name: str = Field(..., description="Name of the tool being called")
    status: ToolCallStatus = Field(..., description="Current status of the tool call")
    result: Optional[str] = Field(None, description="Result of the tool call if completed")
    error: Optional[str] = Field(None, description="Error message if tool call failed")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate tool call ID is not empty."""
        assert isinstance(v, str), f"id must be str, got {type(v)}"
        assert v.strip(), "id cannot be empty"
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate tool name is not empty."""
        assert isinstance(v, str), f"name must be str, got {type(v)}"
        assert v.strip(), "name cannot be empty"
        return v.strip()

    @field_validator('result')
    @classmethod
    def validate_result(cls, v):
        """Validate result if provided."""
        if v is not None:
            assert isinstance(v, str), f"result must be str, got {type(v)}"
        return v

    @field_validator('error')
    @classmethod
    def validate_error(cls, v):
        """Validate error if provided."""
        if v is not None:
            assert isinstance(v, str), f"error must be str, got {type(v)}"
        return v


class Message(BaseModel):
    """Represents a chat message."""
    id: str = Field(..., description="Unique identifier for the message")
    role: MessageRole = Field(..., description="Role of the message sender")
    content: str = Field(..., description="Content of the message")
    timestamp: str = Field(..., description="ISO timestamp when message was created")
    tool_calls: List[ToolCall] = Field(default_factory=list, description="Tool calls associated with this message")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate message ID is not empty."""
        assert isinstance(v, str), f"id must be str, got {type(v)}"
        assert v.strip(), "id cannot be empty"
        return v.strip()

    @field_validator('content')
    @classmethod
    def validate_content(cls, v):
        """Validate message content is not empty."""
        assert isinstance(v, str), f"content must be str, got {type(v)}"
        assert v.strip(), "content cannot be empty"
        return v.strip()

    @field_validator('timestamp')
    @classmethod
    def validate_timestamp(cls, v):
        """Validate timestamp is valid ISO format."""
        assert isinstance(v, str), f"timestamp must be str, got {type(v)}"
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
        except ValueError as e:
            raise ValueError(f"Invalid timestamp format: {e}")
        return v

    @field_validator('tool_calls')
    @classmethod
    def validate_tool_calls(cls, v):
        """Validate tool calls list."""
        assert isinstance(v, list), f"tool_calls must be list, got {type(v)}"
        for call in v:
            assert isinstance(call, ToolCall), f"tool_call must be ToolCall instance, got {type(call)}"
        return v


class ConversationNode(BaseModel):
    """Represents a node in the conversation tree."""
    id: str = Field(..., description="Unique identifier for the conversation node")
    message: Message = Field(..., description="Message associated with this node")
    parent: Optional[str] = Field(None, description="ID of parent node")
    children: List[str] = Field(default_factory=list, description="IDs of child nodes")
    is_current: bool = Field(False, description="Whether this is the current node")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate conversation node ID is not empty."""
        assert isinstance(v, str), f"id must be str, got {type(v)}"
        assert v.strip(), "id cannot be empty"
        return v.strip()

    @field_validator('message')
    @classmethod
    def validate_message(cls, v):
        """Validate message is a Message instance."""
        assert isinstance(v, Message), f"message must be Message instance, got {type(v)}"
        return v

    @field_validator('parent')
    @classmethod
    def validate_parent(cls, v):
        """Validate parent if provided."""
        if v is not None:
            assert isinstance(v, str), f"parent must be str, got {type(v)}"
            assert v.strip(), "parent cannot be empty"
            return v.strip()
        return v

    @field_validator('children')
    @classmethod
    def validate_children(cls, v):
        """Validate children list."""
        assert isinstance(v, list), f"children must be list, got {type(v)}"
        for child_id in v:
            assert isinstance(child_id, str), f"child_id must be str, got {type(child_id)}"
            assert child_id.strip(), "child_id cannot be empty"
        return v

    @field_validator('is_current')
    @classmethod
    def validate_is_current(cls, v):
        """Validate is_current is boolean."""
        assert isinstance(v, bool), f"is_current must be bool, got {type(v)}"
        return v


class BotState(BaseModel):
    """Represents the current state of a bot."""
    id: str = Field(..., description="Unique identifier for the bot")
    name: str = Field(..., description="Name of the bot")
    conversation_tree: Dict[str, ConversationNode] = Field(default_factory=dict, description="Conversation tree", alias="conversationTree")
    current_node_id: Optional[str] = Field(None, description="ID of current conversation node", alias="currentNodeId")
    is_connected: bool = Field(False, description="Whether bot is connected", alias="isConnected")
    is_thinking: bool = Field(False, description="Whether bot is currently thinking", alias="isThinking")
    react_flow_data: Optional[Dict[str, Any]] = Field(None, description="React Flow visualization data", alias="reactFlowData")

    @field_validator('id')
    @classmethod
    def validate_id(cls, v):
        """Validate bot ID is not empty."""
        assert isinstance(v, str), f"id must be str, got {type(v)}"
        assert v.strip(), "id cannot be empty"
        return v.strip()

    @field_validator('name')
    @classmethod
    def validate_name(cls, v):
        """Validate bot name is not empty."""
        assert isinstance(v, str), f"name must be str, got {type(v)}"
        assert v.strip(), "name cannot be empty"
        return v.strip()

    @field_validator('conversation_tree')
    @classmethod
    def validate_conversation_tree(cls, v):
        """Validate conversation tree."""
        assert isinstance(v, dict), f"conversation_tree must be dict, got {type(v)}"
        for node_id, node in v.items():
            assert isinstance(node_id, str), f"node_id must be str, got {type(node_id)}"
            assert isinstance(node, ConversationNode), f"node must be ConversationNode, got {type(node)}"
        return v

    @field_validator('current_node_id')
    @classmethod
    def validate_current_node_id(cls, v):
        """Validate current node ID if provided."""
        if v is not None:
            assert isinstance(v, str), f"current_node_id must be str, got {type(v)}"
            # Allow empty string for current_node_id
            return v
        return v

    @field_validator('is_connected')
    @classmethod
    def validate_is_connected(cls, v):
        """Validate is_connected is boolean."""
        assert isinstance(v, bool), f"is_connected must be bool, got {type(v)}"
        return v

    @field_validator('is_thinking')
    @classmethod
    def validate_is_thinking(cls, v):
        """Validate is_thinking is boolean."""
        assert isinstance(v, bool), f"is_thinking must be bool, got {type(v)}"
        return v


# WebSocket Event Models
class WebSocketEvent(BaseModel):
    """Base class for WebSocket events."""
    type: str = Field(..., description="Type of the event")
    data: Dict[str, Any] = Field(..., description="Event data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate event data is a dictionary."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        return v


class SendMessageEvent(WebSocketEvent):
    """Event for sending a message to a bot."""
    type: str = Field(default="send_message", description="Event type")
    data: Dict[str, Any] = Field(..., description="Message data containing botId and content")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate send message event data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botId' in v, "data must have 'botId' field"
        assert 'content' in v, "data must have 'content' field"
        assert isinstance(v['botId'], str), "botId must be str"
        assert isinstance(v['content'], str), "content must be str"
        assert v['botId'].strip(), "botId cannot be empty"
        assert v['content'].strip(), "content cannot be empty"
        return v


class GetBotStateEvent(WebSocketEvent):
    """Event for getting bot state."""
    type: str = Field(default="get_bot_state", description="Event type")
    data: Dict[str, Any] = Field(..., description="Bot state request data containing botId")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate get bot state event data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botId' in v, "data must have 'botId' field"
        assert isinstance(v['botId'], str), "botId must be str"
        assert v['botId'].strip(), "botId cannot be empty"
        return v


class BotStateResponse(WebSocketEvent):
    """Response containing bot state."""
    type: str = Field(default="bot_state", description="Response type")
    data: Dict[str, Any] = Field(..., description="Bot state data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate bot state response data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botState' in v, "data must have 'botState' field"
        return v


class ErrorResponse(WebSocketEvent):
    """Error response."""
    type: str = Field(default="error", description="Response type")
    data: Dict[str, Any] = Field(..., description="Error data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate error response data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'message' in v, "data must have 'message' field"
        assert isinstance(v['message'], str), "message must be str"
        return v


class ThinkingResponse(WebSocketEvent):
    """Thinking status response."""
    type: str = Field(default="thinking", description="Response type")
    data: Dict[str, Any] = Field(..., description="Thinking status data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate thinking response data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botId' in v, "data must have 'botId' field"
        assert 'isThinking' in v, "data must have 'isThinking' field"
        assert isinstance(v['botId'], str), "botId must be str"
        assert isinstance(v['isThinking'], bool), "isThinking must be bool"
        return v


class MessageResponse(WebSocketEvent):
    """Message response from bot."""
    type: str = Field(default="message", description="Response type")
    data: Dict[str, Any] = Field(..., description="Message response data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate message response data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botId' in v, "data must have 'botId' field"
        assert 'message' in v, "data must have 'message' field"
        assert isinstance(v['botId'], str), "botId must be str"
        return v
class BotResponseEvent(WebSocketEvent):
    """Event for bot response."""
    type: str = Field(default="bot_response", description="Event type")
    data: Dict[str, Any] = Field(..., description="Bot response data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate bot response event data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botId' in v, "data must have 'botId' field"
        assert 'message' in v, "data must have 'message' field"
        assert 'conversationTree' in v, "data must have 'conversationTree' field"
        assert 'currentNodeId' in v, "data must have 'currentNodeId' field"
        assert isinstance(v['botId'], str), "botId must be str"
        return v


class ToolUpdateEvent(WebSocketEvent):
    """Event for tool execution updates."""
    type: str = Field(default="tool_update", description="Event type")
    data: Dict[str, Any] = Field(..., description="Tool update data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate tool update event data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'botId' in v, "data must have 'botId' field"
        assert 'toolCall' in v, "data must have 'toolCall' field"
        assert isinstance(v['botId'], str), "botId must be str"
        return v


class ErrorEvent(WebSocketEvent):
    """Event for errors."""
    type: str = Field(default="error", description="Event type")
    data: Dict[str, Any] = Field(..., description="Error data")

    @field_validator('data')
    @classmethod
    def validate_data(cls, v):
        """Validate error event data."""
        assert isinstance(v, dict), f"data must be dict, got {type(v)}"
        assert 'message' in v, "data must have 'message' field"
        assert isinstance(v['message'], str), "message must be str"
        return v


# Helper functions for creating model instances
def create_message(content: str, role: MessageRole = MessageRole.USER, 
                  tool_calls: List[ToolCall] = None) -> Message:
    """Create a message with automatic ID and timestamp."""
    return Message(
        id=str(uuid.uuid4()),
        role=role,
        content=content,
        timestamp=datetime.utcnow().isoformat(),
        tool_calls=tool_calls or []
    )


def create_conversation_node(message: Message, parent: str = None, is_current: bool = False) -> ConversationNode:
    """Create a conversation node with automatic ID."""
    return ConversationNode(
        id=str(uuid.uuid4()),
        message=message,
        parent=parent,
        children=[],
        is_current=is_current
    )


def create_bot_state(name: str) -> BotState:
    """Create a bot state with automatic ID."""
    return BotState(
        id=str(uuid.uuid4()),
        name=name,
        conversation_tree={},
        current_node_id=None,
        is_connected=False,
        is_thinking=False
    )
def create_tool_call(name: str, status: ToolCallStatus = ToolCallStatus.RUNNING,
                    result: str = None, error: str = None) -> ToolCall:
    """Create a tool call with automatic ID."""
    return ToolCall(
        id=str(uuid.uuid4()),
        name=name,
        status=status,
        result=result,
        error=error
    )