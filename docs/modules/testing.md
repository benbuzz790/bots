# Testing Module

**Module**: `bots/testing/`
**Version**: 3.0.0

## Overview

Testing utilities and mock implementations

## Architecture

```
testing/
├── __init__.py
├── mock_bot.py
```

## Key Components

### MockConversationNode

Mock conversation node for testing purposes.


## Usage Examples

```python
from bots.testing import *

# Usage examples coming soon
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `MockConversationNode` | Class | Mock conversation node for testing purposes. |
| `MockToolHandler` | Class | Mock tool handler for testing purposes. |
| `MockMailbox` | Class | Mock mailbox for testing purposes. |
| `MockBot` | Class | Mock bot implementation for testing purposes. |
| `create_test_conversation` | Function | Create a test conversation from a list of exchanges. |
| `create_mock_bot_with_tools` | Function | Create a mock bot with predefined tools. |
| `assert_conversation_flow` | Function | Assert that a conversation follows the expected flow. |
| `assert_tool_called` | Function | Assert that a tool was called a specific number of times. |
| `assert_tool_called_with` | Function | Assert that a tool was called with specific parameters. |
| `set_test_metadata` | Function | Set test-specific metadata on this node. |
| `get_test_metadata` | Function | Get test-specific metadata from this node. |
| `count_nodes_with_role` | Function | Count nodes with a specific role in the conversation tree. |
| `find_nodes_with_content` | Function | Find all nodes whose content matches the given pattern. |
| `set_mock_response` | Function | Set a mock response for a specific tool. |
| `set_tool_failure` | Function | Configure a tool to fail with a specific error message. |
| `set_execution_delay` | Function | Set an execution delay for a tool (simulates slow operations |
| `get_call_history` | Function | Get the history of all tool calls made. |
| `clear_call_history` | Function | Clear the tool call history. |
| `generate_tool_schema` | Function | Generate a mock tool schema. |
| `generate_request_schema` | Function | Extract mock tool requests from a response. |
| `tool_name_and_input` | Function | Extract tool name and parameters from request schema. |
| `generate_response_schema` | Function | Generate a mock response schema. |
| `generate_error_schema` | Function | Generate a mock error response schema. |
| `exec_requests` | Function | Execute mock tool requests. |
| `set_response_pattern` | Function | Set a response pattern that can include placeholders. |
| `add_response_pattern` | Function | Add a response pattern to the list (cycles through patterns) |
| `set_failure_mode` | Function | Configure the mailbox to simulate API failures. |
| `set_response_delay` | Function | Set a delay for responses (simulates network latency). |
| `get_conversation_history` | Function | Get the history of all conversations processed. |
| `clear_conversation_history` | Function | Clear the conversation history. |
| `send_message` | Function | Send a mock message and return a mock response. |
| `process_response` | Function | Process the mock response into standardized format. |
| `set_response_pattern` | Function | Set a response pattern for the bot. |
| `add_response_pattern` | Function | Add a response pattern (cycles through multiple patterns). |
| `set_failure_mode` | Function | Configure the bot to simulate failures. |
| `set_response_delay` | Function | Set a delay for responses. |
| `add_mock_tool` | Function | Add a mock tool to the bot. |
| `set_tool_response` | Function | Set a mock response for a specific tool. |
| `set_tool_failure` | Function | Configure a tool to fail with a specific error. |
| `get_response_count` | Function | Get the number of responses generated. |
| `get_tool_call_history` | Function | Get the history of tool calls made. |
| `get_conversation_history` | Function | Get the conversation history from the mailbox. |
| `clear_history` | Function | Clear all history (conversation, tool calls, etc.). |
| `set_test_metadata` | Function | Set test-specific metadata on the bot. |
| `get_test_metadata` | Function | Get test-specific metadata from the bot. |
| `respond` | Function | Override respond to track response count. |
| `simulate_conversation` | Function | Simulate a full conversation with multiple exchanges. |
| `reset_conversation` | Function | Reset the conversation to empty state. |
| `mock_func` | Function | No description |
