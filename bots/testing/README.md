# MockBot Testing Framework

The MockBot testing framework provides comprehensive mock implementations for testing the bots framework without making actual API calls.

## Overview

The testing framework includes:

- **MockBot**: Full bot implementation with configurable responses
- **MockToolHandler**: Tool handler with predictable behavior
- **MockMailbox**: Mailbox that simulates LLM communication
- **MockConversationNode**: Enhanced conversation node for testing

## Quick Start

```python
from bots.testing import MockBot

# Create a basic mock bot
bot = MockBot()
bot.set_response_pattern("Hello, {user_input}!")
response = bot.respond("world")  # Returns "Hello, world!"
```

## MockBot Class

### Basic Usage

```python
# Create with custom configuration
bot = MockBot(
    name="TestBot",
    model_engine="gpt-4",
    temperature=0.5,
    autosave=False  # Recommended for testing
)

# Set response patterns
bot.set_response_pattern("You said: '{user_input}'")
bot.add_response_pattern("Response #{call_count}")

# Get responses
response = bot.respond("Hello")
print(f"Bot responded: {response}")
```

### Response Patterns

Response patterns support placeholders:

- `{user_input}`: Last user message content
- `{model}`: Model name being simulated
- `{call_count}`: Number of API calls made
- `{conversation_length}`: Number of messages in conversation

```python
bot.set_response_pattern("Model {model} received: '{user_input}' (call #{call_count})")
```

### Tool Simulation

```python
# Add mock tools
bot.add_mock_tool("calculate")
bot.set_tool_response("calculate", 42)

# Configure tool failures
bot.set_tool_failure("broken_tool", "This tool is broken")

# Check tool usage
history = bot.get_tool_call_history()
print(f"Tools called: {len(history)}")
```

### Failure Simulation

```python
# Simulate API failures
bot.set_failure_mode(True, "Network timeout")

try:
    bot.respond("Hello")
except Exception as e:
    print(f"Expected failure: {e}")

# Add response delays
bot.set_response_delay(0.5)  # 500ms delay
```

## MockToolHandler Class

### Tool Response Configuration

```python
handler = MockToolHandler()

# Set mock responses
handler.set_mock_response("search", ["result1", "result2"])
handler.set_tool_failure("broken_api", "API is down")

# Add execution delays
handler.set_execution_delay("slow_tool", 2.0)

# Check call history
calls = handler.get_call_history()
```

### Tool Execution

```python
# Simulate tool requests
handler.add_request({
    "name": "calculate", 
    "parameters": {"x": 5, "y": 3}
})

# Execute and get results
results = handler.exec_requests()
print(f"Results: {results}")
```

## MockMailbox Class

### Response Configuration

```python
mailbox = MockMailbox()

# Set response patterns
mailbox.set_response_pattern("Mock response: {user_input}")
mailbox.add_response_pattern("Alternative response")

# Configure failures and delays
mailbox.set_failure_mode(True, "API error")
mailbox.set_response_delay(1.0)
```

## MockConversationNode Class

### Enhanced Testing Features

```python
node = MockConversationNode("Hello", "user")

# Add test metadata
node.set_test_metadata("test_id", "conversation_001")

# Count nodes by role
user_count = node.count_nodes_with_role("user")

# Find nodes with content patterns
matches = node.find_nodes_with_content(r"hello|hi")
```

## Utility Functions

### Creating Test Conversations

```python
from bots.testing import create_test_conversation

# Create conversation from exchanges
conversation = create_test_conversation([
    ("user", "Hello"),
    ("assistant", "Hi there!"),
    ("user", "How are you?"),
    ("assistant", "I'm doing well!")
])
```

### Creating Bots with Tools

```python
from bots.testing import create_mock_bot_with_tools

bot = create_mock_bot_with_tools([
    {"name": "search", "response": "Found results"},
    {"name": "calculate", "response": 42},
    {"name": "broken", "should_fail": True, "error_message": "Tool error"}
])
```

## Testing Assertions

### Conversation Flow Testing

```python
from bots.testing import assert_conversation_flow

bot = MockBot()
bot.respond("Hello")
bot.respond("Goodbye")

# Assert the conversation follows expected pattern
assert_conversation_flow(bot, [
    {"role": "user", "content": "Hello"},
    {"role": "assistant"},  # Don't check content
    {"role": "user", "content": "Goodbye"},
    {"role": "assistant", "content": "Expected response"}
])
```

### Tool Usage Testing

```python
from bots.testing import assert_tool_called, assert_tool_called_with

# Assert tool was called
assert_tool_called(bot, "search", times=2)

# Assert tool was called with specific parameters
assert_tool_called_with(bot, "calculate", {"x": 5, "y": 3})
```

## Advanced Testing Patterns

### Conversation Simulation

```python
bot = MockBot()
bot.add_response_pattern("Hello!")
bot.add_response_pattern("I'm fine, thanks!")
bot.add_response_pattern("Goodbye!")

# Simulate full conversation
responses = bot.simulate_conversation([
    ("user", "Hi"),
    ("user", "How are you?"),
    ("user", "See you later")
])

print(f"Bot responses: {responses}")
```

### State Management

```python
# Reset conversation state
bot.reset_conversation()

# Clear all history
bot.clear_history()

# Check response count
count = bot.get_response_count()

# Get conversation history
history = bot.get_conversation_history()
```

### Test Metadata

```python
# Set test-specific data
bot.set_test_metadata("test_case", "integration_test_001")
bot.set_test_metadata("expected_tools", ["search", "calculate"])

# Retrieve in tests
test_case = bot.get_test_metadata("test_case")
expected_tools = bot.get_test_metadata("expected_tools", [])
```

## Integration with Testing Frameworks

### pytest Example

```python
import pytest
from bots.testing import MockBot, assert_conversation_flow

@pytest.fixture
def mock_bot():
    bot = MockBot(name="TestBot")
    bot.set_response_pattern("Test response: {user_input}")
    return bot

def test_basic_response(mock_bot):
    response = mock_bot.respond("hello")
    assert "hello" in response.lower()
    assert mock_bot.get_response_count() == 1

def test_conversation_flow(mock_bot):
    mock_bot.respond("first message")
    mock_bot.respond("second message")

    assert_conversation_flow(mock_bot, [
        {"role": "user", "content": "first message"},
        {"role": "assistant"},
        {"role": "user", "content": "second message"},
        {"role": "assistant"}
    ])

def test_tool_usage():
    bot = create_mock_bot_with_tools([
        {"name": "test_tool", "response": "tool result"}
    ])

    # Simulate tool usage
    bot.tool_handler.add_request({"name": "test_tool", "parameters": {}})
    results = bot.tool_handler.exec_requests()

    assert len(results) == 1
    assert_tool_called(bot, "test_tool", times=1)
```

### unittest Example

```python
import unittest
from bots.testing import MockBot

class TestMockBot(unittest.TestCase):
    def setUp(self):
        self.bot = MockBot()
        self.bot.set_response_pattern("Response: {user_input}")

    def test_response_pattern(self):
        response = self.bot.respond("test input")
        self.assertEqual(response, "Response: test input")

    def test_failure_mode(self):
        self.bot.set_failure_mode(True, "Test failure")

        with self.assertRaises(Exception) as context:
            self.bot.respond("hello")

        self.assertIn("Test failure", str(context.exception))

    def tearDown(self):
        self.bot.clear_history()
```

## Best Practices

### 1. Use Descriptive Response Patterns

```python
# Good: Descriptive and testable
bot.set_response_pattern("Processed '{user_input}' successfully")

# Avoid: Generic responses that don't help with testing
bot.set_response_pattern("OK")
```

### 2. Configure Realistic Tool Responses

```python
# Good: Realistic tool responses
bot.set_tool_response("search", {
    "results": ["item1", "item2"],
    "count": 2,
    "query": "test query"
})

# Avoid: Overly simple responses
bot.set_tool_response("search", "done")
```

### 3. Test Both Success and Failure Cases

```python
def test_tool_success_and_failure():
    bot = MockBot()
    bot.add_mock_tool("api_call")

    # Test success case
    bot.set_tool_response("api_call", {"status": "success"})
    # ... test logic

    # Test failure case
    bot.set_tool_failure("api_call", "API unavailable")
    # ... test logic
```

### 4. Use Assertions for Verification

```python
def test_conversation_with_assertions():
    bot = MockBot()
    bot.respond("Hello")
    bot.respond("Goodbye")

    # Verify conversation structure
    assert_conversation_flow(bot, expected_flow)

    # Verify response count
    assert bot.get_response_count() == 2

    # Verify no unexpected tool calls
    assert len(bot.get_tool_call_history()) == 0
```

### 5. Clean Up Between Tests

```python
def test_with_cleanup():
    bot = MockBot()
    # ... test logic

    # Clean up for next test
    bot.reset_conversation()
    bot.clear_history()
```

## Troubleshooting

### Common Issues

1. **Response patterns not working**: Ensure placeholders are spelled correctly
2. **Tool calls not recorded**: Make sure to call `exec_requests()` after adding requests
3. **Conversation state issues**: Use `reset_conversation()` between tests
4. **Assertion failures**: Check that expected and actual data structures match

### Debug Information

```python
# Get debug information
print(f"Response count: {bot.get_response_count()}")
print(f"Tool calls: {bot.get_tool_call_history()}")
print(f"Conversation: {bot.get_conversation_history()}")
print(f"Messages: {bot.conversation._build_messages()}")
```

This comprehensive MockBot framework provides everything needed for thorough testing of bot functionality without external dependencies or API costs.
