"""Anthropic-specific bot implementation for the bots framework.

This module provides the necessary classes to interact with Anthropic's
Claude models,
implementing the base bot interfaces with Anthropic-specific handling`nfor:
- Message formatting and conversation management
- Tool integration and execution
- Cache control for optimal context window usage
- API communication with retry logic

The main class is AnthropicBot, which provides a complete implementation
ready for
use with Anthropic's API. Supporting classes handle specific aspects of`nthe
Anthropic integration while maintaining the framework's abstractions.

Classes:
    AnthropicNode: Conversation node implementation for Anthropic's
        message format
    AnthropicToolHandler: Tool management for Anthropic's function
        calling format
    AnthropicMailbox: API communication handler with Anthropic-specific
        retry logic
    AnthropicBot: Main bot implementation for Anthropic's Claude models
    CacheController: Manages conversation history caching for context
        optimization
"""

import inspect
import math
import os
import random
import time
from typing import Any, Callable, Dict, List, Optional, Tuple

import anthropic

from bots.foundation.base import (
    Bot,
    ConversationNode,
    Engines,
    Mailbox,
    ToolHandler,
)

# Import OpenTelemetry tracing
try:
    from bots.observability.tracing import get_tracer

    tracer = get_tracer(__name__)
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    tracer = None

# Import OpenTelemetry metrics and cost calculator
try:
    from bots.observability import metrics
    from bots.observability.cost_calculator import calculate_cost

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None
    calculate_cost = None

# Import callbacks with graceful degradation
try:
    from bots.observability.callbacks import BotCallbacks
except ImportError:
    BotCallbacks = Any  # Fallback for type hints

# Set up logging
import logging

logger = logging.getLogger(__name__)


class AnthropicNode(ConversationNode):
    """A conversation node implementation specific to Anthropic's API
    requirements.

    This class extends ConversationNode to handle Anthropic-specific
    message formatting,
    including proper handling of tool calls and results in the
    conversation tree.

    Attributes:
        Inherits all attributes from ConversationNode
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize an AnthropicNode.

        Args:
            **kwargs: Arbitrary keyword arguments passed to parent class.
        """
        super().__init__(**kwargs)

    def _add_tool_results(self, results: List[Dict[str, Any]]) -> None:
        """Add tool execution results to the conversation node.

        For Anthropic bots, tool results need to either be in user nodes
        or stored as pending to be moved to the replies when a
        reply is added.

        Args:
            results: List of tool execution result dictionaries
        """
        if self.role == "user":
            super()._add_tool_results(results)
            self._sync_tool_context()
        else:
            # Deduplicate: existing pending results first, then new results (new ones win)
            existing_dict = {r.get("tool_use_id"): r for r in self.pending_results if r.get("tool_use_id")}
            new_dict = {r.get("tool_use_id"): r for r in results if r.get("tool_use_id")}

            # Merge with new results taking priority
            merged_dict = {**existing_dict, **new_dict}

            self.pending_results = list(merged_dict.values())

    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build message list for Anthropic API.

        Constructs the message history in Anthropic's expected format,
        properly handling
        empty nodes and tool calls. Empty nodes are preserved in the structure but
        filtered from API messages.

        Returns:
            List of message dictionaries formatted for Anthropic's API
        """
        node = self
        conversation_dict = []
        while node:
            # node._sync_tool_context() Don't sync here either
            if not node._is_empty():
                entry = {"role": node.role}
                content_list = [{"type": "text", "text": node.content}]
                if node.tool_calls:
                    for call in node.tool_calls:
                        sub_entry = {"type": "tool_use", **call}
                        content_list.append(sub_entry)
                if node.tool_results:
                    for result in node.tool_results:
                        sub_entry = {"type": "tool_result", **result}
                        content_list.insert(0, sub_entry)
                entry["content"] = content_list
                conversation_dict = [entry] + conversation_dict
            node = node.parent

        return conversation_dict


class AnthropicToolHandler(ToolHandler):
    """Tool handler implementation specific to Anthropic's API
    requirements.

    This class manages the conversion between Python functions and
    Anthropic's tool format,
    handling schema generation, request/response formatting, and error
    handling.
    """

    def __init__(self) -> None:
        """Initialize an AnthropicToolHandler."""
        super().__init__()

    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate Anthropic-compatible tool schema from a Python function.

        Args:
            func: The Python function to convert into a tool schema

        Returns:
            Dictionary containing the tool schema in Anthropic's format with:
                - name: The function name
                - description: The function's docstring
                - input_schema: Object describing expected parameters
        """
        sig: inspect.Signature = inspect.signature(func)
        doc: str = inspect.getdoc(func) or "No description provided."
        tool: Dict[str, Any] = {
            "name": func.__name__,
            "description": doc,
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        for param_name, param in sig.parameters.items():
            tool["input_schema"]["properties"][param_name] = {"type": "string"}
            if param.default == inspect.Parameter.empty:
                tool["input_schema"]["required"].append(param_name)
        return tool

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """Generate request schema from an Anthropic API response.

        Args:
            response: The raw response from Anthropic's API

        Returns:
            List of request schemas (multiple requests may be in one message)
        """
        requests: List[Dict[str, Any]] = []
        for block in response.content:
            if block.type == "tool_use":
                request = {attr: getattr(block, attr) for attr in ["type", "id", "name", "input"]}
                requests.append(request)
        return requests

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Extract tool name and input parameters from a request schema.

        Args:
            request_schema: The request schema to parse

        Returns:
            Tuple containing:
                - tool name (str)
                - tool input parameters (dict)
        """
        tool_name: str = request_schema["name"]
        tool_input: Dict[str, Any] = request_schema["input"]
        return (tool_name, tool_input)

    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate response schema for tool execution results.

        Args:
            request: The original tool request
            tool_output_kwargs: The tool's execution results

        Returns:
            Dictionary containing the response in Anthropic's expected format
        """
        response: Dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": request.get("id", "unknown id"),
            "content": tool_output_kwargs,
        }
        return response

    def generate_error_schema(self, request_schema: Optional[Dict[str, Any]], error_msg: str) -> Dict[str, Any]:
        """Generate an error response schema in Anthropic's format.

        Args:
            request_schema: Optional original request schema that caused the error
            error_msg: The error message to include

        Returns:
            Dictionary containing the error in Anthropic's expected format
        """
        return {
            "type": "tool_result",
            "tool_use_id": (request_schema.get("id", "unknown id") if request_schema else "unknown id"),
            "content": error_msg,
        }


class AnthropicMailbox(Mailbox):
    """Handles communication with Anthropic's API.

    This class manages message sending and response processing for
    Anthropic models,
    including retry logic for API errors and handling of incomplete
    responses.

    Attributes:
        last_message: Optional[Dict[str, Any]] - The last message sent/received
        client: Optional[anthropic.Anthropic] - The Anthropic API client instance
    """

    def __init__(self, verbose: bool = False):
        """Initialize an AnthropicMailbox.

        Args:
            verbose: Whether to enable verbose logging (default: False)
        """
        super().__init__()
        self.last_message: Optional[Dict[str, Any]] = None
        self.client: Optional[anthropic.Anthropic] = None

    def send_message(
        self,
        bot: "AnthropicBot",
        timeout: float = 600.0,
        max_retries: int = 3,
        base_delay: float = 1.0,
        timeout_retries: int = 2,
        timeout_base_delay: float = 5.0,
    ) -> Any:
        """Send a message to the Anthropic API with retry logic.

        Handles API communication with exponential backoff for transient errors
        and special handling for timeout errors. Includes OpenTelemetry tracing
        when enabled.

        Args:
            bot: The AnthropicBot instance making the request
            timeout: Maximum time to wait for API response (default: 600s)
            max_retries: Maximum number of retry attempts for API errors
            base_delay: Base delay in seconds for exponential backoff
            timeout_retries: Number of retries specifically for timeout errors
            timeout_base_delay: Base delay for timeout retry attempts

        Returns:
            The API response object from Anthropic

        Raises:
            ValueError: If no API key is found
            anthropic.APITimeoutError: If request times out after retries
            Exception: If max retries are reached
        """
        # Check if tracing is enabled for this bot
        should_trace = TRACING_AVAILABLE and hasattr(bot, "_tracing_enabled") and bot._tracing_enabled

        if should_trace:
            span = tracer.start_span("mailbox.send_message")
            span.set_attribute("provider", "anthropic")
            span.set_attribute("model", bot.model_engine.value)
            span.set_attribute("timeout", timeout)
            span.set_attribute("max_retries", max_retries)
        else:
            span = None

        try:
            if span:
                span.add_event("mailbox.send.start")

            api_key: Optional[str] = bot.api_key
            if not api_key:
                api_key = os.getenv("ANTHROPIC_API_KEY")
                if not api_key:
                    logger.error("API key not found", extra={"provider": "anthropic"})
                    raise ValueError("Anthropic API key not found. Set up 'ANTHROPIC_API_KEY' environment variable.")

            # Initialize client with timeout
            self.client = anthropic.Anthropic(api_key=api_key, timeout=timeout)
            conversation: AnthropicNode = bot.conversation
            tools: Optional[List[Dict[str, Any]]] = None
            if bot.tool_handler and bot.tool_handler.tools:
                tools = bot.tool_handler.tools
                tools[-1]["cache_control"] = {"type": "ephemeral"}

            # Build the create dictionary
            create_dict: Dict[str, Any] = {
                "model": bot.model_engine.value,
                "max_tokens": bot.max_tokens,
                "temperature": bot.temperature,
                "messages": conversation._build_messages(),
            }

            if bot.system_message:
                create_dict["system"] = bot.system_message

            if tools:
                create_dict["tools"] = tools

            if span:
                span.set_attribute("message_count", len(create_dict["messages"]))
                if tools:
                    span.set_attribute("tool_count", len(tools))

            # Retry loop with exponential backoff
            for attempt in range(max_retries):
                try:
                    if span:
                        span.add_event("api.call.attempt", {"attempt": attempt + 1})

                    api_start_time = time.time()
                    response = self.client.messages.create(**create_dict)

                    # Capture token usage and cost
                    if span and hasattr(response, "usage"):
                        span.set_attribute("input_tokens", response.usage.input_tokens)
                        span.set_attribute("output_tokens", response.usage.output_tokens)
                    # Calculate and record cost and metrics
                    if METRICS_AVAILABLE and hasattr(response, "usage"):
                        try:
                            # Record token usage
                            metrics.record_tokens(
                                response.usage.input_tokens,
                                response.usage.output_tokens,
                                provider="anthropic",
                                model=bot.model_engine.value,
                            )

                            # Calculate and record cost
                            cost = calculate_cost(
                                provider="anthropic",
                                model=bot.model_engine.value,
                                input_tokens=response.usage.input_tokens,
                                output_tokens=response.usage.output_tokens,
                            )
                            metrics.record_cost(cost, provider="anthropic", model=bot.model_engine.value)
                        except Exception as e:
                            logger.warning(f"Failed to record metrics: {e}")

                    # Record API call metrics
                    if METRICS_AVAILABLE:
                        try:
                            api_duration = time.time() - api_start_time
                            metrics.record_api_call(
                                duration=api_duration, provider="anthropic", model=bot.model_engine.value, status="success"
                            )
                        except Exception as e:
                            logger.warning(f"Failed to record API metrics: {e}")

                    if span:
                        span.add_event("api.call.success")

                    return response

                except anthropic.APITimeoutError as e:
                    # Record timeout error metric
                    if METRICS_AVAILABLE:
                        try:
                            metrics.record_error(error_type="APITimeoutError", provider="anthropic", operation="api_call")
                        except Exception:
                            pass

                    # Special handling for timeout errors
                    if attempt < timeout_retries:
                        timeout_delay = timeout_base_delay * (attempt + 1)
                        logger.warning(
                            "API timeout, retrying",
                            extra={"attempt": attempt + 1, "delay": timeout_delay, "provider": "anthropic"},
                        )
                        if span:
                            span.add_event("api.timeout", {"attempt": attempt + 1, "delay": timeout_delay})
                        time.sleep(timeout_delay)
                        continue
                    else:
                        logger.exception(
                            "Max timeout retries reached", extra={"timeout_retries": timeout_retries, "provider": "anthropic"}
                        )
                        if span:
                            span.record_exception(e)
                        raise

                except Exception as e:
                    # Handle other API errors with exponential backoff
                    if attempt >= max_retries - 1:
                        # Last attempt - log and raise
                        logger.exception(
                            "Max retries reached",
                            extra={
                                "error_type": e.__class__.__name__,
                                "provider": "anthropic",
                                "create_dict": str(create_dict),
                            },
                        )
                        if span:
                            span.record_exception(e)
                        raise

                    # Calculate exponential backoff delay
                    delay = base_delay * (2**attempt) + random.uniform(0, 1)
                    logger.warning(
                        "API error, retrying with exponential backoff",
                        extra={
                            "attempt": attempt + 1,
                            "error_type": e.__class__.__name__,
                            "delay": delay,
                            "provider": "anthropic",
                        },
                    )
                    if span:
                        span.add_event(
                            "api.error.retry", {"attempt": attempt + 1, "error_type": e.__class__.__name__, "delay": delay}
                        )
                    time.sleep(delay)

        finally:
            if span:
                span.end()

    def process_response(self, response: Dict[str, Any], bot: "AnthropicBot") -> Tuple[str, str, Dict[str, Any]]:
        """Process the API response and handle incomplete responses.

        Manages continuation of responses that hit the max_tokens limit and
        extracts the relevant text and role information.

        Args:
            response: The API response to process
            bot: The AnthropicBot instance that made the request

        Returns:
            Tuple containing:
                - response text (str)
                - response role (str)
                - additional metadata (dict)

        Raises:
            anthropic.BadRequestError: If the API returns a 400 error
        """
        try:

            def should_continue(response) -> bool:
                """Determine if response continuation is needed.

                Args:
                    response: The Anthropic API response object

                Returns:
                    bool: True if the response was truncated and contains no
                    tool calls
                """
                return False  # FEATURE DISABLED - some weird interaction with max_tokens and
                # the new api makes this hang indefinitely
                return response.stop_reason == "max_tokens" and any(
                    isinstance(block, anthropic.types.ToolUseBlock) for block in response.content
                )

            # TODO: Sometimes Claude responds without a text block, and content[0]
            # is a tool use block. Need to check for this case and add a tool use
            # block manually.
            if not getattr(response.content[0], "text", None):
                block = anthropic.types.TextBlock(text="~", type="text")
                response.content.insert(0, block)

            # while should_continue(response):
            #     if bot.conversation.role == "user":  # base case
            #         bot.conversation._add_reply(role="assistant", content=response.content[0].text)
            #     elif bot.conversation.role == "assistant":  # recursive case
            #         bot.conversation.content += response
            #     response = self.send_message(bot)

            # process the complete response
            response_role: str = response.role
            response_text: str = getattr(response.content[0], "text", "~")
        except anthropic.BadRequestError as e:
            if e.status_code == 400:
                pass
            raise e
        return (response_text, response_role, {})


class AnthropicBot(Bot):
    """
    A bot implementation using the Anthropic API.

    Use when you need to create a bot that interfaces with Anthropic's
    chat completion models.
    Provides a complete implementation with Anthropic-specific
    conversation management,
    tool handling, and message processing. Supports both simple chat
    interactions and
    complex tool-using conversations.

    Inherits from:
        Bot: Base class for all bot implementations, providing core
        conversation and tool management

    Attributes:
        api_key (str): Anthropic API key for authentication
        model_engine (Engines): The Anthropic model being used (e.g., GPT4)
        max_tokens (int): Maximum tokens allowed in completion responses
        temperature (float): Response randomness factor (0-1)
        name (str): Instance name for identification
        role (str): Bot's role identifier
        role_description (str): Detailed description of bot's
            role/personality (for humans to read, not used in api)
        system_message (str): System-level instructions for the bot
        tool_handler (AnthropicToolHandler): Manages function calling capabilities
        conversation (AnthropicNode): Manages conversation history
        mailbox (AnthropicMailbox): Handles API communication
        autosave (bool): Whether to automatically save state after responses

    Example:
        ```python
        # Create a documentation expert bot
        bot = ChatGPT_Bot(
            model_engine=Engines.GPT4,
            temperature=0.3,
            role_description="a Python documentation expert"
        )

        # Add tools and use the bot
        bot.add_tool(my_function)
        response = bot.respond("Please help document this code.")

        # Save the bot's state for later use
        bot.save("doc_expert.bot")
        ```
    """

    def __init__(
        self,
        api_key: Optional[str] = None,
        model_engine: Engines = Engines.CLAUDE4_SONNET,
        max_tokens: int = 32000,
        temperature: float = 0.3,
        name: str = "Claude",
        role: str = "assistant",
        role_description: str = "a friendly AI assistant",
        autosave: bool = True,
        enable_tracing: Optional[bool] = None,
        callbacks: Optional[BotCallbacks] = None,
    ):
        """Initialize an AnthropicBot.

        Args:
            api_key: Optional API key (will use ANTHROPIC_API_KEY env var if
            not provided)
            model_engine: The Anthropic model to use (default:
            CLAUDE37_SONNET_20250219)
            max_tokens: Maximum tokens per response (default: 32000)
            temperature: Response randomness, 0-1 (default: 0.3)
            name: Bot's name (default: 'Claude')
            role: Bot's role (default: 'assistant')
            role_description: Description of bot's role (default: 'a friendly
            AI assistant')
            autosave: Whether to autosave state after responses (default: True,
            saves to cwd)
            enable_tracing: Enable OpenTelemetry tracing (default: None, uses global setting)
            callbacks: Optional callback system for progress/monitoring (default: None)
        """
        super().__init__(
            api_key,
            model_engine,
            max_tokens,
            temperature,
            name,
            role,
            role_description,
            conversation=AnthropicNode._create_empty(AnthropicNode),
            tool_handler=AnthropicToolHandler(),
            mailbox=AnthropicMailbox(),
            autosave=autosave,
            enable_tracing=enable_tracing,
            callbacks=callbacks,
        )

        # Set bot reference in tool_handler so callbacks can be invoked
        self.tool_handler.bot = self


# class AnthropicTools:

#     def web_search():
#         """Returns the web search schema to be directly appended to the
#         tools block"""
#         return {
#             "type": "web_search_20250305",
#             "name": "web_search",
#             "max_uses": 10,
#         }

#     # def text_editor():
#     #     """Returns the text editor schema to be directly appended to the
#     #     tools block"""
#     #     return {
#     #         "type": "text_editor_20250429",
#     #         "name": "str_replace_based_edit_tool"
#     #     }


class CacheController:
    """Manages cache control directives in Anthropic message histories.

    This class handles the placement and management of cache control
    markers in the
    conversation history to optimize context window usage. It ensures
    that cache
    control directives are properly placed and don't interfere with
    tool operations.

    The controller maintains a balance between preserving important context and
    allowing older messages to be cached or dropped when the context
    window fills up.
    """

    def find_cache_control_positions(self, messages: List[Dict[str, Any]]) -> List[int]:
        """Find positions of all cache control directives in the message history.

        Args:
            messages: List of message dictionaries to search

        Returns:
            List of indices where cache control directives are found
        """
        positions = []
        for idx, msg in enumerate(messages):
            content = msg.get("content", None)
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and "cache_control" in item:
                        positions.append(idx)
                        break
            elif isinstance(content, dict) and "cache_control" in content:
                positions.append(idx)
            tool_calls = msg.get("tool_calls", None)
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict) and tool_call.get("cache_control"):
                        positions.append(idx)
                        break
        return sorted(list(set(positions)))

    def should_add_cache_control(
        self,
        total_messages: int,
        last_control_pos: int,
        threshold: float = 5.0,
    ) -> bool:
        """Determine if a new cache control directive should be added.

        Args:
            total_messages: Total number of messages in history
            last_control_pos: Position of the last cache control directive
            threshold: Growth factor for determining new control placement
            (default: 5.0)

        Returns:
            True if a new cache control directive should be added
        """
        required_length = last_control_pos * (1 + threshold)
        return total_messages >= math.ceil(required_length)

    def shift_cache_control_out_of_tool_block(self, messages: List[Dict[str, Any]], position: int) -> int:
        """Move cache control directives out of tool-related message blocks.

        Cache controls should not be placed within tool call or result
        blocks as this
        can interfere with tool operation. This method finds the nearest
        safe position
        to move the cache control directive to.

        Args:
            messages: List of messages to modify
            position: Current position of the cache control directive

        Returns:
            New position where the cache control directive was moved to
        """
        if position >= len(messages):
            return position
        msg = messages[position]
        content = msg.get("content", None)
        has_tool_block = False
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get("type") in [
                    "tool_call",
                    "tool_result",
                ]:
                    has_tool_block = True
                    break
        elif isinstance(content, dict) and content.get("type") in [
            "tool_call",
            "tool_result",
        ]:
            has_tool_block = True
        if has_tool_block:
            new_position = position + 1
            while new_position < len(messages):
                next_content = messages[new_position].get("content", None)
                is_tool = False
                if isinstance(next_content, list):
                    is_tool = any(
                        isinstance(item, dict) and item.get("type") in ["tool_call", "tool_result"] for item in next_content
                    )
                elif isinstance(next_content, dict):
                    is_tool = next_content.get("type") in [
                        "tool_call",
                        "tool_result",
                    ]
                if not is_tool:
                    self.remove_cache_control_at_position(messages, position)
                    self.insert_cache_control(messages, new_position)
                    return new_position
                new_position += 1
            new_position = position - 1
            while new_position >= 0:
                prev_content = messages[new_position].get("content", None)
                is_tool = False
                if isinstance(prev_content, list):
                    is_tool = any(
                        isinstance(item, dict) and item.get("type") in ["tool_call", "tool_result"] for item in prev_content
                    )
                elif isinstance(prev_content, dict):
                    is_tool = prev_content.get("type") in [
                        "tool_call",
                        "tool_result",
                    ]
                if not is_tool:
                    self.remove_cache_control_at_position(messages, position)
                    self.insert_cache_control(messages, new_position)
                    return new_position
                new_position -= 1
        return position

    def insert_cache_control(self, messages: List[Dict[str, Any]], position: int) -> None:
        """Insert a cache control directive at the specified position.

        Args:
            messages: List of messages to modify
            position: Position where the cache control should be inserted
        """
        if position < 0 or position > len(messages):
            position = len(messages) - 1
        msg = messages[position]
        content = msg.get("content", None)
        if isinstance(content, str):
            msg["content"] = [
                {
                    "type": "text",
                    "text": content,
                    "cache_control": {"type": "ephemeral"},
                }
            ]
        elif isinstance(content, list):
            if not any(("cache_control" in item for item in content if isinstance(item, dict))):
                for item in content:
                    if isinstance(item, dict) and "type" in item:
                        if item["type"] not in ["tool_call", "tool_result"]:
                            item["cache_control"] = {"type": "ephemeral"}
                            break
        elif isinstance(content, dict) and "cache_control" not in content:
            if content.get("type") not in ["tool_call", "tool_result"]:
                content["cache_control"] = {"type": "ephemeral"}
        tool_calls = msg.get("tool_calls", None)
        if tool_calls:
            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    tool_call.pop("cache_control", None)

    def remove_cache_control_at_position(self, messages: List[Dict[str, Any]], position: int) -> None:
        """Remove cache control directive at the specified position.

        Args:
            messages: List of messages to modify
            position: Position of the cache control to remove
        """
        if position < 0 or position >= len(messages):
            return
        msg = messages[position]
        content = msg.get("content", None)
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and "cache_control" in item:
                    del item["cache_control"]
        elif isinstance(content, dict) and "cache_control" in content:
            del content["cache_control"]
        tool_calls = msg.get("tool_calls", None)
        if tool_calls:
            for tool_call in tool_calls:
                if isinstance(tool_call, dict) and "cache_control" in tool_call:
                    del tool_call["cache_control"]

    def manage_cache_controls(self, messages: List[Dict[str, Any]], threshold: float = 5.0) -> List[Dict[str, Any]]:
        """Manage cache control directives across the entire message history.

        Use when you need to optimize the conversation context window by
        managing which
        parts of the conversation history can be cached or dropped.

        This method ensures proper placement and maintenance of cache control directives:
        - Prevents interference with tool operations
        - Limits the total number of cache controls

        Args:
            messages: List of messages to manage
            threshold: Growth factor for cache control placement (default: 5.0)

        Returns:
            Modified list of messages with properly managed cache controls
        """
        cache_control_positions = self.find_cache_control_positions(messages)
        if not cache_control_positions:
            initial_position = math.ceil(len(messages) * 0.75) - 1
            self.insert_cache_control(messages, initial_position)
            initial_position = self.shift_cache_control_out_of_tool_block(messages, initial_position)
            cache_control_positions = [initial_position]
        elif len(cache_control_positions) == 1:
            last_control_pos = cache_control_positions[0]
            new_pos = self.shift_cache_control_out_of_tool_block(messages, last_control_pos)
            if new_pos != last_control_pos:
                last_control_pos = new_pos
                cache_control_positions = [new_pos]
            if self.should_add_cache_control(len(messages), last_control_pos, threshold):
                new_position = math.ceil(len(messages) * threshold) - 1
                self.insert_cache_control(messages, new_position)
                new_position = self.shift_cache_control_out_of_tool_block(messages, new_position)
                cache_control_positions.append(new_position)
        else:
            updated_positions = []
            for pos in cache_control_positions:
                new_pos = self.shift_cache_control_out_of_tool_block(messages, pos)
                if new_pos not in updated_positions:
                    updated_positions.append(new_pos)
            cache_control_positions = sorted(updated_positions)
            last_control_pos = max(cache_control_positions)
            if self.should_add_cache_control(len(messages), last_control_pos, threshold):
                new_position = math.ceil(len(messages) * threshold) - 1
                self.insert_cache_control(messages, new_position)
                new_position = self.shift_cache_control_out_of_tool_block(messages, new_position)
                if cache_control_positions[0] != 0:
                    self.remove_cache_control_at_position(messages, cache_control_positions[0])
                    self.insert_cache_control(messages, 0)
                    self.shift_cache_control_out_of_tool_block(messages, 0)
                cache_control_positions = self.find_cache_control_positions(messages)
                if len(cache_control_positions) > 2:
                    for pos in cache_control_positions[2:]:
                        self.remove_cache_control_at_position(messages, pos)
        return messages
