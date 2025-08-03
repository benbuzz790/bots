# Missing validation functions and constants
VALID_BOT_NAME = "TestBot"
VALID_MESSAGE_CONTENT = "Test message content"
INVALID_EMPTY_STRING = ""
INVALID_WHITESPACE_STRING = "   "
INVALID_NON_STRING = 123
INVALID_NONE = None
INVALID_DICT = {}
INVALID_LIST = []

def assert_bot_state_valid(bot_state):
    """Assert that a bot state is valid."""
    assert bot_state is not None
    assert hasattr(bot_state, 'id')
    assert hasattr(bot_state, 'name')
    return True

def assert_message_valid(message):
    """Assert that a message is valid."""
    assert message is not None
    assert hasattr(message, 'content')
    assert hasattr(message, 'role')
    return True
def assert_conversation_node_valid(node):
    """Assert that a conversation node is valid."""
    assert node is not None
    assert hasattr(node, 'id')
    assert hasattr(node, 'message')
    return True

def assert_tool_call_valid(tool_call):
    """Assert that a tool call is valid."""
    assert tool_call is not None
    assert hasattr(tool_call, 'id')
    assert hasattr(tool_call, 'name')
    return True