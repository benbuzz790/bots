"""
Mock implementations for testing the bots framework.

This module provides configurable mock implementations that can be used for testing
without making actual API calls to LLM services.
"""

import json
import re
import time
from typing import Any, Callable, Dict, List, Optional, Tuple, Type, Union

from bots.foundation.base import Bot, ConversationNode, Engines, Mailbox, ToolHandler


class MockConversationNode(ConversationNode):
    """Mock conversation node for testing purposes.

    Provides the same interface as ConversationNode but with additional
    testing utilities and predictable behavior.
    """

    def __init__(self, content: str = "", role: str = "user", **kwargs):
        """Initialize a mock conversation node."""
        super().__init__(content=content, role=role, **kwargs)
        self._test_metadata = {}

    def set_test_metadata(self, key: str, value: Any) -> None:
        """Set test-specific metadata on this node."""
        self._test_metadata[key] = value

    def get_test_metadata(self, key: str, default: Any = None) -> Any:
        """Get test-specific metadata from this node."""
        return self._test_metadata.get(key, default)

    def count_nodes_with_role(self, role: str) -> int:
        """Count nodes with a specific role in the conversation tree."""
        count = 0
        if self.role == role:
            count += 1
        for reply in self.replies:
            if hasattr(reply, "count_nodes_with_role"):
                count += reply.count_nodes_with_role(role)
            elif hasattr(reply, "role") and reply.role == role:
                count += 1
        return count

    def find_nodes_with_content(self, content_pattern: str) -> List["MockConversationNode"]:
        """Find all nodes whose content matches the given pattern."""
        matches = []
        if re.search(content_pattern, self.content):
            matches.append(self)
        for reply in self.replies:
            if hasattr(reply, "find_nodes_with_content"):
                matches.extend(reply.find_nodes_with_content(content_pattern))
            elif hasattr(reply, "content") and re.search(content_pattern, reply.content):
                matches.append(reply)
        return matches

    @staticmethod
    def _create_empty(cls: Optional[Type["ConversationNode"]] = None) -> "MockConversationNode":
        """Create an empty root node.

        Use when initializing a new conversation tree that needs an empty root.

        Parameters:
            cls (Optional[Type[ConversationNode]]): Optional specific node class to use

        Returns:
            MockConversationNode: An empty node with role='empty' and no content
        """
        return MockConversationNode(role="empty", content="")


class MockToolHandler(ToolHandler):
    """Mock tool handler for testing purposes.

    Provides configurable responses for tool calls without executing actual functions.
    Useful for testing bot behavior with tools in a controlled environment.
    """

    def __init__(self):
        """Initialize the mock tool handler."""
        super().__init__()
        self._mock_responses = {}
        self._call_history = []
        self._should_fail = {}
        self._execution_delays = {}

    def set_mock_response(self, tool_name: str, response: Any) -> None:
        """Set a mock response for a specific tool.

        Args:
            tool_name: Name of the tool to mock
            response: Response to return when the tool is called
        """
        self._mock_responses[tool_name] = response

    def set_tool_failure(self, tool_name: str, error_message: str) -> None:
        """Configure a tool to fail with a specific error message.

        Args:
            tool_name: Name of the tool that should fail
            error_message: Error message to return
        """
        self._should_fail[tool_name] = error_message

    def set_execution_delay(self, tool_name: str, delay_seconds: float) -> None:
        """Set an execution delay for a tool (simulates slow operations).

        Args:
            tool_name: Name of the tool to add delay to
            delay_seconds: Number of seconds to delay
        """
        self._execution_delays[tool_name] = delay_seconds

    def get_call_history(self) -> List[Dict[str, Any]]:
        """Get the history of all tool calls made."""
        return self._call_history.copy()

    def clear_call_history(self) -> None:
        """Clear the tool call history."""
        self._call_history.clear()

    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate a mock tool schema."""
        import inspect

        # Get function signature
        try:
            sig = inspect.signature(func)
            params = {}
            for param_name, param in sig.parameters.items():
                param_info = {"type": "string", "description": f"Parameter {param_name}"}
                if param.annotation != inspect.Parameter.empty:
                    param_info["type"] = str(param.annotation).replace("<class '", "").replace("'>", "")
                if param.default != inspect.Parameter.empty:
                    param_info["default"] = param.default
                params[param_name] = param_info
        except (ValueError, TypeError):
            params = {}

        return {
            "name": func.__name__,
            "description": func.__doc__ or f"Mock tool: {func.__name__}",
            "parameters": {
                "type": "object",
                "properties": params,
                "required": (
                    [name for name, param in sig.parameters.items() if param.default == inspect.Parameter.empty]
                    if "sig" in locals()
                    else []
                ),
            },
        }

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """Extract mock tool requests from a response."""
        # For testing, we'll look for a specific format in the response
        if hasattr(response, "tool_calls") and response.tool_calls:
            return response.tool_calls
        elif isinstance(response, dict) and "tool_calls" in response:
            return response["tool_calls"]
        else:
            return []

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract tool name and parameters from request schema."""
        if isinstance(request_schema, dict):
            tool_name = request_schema.get("name") or request_schema.get("function", {}).get("name")
            parameters = request_schema.get("parameters", {}) or request_schema.get("function", {}).get("arguments", {})

            # Handle string parameters (JSON)
            if isinstance(parameters, str):
                try:
                    parameters = json.loads(parameters)
                except json.JSONDecodeError:
                    parameters = {}

            return tool_name, parameters
        return None, {}

    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a mock response schema."""
        tool_name, _ = self.tool_name_and_input(request)

        return {
            "tool_use_id": request.get("id", f"mock_call_{len(self._call_history)}"),
            "content": str(tool_output_kwargs),
            "tool_name": tool_name,
            "status": "success",
        }

    def generate_error_schema(self, request_schema: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Generate a mock error response schema."""
        tool_name, _ = self.tool_name_and_input(request_schema)

        return {
            "tool_use_id": request_schema.get("id", f"mock_error_{len(self._call_history)}"),
            "content": f"Error: {error_msg}",
            "tool_name": tool_name,
            "status": "error",
        }

    def exec_requests(self) -> List[Dict[str, Any]]:
        """Execute mock tool requests."""
        results = []

        for request_schema in self.requests:
            tool_name, input_kwargs = self.tool_name_and_input(request_schema)

            if tool_name is None:
                continue

            # Record the call
            call_record = {"tool_name": tool_name, "parameters": input_kwargs, "timestamp": time.time()}
            self._call_history.append(call_record)

            # Add execution delay if configured
            if tool_name in self._execution_delays:
                time.sleep(self._execution_delays[tool_name])

            # Check if tool should fail
            if tool_name in self._should_fail:
                error_msg = self._should_fail[tool_name]
                response_schema = self.generate_error_schema(request_schema, error_msg)
            else:
                # Get mock response or use default
                if tool_name in self._mock_responses:
                    mock_output = self._mock_responses[tool_name]
                elif tool_name in self.function_map:
                    # If we have the actual function, we could call it or return a default
                    mock_output = f"Mock response for {tool_name} with args: {input_kwargs}"
                else:
                    mock_output = f"Mock tool {tool_name} executed successfully"

                response_schema = self.generate_response_schema(request_schema, mock_output)

            self.results.append(response_schema)
            results.append(response_schema)

        return results


class MockMailbox(Mailbox):
    """Mock mailbox for testing purposes.

    Simulates LLM communication without making actual API calls.
    Provides configurable responses and behavior patterns.
    """

    def __init__(self):
        """Initialize the mock mailbox."""
        super().__init__()
        self._response_patterns = []
        self._default_response = "Mock response from {model}"
        self._call_count = 0
        self._should_fail = False
        self._failure_message = "Mock API failure"
        self._response_delay = 0.0
        self._conversation_history = []

    def set_response_pattern(self, pattern: str) -> None:
        """Set a response pattern that can include placeholders.

        Available placeholders:
        - {user_input}: The last user message
        - {model}: The model name
        - {call_count}: Number of calls made
        - {conversation_length}: Number of messages in conversation

        Args:
            pattern: Response pattern string with optional placeholders
        """
        self._response_patterns = [pattern]

    def add_response_pattern(self, pattern: str) -> None:
        """Add a response pattern to the list (cycles through patterns).

        Args:
            pattern: Response pattern string with optional placeholders
        """
        self._response_patterns.append(pattern)

    def set_failure_mode(self, should_fail: bool, message: str = "Mock API failure") -> None:
        """Configure the mailbox to simulate API failures.

        Args:
            should_fail: Whether to fail on the next request
            message: Error message to use for failures
        """
        self._should_fail = should_fail
        self._failure_message = message

    def set_response_delay(self, delay_seconds: float) -> None:
        """Set a delay for responses (simulates network latency).

        Args:
            delay_seconds: Number of seconds to delay responses
        """
        self._response_delay = delay_seconds

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the history of all conversations processed."""
        return self._conversation_history.copy()

    def clear_conversation_history(self) -> None:
        """Clear the conversation history."""
        self._conversation_history.clear()

    def send_message(self, bot: "Bot") -> Dict[str, Any]:
        """Send a mock message and return a mock response.

        Args:
            bot: The bot instance making the request

        Returns:
            Mock response dictionary

        Raises:
            Exception: If failure mode is enabled
        """
        # Add response delay if configured
        if self._response_delay > 0:
            time.sleep(self._response_delay)

        # Check if we should fail
        if self._should_fail:
            raise Exception(self._failure_message)

        # Build conversation context
        messages = bot.conversation._build_messages()
        self._conversation_history.append(
            {
                "timestamp": time.time(),
                "messages": messages,
                "model": bot.model_engine.value if hasattr(bot.model_engine, "value") else str(bot.model_engine),
            }
        )

        # Get the last user message for context
        user_input = ""
        for msg in reversed(messages):
            if msg.get("role") == "user":
                user_input = msg.get("content", "")
                break

        # Select response pattern
        if self._response_patterns:
            pattern_index = self._call_count % len(self._response_patterns)
            response_pattern = self._response_patterns[pattern_index]
        else:
            response_pattern = self._default_response

        # Format the response
        response_text = response_pattern.format(
            user_input=user_input,
            model=bot.model_engine.value if hasattr(bot.model_engine, "value") else str(bot.model_engine),
            call_count=self._call_count,
            conversation_length=len(messages),
        )

        self._call_count += 1

        # Create mock response structure
        mock_response = {
            "content": response_text,
            "role": "assistant",
            "model": bot.model_engine.value if hasattr(bot.model_engine, "value") else str(bot.model_engine),
            "usage": {
                "prompt_tokens": sum(len(msg.get("content", "").split()) for msg in messages),
                "completion_tokens": len(response_text.split()),
                "total_tokens": sum(len(msg.get("content", "").split()) for msg in messages) + len(response_text.split()),
            },
        }

        return mock_response

    def process_response(self, response: Dict[str, Any], bot: Optional["Bot"] = None) -> Tuple[str, str, Dict[str, Any]]:
        """Process the mock response into standardized format.

        Args:
            response: Mock response from send_message
            bot: Optional bot reference

        Returns:
            Tuple of (response_text, role, metadata)
        """
        response_text = response.get("content", "Mock response")
        role = response.get("role", "assistant")

        # Extract metadata
        metadata = {
            "model": response.get("model", "mock-model"),
            "usage": response.get("usage", {}),
            "mock_call_count": self._call_count - 1,
        }

        return response_text, role, metadata


class MockBot(Bot):
    """Mock bot implementation for testing purposes.

    Provides a fully functional bot that doesn't make actual API calls.
    Useful for testing bot behavior, conversation flow, and tool integration
    without incurring API costs or dealing with network issues.

    Features:
    - Configurable response patterns
    - Predictable behavior for testing
    - Tool simulation support
    - Conversation history tracking
    - Failure mode simulation
    - No API key required

    Example:
        ```python
        from bots.testing import MockBot

        # Basic usage
        bot = MockBot()
        bot.set_response_pattern("Hello, {user_input}!")
        response = bot.respond("world")  # Returns "Hello, world!"

        # With tools
        bot.add_mock_tool("calculate", lambda x, y: x + y)
        bot.set_tool_response("calculate", 42)

        # Simulate failures
        bot.set_failure_mode(True, "Simulated network error")
        ```
    """

    def __init__(
        self,
        name: str = "MockBot",
        model_engine: Union[Engines, str] = Engines.GPT4,
        max_tokens: int = 1000,
        temperature: float = 0.7,
        role: str = "assistant",
        role_description: str = "A helpful mock assistant for testing",
        conversation: Optional[ConversationNode] = None,
        autosave: bool = False,  # Default to False for testing
        enable_tracing: Optional[bool] = None,  # Support tracing parameter
    ):
        """Initialize a mock bot.

        Args:
            name: Name of the bot
            model_engine: Model engine to simulate
            max_tokens: Maximum tokens (for simulation)
            temperature: Temperature setting (for simulation)
            role: Bot's role
            role_description: Description of the bot's role
            conversation: Initial conversation state
            autosave: Whether to autosave (disabled by default for testing)
            enable_tracing: Whether to enable OpenTelemetry tracing (None = use default)
        """
        # Convert string to Engines enum if needed
        if isinstance(model_engine, str):
            model_engine = Engines.get(model_engine) or Engines.GPT4

        # Create mock components
        mock_tool_handler = MockToolHandler()
        mock_mailbox = MockMailbox()

        # Use MockConversationNode if no conversation provided
        if conversation is None:
            conversation = MockConversationNode._create_empty()
        elif not isinstance(conversation, MockConversationNode):
            # Convert regular ConversationNode to MockConversationNode if needed
            if hasattr(conversation, "_is_empty") and conversation._is_empty():
                conversation = MockConversationNode._create_empty()

        # Initialize the parent Bot class
        super().__init__(
            api_key=None,  # No API key needed for mock
            model_engine=model_engine,
            max_tokens=max_tokens,
            temperature=temperature,
            name=name,
            role=role,
            role_description=role_description,
            conversation=conversation,
            tool_handler=mock_tool_handler,
            mailbox=mock_mailbox,
            autosave=autosave,
            enable_tracing=enable_tracing,  # Pass through tracing parameter
        )

        # Additional mock-specific attributes
        self._response_count = 0
        self._test_metadata = {}

    def set_response_pattern(self, pattern: str) -> None:
        """Set a response pattern for the bot.

        Args:
            pattern: Response pattern with optional placeholders
        """
        self.mailbox.set_response_pattern(pattern)

    def add_response_pattern(self, pattern: str) -> None:
        """Add a response pattern (cycles through multiple patterns).

        Args:
            pattern: Response pattern with optional placeholders
        """
        self.mailbox.add_response_pattern(pattern)

    def set_failure_mode(self, should_fail: bool, message: str = "Mock failure") -> None:
        """Configure the bot to simulate failures.

        Args:
            should_fail: Whether the next request should fail
            message: Error message for the failure
        """
        self.mailbox.set_failure_mode(should_fail, message)

    def set_response_delay(self, delay_seconds: float) -> None:
        """Set a delay for responses.

        Args:
            delay_seconds: Number of seconds to delay
        """
        self.mailbox.set_response_delay(delay_seconds)

    def add_mock_tool(self, name: str, func: Optional[Callable] = None) -> None:
        """Add a mock tool to the bot.

        Args:
            name: Name of the tool
            func: Optional function to use for the tool (can be mocked)
        """
        if func is None:
            # Create a simple mock function
            def mock_func(*args, **kwargs):
                return f"Mock result from {name}"

            mock_func.__name__ = name
            mock_func.__doc__ = f"Mock tool: {name}"
            func = mock_func
        else:
            # Ensure the function has the correct name
            if not hasattr(func, "__name__") or func.__name__ != name:
                func.__name__ = name

        # Add the tool directly to avoid the module context creation issues
        schema = self.tool_handler.generate_tool_schema(func)
        self.tool_handler.tools.append(schema)
        self.tool_handler.function_map[func.__name__] = func

    def set_tool_response(self, tool_name: str, response: Any) -> None:
        """Set a mock response for a specific tool.

        Args:
            tool_name: Name of the tool
            response: Response to return when the tool is called
        """
        self.tool_handler.set_mock_response(tool_name, response)

    def set_tool_failure(self, tool_name: str, error_message: str) -> None:
        """Configure a tool to fail with a specific error.

        Args:
            tool_name: Name of the tool
            error_message: Error message to return
        """
        self.tool_handler.set_tool_failure(tool_name, error_message)

    def get_response_count(self) -> int:
        """Get the number of responses generated."""
        return self._response_count

    def get_tool_call_history(self) -> List[Dict[str, Any]]:
        """Get the history of tool calls made."""
        return self.tool_handler.get_call_history()

    def get_conversation_history(self) -> List[Dict[str, Any]]:
        """Get the conversation history from the mailbox."""
        return self.mailbox.get_conversation_history()

    def clear_history(self) -> None:
        """Clear all history (conversation, tool calls, etc.)."""
        self.tool_handler.clear_call_history()
        self.mailbox.clear_conversation_history()
        self._response_count = 0

    def set_test_metadata(self, key: str, value: Any) -> None:
        """Set test-specific metadata on the bot."""
        self._test_metadata[key] = value

    def get_test_metadata(self, key: str, default: Any = None) -> Any:
        """Get test-specific metadata from the bot."""
        return self._test_metadata.get(key, default)

    def respond(self, prompt: str, role: str = "user") -> str:
        """Override respond to track response count."""
        response = super().respond(prompt, role)
        self._response_count += 1
        return response

    def simulate_conversation(self, messages: List[Tuple[str, str]]) -> List[str]:
        """Simulate a full conversation with multiple exchanges.

        Args:
            messages: List of (role, content) tuples

        Returns:
            List of bot responses
        """
        responses = []
        for role, content in messages:
            if role == "user":
                response = self.respond(content, role)
                responses.append(response)
            else:
                # For non-user messages, just add to conversation without responding
                self.conversation = self.conversation._add_reply(content=content, role=role)
        return responses

    def reset_conversation(self) -> None:
        """Reset the conversation to empty state."""
        self.conversation = MockConversationNode._create_empty()
        self.clear_history()

    def __repr__(self) -> str:
        """String representation for debugging."""
        return f"MockBot(name='{self.name}', model='{self.model_engine.value}', responses={self._response_count})"


# Utility functions for testing


def create_test_conversation(exchanges: List[Tuple[str, str]]) -> MockConversationNode:
    """Create a test conversation from a list of exchanges.

    Args:
        exchanges: List of (role, content) tuples

    Returns:
        MockConversationNode with the conversation tree (returns the leaf node)
    """
    root = MockConversationNode._create_empty()
    current = root

    for role, content in exchanges:
        new_node = MockConversationNode(content=content, role=role)
        new_node.parent = current
        current.replies.append(new_node)
        current = new_node

    # Return the leaf node so _build_messages() works correctly
    return current


def create_mock_bot_with_tools(tool_configs: List[Dict[str, Any]]) -> MockBot:
    """Create a mock bot with predefined tools.

    Args:
        tool_configs: List of tool configuration dictionaries
                     Each dict should have 'name', 'response', and optionally 'should_fail'

    Returns:
        Configured MockBot instance
    """
    bot = MockBot()

    for config in tool_configs:
        name = config["name"]
        response = config.get("response", f"Mock response from {name}")
        should_fail = config.get("should_fail", False)
        error_message = config.get("error_message", f"Mock error from {name}")

        # Add the mock tool
        bot.add_mock_tool(name)

        if should_fail:
            bot.set_tool_failure(name, error_message)
        else:
            bot.set_tool_response(name, response)

    return bot


def assert_conversation_flow(bot: MockBot, expected_flow: List[Dict[str, str]]) -> bool:
    """Assert that a conversation follows the expected flow.

    Args:
        bot: MockBot instance to test
        expected_flow: List of expected message dictionaries with 'role' and 'content'

    Returns:
        True if the flow matches, raises AssertionError otherwise
    """
    messages = bot.conversation._build_messages()

    if len(messages) != len(expected_flow):
        raise AssertionError(f"Expected {len(expected_flow)} messages, got {len(messages)}")

    for i, (actual, expected) in enumerate(zip(messages, expected_flow)):
        if actual["role"] != expected["role"]:
            raise AssertionError(f"Message {i}: expected role '{expected['role']}', got '{actual['role']}'")

        if expected.get("content") and actual["content"] != expected["content"]:
            raise AssertionError(f"Message {i}: expected content '{expected['content']}', got '{actual['content']}'")

    return True


def assert_tool_called(bot: MockBot, tool_name: str, times: int = 1) -> bool:
    """Assert that a tool was called a specific number of times.

    Args:
        bot: MockBot instance to check
        tool_name: Name of the tool to check
        times: Expected number of calls

    Returns:
        True if assertion passes, raises AssertionError otherwise
    """
    history = bot.get_tool_call_history()
    actual_calls = sum(1 for call in history if call["tool_name"] == tool_name)

    if actual_calls != times:
        raise AssertionError(f"Expected {tool_name} to be called {times} times, was called {actual_calls} times")

    return True


def assert_tool_called_with(bot: MockBot, tool_name: str, expected_params: Dict[str, Any]) -> bool:
    """Assert that a tool was called with specific parameters.

    Args:
        bot: MockBot instance to check
        tool_name: Name of the tool to check
        expected_params: Expected parameters

    Returns:
        True if assertion passes, raises AssertionError otherwise
    """
    history = bot.get_tool_call_history()
    matching_calls = [call for call in history if call["tool_name"] == tool_name and call["parameters"] == expected_params]

    if not matching_calls:
        raise AssertionError(f"Tool {tool_name} was not called with parameters {expected_params}")

    return True


# Example usage and test patterns

if __name__ == "__main__":
    # Example 1: Basic mock bot usage
    print("=== Example 1: Basic Mock Bot ===")
    bot = MockBot(name="TestBot")
    bot.set_response_pattern("You said: '{user_input}'. This is response #{call_count}.")

    response1 = bot.respond("Hello")
    response2 = bot.respond("How are you?")

    print(f"Response 1: {response1}")
    print(f"Response 2: {response2}")
    print(f"Total responses: {bot.get_response_count()}")

    # Example 2: Mock bot with tools
    print("\n=== Example 2: Mock Bot with Tools ===")
    tool_bot = create_mock_bot_with_tools(
        [
            {"name": "calculate", "response": 42},
            {"name": "search", "response": "Found 3 results"},
            {"name": "broken_tool", "should_fail": True, "error_message": "Tool is broken"},
        ]
    )

    tool_bot.set_response_pattern("I'll use the {user_input} tool for you.")

    # Simulate tool usage (in real usage, the LLM would trigger tools)
    tool_bot.tool_handler.add_request({"name": "calculate", "parameters": {"x": 5, "y": 7}})
    tool_results = tool_bot.tool_handler.exec_requests()

    print(f"Tool results: {tool_results}")
    print(f"Tool call history: {tool_bot.get_tool_call_history()}")

    # Example 3: Conversation simulation
    print("\n=== Example 3: Conversation Simulation ===")
    conv_bot = MockBot()
    conv_bot.add_response_pattern("Hello there!")
    conv_bot.add_response_pattern("I'm doing well, thanks!")
    conv_bot.add_response_pattern("That's interesting!")

    conversation = [("user", "Hi"), ("user", "How are you?"), ("user", "I like programming")]

    responses = conv_bot.simulate_conversation(conversation)
    print(f"Conversation responses: {responses}")

    # Example 4: Testing assertions
    print("\n=== Example 4: Testing Assertions ===")
    test_bot = MockBot()
    test_bot.respond("Hello")
    test_bot.respond("Goodbye")

    try:
        assert_conversation_flow(
            test_bot,
            [
                {"role": "user", "content": "Hello"},
                {"role": "assistant"},  # Don't check content
                {"role": "user", "content": "Goodbye"},
                {"role": "assistant"},
            ],
        )
        print("Conversation flow assertion passed!")
    except AssertionError as e:
        print(f"Assertion failed: {e}")

    print("\n=== Mock Bot Examples Complete ===")
