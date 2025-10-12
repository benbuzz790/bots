import ast
import copy
import hashlib
import importlib
import inspect
import json
import logging
import os
import re
import sys
import textwrap
import types
from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
from types import ModuleType
from typing import Any, Callable, Dict, List, Optional, Tuple, Type

from bots.utils.helpers import _py_ast_to_source, formatted_datetime

# Module-level logger
logger = logging.getLogger(__name__)

# OpenTelemetry imports with graceful degradation
try:
    from bots.observability.tracing import get_default_tracing_preference, get_tracer, is_tracing_enabled

    tracer = get_tracer(__name__)
    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    tracer = None

    # Provide dummy functions if import fails
    def is_tracing_enabled():
        return False

    def get_default_tracing_preference():
        return False


# Import callbacks with graceful degradation
try:
    from bots.observability.callbacks import BotCallbacks

    CALLBACKS_AVAILABLE = True
except ImportError:
    CALLBACKS_AVAILABLE = False
    BotCallbacks = None

# Import metrics with graceful degradation
try:
    from bots.observability import metrics

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None


"""Core foundation classes for the bots framework.
This module provides the fundamental abstractions and base classes that power the bots framework:
- Bot: Abstract base class for all LLM implementations
- ToolHandler: Manages function/module tools with context preservation
- ConversationNode: Tree-based conversation storage
- Mailbox: Abstract interface for LLM service communication
- Engines: Supported LLM model configurations
The classes in this module are designed to:
- Provide a consistent interface across different LLM implementations
- Enable sophisticated context and tool management
- Support complete bot portability and state preservation
- Handle conversation branching and context management efficiently
Example:
    `python
    from bots import AnthropicBot
    import my_tools
    # Create a bot with tools
    bot = AnthropicBot()
    bot.add_tools(my_tools)
    # Basic interaction
    response = bot.respond("Hello!")
    # Save bot state
    bot.save("my_bot.bot")
    `
"""


def load(filepath: str) -> "Bot":
    """Load a saved bot from a file.

    Use when you need to restore a previously saved bot with its complete state,
    including conversation history, tools, and configuration.

    Parameters:
        filepath (str): Path to the .bot file containing the saved bot state

    Returns:
        Bot: A reconstructed Bot instance with the saved state

    Example:
        ```python
        bot = bots.load("my_saved_bot.bot")
        bot.respond("Continue our previous conversation")
        ```
    """
    return Bot.load(filepath)


class Engines(str, Enum):
    """Enum class representing different AI model engines."""

    GPT4 = "gpt-4"
    GPT41 = "gpt-4.1"
    GPT4_0613 = "gpt-4-0613"
    GPT4_32K = "gpt-4-32k"
    GPT4_32K_0613 = "gpt-4-32k-0613"
    GPT35TURBO = "gpt-3.5-turbo"
    GPT35TURBO_16K = "gpt-3.5-turbo-16k"
    GPT35TURBO_0125 = "gpt-3.5-turbo-0125"
    GPT35TURBO_INSTRUCT = "gpt-3.5-turbo-instruct"
    CLAUDE3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE35_HAIKU = "claude-3-5-haiku-latest"
    CLAUDE37_SONNET_20250219 = "claude-3-7-sonnet-latest"
    CLAUDE4_OPUS = "claude-opus-4-20250514"
    CLAUDE41_OPUS = "claude-opus-4-1"
    CLAUDE4_SONNET = "claude-sonnet-4-20250514"
    CLAUDE45_SONNET = "claude-sonnet-4-5-20250929"
    GEMINI25_FLASH = "gemini-2.5-flash"

    @staticmethod
    def get(name: str) -> Optional["Engines"]:
        """Retrieve an Engines enum member by its string value.

        Use when you need to convert a model name string to an Engines enum member.

        Parameters:
            name (str): The string value of the engine (e.g., 'gpt-4', 'claude-3-opus-20240229')

        Returns:
            Optional[Engines]: The corresponding Engines enum member, or None if not found

        Example:
            ```python
            engine = Engines.get('gpt-4')
            if engine:
                bot = Bot(model_engine=engine)
            ```
        """
        for engine in Engines:
            if engine.value == name:
                return engine
        return None

    @staticmethod
    def get_bot_class(model_engine: "Engines") -> Type["Bot"]:
        """Get the appropriate Bot subclass for a given model engine.

        Use when you need to programmatically determine which Bot implementation
        to use for a specific model engine.

        Parameters:
            model_engine (Engines): The engine enum member to get the bot class for

        Returns:
            Type[Bot]: The Bot subclass (ChatGPT_Bot or AnthropicBot)

        Raises:
            ValueError: If the model engine is not supported

        Example:
            ```python
            bot_class = Engines.get_bot_class(Engines.GPT4)
            bot = bot_class(api_key="key")
            ```
        """
        from bots.foundation.anthropic_bots import AnthropicBot
        from bots.foundation.gemini_bots import GeminiBot
        from bots.foundation.openai_bots import ChatGPT_Bot

        if model_engine.value.startswith("gpt"):
            return ChatGPT_Bot
        elif model_engine.value.startswith("claude"):
            return AnthropicBot
        elif model_engine.value.startswith("gemini"):
            return GeminiBot
        else:
            raise ValueError(f"Unsupported model engine: {model_engine}")

    @staticmethod
    def get_conversation_node_class(class_name: str) -> Type["ConversationNode"]:
        """Get the appropriate ConversationNode subclass by name.

        Use when you need to reconstruct conversation nodes from saved bot state.

        Parameters:
            class_name (str): Name of the node class ('OpenAINode', 'AnthropicNode', or 'GeminiNode')

        Returns:
            Type[ConversationNode]: The ConversationNode subclass

        Raises:
            ValueError: If the class name is not a supported node type
        """
        from bots.foundation.anthropic_bots import AnthropicNode
        from bots.foundation.gemini_bots import GeminiNode
        from bots.foundation.openai_bots import OpenAINode

        NODE_CLASS_MAP = {"OpenAINode": OpenAINode, "AnthropicNode": AnthropicNode, "GeminiNode": GeminiNode}

        # Support MockConversationNode for testing
        if class_name == "MockConversationNode":
            try:
                from bots.testing.mock_bot import MockConversationNode

                return MockConversationNode
            except ImportError:
                pass  # Fall through to error

        node_class = NODE_CLASS_MAP.get(class_name)
        if node_class is None:
            raise ValueError(f"Unsupported conversation node type: {class_name}")
        return node_class


class ConversationNode:
    """Tree-based storage for conversation history and tool interactions.

    ConversationNode implements a linked tree structure that enables sophisticated
    conversation management, including branching conversations and tool usage tracking.
    Each node represents a message in the conversation and can have multiple replies,
    forming a tree structure.

    Attributes:
        role (str): The role of the message sender ('user', 'assistant', etc.)
        content (str): The message content
        parent (ConversationNode): Reference to the parent node
        replies (List[ConversationNode]): List of reply nodes
        tool_calls (List[Dict]): Tool invocations made in this message
        tool_results (List[Dict]): Results from tool executions
        pending_results (List[Dict]): Tool results waiting to be processed

    Example:
        ```python
        # Create a conversation tree
        root = ConversationNode(role='user', content='Hello')
        response = root._add_reply(role='assistant', content='Hi there!')
        ```
    """

    def __init__(
        self,
        content: str,
        role: str,
        tool_calls: Optional[List[Dict]] = None,
        tool_results: Optional[List[Dict]] = None,
        pending_results: Optional[List[Dict]] = None,
        **kwargs,
    ) -> None:
        """Initialize a new ConversationNode.

        Args:
        content (str): The message content
        role (str): The role of the message sender
        tool_calls (Optional[List[Dict]]): Tool invocations made in this message
        tool_results (Optional[List[Dict]]): Results from tool executions
        pending_results (Optional[List[Dict]]): Tool results waiting to be processed
        **kwargs: Additional attributes to set on the node
        """
        self.content = content
        self.role = role
        self.parent: ConversationNode = None
        self.replies: list[ConversationNode] = []
        self.tool_calls = tool_calls or []
        self._tool_results = tool_results or []
        self.pending_results = pending_results or []
        for key, value in kwargs.items():
            setattr(self, key, value)

    @property
    def tool_results(self):
        """Get tool results."""
        return self._tool_results

    @tool_results.setter
    def tool_results(self, value):
        """Set tool results with validation."""
        validation_errors = []
        if value is not None and (not isinstance(value, list)):
            validation_errors.append(f"tool_results must be a list, got {type(value)}")
        if isinstance(value, list):
            for i, result in enumerate(value):
                if not isinstance(result, dict):
                    validation_errors.append(f"tool_results[{i}] must be a dict, got {type(result)}")
                    continue
                # Check for either tool_use_id (Anthropic) or tool_call_id (OpenAI) or role (OpenAI tool messages)
                has_id = "tool_use_id" in result or "tool_call_id" in result or result.get("role") == "tool"
                if not has_id:
                    validation_errors.append(f"tool_results[{i}] missing required key 'tool_use_id' or 'tool_call_id'")
                # Only validate tool_use_id format if it exists (Anthropic-specific)
                if "tool_use_id" in result and not isinstance(result["tool_use_id"], str):
                    validation_errors.append(
                        f"tool_results[{i}]['tool_use_id'] must be a string, got {type(result['tool_use_id'])}"
                    )
                if "content" not in result:
                    validation_errors.append(f"tool_results[{i}] missing required key 'content'")
            if value:
                tool_use_ids = [r.get("tool_use_id") for r in value if isinstance(r, dict) and "tool_use_id" in r]
                if len(tool_use_ids) != len(set(tool_use_ids)):
                    validation_errors.append("Duplicate tool_use_ids found in tool_results")
        # Relax the role validation - only enforce for Anthropic (which uses tool_use_id)
        if value and self.role != "user":
            # Check if these are Anthropic-style results (have tool_use_id)
            has_anthropic_style = any(isinstance(r, dict) and "tool_use_id" in r for r in value)
            if has_anthropic_style:
                validation_errors.append(
                    f"tool_results should only be set on user role nodes, but this node has role '{self.role}'"
                )

        if validation_errors:
            raise ValueError(f"Invalid tool_results: {'; '.join(validation_errors)}")

        self._tool_results = value or []

    @staticmethod
    def _create_empty(cls: Optional[Type["ConversationNode"]] = None) -> "ConversationNode":
        """Create an empty root node.

        Use when initializing a new conversation tree that needs an empty root.

        Parameters:
            cls (Optional[Type[ConversationNode]]): Optional specific node class to use

        Returns:
            ConversationNode: An empty node with role='empty' and no content
        """
        if cls:
            return cls(role="empty", content="")
        return ConversationNode(role="empty", content="")

    def _is_empty(self) -> bool:
        """Check if this is an empty root node.

        Returns:
            bool: True if this is an empty root node, False otherwise
        """
        return self.role == "empty" and self.content == ""

    def _add_reply(self, **kwargs) -> "ConversationNode":
        """Add a new reply node to this conversation node.

        Creates a new node as a child of this one, handling tool context
        synchronization between siblings.

        Returns:
            ConversationNode: The newly created reply node

        Example:
            ```python
            node = root._add_reply(content="Hello", role="user")
            response = node._add_reply(content="Hi!", role="assistant")
            ```
        """
        reply = type(self)(**kwargs)
        reply.parent = self
        self.replies.append(reply)
        if self.pending_results:
            reply.tool_results.extend(self.pending_results)
            self.pending_results = []
        return reply

    def _sync_tool_context(self) -> None:
        """Synchronize tool results across all sibling nodes of self.

        Use when tool results need to be shared between parallel conversation branches.
        Takes the union of all tool results from sibling nodes and ensures each sibling
        has access to all results.

        Side Effects:
            Updates tool_results for all sibling nodes to include all unique results.
        """
        if self.role != "user":
            return
        if not self.parent or self.parent.role != "assistant":
            return
        if not self.parent.tool_calls:
            return
        if self.parent and self.parent.replies:
            tool_results_dict = {}
            siblings = [node for node in self.parent.replies if node != self] + [self]
            for node in siblings:
                for result in node.tool_results:
                    result_str = str(sorted(result.items()))
                    tool_id = hashlib.md5(result_str.encode()).hexdigest()
                    tool_results_dict[tool_id] = result
            all_tool_results = list(tool_results_dict.values())
            for sibling in self.parent.replies:
                sibling.tool_results = all_tool_results.copy()

    def _add_tool_calls(self, calls: List[Dict[str, Any]]) -> None:
        """Add tool call records to this node.

        Use when new tool calls are made during the conversation.

        Parameters:
            calls (List[Dict[str, Any]]): List of tool call records to add
        """
        self.tool_calls.extend(calls)

    def _add_tool_results(self, results: List[Dict[str, Any]]) -> None:
        """Add tool execution results to this node.

        Use when tool execution results are received and need to be recorded.
        Automatically synchronizes results with sibling nodes.

        Parameters:
            results (List[Dict[str, Any]]): List of tool result records to add

        Side Effects:
            - Updates this node's tool_results
            - Synchronizes results across sibling nodes
        """

        def make_hash(result):
            """Create hash of result for deduplication."""
            result_str = str(sorted(result.items()))
            return hashlib.md5(result_str.encode()).hexdigest()

        existing_dict = {make_hash(r): r for r in self.tool_results}
        new_dict = {make_hash(r): r for r in results}
        merged_dict = {**existing_dict, **new_dict}
        self.tool_results = list(merged_dict.values())
        self._sync_tool_context()

    def _find_root(self) -> "ConversationNode":
        """Navigate to the root node of the conversation tree.

        Use when you need to access the starting point of the conversation.

        Returns:
            ConversationNode: The root node of the conversation tree
        """
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def _root_dict(self) -> Dict[str, Any]:
        """Convert the entire conversation tree to a dictionary.

        Use when serializing the complete conversation for saving or transmission.
        Starts from the root node and includes all branches.

        Returns:
            Dict[str, Any]: Dictionary representation of the complete conversation tree
        """
        root = self._find_root()
        return root._to_dict_recursive()

    def _to_dict_recursive(self) -> Dict[str, Any]:
        """Recursively convert this node and all its replies to a dictionary.

        Use when you need to serialize a subtree of the conversation.

        Returns:
            Dict[str, Any]: Dictionary containing this node and all its descendants
        """
        result = self._to_dict_self()
        if self.replies:
            result["replies"] = [reply._to_dict_recursive() for reply in self.replies]
        return result

    def _to_dict_self(self) -> Dict[str, Any]:
        """Convert just this node to a dictionary.

        Use when serializing a single conversation node.
        Omits replies, parent references, and callable attributes.

        Returns:
            Dict[str, Any]: Dictionary containing this node's attributes

        Note:
            Only serializes basic types (str, int, float, bool, list, dict)
            and converts other types to strings.
        """
        result = {}
        for k in dir(self):
            if not k.startswith("_") and k not in {"parent", "replies"} and (not callable(getattr(self, k))):
                value = getattr(self, k)
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    result[k] = value
                else:
                    result[k] = str(value)
        result["node_class"] = self.__class__.__name__
        return result

    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build a chronological list of messages from root to this node.

        Use when you need to construct the conversation history for an LLM API call.
        Includes tool calls and results in each message where present.

        Returns:
            List[Dict[str, Any]]: List of message dictionaries, each containing:
                - role: The message sender's role
                - content: The message text
                - tool_calls: (optional) List of tool calls made
                - tool_results: (optional) List of tool execution results

        Note:
            Empty root nodes are excluded from the message list.
        """
        node = self
        if node._is_empty():
            return []
        conversation_list_dict = []
        while node:
            if not node._is_empty():
                entry = {"role": node.role, "content": node.content}
                if node.tool_calls is not None:
                    entry["tool_calls"] = node.tool_calls
                if node.tool_results is not None:
                    entry["tool_results"] = node.tool_results
                conversation_list_dict = [entry] + conversation_list_dict
            node = node.parent
        return conversation_list_dict

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> "ConversationNode":
        reply_data = data.pop("replies", [])
        node_class = Engines.get_conversation_node_class(data.pop("node_class", cls.__name__))
        node = node_class(**data)
        for reply in reply_data:
            reply_node = cls._from_dict(reply)
            reply_node.parent = node
            node.replies.append(reply_node)
        return node

    def _node_count(self) -> int:
        """Count the total number of nodes in the conversation tree.

        Use when you need to measure the size of the conversation.
        Counts from the root node down through all branches.

        Returns:
            int: Total number of nodes in the conversation tree

        Example:
            ```python
            total_messages = node._node_count()
            print(f"This conversation has {total_messages} messages")
            ```
        """
        root = self._find_root()

        def count_recursive(current_node):
            count = 1
            for reply in current_node.replies:
                count += count_recursive(reply)
            return count

        return count_recursive(root)


@dataclass
class ModuleContext:
    """Context container for module-level tool preservation.

    Stores all necessary information to reconstruct a module and its tools,
    including source code, namespace, and execution environment.

    Attributes:
        name (str): The module's name
        source (str): The module's complete source code
        file_path (str): Original file path or generated path for dynamic modules
        namespace (ModuleType): The module's execution namespace
        code_hash (str): Hash of the source code for version checking
    """

    name: str
    source: str
    file_path: str
    namespace: ModuleType
    code_hash: str


class ToolHandlerError(Exception):
    """Base exception class for ToolHandler errors.

    Use as a base class for all tool-related exceptions to allow
    specific error handling for tool operations.
    """

    pass


class ToolNotFoundError(ToolHandlerError):
    """Raised when a requested tool is not available.

    Use when attempting to use a tool that hasn't been registered
    with the ToolHandler.
    """

    pass


class ModuleLoadError(ToolHandlerError):
    """Raised when a module cannot be loaded for tool extraction.

    Use when there are issues loading a module's source code,
    executing it in a new namespace, or extracting its tools.
    """

    pass


class ToolHandler(ABC):
    """Abstract base class for managing bot tool operations.

    ToolHandler provides a complete system for:
    - Registering Python functions as bot tools
    - Preserving tool context and dependencies
    - Managing tool execution and results
    - Serializing and deserializing tool state

    The class supports both individual function tools and complete module imports,
    preserving all necessary context for tool operation across bot save/load cycles.

    Attributes:
        tools (List[Dict[str, Any]]): Registered tool schemas
        function_map (Dict[str, Callable]): Mapping of tool names to functions
        requests (List[Dict[str, Any]]): Pending tool execution requests
        results (List[Dict[str, Any]]): Results from tool executions
        modules (Dict[str, ModuleContext]): Module contexts for imported tools

    Example:
        ```python
        class MyToolHandler(ToolHandler):
            # Implement abstract methods...
            pass

        handler = MyToolHandler()
        handler.add_tools(my_module)
        ```
    """

    def __init__(self):
        self.tools: List[Dict[str, Any]] = []
        self.function_map: Dict[str, Callable] = {}
        self.requests: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.modules: Dict[str, ModuleContext] = {}

    @staticmethod
    def _clean_decorator_source(source):
        """Clean decorator source by parsing the source file and extracting the
        decorator function."""
        frame = inspect.currentframe()
        try:
            while frame:
                frame_info = inspect.getframeinfo(frame)
                if frame_info.filename.endswith(".py") and "test_" in frame_info.filename:
                    test_file = frame_info.filename
                    try:
                        with open(test_file, "r", encoding="utf-8") as f:
                            file_content = f.read()
                        tree = ast.parse(file_content)
                        source_lines = source.strip().split("\n")
                        decorator_name = None
                        for line in source_lines:
                            if line.strip().startswith("def ") and "(" in line:
                                func_line = line.strip()
                                decorator_name = func_line[4 : func_line.index("(")].strip()
                                break
                        if decorator_name:
                            for node in ast.walk(tree):
                                if isinstance(node, ast.FunctionDef) and node.name == decorator_name:
                                    cleaned = _py_ast_to_source(node)
                                    return cleaned
                    except Exception:
                        break
                frame = frame.f_back
        finally:
            del frame
        cleaned = textwrap.dedent(source).strip()
        return cleaned

    @staticmethod
    def _clean_function_source(source):
        """Clean function source using AST parsing and regeneration."""
        try:
            tree = ast.parse(source)
            cleaned = _py_ast_to_source(tree)
            return cleaned
        except SyntaxError:
            import textwrap

            cleaned = textwrap.dedent(source).strip()
            return cleaned

    @abstractmethod
    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate the tool schema for the bot's api. Must be implemented per provider.

        Use to create a consistent tool description that the LLM can understand.
        Must extract relevant information from the function's signature and docstring.

        Parameters:
            func (Callable): The function to generate a schema for

        Returns:
            Dict[str, Any]: Schema describing the tool's:
                - name and description
                - parameters and their types
                - return value format
                - usage instructions

        Example Schema:
            {
                "name": "calculate_area",
                "description": "Calculate the area of a circle",
                "parameters": {
                    "radius": {"type": "float", "description": "Circle radius"}
                },
                "returns": "float: The calculated area"
            }
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool requests from an LLM response. Must be implemented per provider.

        Use to parse the LLM's response and identify any tool usage requests.
        Multiple tool requests may be present in a single response.

        Parameters:
            response (Any): Raw response from the LLM service

        Returns:
            List[Dict[str, Any]]: List of parsed tool request schemas, each containing:
                - Specific requirements per provider

        Example:
            ```python
            response = llm_service.get_response()
            requests = handler.generate_request_schema(response)
            # [{"name": "view_file", "parameters": {"path": "main.py"}}, ...]
            ```
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """Extract tool name and parameters from a request schema. Must be implemented per provider.

        Use to parse a tool request into components that can be used for execution.
        Validates and prepares the input parameters for the tool function.

        Parameters:
            request_schema (Dict[str, Any]): The request schema to parse

        Returns:
            Tuple[Optional[str], Dict[str, Any]]:
                - Tool name (or None if request should be skipped)
                - Dictionary of prepared input parameters

        Example:
            ```python
            name, params = handler.tool_name_and_input({
                "name": "calculate_area",
                "parameters": {"radius": "5.0"}
            })
            if name:
                result = handler.function_map[name](**params)
            ```
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Generate a response schema from tool execution results. Must be implemented per provider.

        Use to format tool output in a way the LLM can understand and process.
        Maintains connection between request and response through request metadata.

        Parameters:
            request (Dict[str, Any]): The original request schema
            tool_output_kwargs (Dict[str, Any]): The tool's execution results

        Returns:
            Dict[str, Any]: Formatted response schema containing:
                - Specific Schema for provider

        Example:
            ```python
            result = tool_func(**params)
            response = handler.generate_response_schema(request, result)
            # {"tool_name": "view_file", "status": "success", "content": "file contents..."}
            ```
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def generate_error_schema(self, request_schema: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """Generate an error response schema. Must be implemented per provider.

        Use to format error messages in a way the LLM can understand and handle appropriately.
        Should maintain consistency with successful response schemas.

        Parameters:
            request_schema (Dict[str, Any]): The request that caused the error
            error_msg (str): The error message to include

        Returns:
            Dict[str, Any]: Error response schema containing:
                - Required schema per provider

        Example:
            ```python
            try:
                result = tool_func(**params)
            except Exception as e:
                error = handler.generate_error_schema(request, str(e))
                # {"status": "error", "message": "File not found", "type": "FileNotFoundError"}
            ```
        """

    def extract_requests(self, response: Any) -> List[Dict[str, Any]]:
        """Extract and parse tool requests from an LLM response.

        Use when you need to identify and process tool usage requests
        from a raw LLM response.

        Parameters:
            response (Any): The raw response from the LLM service

        Returns:
            List[Dict[str, Any]]: List of parsed request schemas

        Side Effects:
            - Clears existing self.requests
            - Sets self.requests to the newly parsed requests

        Example:
            ```python
            requests = handler.extract_requests(llm_response)
            # [{"name": "view_file", "parameters": {...}}, ...]
            ```
        """
        self.requests = self.generate_request_schema(response)
        return self.requests

    def exec_requests(self) -> List[Dict[str, Any]]:
        """Execute pending tool requests and generate results.

        Use when you need to process all pending tool requests that have been
        extracted from an LLM response. Handles execution, error handling,
        and result formatting.

        Returns:
            List[Dict[str, Any]]: List of result schemas, each containing:
                - Tool execution results or error information
                - Status of the execution
                - Any relevant metadata

        Side Effects:
            - Executes tool functions with provided parameters
            - Updates self.results with execution results
            - May produce tool-specific side effects (file operations, etc.)

        Raises:
            ToolNotFoundError: If a requested tool is not available
            TypeError: If tool arguments are invalid
            Exception: For other tool execution errors

        Example:
            ```python
            handler.extract_requests(response)
            results = handler.exec_requests()
            # [{"status": "success", "content": "file contents..."}, ...]
            ```
        """
        results = []
        requests = self.requests

        # Check if tracing is available and enabled
        if TRACING_AVAILABLE and tracer:
            with tracer.start_as_current_span("tools.execute_all") as span:
                span.set_attribute("tool.count", len(requests))
                for request_schema in requests:
                    tool_name, input_kwargs = self.tool_name_and_input(request_schema)
                    if tool_name is None:
                        continue

                    with tracer.start_as_current_span(f"tool.{tool_name}") as tool_span:
                        tool_span.set_attribute("tool.name", tool_name)

                        # Invoke on_tool_start callback
                        if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                            try:
                                self.bot.callbacks.on_tool_start(
                                    tool_name, metadata={"request": request_schema, "tool_args": input_kwargs}
                                )
                            except Exception:
                                pass

                        import time

                        tool_start_time = time.time()

                        try:
                            if tool_name not in self.function_map:
                                raise ToolNotFoundError(f"Tool '{tool_name}' not found in function map")
                            func = self.function_map[tool_name]
                            output_kwargs = func(**input_kwargs)
                            response_schema = self.generate_response_schema(request_schema, output_kwargs)

                            # Record metrics for successful tool execution
                            tool_duration = time.time() - tool_start_time
                            if METRICS_AVAILABLE and metrics:
                                try:
                                    metrics.record_tool_execution(tool_duration, tool_name, success=True)
                                except Exception:
                                    pass

                            # Invoke on_tool_complete callback
                            if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                                try:
                                    self.bot.callbacks.on_tool_complete(
                                        tool_name, output_kwargs, metadata={"duration": tool_duration}
                                    )
                                except Exception:
                                    pass

                            tool_span.set_attribute("tool.status", "success")
                            if isinstance(output_kwargs, str):
                                tool_span.set_attribute("tool.result_length", len(output_kwargs))
                        except ToolNotFoundError as e:
                            error_msg = "Error: Tool not found.\n\n" + str(e)
                            response_schema = self.generate_error_schema(request_schema, error_msg)

                            # Record error metrics
                            tool_duration = time.time() - tool_start_time
                            if METRICS_AVAILABLE and metrics:
                                try:
                                    metrics.record_tool_execution(tool_duration, tool_name, success=False)
                                    metrics.record_tool_failure(tool_name, "ToolNotFoundError")
                                except Exception:
                                    pass

                            # Invoke on_tool_error callback
                            if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                                try:
                                    self.bot.callbacks.on_tool_error(tool_name, e, metadata={"duration": tool_duration})
                                except Exception:
                                    pass

                            tool_span.set_attribute("tool.status", "error")
                            tool_span.set_attribute("tool.error_type", "ToolNotFoundError")
                            tool_span.record_exception(e)
                        except TypeError as e:
                            error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
                            response_schema = self.generate_error_schema(request_schema, error_msg)

                            # Record error metrics
                            tool_duration = time.time() - tool_start_time
                            if METRICS_AVAILABLE and metrics:
                                try:
                                    metrics.record_tool_execution(tool_duration, tool_name, success=False)
                                    metrics.record_tool_failure(tool_name, "TypeError")
                                except Exception:
                                    pass

                            # Invoke on_tool_error callback
                            if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                                try:
                                    self.bot.callbacks.on_tool_error(tool_name, e, metadata={"duration": tool_duration})
                                except Exception:
                                    pass

                            tool_span.set_attribute("tool.status", "error")
                            tool_span.set_attribute("tool.error_type", "TypeError")
                            tool_span.record_exception(e)
                        except Exception as e:
                            error_msg = f"Unexpected error while executing tool '{tool_name}': {str(e)}"
                            response_schema = self.generate_error_schema(request_schema, error_msg)

                            # Record error metrics
                            tool_duration = time.time() - tool_start_time
                            if METRICS_AVAILABLE and metrics:
                                try:
                                    metrics.record_tool_execution(tool_duration, tool_name, success=False)
                                    metrics.record_tool_failure(tool_name, type(e).__name__)
                                except Exception:
                                    pass

                            # Invoke on_tool_error callback
                            if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                                try:
                                    self.bot.callbacks.on_tool_error(tool_name, e, metadata={"duration": tool_duration})
                                except Exception:
                                    pass

                            tool_span.set_attribute("tool.status", "error")
                            tool_span.set_attribute("tool.error_type", type(e).__name__)
                            tool_span.record_exception(e)

                        results.append(response_schema)

                self.results = results
                return results
        else:
            # Non-tracing path
            for request_schema in requests:
                tool_name, input_kwargs = self.tool_name_and_input(request_schema)
                if tool_name is None:
                    continue

                # Invoke on_tool_start callback
                if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                    try:
                        self.bot.callbacks.on_tool_start(
                            tool_name, metadata={"request": request_schema, "tool_args": input_kwargs}
                        )
                    except Exception:
                        pass

                import time

                tool_start_time = time.time()

                try:
                    if tool_name not in self.function_map:
                        raise ToolNotFoundError(f"Tool '{tool_name}' not found in function map")
                    func = self.function_map[tool_name]
                    output_kwargs = func(**input_kwargs)
                    response_schema = self.generate_response_schema(request_schema, output_kwargs)

                    # Record metrics for successful tool execution
                    tool_duration = time.time() - tool_start_time
                    if METRICS_AVAILABLE and metrics:
                        try:
                            metrics.record_tool_execution(tool_duration, tool_name, success=True)
                        except Exception:
                            pass

                    # Invoke on_tool_complete callback
                    if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                        try:
                            self.bot.callbacks.on_tool_complete(tool_name, output_kwargs, metadata={"duration": tool_duration})
                        except Exception:
                            pass

                except ToolNotFoundError as e:
                    error_msg = "Error: Tool not found.\n\n" + str(e)
                    response_schema = self.generate_error_schema(request_schema, error_msg)

                    # Record error metrics
                    tool_duration = time.time() - tool_start_time
                    if METRICS_AVAILABLE and metrics:
                        try:
                            metrics.record_tool_execution(tool_duration, tool_name, success=False)
                            metrics.record_tool_failure(tool_name, "ToolNotFoundError")
                        except Exception:
                            pass

                    # Invoke on_tool_error callback
                    if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                        try:
                            self.bot.callbacks.on_tool_error(tool_name, e, metadata={"duration": tool_duration})
                        except Exception:
                            pass

                except TypeError as e:
                    error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
                    response_schema = self.generate_error_schema(request_schema, error_msg)

                    # Record error metrics
                    tool_duration = time.time() - tool_start_time
                    if METRICS_AVAILABLE and metrics:
                        try:
                            metrics.record_tool_execution(tool_duration, tool_name, success=False)
                            metrics.record_tool_failure(tool_name, "TypeError")
                        except Exception:
                            pass

                    # Invoke on_tool_error callback
                    if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                        try:
                            self.bot.callbacks.on_tool_error(tool_name, e, metadata={"duration": tool_duration})
                        except Exception:
                            pass

                except Exception as e:
                    error_msg = f"Unexpected error while executing tool '{tool_name}': {str(e)}"
                    response_schema = self.generate_error_schema(request_schema, error_msg)

                    # Record error metrics
                    tool_duration = time.time() - tool_start_time
                    if METRICS_AVAILABLE and metrics:
                        try:
                            metrics.record_tool_execution(tool_duration, tool_name, success=False)
                            metrics.record_tool_failure(tool_name, type(e).__name__)
                        except Exception:
                            pass

                    # Invoke on_tool_error callback
                    if hasattr(self, "bot") and self.bot and hasattr(self.bot, "callbacks") and self.bot.callbacks:
                        try:
                            self.bot.callbacks.on_tool_error(tool_name, e, metadata={"duration": tool_duration})
                        except Exception:
                            pass

                results.append(response_schema)

            self.results = results
            return results

    def _create_builtin_wrapper(self, func: Callable) -> str:
        """Create a wrapper function source code for built-in functions.

        Use when adding built-in Python functions as tools. Creates a wrapper
        that maintains proper type handling and module context.

        Parameters:
            func (Callable): The built-in function to wrap

        Returns:
            str: Source code for the wrapper function

        Note:
            - Automatically handles float conversion for numeric functions
            - Preserves original module context
            - Maintains function name and basic documentation
        """
        source = (
            f"def {func.__name__}(x):\n"
            f'    """Wrapper for built-in function {func.__name__} from {func.__module__}"""\n'
            f"    import {func.__module__}\n"
            f"    return {func.__module__}.{func.__name__}(float(x))\n"
        )
        return source

    def _create_dynamic_wrapper(self, func: Callable) -> str:
        """Create a wrapper function source code for dynamic or lambda functions.

        Use when adding functions that don't have accessible source code or
        are dynamically created.

        Parameters:
            func (Callable): The function to create a wrapper for

        Returns:
            str: Source code for the wrapper function

        Note:
            - Preserves function signature if available
            - Copies docstring if present
            - Creates self-contained implementation
            - Handles both normal and dynamic functions
        """
        import inspect

        # Get function signature
        sig = inspect.signature(func)

        # Create function header
        source = f"def {func.__name__}{sig}:\n"

        # Add docstring if present
        if func.__doc__:
            source += f'    """{func.__doc__}"""\n'

        # Try to reconstruct the function body
        if hasattr(func, "__code__"):
            try:
                # Try to get original source first
                body = inspect.getsource(func).split("\n", 1)[1]
                source += body
            except Exception:
                # If we can't get source, create a simple implementation
                # that raises an informative error
                # Create a wrapper that will be restored from serialized data during load
                # This wrapper will be replaced with the actual function when the bot is loaded
                source += f"    # Dynamic function {func.__name__} - will be restored from serialized data\n"
                source += f'    # Original signature: {inspect.signature(func) if hasattr(func, "__code__") else "unknown"}\n'
                source += (
                    f"    raise NotImplementedError(\"Dynamic function '{func.__name__}' not yet restored from save data\")\n"
                )
        else:
            source += "    pass\n"

        return source

    def _extract_annotation_names(self, source_code: str) -> set:
        """Extract all names used in type annotations from source code."""
        import ast
        import re

        annotation_names = set()
        try:
            tree = ast.parse(source_code)
            for node in ast.walk(tree):
                if isinstance(node, ast.FunctionDef):
                    for arg in node.args.args:
                        if arg.annotation:
                            annotation_names.update(self._extract_names_from_ast_node(arg.annotation))
                    if node.returns:
                        annotation_names.update(self._extract_names_from_ast_node(node.returns))
                elif isinstance(node, ast.AnnAssign):
                    if node.annotation:
                        annotation_names.update(self._extract_names_from_ast_node(node.annotation))
        except SyntaxError:
            patterns = [
                ":\\s*([A-Za-z_][A-Za-z0-9_]*)",
                "->\\s*([A-Za-z_][A-Za-z0-9_]*)",
                "\\[\\s*([A-Za-z_][A-Za-z0-9_]*)",
                ",\\s*([A-Za-z_][A-Za-z0-9_]*)",
            ]
            for pattern in patterns:
                matches = re.findall(pattern, source_code)
                annotation_names.update(matches)
        return annotation_names

    def _extract_names_from_ast_node(self, node) -> set:
        """Extract all names from an AST annotation node."""
        names = set()
        if isinstance(node, ast.Name):
            names.add(node.id)
        elif isinstance(node, ast.Attribute):
            if isinstance(node.value, ast.Name):
                names.add(node.value.id)
        elif isinstance(node, ast.Subscript):
            names.update(self._extract_names_from_ast_node(node.value))
            if isinstance(node.slice, ast.Tuple):
                for elt in node.slice.elts:
                    names.update(self._extract_names_from_ast_node(elt))
            else:
                names.update(self._extract_names_from_ast_node(node.slice))
        elif hasattr(node, "elts"):
            for elt in node.elts:
                names.update(self._extract_names_from_ast_node(elt))
        return names

    def _capture_annotation_context(self, func: Callable, context: dict) -> None:
        """Capture all objects referenced in function annotations."""
        if not hasattr(func, "__globals__"):
            return
        try:
            source = inspect.getsource(func)
            annotation_names = self._extract_annotation_names(source)
            for name in annotation_names:
                if name in func.__globals__:
                    context[name] = func.__globals__[name]
        except (TypeError, OSError):
            if hasattr(func, "__annotations__") and func.__annotations__:
                for annotation in func.__annotations__.values():
                    if hasattr(annotation, "__name__"):
                        name = annotation.__name__
                        if name in func.__globals__:
                            context[name] = func.__globals__[name]

    def _build_function_context(self, func: Callable) -> dict:
        """Build the execution context for a function by capturing all necessary dependencies."""
        code = func.__code__
        names = code.co_names
        context = {name: func.__globals__[name] for name in names if name in func.__globals__}
        self._capture_annotation_context(func, context)
        for name, value in func.__globals__.items():
            if not name.startswith("__"):
                context[name] = value
        context = self._merge_with_original_module(func, context)
        for name, value in func.__globals__.items():
            if isinstance(value, types.ModuleType) or callable(value):
                context[name] = value
        return context

    def _merge_with_original_module(self, func: Callable, context: dict) -> dict:
        """Merge function context with its original module namespace."""
        import importlib

        try:
            original_module = importlib.import_module(func.__module__)
            for name, value in original_module.__dict__.items():
                if not name.startswith("__"):
                    context[name] = value
        except ImportError:
            pass
        try:
            original_module = importlib.import_module(func.__module__)
            for name, value in original_module.__dict__.items():
                if not name.startswith("__") and name not in context:
                    if callable(value) or isinstance(value, type):
                        context[name] = value
        except ImportError:
            pass
        return context

    def _capture_helper_functions(self, func: Callable, source: str, context: dict) -> str:
        """Capture helper functions that the main function depends on."""
        helper_functions_source = []
        try:
            import ast

            tree = ast.parse(source)
            function_calls = set()
            for node in ast.walk(tree):
                if isinstance(node, ast.Call):
                    if isinstance(node.func, ast.Name):
                        function_calls.add(node.func.id)
            for func_name in function_calls:
                if func_name in context and callable(context[func_name]):
                    helper_func = context[func_name]
                    if (
                        hasattr(helper_func, "__module__")
                        and helper_func.__module__ == func.__module__
                        and func_name.startswith("_")
                        and (not inspect.isbuiltin(helper_func))
                    ):
                        try:
                            helper_source = inspect.getsource(helper_func)
                            helper_source = self._clean_function_source(helper_source)
                            helper_functions_source.append(helper_source)
                        except (TypeError, OSError):
                            pass
            if helper_functions_source:
                source = source + "\n\n" + "\n\n".join(helper_functions_source)
        except Exception:
            pass
        return source

    def _process_decorators(self, func: Callable, source: str, context: dict) -> str:
        """Process and capture decorator source code and dependencies."""
        import re

        decorator_matches = re.findall("@(\\w+)", source)
        for decorator_name in decorator_matches:
            if decorator_name in func.__globals__:
                context[decorator_name] = func.__globals__[decorator_name]
                source = self._capture_decorator_source(func.__globals__[decorator_name], source, context)
        missing_decorators = [name for name in decorator_matches if name not in func.__globals__]
        if missing_decorators:
            source = self._capture_local_decorators(missing_decorators, source, context)
        return source

    def _capture_decorator_source(self, decorator_func: Callable, source: str, context: dict) -> str:
        """Capture source code and dependencies for a specific decorator."""
        if not callable(decorator_func) or inspect.isbuiltin(decorator_func):
            return source
        try:
            decorator_source = inspect.getsource(decorator_func)
            self._capture_annotation_context(decorator_func, context)
            if hasattr(decorator_func, "__globals__"):
                for dec_name, dec_value in decorator_func.__globals__.items():
                    if not dec_name.startswith("__"):
                        if isinstance(dec_value, (int, float, str, bool, list, dict)):
                            context[dec_name] = dec_value
                        elif isinstance(dec_value, types.ModuleType):
                            context[dec_name] = dec_value
                        elif hasattr(dec_value, "__module__"):
                            context[dec_name] = dec_value
            decorator_source = self._handle_decorator_closures(decorator_func, decorator_source, context)
            source = self._clean_decorator_source(decorator_source) + "\n\n" + source
        except (TypeError, OSError):
            pass
        return source

    def _handle_decorator_closures(self, decorator_func: Callable, decorator_source: str, context: dict) -> str:
        """Handle closure variables for decorator functions."""
        if not (hasattr(decorator_func, "__closure__") and decorator_func.__closure__):
            return decorator_source
        freevars = decorator_func.__code__.co_freevars
        closure_defs = []
        for k, var_name in enumerate(freevars):
            if k < len(decorator_func.__closure__) and decorator_func.__closure__[k] is not None:
                try:
                    closure_value = decorator_func.__closure__[k].cell_contents
                    closure_defs.append(f"{var_name} = {repr(closure_value)}")
                    context[var_name] = closure_value
                except ValueError:
                    pass
        if closure_defs:
            decorator_source = "\n".join(closure_defs) + "\n\n" + decorator_source
        return decorator_source

    def _capture_local_decorators(self, missing_decorators: list, source: str, context: dict) -> str:
        """Capture locally-defined decorators from the call stack."""
        frame = inspect.currentframe()
        try:
            while frame:
                frame_locals = frame.f_locals
                for decorator_name in missing_decorators:
                    if decorator_name in frame_locals:
                        decorator_func = frame_locals[decorator_name]
                        if callable(decorator_func):
                            try:
                                decorator_source = inspect.getsource(decorator_func)
                                self._capture_annotation_context(decorator_func, context)
                                decorator_source = self._handle_decorator_closures(decorator_func, decorator_source, context)
                                source = self._clean_decorator_source(decorator_source) + "\n\n" + source
                            except (TypeError, OSError) as e:
                                print(f"DEBUG: Could not capture decorator {decorator_name}: {e}")
                frame = frame.f_back
        finally:
            del frame
        return source

    def add_tool(self, func: Callable) -> None:
        """Add a single Python function as a tool for LLM use.

        Use when you need to make an individual function available as a tool.
        Handles all necessary context preservation and function wrapping.

        Parameters:
            func (Callable): The function to add as a tool

        Raises:
            ValueError: If tool schema generation fails
            TypeError: If function source cannot be accessed
            OSError: If there are issues accessing function source

        Side Effects:
            - Creates module context if none exists
            - Adds function to tool registry
            - Updates function map

        Example:
            ```python
            def calculate_area(radius: float) -> float:
                '''Calculate circle area. Use when...'''
                return 3.14159 * radius * radius

            handler.add_tool(calculate_area)
            ```

        Note:
            - Preserves function's full context including docstring
            - Creates wrappers for built-in and dynamic functions
            - Maintains all necessary dependencies
        """
        schema = self.generate_tool_schema(func)
        if not schema:
            raise ValueError("Schema undefined. ToolHandler.generate_tool_schema() may not be implemented.")
        if not hasattr(func, "__module_context__"):
            # Check if this is a dynamic function that we can't get source for
            try:
                # Try to get source - if this fails, it's a dynamic function
                inspect.getsource(func)
                # If we get here, we can get source, so process normally
                source, context = self._prepare_function_source_and_context(func)
                func = self._create_module_context_and_function(func, source, context)
            except (TypeError, OSError):
                # This is a dynamic function - store it directly without creating a wrapper
                # The serialization/deserialization will handle it during save/load
                pass  # Keep the original function as-is
        self.tools.append(schema)
        self.function_map[func.__name__] = func

    def _prepare_function_source_and_context(self, func: Callable) -> tuple[str, dict]:
        """Prepare the source code and execution context for a function."""
        if inspect.isbuiltin(func) or inspect.ismethoddescriptor(func):
            return (self._create_builtin_wrapper(func), {})
        try:
            source = inspect.getsource(func)
            source = self._clean_function_source(source)
            if hasattr(func, "__globals__"):
                context = self._build_function_context(func)
                source = self._process_decorators(func, source, context)
                source = self._capture_helper_functions(func, source, context)
            else:
                context = {}
            return (source, context)
        except (TypeError, OSError):
            return (self._create_dynamic_wrapper(func), {})

    def _create_module_context_and_function(self, func: Callable, source: str, context: dict) -> Callable:
        """Create a module context and return the function with context attached."""
        module_name = f"dynamic_module_{hash(source)}"
        file_path = f"dynamic_module_{hash(str(func))}"
        module = ModuleType(module_name)
        module.__file__ = file_path
        module.__dict__.update(context)
        module_context = ModuleContext(
            name=module_name, source=source, file_path=file_path, namespace=module, code_hash=self._get_code_hash(source)
        )
        exec(source, module.__dict__)
        new_func = module.__dict__[func.__name__]
        new_func.__module_context__ = module_context
        self.modules[file_path] = module_context
        return new_func

    def _add_tools_from_file(self, filepath: str) -> None:
        """Add all non-private functions from a Python file as tools.

        Use when you want to add all suitable functions from a Python file.
        Handles module loading, dependency preservation, and context management.

        Parameters:
            filepath (str): Path to the Python file containing tool functions

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ModuleLoadError: If there's an error loading the module or its dependencies
            SyntaxError: If the Python file contains syntax errors

        Side Effects:
            - Creates module context for the file
            - Adds all non-private functions as tools
            - Preserves module dependencies and imports
            - Updates module registry

        Example:
            ```python
            handler._add_tools_from_file("path/to/tools.py")
            ```

        Note:
            - Only adds top-level functions (not nested in classes/functions)
            - Skips functions whose names start with underscore
            - Maintains original module context for all functions
            - Preserves source code for serialization
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found.")
        abs_file_path = os.path.abspath(filepath)
        module_name = f"dynamic_module_{hashlib.md5(abs_file_path.encode()).hexdigest()}"
        try:
            with open(abs_file_path, "r") as file:
                source = file.read()
            module = ModuleType(module_name)
            module.__file__ = abs_file_path
            tree = ast.parse(source)
            function_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            sys.path.insert(0, os.path.dirname(abs_file_path))
            try:
                exec(source, module.__dict__)
            finally:
                sys.path.pop(0)
            module_context = ModuleContext(
                name=module_name,
                source=source,
                file_path=abs_file_path,
                namespace=module,
                code_hash=self._get_code_hash(source),
            )
            self.modules[abs_file_path] = module_context
            for node in function_nodes:
                if not node.name.startswith("_"):
                    func = module.__dict__.get(node.name)
                    if func:
                        func.__module_context__ = module_context
                        self.add_tool(func)
        except Exception as e:
            raise ModuleLoadError(f"Error loading module from {filepath}: {str(e)}") from e

    def _add_tools_from_module(self, module: ModuleType) -> None:
        """Add all non-private functions from a Python module as tools.

        Use when you want to add functions from an imported module or
        dynamically created module object.

        Parameters:
            module (ModuleType): Module object containing the tool functions

        Raises:
            ModuleLoadError: If module lacks both __file__ and __source__ attributes
            ImportError: If module dependencies cannot be resolved
            Exception: For other module processing errors

        Side Effects:
            - Creates module context if needed
            - Adds all non-private functions as tools
            - Updates module registry
            - Preserves module state and dependencies

        Example:
            ```python
            import my_tools
            handler._add_tools_from_module(my_tools)
            ```

        Note:
            - Module must have either __file__ or __source__ attribute
            - Only processes top-level functions
            - Skips functions whose names start with underscore
            - Maintains complete module context
        """
        if hasattr(module, "__file__") and os.path.exists(module.__file__):
            self._add_tools_from_file(module.__file__)
        elif hasattr(module, "__source__"):
            source = module.__source__
            module_name = f"dynamic_module_{hashlib.md5(module.__name__.encode()).hexdigest()}"
            try:
                dynamic_module = ModuleType(module_name)
                dynamic_module.__file__ = f"dynamic_module_{hash(source)}"
                exec(source, dynamic_module.__dict__)
                module_context = ModuleContext(
                    name=module_name,
                    source=source,
                    file_path=dynamic_module.__file__,
                    namespace=dynamic_module,
                    code_hash=self._get_code_hash(source),
                )
                self.modules[dynamic_module.__file__] = module_context
                for name, func in inspect.getmembers(dynamic_module, inspect.isfunction):
                    if not name.startswith("_"):
                        func.__module_context__ = module_context
                        self.add_tool(func)
            except Exception as e:
                raise ModuleLoadError(f"Error loading module {module.__name__}: {str(e)}") from e
        else:
            raise ModuleLoadError(f"Module {module.__name__} has neither file path nor source. Cannot load.")

    def _add_imports_to_source(self, module_context) -> str:
        """Add necessary imports to module source code by extracting existing imports."""
        source = module_context.source
        imports_needed = []

        # Track import line numbers so we can remove them later
        import_line_numbers = set()

        try:
            tree = ast.parse(source)
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    # Track line numbers of import statements
                    if hasattr(node, "lineno"):
                        import_line_numbers.add(node.lineno)
                    for alias in node.names:
                        if alias.asname:
                            imports_needed.append(f"import {alias.name} as {alias.asname}")
                        else:
                            imports_needed.append(f"import {alias.name}")
                elif isinstance(node, ast.ImportFrom):
                    # Track line numbers of from...import statements
                    if hasattr(node, "lineno"):
                        import_line_numbers.add(node.lineno)
                    module_name = node.module or ""
                    names = []
                    for alias in node.names:
                        if alias.asname:
                            names.append(f"{alias.name} as {alias.asname}")
                        else:
                            names.append(alias.name)
                    if names:
                        imports_needed.append(f"from {module_name} import {', '.join(names)}")
        except SyntaxError:
            import_patterns = ["^import\\s+[\\w\\.,\\s]+", "^from\\s+[\\w\\.]+\\s+import\\s+[\\w\\.,\\s\\*]+"]
            source_lines = source.split("\n")
            for line_num, line in enumerate(source_lines, 1):
                line_stripped = line.strip()
                for pattern in import_patterns:
                    if re.match(pattern, line_stripped):
                        imports_needed.append(line_stripped)
                        import_line_numbers.add(line_num)
                        break
        try:
            tree = ast.parse(source)
            annotation_names = set()

            class AnnotationVisitor(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    if node.returns:
                        self._extract_names_from_annotation(node.returns, annotation_names)
                    for arg in node.args.args:
                        if arg.annotation:
                            self._extract_names_from_annotation(arg.annotation, annotation_names)
                    self.generic_visit(node)

                def visit_AsyncFunctionDef(self, node):
                    if node.returns:
                        self._extract_names_from_annotation(node.returns, annotation_names)
                    for arg in node.args.args:
                        if arg.annotation:
                            self._extract_names_from_annotation(arg.annotation, annotation_names)
                    self.generic_visit(node)

                def _extract_names_from_annotation(self, annotation, names_set):
                    """Extract all names from a type annotation."""
                    if isinstance(annotation, ast.Name):
                        names_set.add(annotation.id)
                    elif isinstance(annotation, ast.Attribute):
                        if isinstance(annotation.value, ast.Name):
                            names_set.add(annotation.value.id)
                    elif isinstance(annotation, ast.Subscript):
                        self._extract_names_from_annotation(annotation.value, names_set)
                        if hasattr(annotation, "slice"):
                            if isinstance(annotation.slice, ast.Name):
                                names_set.add(annotation.slice.id)
                            elif hasattr(annotation.slice, "elts"):
                                for elt in annotation.slice.elts:
                                    self._extract_names_from_annotation(elt, names_set)
                            else:
                                self._extract_names_from_annotation(annotation.slice, names_set)

            visitor = AnnotationVisitor()
            visitor.visit(tree)
            if hasattr(module_context, "namespace") and hasattr(module_context.namespace, "__dict__"):
                namespace_dict = module_context.namespace.__dict__
                typing_imports = []
                for name in annotation_names:
                    if name in namespace_dict:
                        value = namespace_dict[name]
                        if hasattr(value, "__module__") and value.__module__ == "typing":
                            typing_imports.append(name)
                if typing_imports:
                    typing_import = f"from typing import {', '.join(sorted(typing_imports))}"
                    imports_needed.append(typing_import)
                all_names_used = set()

                class NameCollector(ast.NodeVisitor):
                    def visit_Name(self, node):
                        if isinstance(node.ctx, ast.Load):
                            all_names_used.add(node.id)
                        self.generic_visit(node)

                name_collector = NameCollector()
                name_collector.visit(tree)
                module_imports = {}
                for name in all_names_used:
                    if name in namespace_dict:
                        value = namespace_dict[name]
                        if hasattr(value, "__module__") and value.__module__:
                            module_name = value.__module__
                            if module_name in ["functools", "itertools", "collections", "operator", "re", "math", "datetime"]:
                                if module_name not in module_imports:
                                    module_imports[module_name] = []
                                module_imports[module_name].append(name)
                for module_name, names in module_imports.items():
                    if names:
                        module_import = f"from {module_name} import {', '.join(sorted(names))}"
                        imports_needed.append(module_import)
        except Exception:
            pass

        # Remove duplicate imports
        unique_imports = []
        seen = set()
        for imp in imports_needed:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)

        # Remove existing import lines from source before adding them back
        if import_line_numbers:
            source_lines = source.split("\n")
            # Filter out lines that are imports (1-indexed line numbers)
            filtered_lines = [line for i, line in enumerate(source_lines, 1) if i not in import_line_numbers]
            # Remove leading empty lines
            while filtered_lines and not filtered_lines[0].strip():
                filtered_lines.pop(0)
            source = "\n".join(filtered_lines)

        # Add imports to the beginning
        if unique_imports:
            import_block = "\n".join(unique_imports) + "\n\n"
            source = import_block + source

        return source

    def to_dict(self) -> Dict[str, Any]:
        """Serialize the complete ToolHandler state to a dictionary.

        Use when you need to save or transmit the tool handler's state,
        including all tools, modules, and execution state.

        Returns:
            Dict[str, Any]: Serialized state containing:
                - Handler class information
                - Registered tools and their schemas
                - Module contexts and source code
                - Function mappings and relationships
                - Current requests and results

        Note:
            - Preserves complete module contexts
            - Handles both file-based and dynamic modules
            - Includes function source code for reconstruction
            - Maintains tool relationships and dependencies
        """
        module_details = {}
        function_paths = {}
        for file_path, module_context in self.modules.items():
            enhanced_source = self._add_imports_to_source(module_context)
            module_details[file_path] = {
                "name": module_context.name,
                "source": enhanced_source,
                "file_path": module_context.file_path,
                "code_hash": self._get_code_hash(enhanced_source),
                "globals": self._serialize_globals(module_context.namespace.__dict__),
            }
        for name, func in self.function_map.items():
            module_context = getattr(func, "__module_context__", None)
            if module_context:
                function_paths[name] = module_context.file_path
            else:
                function_paths[name] = "dynamic"
        # Serialize dynamic functions
        # Serialize dynamic functions
        dynamic_functions = {}
        for name, func in self.function_map.items():
            if function_paths.get(name) == "dynamic":
                dynamic_functions[name] = self._serialize_dynamic_function(func)

        result = {
            "class": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "tools": self.tools.copy(),
            "requests": self.requests.copy(),
            "results": self.results.copy(),
            "modules": module_details,
            "function_paths": function_paths,
        }

        # Add dynamic functions if any exist
        if dynamic_functions:
            result["dynamic_functions"] = dynamic_functions

        return result

    def _serialize_globals(self, namespace_dict: dict) -> dict:
        """Serialize globals including modules and other necessary objects."""
        serialized = {}
        for k, v in namespace_dict.items():
            if k.startswith("__"):
                continue
            if isinstance(v, (int, float, str, bool, list, dict)):
                serialized[k] = v
            elif isinstance(v, types.ModuleType):
                serialized[k] = {
                    "__module_type__": True,
                    "name": v.__name__,
                    "spec": getattr(v, "__spec__", None) and v.__spec__.name,
                }
            elif hasattr(v, "__module__") and hasattr(v, "__name__"):
                if k == "_original_func":
                    # Special handling for _original_func - use pickle
                    try:
                        import base64

                        import dill

                        pickled_func = dill.dumps(v)
                        encoded_func = base64.b64encode(pickled_func).decode("ascii")
                        serialized[k] = {"__original_func__": True, "pickled": encoded_func, "name": v.__name__}
                    except Exception as e:
                        print(f"Warning: Could not dill serialize _original_func: {e}")
                        pass  # Skip if we can't pickle
                elif k.startswith("_") and callable(v):
                    # Skip helper functions from dynamic modules - they'll be recreated from source
                    if (
                        hasattr(v, "__module__")
                        and v.__module__
                        and ("dynamic_module_" in v.__module__ or "__runtime__" in v.__module__)
                    ):
                        pass  # Skip dynamic module helper functions
                    else:
                        # Serialize helper functions using dill for non-dynamic modules
                        try:
                            import base64

                            import dill

                            pickled_func = dill.dumps(v)
                            encoded_func = base64.b64encode(pickled_func).decode("ascii")
                            serialized[k] = {"__helper_func__": True, "pickled": encoded_func, "name": v.__name__}
                        except Exception as e:
                            print(f"Warning: Could not dill serialize helper function {k}: {e}")
                            pass  # Skip if we can't pickle
                else:
                    pass  # Skip other non-helper functions
        return serialized

    def _serialize_dynamic_function(self, func: Callable) -> Dict[str, Any]:
        """Serialize dynamic function using dill with metadata fallback"""
        import base64
        import hashlib

        # Try dill first
        try:
            import dill

            # Serialize the function
            serialized_data = dill.dumps(func)
            encoded_data = base64.b64encode(serialized_data).decode("ascii")

            # Create hash for verification
            content_hash = hashlib.sha256(serialized_data).hexdigest()

            return {
                "type": "dill",
                "success": True,
                "data": encoded_data,
                "hash": content_hash,
                "name": getattr(func, "__name__", "unknown"),
                "signature": str(inspect.signature(func)) if hasattr(func, "__code__") else "unknown",
            }
        except ImportError:
            pass  # Fall through to metadata-only
        except Exception as e:
            print(f"Warning: Dill serialization failed for {getattr(func, '__name__', 'unknown')}: {e}")

        # Fallback to metadata-only approach
        return self._serialize_function_metadata(func)

    def _serialize_function_metadata(self, func: Callable) -> Dict[str, Any]:
        """Serialize function metadata only (safe fallback)"""
        import hashlib
        import json

        try:
            metadata = {
                "name": getattr(func, "__name__", "unknown"),
                "doc": getattr(func, "__doc__", None),
                "module": getattr(func, "__module__", None),
                "qualname": getattr(func, "__qualname__", None),
            }

            # Try to get signature
            try:
                metadata["signature"] = str(inspect.signature(func))
            except (ValueError, TypeError):
                metadata["signature"] = "unknown"

            # Try to capture closure variable info (names and types only, not values)
            if hasattr(func, "__closure__") and func.__closure__:
                closure_info = []
                code = func.__code__
                for i, cell in enumerate(func.__closure__):
                    var_name = code.co_freevars[i]
                    try:
                        value = cell.cell_contents
                        closure_info.append(
                            {
                                "name": var_name,
                                "type": type(value).__name__,
                                "repr": (
                                    repr(value) if isinstance(value, (int, float, str, bool)) else f"<{type(value).__name__}>"
                                ),
                            }
                        )
                    except ValueError:
                        closure_info.append({"name": var_name, "type": "empty_cell"})
                metadata["closure_info"] = closure_info

            # Create hash of metadata
            json_str = json.dumps(metadata, sort_keys=True)
            content_hash = hashlib.sha256(json_str.encode()).hexdigest()

            return {
                "type": "metadata",
                "success": True,
                "metadata": metadata,
                "hash": content_hash,
                "name": metadata["name"],
                "signature": metadata["signature"],
            }

        except Exception as e:
            return {"type": "metadata", "success": False, "error": str(e), "error_type": type(e).__name__}

    def _deserialize_dynamic_function(self, func_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Restore function from serialized data"""
        if func_data.get("type") == "dill":
            return self._deserialize_with_dill(func_data)
        elif func_data.get("type") == "metadata":
            return self._deserialize_with_metadata(func_data)
        else:
            return False, f"Unknown serialization type: {func_data.get('type', 'unknown')}"

    def _deserialize_with_dill(self, func_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Deserialize function using dill"""
        import base64

        try:
            import dill

            if not func_data.get("success", False):
                return False, f"Original serialization failed: {func_data.get('error', 'unknown')}"

            # Decode and verify hash
            encoded_data = func_data["data"]
            serialized_data = base64.b64decode(encoded_data.encode("ascii"))

            computed_hash = hashlib.sha256(serialized_data).hexdigest()
            if computed_hash != func_data["hash"]:
                return False, "Hash mismatch - potential tampering detected"

            # Safe to deserialize after hash verification
            restored_func = dill.loads(serialized_data)
            return True, restored_func

        except ImportError:
            return False, "dill package not available for deserialization"
        except Exception as e:
            return False, f"Deserialization error: {type(e).__name__}: {str(e)}"

    def _deserialize_with_metadata(self, func_data: Dict[str, Any]) -> Tuple[bool, Any]:
        """Create informative placeholder from metadata"""
        try:
            if not func_data.get("success", False):
                return False, f"Original serialization failed: {func_data.get('error', 'unknown')}"

            metadata = func_data["metadata"]

            # Create a placeholder function that provides useful information
            def placeholder_func(*args, **kwargs):
                info = f"Dynamic function '{metadata['name']}' cannot be restored after save/load\n"
                info += f"Original signature: {metadata.get('signature', 'unknown')}\n"
                if metadata.get("doc"):
                    info += f"Documentation: {metadata['doc']}\n"
                if metadata.get("closure_info"):
                    info += f"Had closure variables: {[c['name'] for c in metadata['closure_info']]}\n"
                info += "Consider using file-based tools instead of dynamic functions for save/load compatibility."
                raise NotImplementedError(info)

            # Set metadata on placeholder
            placeholder_func.__name__ = metadata["name"]
            placeholder_func.__doc__ = f"Placeholder for dynamic function. Original doc: {metadata.get('doc', 'None')}"

            return True, placeholder_func

        except Exception as e:
            return False, f"Placeholder creation error: {type(e).__name__}: {str(e)}"

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ToolHandler":
        """Reconstruct a ToolHandler instance from serialized state.

        Use when restoring a previously serialized tool handler,
        such as when loading a saved bot state.

        Parameters:
            data (Dict[str, Any]): Serialized state from to_dict()

        Returns:
            ToolHandler: Reconstructed handler instance

        Side Effects:
            - Creates new module contexts
            - Reconstructs function objects
            - Restores tool registry
            - Preserves request/result history

        Note:
            - Only restores explicitly registered tools
            - Verifies code hashes for security
            - Maintains original module structure
            - Preserves execution state (requests/results)

        Example:
            ```python
            saved_state = handler.to_dict()
            # Later...
            new_handler = ToolHandler.from_dict(saved_state)
            ```
        """
        handler = cls()
        handler.results = data.get("results", [])
        handler.requests = data.get("requests", [])
        handler.tools = data.get("tools", []).copy()
        function_paths = data.get("function_paths", {})
        for file_path, module_data in data.get("modules", {}).items():
            current_code_hash = cls._get_code_hash(module_data["source"])
            if current_code_hash != module_data["code_hash"]:
                print(f"Warning: Code hash mismatch for module {file_path}. Skipping.")
                continue
            try:
                module = ModuleType(module_data["name"])
                module.__file__ = file_path
                source = module_data["source"]
                if "globals" in module_data:
                    cls._deserialize_globals(module.__dict__, module_data["globals"])

                exec(source, module.__dict__)
                module_context = ModuleContext(
                    name=module_data["name"],
                    source=source,
                    file_path=module_data["file_path"],
                    namespace=module,
                    code_hash=current_code_hash,
                )
                handler.modules[module_data["file_path"]] = module_context
                for func_name, path in function_paths.items():
                    if path == module_data["file_path"] and func_name in module.__dict__:
                        func = module.__dict__[func_name]
                        if callable(func):
                            func.__module_context__ = module_context
                            handler.function_map[func_name] = func
            except Exception as e:
                import sys
                import traceback

                print(f"Warning: Failed to load module {file_path}")
                print(f"  Error: {type(e).__name__}: {str(e)}")
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_traceback:
                    tb_frame = exc_traceback.tb_frame
                    tb_lineno = exc_traceback.tb_lineno
                    print(f"  Location: {tb_frame.f_code.co_filename}:{tb_lineno}")
                    print(f"  Function: {tb_frame.f_code.co_name}")
                    if tb_frame.f_locals:
                        relevant_locals = {
                            k: v for k, v in tb_frame.f_locals.items() if not k.startswith("__") and (not callable(v))
                        }
                        if relevant_locals:
                            print(f"  Local variables: {relevant_locals}")
                tb_lines = traceback.format_tb(exc_traceback)
                if tb_lines:
                    print("  Full stack trace:")
                    for i, line in enumerate(tb_lines):
                        print(f"    Frame {i}: {line.strip()}")
                if exc_traceback and hasattr(exc_traceback, "tb_lineno"):
                    try:
                        source_lines = source.split("\n")
                        error_line = exc_traceback.tb_lineno
                        start_line = max(0, error_line - 3)
                        end_line = min(len(source_lines), error_line + 2)
                        print(f"  Source context (lines {start_line + 1}-{end_line}):")
                        for i in range(start_line, end_line):
                            prefix = ">>> " if i + 1 == error_line else "    "
                            print(f"  {prefix}{i + 1:3d}: {source_lines[i]}")
                    except Exception:
                        pass
                continue
        # Restore dynamic functions
        if "dynamic_functions" in data:
            for func_name, func_data in data["dynamic_functions"].items():
                success, result = handler._deserialize_dynamic_function(func_data)
                if success:
                    handler.function_map[func_name] = result
                else:
                    print(f"Warning: Failed to restore dynamic function {func_name}: {result}")

        return handler

    @staticmethod
    def _deserialize_globals(module_dict: dict, serialized_globals: dict):
        """Deserialize globals including module reconstruction."""
        import importlib

        for k, v in serialized_globals.items():
            if isinstance(v, dict) and v.get("__module_type__"):
                module_name = v["name"]
                try:
                    imported_module = importlib.import_module(module_name)
                    module_dict[k] = imported_module
                except ImportError as e:
                    print(f"Warning: Could not import module {module_name}: {e}")
                    pass
            elif isinstance(v, dict) and v.get("__original_func__"):
                # Reconstruct _original_func from pickled data
                try:
                    import base64

                    import dill

                    encoded_func = v["pickled"]
                    pickled_func = base64.b64decode(encoded_func.encode("ascii"))
                    module_dict[k] = dill.loads(pickled_func)
                except Exception as e:
                    print(f"Warning: Could not dill deserialize _original_func: {e}")
                    pass
            elif isinstance(v, dict) and v.get("__helper_func__"):
                # Reconstruct helper function from pickled data
                try:
                    import base64

                    import dill

                    encoded_func = v["pickled"]
                    pickled_func = base64.b64decode(encoded_func.encode("ascii"))
                    module_dict[k] = dill.loads(pickled_func)
                except Exception as e:
                    print(f"Warning: Could not dill deserialize helper function {k}: {e}")
                    pass
            else:
                module_dict[k] = v

    def get_tools_json(self) -> str:
        """Get a JSON string representation of all registered tools.

        Use when you need a serialized view of the available tools,
        such as for debugging or external tool discovery.

        Returns:
            str: JSON string containing all tool schemas, formatted with indentation

        Example:
            ```python
            tools_json = handler.get_tools_json()
            print(f"Available tools: {tools_json}")
            ```
        """
        return json.dumps(self.tools, indent=1)

    def clear(self) -> None:
        """Clear all stored tool results and requests.

        Use when you need to reset the handler's execution state
        without affecting the registered tools.

        Side Effects:
            - Empties self.results list
            - Empties self.requests list
        """
        self.results = []
        self.requests = []

    def add_request(self, request: Dict[str, Any]) -> None:
        """Add a new tool request to the pending requests.

        Use when manually adding a tool request rather than
        extracting it from an LLM response.

        Parameters:
            request (Dict[str, Any]): Tool request schema to add

        Side Effects:
            - Appends request to self.requests list
        """
        self.requests.append(request)

    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a new tool result to the stored results.

        Use when manually adding a tool result rather than
        generating it through exec_requests().

        Parameters:
            result (Dict[str, Any]): Tool result schema to add

        Side Effects:
            - Appends result to self.results list
        """
        self.results.append(result)

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all stored tool execution results.

        Use when you need to access the complete history of
        tool execution results.

        Returns:
            List[Dict[str, Any]]: List of all tool result schemas
        """
        return self.results

    def get_requests(self) -> List[Dict[str, Any]]:
        """Get all stored tool requests.

        Use when you need to access the complete history of
        tool execution requests.

        Returns:
            List[Dict[str, Any]]: List of all tool request schemas
        """
        return self.requests

    @staticmethod
    def _get_code_hash(code: str) -> str:
        """Generate an MD5 hash of a code string.

        Use when creating a unique identifier for code content
        or verifying code integrity during deserialization.

        Parameters:
            code (str): Source code string to hash

        Returns:
            str: MD5 hash of the code string
        """
        return hashlib.md5(code.encode()).hexdigest()

    def __str__(self) -> str:
        """Create a simple string representation of the ToolHandler.

        Use when you need a quick overview of the handler's state,
        showing just the number of tools and modules.

        Returns:
            str: Brief summary string showing tool and module counts

        Example:
            ```python
            handler = ToolHandler()
            print(handler)  # "ToolHandler with 5 tools and 2 modules"
            ```
        """
        return f"ToolHandler with {len(self.tools)} tools and {len(self.modules)} modules"

    def __repr__(self) -> str:
        """Create a detailed string representation of the ToolHandler.

        Use when you need a complete technical view of the handler's state,
        including all tool names and module paths.

        Returns:
            str: Detailed string showing:
                - List of all registered tool names
                - List of all module paths

        Example:
            ```python
            handler = ToolHandler()
            print(repr(handler))  # Shows all tools and modules
            ```
        """
        tool_names = list(self.function_map.keys())
        return f"ToolHandler(tools={tool_names}, modules={list(self.modules.keys())})"


class Mailbox(ABC):
    """Abstract base class for LLM service communication.

    Mailbox provides a standardized interface for sending messages to and receiving
    responses from different LLM services (OpenAI, Anthropic, etc.). It handles:
    - Message formatting and sending
    - Response parsing and processing
    - Logging of all communications
    - Tool result integration

    The class abstracts away the differences between various LLM APIs,
    providing a consistent interface for the Bot class.

    Example:
        ```python
        class AnthropicMailbox(Mailbox):
            def send_message(self, bot):
                # Implementation for Anthropic API
                pass

            def process_response(self, response, bot=None):
                # Parse Anthropic response format
                pass
        ```
    """

    def __init__(self):
        self.log_file = "data\\mailbox_log.txt"

    def log_message(self, message: str, direction: str) -> None:
        timestamp = formatted_datetime()
        log_entry = f"[{timestamp}] {direction.upper()}:\n{message}\n\n"
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(log_entry)

    @abstractmethod
    def send_message(self, bot: "Bot") -> Dict[str, Any]:
        """Send a message to the LLM service.

        Use to handle the specifics of communicating with a particular LLM API.
        Must handle message formatting, API calls, and initial response parsing.

        Parameters:
            bot (Bot): Reference to the bot instance making the request.
                      Contains conversation history and configuration.

        Returns:
            Dict[str, Any]: Raw response from the LLM service

        Raises:
            Exception: For API errors, rate limits, or other communication issues

        Note:
            - Should use bot.conversation for message history
            - May handle tool results depending on API requirements
            - Should respect bot.model_engine and other configuration
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def process_response(self, response: Dict[str, Any], bot: Optional["Bot"] = None) -> Tuple[str, str, Dict[str, Any]]:
        """Process the raw LLM response into a standardized format.

        Use to convert service-specific response formats into a consistent structure
        that can be used by the Bot class. Handles extraction of message content,
        role information, and any additional metadata.

        Parameters:
            response (Dict[str, Any]): Raw response from the LLM service
            bot (Optional[Bot]): Reference to bot instance, required for services
                that need to send additional messages during processing (e.g.,
                OpenAI's tool handling)

        Returns:
            Tuple[str, str, Dict[str, Any]]: Processed response containing:
                - response_text: The main message content
                - role: Message sender's role (e.g., "assistant")
                - metadata: Additional information to be stored with the message

        Note:
            - If tool_handler is present, tool requests and results are already
              processed and available in tool_handler.requests/results
            - Metadata dict is passed directly to ConversationNode's kwargs
            - Each metadata item becomes an attribute of the ConversationNode
        """
        raise NotImplementedError("You must implement this method in a subclass")

    def _log_outgoing(self, conversation: ConversationNode, model: Engines, max_tokens, temperature):
        log_message = {
            "date": formatted_datetime(),
            "messages": conversation._build_messages(),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model,
        }
        self._log_message(json.dumps(log_message, indent=1), "OUTGOING")

    def _log_incoming(self, processed_response):
        log_message = {"date": formatted_datetime(), "response": processed_response}
        self._log_message(json.dumps(log_message, indent=1), "INCOMING")

    def _log_message(self, message: str, direction: str) -> None:
        timestamp = formatted_datetime()
        log_entry = f"[{timestamp}] {direction.upper()}:\n{message}\n\n"
        with open(self.log_file, "a", encoding="utf-8") as file:
            file.write(log_entry)


class Bot(ABC):
    """Abstract base class for LLM-powered conversational agents.

    The Bot class provides a unified interface for working with different LLM services,
    handling conversation management, tool usage, and state persistence. Key features:

    - Simple primary interface (respond(), chat())
    - Comprehensive tool support
    - Complete state preservation
    - Tree-based conversation management
    - Configurable parameters for each LLM

    The class is designed to make basic usage simple while allowing access to
    advanced features when needed.

    Attributes:
        api_key (Optional[str]): API key for the LLM service
        name (str): Name identifier for the bot
        model_engine (Engines): The specific LLM model to use
        max_tokens (int): Maximum tokens in model responses
        temperature (float): Randomness in model responses (0.0-1.0)
        role (str): Bot's role identifier
        role_description (str): Detailed description of bot's role
        conversation (ConversationNode): Current conversation state
        system_message (str): System-level instructions for the bot
        tool_handler (Optional[ToolHandler]): Manager for bot's tools
        mailbox (Optional[Mailbox]): Handler for LLM communication
        autosave (bool): Whether to automatically save state

    Example:
        ```python
        class MyBot(Bot):
            def __init__(self, api_key: str):
                super().__init__(
                    api_key=api_key,
                    model_engine=Engines.GPT4,
                    name="MyBot",
                    role="assistant",
                    role_description="A helpful AI assistant"
         )

        bot = MyBot("api_key")
        bot.add_tools(my_tools)
        response = bot.respond("Hello!")
        ```
    """

    def __init__(
        self,
        api_key: Optional[str],
        model_engine: Engines,
        max_tokens: int,
        temperature: float,
        name: str,
        role: str,
        role_description: str,
        conversation: Optional[ConversationNode] = ConversationNode._create_empty(),
        tool_handler: Optional[ToolHandler] = None,
        mailbox: Optional[Mailbox] = None,
        autosave: bool = True,
        enable_tracing: Optional[bool] = None,
        callbacks: Optional["BotCallbacks"] = None,
    ) -> None:
        """Initialize a new Bot instance.

        Parameters:
            api_key (Optional[str]): API key for the LLM service
            model_engine (Engines): The specific LLM model to use
            max_tokens (int): Maximum tokens in model responses
            temperature (float): Randomness in model responses (0.0-1.0)
            name (str): Name identifier for the bot
            role (str): Bot's role identifier
            role_description (str): Detailed description of bot's role
            conversation (Optional[ConversationNode]): Initial conversation state
            tool_handler (Optional[ToolHandler]): Manager for bot's tools
            mailbox (Optional[Mailbox]): Handler for LLM communication
            autosave (bool): Whether to automatically save state after responses. Saves to cwd.
            enable_tracing (Optional[bool]): Enable OpenTelemetry tracing. None uses default (True).
            callbacks (Optional[BotCallbacks]): Callback system for progress/monitoring. None disables callbacks.
        """
        self.api_key = api_key
        self.name = name
        self.model_engine = model_engine
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.role = role
        self.role_description = role_description
        self.conversation: ConversationNode = conversation
        self.system_message = ""
        self.tool_handler = tool_handler
        self.mailbox = mailbox
        self.autosave = autosave
        self.filename = None  # Track source filename for intelligent save behavior
        self.callbacks = callbacks  # Optional callback system for progress/monitoring

        # Determine if tracing should be enabled
        # Determine if tracing should be enabled
        if enable_tracing is None:
            # Default to True if tracing is available and not globally disabled
            self._tracing_enabled = TRACING_AVAILABLE and is_tracing_enabled()
        else:
            # User explicitly specified, respect their choice (but still check if SDK is disabled)
            self._tracing_enabled = TRACING_AVAILABLE and enable_tracing and is_tracing_enabled()

        if isinstance(self.model_engine, str):
            self.model_engine = Engines.get(self.model_engine)

    def respond(self, prompt: str, role: str = "user") -> str:
        """Send a prompt to the bot and get its response.

        This is the primary interface for interacting with the bot. The method:
        1. Adds the prompt to the conversation history
        2. Sends the conversation to the LLM
        3. Processes any tool usage requests
        4. Returns the final response

        Parameters:
            prompt (str): The message to send to the bot
            role (str): Role of the message sender (defaults to 'user')

        Returns:
            str: The bot's response text

        Note:
            - Automatically saves state if autosave is enabled
            - Tool usage is handled automatically if tools are available
            - Full conversation context is maintained

        Example:
            ```python
            bot.add_tools(file_tools)
            response = bot.respond("Please read config.json")
            ```
        """
        if self._tracing_enabled and tracer:
            with tracer.start_as_current_span("bot.respond") as span:
                span.set_attribute("bot.name", self.name)
                span.set_attribute("bot.model", self.model_engine.value)
                span.set_attribute("prompt.length", len(prompt))
                span.set_attribute("prompt.role", role)
                return self._respond_impl(prompt, role)
        else:
            return self._respond_impl(prompt, role)

    def _respond_impl(self, prompt: str, role: str = "user") -> str:
        """Internal implementation of respond without tracing."""
        # Invoke on_respond_start callback
        if self.callbacks:
            try:
                self.callbacks.on_respond_start(prompt, metadata={"bot_name": self.name, "model": self.model_engine.value})
            except Exception as e:
                logger.warning(f"Callback on_respond_start failed: {e}")

        try:
            self.conversation = self.conversation._add_reply(content=prompt, role=role)
            if self.autosave:
                self.save(f"{self.name}", quicksave=True)
            reply, _ = self._cvsn_respond()
            if self.autosave:
                self.save(f"{self.name}", quicksave=True)

            # Invoke on_respond_complete callback
            if self.callbacks:
                try:
                    self.callbacks.on_respond_complete(reply, metadata={"bot_name": self.name})
                except Exception as e:
                    logger.warning(f"Callback on_respond_complete failed: {e}")

            return reply
        except Exception as e:
            # Invoke on_respond_error callback
            if self.callbacks:
                try:
                    self.callbacks.on_respond_error(e, metadata={"bot_name": self.name, "prompt": prompt})
                except Exception as callback_error:
                    logger.warning(f"Callback on_respond_error failed: {callback_error}")
            raise

    def add_tools(self, *args) -> None:
        """Add Python functions as tools available to the bot.

        Use to provide the bot with capabilities by adding Python functions
        as tools. Functions' docstrings are used to describe the tools to the LLM.

        The method is highly flexible in what it accepts:
        - Individual Python functions
        - Python files containing functions
        - Imported Python modules
        - Mixed combinations of the above
        - Lists/tuples of any supported type

        Parameters:
            *args: Variable arguments that can be:
                - str: Path to Python file with tools
                - ModuleType: Module containing tools
                - Callable: Single function to add
                - List/Tuple: Collection of any above types

        Raises:
            TypeError: If an argument is not a supported type
            FileNotFoundError: If a specified file doesn't exist
            ModuleLoadError: If there's an error loading a module

        Example:
            ```python
            # Single function
            bot.add_tools(calculate_area)

            # Multiple files and modules
            bot.add_tools(
                "tools/file_ops.py",
                math_tools,
                "tools/network.py",
                [process_data, custom_sort]
            )
            ```

        Note:
            - Only adds top-level functions (not nested or class methods)
            - Preserves full module context for imported tools
            - Tools persist across save/load cycles
        """

        def process_item(item):
            if isinstance(item, str):
                self.tool_handler._add_tools_from_file(item)
            elif isinstance(item, ModuleType):
                self.tool_handler._add_tools_from_module(item)
            elif isinstance(item, Callable):
                self.tool_handler.add_tool(item)
            elif isinstance(item, (list, tuple)):
                for subitem in item:
                    process_item(subitem)
            else:
                raise TypeError(f"Unsupported type for tool addition: {type(item)}")

        for arg in args:
            process_item(arg)

    def _cvsn_respond(self) -> Tuple[str, ConversationNode]:
        """Process a conversation turn with the LLM, including tool handling.

        Use when implementing core conversation flow. This method:
        1. Gets LLM response using current conversation context
        2. Handles any tool usage requests
        3. Updates conversation history
        4. Manages tool results and context

        Returns:
            Tuple[str, ConversationNode]:
                - response_text: The LLM's response text
                - node: The new conversation node created

        Raises:
            Exception: Any errors from LLM communication or tool execution

        Side Effects:
            - Updates conversation tree with new node
            - Processes tool requests if any
            - Updates tool results in conversation context

        Note:
            - Clears tool handler state before processing
            - Automatically handles tool request extraction
            - Maintains conversation tree structure
            - Preserves tool execution results
        """
        if self._tracing_enabled and tracer:
            with tracer.start_as_current_span("bot._cvsn_respond") as span:
                try:
                    self.tool_handler.clear()
                    response = self.mailbox.send_message(self)
                    _ = self.tool_handler.extract_requests(response)
                    span.set_attribute("tool.request_count", len(self.tool_handler.requests))
                    text, role, data = self.mailbox.process_response(response, self)
                    self.conversation = self.conversation._add_reply(content=text, role=role, **data)
                    self.conversation._add_tool_calls(self.tool_handler.requests)

                    # Invoke callback to display bot response before tools execute
                    if self.callbacks:
                        try:
                            self.callbacks.on_api_call_complete(
                                metadata={"bot_response": text, "tool_count": len(self.tool_handler.requests)}
                            )
                        except Exception as e:
                            logger.warning(f"Callback on_api_call_complete failed: {e}")

                    _ = self.tool_handler.exec_requests()
                    span.set_attribute("tool.result_count", len(self.tool_handler.results))
                    self.conversation._add_tool_results(self.tool_handler.results)
                    return (text, self.conversation)
                except Exception as e:
                    span.record_exception(e)
                    raise e
        else:
            try:
                self.tool_handler.clear()
                response = self.mailbox.send_message(self)
                _ = self.tool_handler.extract_requests(response)
                text, role, data = self.mailbox.process_response(response, self)
                self.conversation = self.conversation._add_reply(content=text, role=role, **data)
                self.conversation._add_tool_calls(self.tool_handler.requests)

                # Invoke callback to display bot response before tools execute
                if self.callbacks:
                    try:
                        self.callbacks.on_api_call_complete(
                            metadata={"bot_response": text, "tool_count": len(self.tool_handler.requests)}
                        )
                    except Exception as e:
                        logger.warning(f"Callback on_api_call_complete failed: {e}")

                _ = self.tool_handler.exec_requests()
                self.conversation._add_tool_results(self.tool_handler.results)
                return (text, self.conversation)
            except Exception as e:
                raise e

    def set_system_message(self, message: str) -> None:
        """Set the system-level instructions for the bot.

        Use to provide high-level guidance or constraints that should
        apply to all of the bot's responses.

        Parameters:
            message (str): System instructions for the bot

        Example:
            ```python
            bot.set_system_message(
                "You are a code review expert. Focus on security and performance."
            )
            ```
        """
        self.system_message = message

    @classmethod
    def load(cls, filepath: str, api_key: Optional[str] = None) -> "Bot":
        """Load a saved bot from a file.

        Use to restore a previously saved bot with its complete state,
        including conversation history, tools, and configuration.

        Parameters:
            filepath (str): Path to the .bot file to load
            api_key (Optional[str]): New API key to use, if different from saved

        Returns:
            Bot: Reconstructed bot instance with restored state

        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ValueError: If the file contains invalid bot data

        Example:
            ```python
            # Save bot state
            bot.save("code_review_bot.bot")

            # Later, restore the bot
            bot = Bot.load("code_review_bot.bot", api_key="new_key")
            ```

        Note:
            - API keys are not saved for security
            - Tool functions are fully restored with their context
            - Conversation history is preserved exactly
        """
        with open(filepath, "r") as file:
            data = json.load(file)
        bot_class = Engines.get_bot_class(Engines(data["model_engine"]))
        init_params = inspect.signature(bot_class.__init__).parameters
        constructor_args = {k: v for k, v in data.items() if k in init_params}
        bot = bot_class(**constructor_args)
        bot.api_key = api_key if api_key is not None else None
        if "tool_handler" in data:
            tool_handler_class = data["tool_handler"]["class"]
            module_name, class_name = tool_handler_class.rsplit(".", 1)
            module = importlib.import_module(module_name)
            actual_class = getattr(module, class_name)
            bot.tool_handler = actual_class().from_dict(data["tool_handler"])
        for key, value in data.items():
            if key not in constructor_args and key not in ("conversation", "tool_handler", "tools"):
                setattr(bot, key, value)
        if "conversation" in data and data["conversation"]:
            node_class = Engines.get_conversation_node_class(data["conversation"]["node_class"])
            bot.conversation = node_class._from_dict(data["conversation"])
            while bot.conversation.replies:
                bot.conversation = bot.conversation.replies[-1]
        bot.filename = filepath
        return bot

    def save(self, filename: Optional[str] = None, quicksave: bool = False) -> str:
        """Save the bot's complete state to a file.

        Use to preserve the bot's entire state including:
        - Configuration and parameters
        - Conversation history
        - Tool definitions and context
        - System messages and role information

        Parameters:
            filename (Optional[str]): Name for the save file
                If None, generates name using bot name and timestamp
                Adds .bot extension if not present
            quicksave (bool): If True, saves to quicksave.bot (ephemeral working file)
                Quicksave doesn't update the tracked filename

        Returns:
            str: Path to the saved file

        Example:
            ```python
            # Save with generated name
            path = bot.save()  # e.g., "MyBot@2024-01-20_15-30-45.bot"

            # Save with specific name
            path = bot.save("code_review_bot")  # saves as "code_review_bot.bot"

            # Quicksave (autosave)
            path = bot.save(quicksave=True)  # saves as "quicksave.bot"
            ```

        Note:
            - API keys are not saved for security
            - Creates directories in path if they don't exist
            - Maintains complete tool context for restoration
        """
        if quicksave:
            filename = "quicksave.bot"
        elif filename is None:
            filename = getattr(self, "filename", None) or f"{self.name}@{formatted_datetime()}.bot"

        if not filename.endswith(".bot"):
            filename = filename + ".bot"
        directory = os.path.dirname(filename)
        if directory and (not os.path.exists(directory)):
            os.makedirs(directory)
        data = {key: value for key, value in self.__dict__.items() if not key.startswith("_")}
        data.pop("api_key", None)
        data.pop("mailbox", None)
        data["bot_class"] = self.__class__.__name__
        data["model_engine"] = self.model_engine.value
        data["conversation"] = self.conversation._root_dict()
        data["conversation"] = self.conversation._root_dict()
        # Preserve tracing state
        if hasattr(self, "_tracing_enabled"):
            data["enable_tracing"] = self._tracing_enabled
            data["tool_handler"] = self.tool_handler.to_dict()
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                data[key] = str(value)
        with open(filename, "w") as file:
            json.dump(data, file, indent=1)

        # Only update tracked filename for non-quicksave saves
        if not quicksave:
            self.filename = filename

        return filename

    def chat(self) -> None:
        """Start an interactive chat session with the bot.

        Use when you want to have a continuous conversation with the bot
        in the terminal. The session continues until '/exit' is entered.

        Features:
        - Simple text-based interface
        - Shows tool usage information
        - Maintains conversation context
        - Visual separators between messages

        Example:
            ```python
            bot.add_tools(my_tools)
            bot.chat()
            # You: Please analyze the code in main.py
            # Bot: I'll take a look...
            # Used Tool: view_file
            # ...
            ```

        Note:
            - Enter '/exit' to end the session
            - Tool usage is displayed if tools are available
            - State is saved according to autosave setting
        """
        separator = "\n---\n"
        print(separator)
        print('System: Chat started. Type "/exit" to exit.')
        uinput = ""
        while uinput != "/exit":
            print(separator)
            uinput = input("You: ")
            if uinput is None or uinput == "/exit":
                break
            print(separator)
            print(f"{self.name}: {self.respond(uinput)}")
            print(separator)
            if self.tool_handler:
                for request in self.tool_handler.get_requests():
                    tool_name, _ = self.tool_handler.tool_name_and_input(request)
                    print(f"Used Tool: {tool_name}")
                    print(separator)

    def __mul__(self, other: int) -> List["Bot"]:
        """Create multiple copies of this bot.

        Use when you need multiple instances of the same bot configuration,
        for example when running parallel operations.

        Parameters:
            other (int): Number of copies to create

        Returns:
            List[Bot]: List of independent bot copies

        Example:
            ```python
            # Create 3 identical bots
            bots = base_bot * 3

            # Use in parallel operations
            results = [bot.respond("Hello") for bot in bots]
            ```

        Note:
            - Each copy is completely independent
            - Copies include all configuration and tools
        """
        if isinstance(other, int):
            return [copy.deepcopy(self) for _ in range(other)]
        raise NotImplementedError("Bot multiplcation not defined for non-integer values")

    def __str__(self) -> str:
        """Create a human-readable string representation of the bot.

        Use when you need a detailed, formatted view of the bot's state,
        including conversation history and tool usage.

        Returns:
            str: Formatted string containing:
                - Bot metadata (name, role, model)
                - Complete conversation history with indentation
                - Tool calls and results
                - Available tool count

        Note:
            - Conversation is shown as a tree structure
            - Tool results are included with each message
            - Handles deep conversation trees with level indicators
            - Formats content for readable terminal output

        Example:
            ```python
            bot = MyBot("api_key")
            print(bot)  # Shows complete bot state
            ```
        """

        def format_conversation(node, level=0):
            display_level = min(level, 5)
            indent_size = 1
            marker_size = 4
            indent = " " * indent_size * display_level
            available_width = max(40, 80 - display_level * indent_size - marker_size)
            messages = []
            if hasattr(node, "role"):
                if node.role == "user":
                    base_name = "You"
                elif node.role == "assistant":
                    base_name = self.name
                else:
                    base_name = node.role.title()
            else:
                base_name = "System"
            if level > display_level:
                hidden_levels = level - display_level
                if hidden_levels <= 3:
                    depth_indicator = ">" * hidden_levels
                else:
                    depth_indicator = f">>>({hidden_levels})"
                name_display = f"{depth_indicator} {base_name}"
            else:
                name_display = base_name
            content = node.content if hasattr(node, "content") else str(node)
            wrapped_content = "\n".join(
                textwrap.wrap(
                    content, width=available_width, initial_indent=indent + "â”‚ ", subsequent_indent=indent + "â”‚ "
                )
            )
            tool_info = []
            if hasattr(node, "tool_calls") and node.tool_calls:
                tool_info.append(f"{indent}â”‚ Tool Calls:")
                for call in node.tool_calls:
                    if isinstance(call, dict):
                        tool_info.append(f"{indent}â”‚   - {call.get('name', 'unknown')}")
            if hasattr(node, "tool_results") and node.tool_results:
                tool_info.append(f"{indent}â”‚ Tool Results:")
                for result in node.tool_results:
                    if isinstance(result, dict):
                        tool_info.append(f"{indent}â”‚   - {str(result.get('content', ''))[:available_width]}")
            if hasattr(node, "pending_results") and node.pending_results:
                tool_info.append(f"{indent}â”‚ Pending Results:")
                for result in node.pending_results:
                    if isinstance(result, dict):
                        tool_info.append(f"{indent}â”‚   - {str(result.get('content', ''))[:available_width]}")
                    else:
                        raise ValueError()
            messages.append(f"{indent}â”œâ”€ {name_display}")
            messages.append(wrapped_content)
            if hasattr(node, "tool_calls") and node.tool_calls:
                messages.append(f"{indent}â”‚ Tool Calls:")
                for call in node.tool_calls:
                    if isinstance(call, dict):
                        messages.append(f"{indent}â”‚   - {call.get('name', 'unknown')}")
            if hasattr(node, "tool_results") and node.tool_results:
                messages.append(f"{indent}â”‚ Tool Results:")
                for result in node.tool_results:
                    if isinstance(result, dict):
                        messages.append(f"{indent}â”‚   - {str(result.get('content', ''))[:available_width]}")
            if hasattr(node, "pending_results") and node.pending_results:
                messages.append(f"{indent}â”‚ Pending Results:")
                for result in node.pending_results:
                    if isinstance(result, dict):
                        messages.append(f"{indent}â”‚   - {str(result.get('content', ''))[:available_width]}")
            messages.append(f"{indent}â””" + "â”€" * 40)
            if hasattr(node, "replies") and node.replies:
                for reply in node.replies:
                    messages.extend(format_conversation(reply, level + 1))
            return messages

        lines = []
        lines.append("â•”" + "â•" * 12)
        lines.append(f"â•‘ {self.name}")
        lines.append(f"â•‘ Role: {self.role}")
        lines.append(f"â•‘ Model: {self.model_engine.value}")
        if self.tool_handler:
            tool_count = len(self.tool_handler.tools)
            lines.append(f"â•‘ Tools Available: {tool_count}")
        lines.append("â•š" + "â•" * 78 + "â•\n")
        if self.conversation:
            root = self.conversation
            while hasattr(root, "parent") and root.parent:
                if root.parent._is_empty() and len(root.parent.replies) == 1:
                    break
                root = root.parent
            lines.extend(format_conversation(root))
        return "\n".join(lines)
