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
    ```python
    from bots import AnthropicBot
    import my_tools

    # Create a bot with tools
    bot = AnthropicBot()
    bot.add_tools(my_tools)

    # Basic interaction
    response = bot.respond("Hello!")

    # Save bot state
    bot.save("my_bot.bot")
    ```
"""

import ast
import copy
import hashlib
import importlib
import inspect
import json
import keyword
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


def _clean_decorator_source(source):
    """Clean decorator source by parsing the source file and extracting the
    decorator function."""

    # Try to find the source file where the decorator was defined
    # We'll look at the call stack to find the test file
    frame = inspect.currentframe()
    try:
        while frame:
            frame_info = inspect.getframeinfo(frame)
            if frame_info.filename.endswith(".py") and "test_" in frame_info.filename:
                # Found a test file - this is likely where our decorator is defined
                test_file = frame_info.filename

                try:
                    # Read and parse the entire test file
                    with open(test_file, "r", encoding="utf-8") as f:
                        file_content = f.read()

                    tree = ast.parse(file_content)

                    # Look for function definitions that match our decorator
                    # Extract the first line of our source to identify the decorator
                    source_lines = source.strip().split("\n")
                    decorator_name = None

                    for line in source_lines:
                        if line.strip().startswith("def ") and "(" in line:
                            # Extract function name
                            func_line = line.strip()
                            decorator_name = func_line[4 : func_line.index("(")].strip()
                            break

                    if decorator_name:

                        # Find the decorator function in the AST
                        for node in ast.walk(tree):
                            if isinstance(node, ast.FunctionDef) and node.name == decorator_name:
                                # Found the decorator function - extract it with proper indentation
                                cleaned = _py_ast_to_source(node)

                                # The closure variables should already be handled by the closure capture logic
                                # in the main add_tool method, so just return the clean decorator function
                                return cleaned

                except Exception:
                    break

            frame = frame.f_back
    finally:
        del frame

    # Fallback to original approach if AST extraction fails
    cleaned = textwrap.dedent(source).strip()
    return cleaned


def _clean_function_source(source):
    """Clean function source using AST parsing and regeneration."""
    try:
        # Parse the function source into an AST
        tree = ast.parse(source)
        # Regenerate clean source code with proper indentation
        cleaned = _py_ast_to_source(tree)
        return cleaned
    except SyntaxError:
        # Fallback to textwrap.dedent
        import textwrap

        cleaned = textwrap.dedent(source).strip()
        return cleaned


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
    GPT4_0613 = "gpt-4-0613"
    GPT4_32K = "gpt-4-32k"
    GPT4_32K_0613 = "gpt-4-32k-0613"
    GPT4TURBO = "gpt-4-turbo-preview"
    GPT4TURBO_0125 = "gpt-4-0125-preview"
    GPT4TURBO_VISION = "gpt-4-vision-preview"
    GPT35TURBO = "gpt-3.5-turbo"
    GPT35TURBO_16K = "gpt-3.5-turbo-16k"
    GPT35TURBO_0125 = "gpt-3.5-turbo-0125"
    GPT35TURBO_INSTRUCT = "gpt-3.5-turbo-instruct"
    CLAUDE3_HAIKU = "claude-3-haiku-20240307"
    CLAUDE3_SONNET = "claude-3-sonnet-20240229"
    CLAUDE3_OPUS = "claude-3-opus-20240229"
    CLAUDE35_SONNET_20240620 = "claude-3-5-sonnet-20240620"
    CLAUDE35_SONNET_20241022 = "claude-3-5-sonnet-20241022"
    CLAUDE37_SONNET_20250219 = "claude-3-7-sonnet-20250219"
    CLAUDE4_OPUS = "claude-opus-4-20250514"
    CLAUDE4_SONNET = "claude-sonnet-4-20250514"

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
        from bots.foundation.openai_bots import ChatGPT_Bot

        if model_engine.value.startswith("gpt"):
            return ChatGPT_Bot
        elif model_engine.value.startswith("claude"):
            return AnthropicBot
        else:
            raise ValueError(f"Unsupported model engine: {model_engine}")

    @staticmethod
    def get_conversation_node_class(class_name: str) -> Type["ConversationNode"]:
        """Get the appropriate ConversationNode subclass by name.

        Use when you need to reconstruct conversation nodes from saved bot state.

        Parameters:
            class_name (str): Name of the node class ('OpenAINode' or 'AnthropicNode')

        Returns:
            Type[ConversationNode]: The ConversationNode subclass

        Raises:
            ValueError: If the class name is not a supported node type
        """
        from bots.foundation.anthropic_bots import AnthropicNode
        from bots.foundation.openai_bots import OpenAINode

        NODE_CLASS_MAP = {"OpenAINode": OpenAINode, "AnthropicNode": AnthropicNode}
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

        Parameters:
            content (str): The message content
            role (str): The role of the message sender
            tool_calls (Optional[List[Dict]]): Tool invocations made in this message
            tool_results (Optional[List[Dict]]): Results from tool executions
            pending_results (Optional[List[Dict]]): Tool results waiting to be processed
            **kwargs: Additional attributes to set on the node
        """
        self.role = role
        self.content = content
        self.parent: ConversationNode = None
        self.replies: list[ConversationNode] = []
        self.tool_calls = tool_calls or []
        self.tool_results = tool_results or []
        self.pending_results = pending_results or []
        for key, value in kwargs.items():
            setattr(self, key, value)

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

        Parameters:
            **kwargs: Attributes to set on the new node (content, role, etc.)

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
            reply.tool_results = self.pending_results.copy()
            self.pending_results = []
        reply._sync_tool_context()
        return reply

    def _sync_tool_context(self) -> None:
        """Synchronize tool results across all sibling nodes.

        Use when tool results need to be shared between parallel conversation branches.
        Takes the union of all tool results from sibling nodes and ensures each sibling
        has access to all results.

        Side Effects:
            Updates tool_results for all sibling nodes to include all unique results.
        """
        if self.parent and self.parent.replies:
            all_tool_results = []
            for sibling in self.parent.replies:
                for result in sibling.tool_results:
                    if result not in all_tool_results: # Content comparison of JSON strings
                        all_tool_results.append(result)
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
        self.tool_results.extend(results)
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
        for request_schema in requests:
            tool_name, input_kwargs = self.tool_name_and_input(request_schema)
            if tool_name is None:
                continue
            try:
                if tool_name not in self.function_map:
                    raise ToolNotFoundError(f"Tool '{tool_name}' not found in function map")
                func = self.function_map[tool_name]
                output_kwargs = func(**input_kwargs)
                response_schema = self.generate_response_schema(request_schema, output_kwargs)
            except ToolNotFoundError as e:
                error_msg = "Error: Tool not found.\n\n" + str(e)
                response_schema = self.generate_error_schema(request_schema, error_msg)
            except TypeError as e:
                error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
                response_schema = self.generate_error_schema(request_schema, error_msg)
            except Exception as e:
                error_msg = f"Unexpected error while executing tool '{tool_name}': {str(e)}"
                response_schema = self.generate_error_schema(request_schema, error_msg)
            self.results.append(response_schema)
            results.append(response_schema)
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
            - Creates fallback implementation if source is not accessible
            - Handles both normal and dynamic functions
        """
        source = f"def {func.__name__}{inspect.signature(func)}:\n"
        if func.__doc__:
            source += f'    """{func.__doc__}"""\n'
        if hasattr(func, "__code__"):
            try:
                body = inspect.getsource(func).split("\n", 1)[1]
                source += body
            except Exception:
                source += "    return func(*args, **kwargs)\n"
        else:
            source += "    pass\n"
        return source

    def _extract_annotation_names(self, source_code: str) -> set:
        """Extract all names used in type annotations from source code."""
        import ast
        import re

        annotation_names = set()

        try:
            # Parse the source code into an AST
            tree = ast.parse(source_code)

            # Walk through all nodes to find annotations
            for node in ast.walk(tree):
                # Function annotations (parameters and return types)
                if isinstance(node, ast.FunctionDef):
                    # Parameter annotations
                    for arg in node.args.args:
                        if arg.annotation:
                            annotation_names.update(self._extract_names_from_ast_node(arg.annotation))

                    # Return type annotation
                    if node.returns:
                        annotation_names.update(self._extract_names_from_ast_node(node.returns))

                # Variable annotations (like: x: int = 5)
                elif isinstance(node, ast.AnnAssign):
                    if node.annotation:
                        annotation_names.update(self._extract_names_from_ast_node(node.annotation))

        except SyntaxError:
            # Fallback: use regex if AST parsing fails
            # Match common annotation patterns
            patterns = [
                r":\s*([A-Za-z_][A-Za-z0-9_]*)",  # param: Type
                r"->\s*([A-Za-z_][A-Za-z0-9_]*)",  # -> ReturnType
                r"\[\s*([A-Za-z_][A-Za-z0-9_]*)",  # List[Type]
                r",\s*([A-Za-z_][A-Za-z0-9_]*)",  # Dict[str, Type]
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
            # Handle things like typing.Optional
            if isinstance(node.value, ast.Name):
                names.add(node.value.id)  # Add 'typing'
        elif isinstance(node, ast.Subscript):
            # Handle generic types like List[str], Dict[str, int]
            names.update(self._extract_names_from_ast_node(node.value))
            if isinstance(node.slice, ast.Tuple):
                for elt in node.slice.elts:
                    names.update(self._extract_names_from_ast_node(elt))
            else:
                names.update(self._extract_names_from_ast_node(node.slice))
        elif hasattr(node, "elts"):  # Handle tuples/lists in annotations
            for elt in node.elts:
                names.update(self._extract_names_from_ast_node(elt))

        return names

    def _capture_annotation_context(self, func: Callable, context: dict) -> None:
        """Capture all objects referenced in function annotations."""
        if not hasattr(func, "__globals__"):
            return

        # Get the function's source to analyze annotations
        try:
            source = inspect.getsource(func)
            annotation_names = self._extract_annotation_names(source)

            # For each name found in annotations, try to capture it from globals
            for name in annotation_names:
                if name in func.__globals__:
                    context[name] = func.__globals__[name]

        except (TypeError, OSError):
            # If we can't get source, fall back to __annotations__
            if hasattr(func, "__annotations__") and func.__annotations__:
                # This is a simplified fallback - get basic type names
                for annotation in func.__annotations__.values():
                    if hasattr(annotation, "__name__"):
                        name = annotation.__name__
                        if name in func.__globals__:
                            context[name] = func.__globals__[name]

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
            if inspect.isbuiltin(func) or inspect.ismethoddescriptor(func):
                source = self._create_builtin_wrapper(func)
                context = {}
            else:
                try:
                    source = inspect.getsource(func)
                    source = _clean_function_source(source)
                    if hasattr(func, "__globals__"):
                        code = func.__code__
                        names = code.co_names
                        context = {name: func.__globals__[name] for name in names if name in func.__globals__}

                        # CRITICAL: Capture ALL annotation dependencies
                        self._capture_annotation_context(func, context)

                        # UNION FIX: Capture EVERYTHING from both function globals AND original module
                        import importlib
                        import types

                        # First, add ALL function globals (not just co_names)
                        for name, value in func.__globals__.items():
                            if not name.startswith("__"):
                                context[name] = value

                        # Then, union with the original module namespace
                        try:
                            original_module = importlib.import_module(func.__module__)
                            for name, value in original_module.__dict__.items():
                                if not name.startswith("__"):
                                    # Module namespace takes precedence over function globals for conflicts
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

                        # Add all imports from the original module
                        import types

                        for name, value in func.__globals__.items():
                            if isinstance(value, types.ModuleType) or callable(value):
                                context[name] = value

                        # Enhanced decorator handling with annotation support
                        import re

                        decorator_matches = re.findall(r"@(\w+)", source)
                        for decorator_name in decorator_matches:
                            if decorator_name in func.__globals__:
                                context[decorator_name] = func.__globals__[decorator_name]

                                try:
                                    decorator_func = func.__globals__[decorator_name]
                                    if callable(decorator_func) and not inspect.isbuiltin(decorator_func):
                                        decorator_source = inspect.getsource(decorator_func)

                                        # CRITICAL: Capture annotation context from decorator
                                        self._capture_annotation_context(decorator_func, context)

                                        # Enhanced decorator dependency capture
                                        if hasattr(decorator_func, "__globals__"):
                                            # Capture ALL globals that the decorator might need
                                            for dec_name, dec_value in decorator_func.__globals__.items():
                                                if not dec_name.startswith("__"):
                                                    if isinstance(dec_value, (int, float, str, bool, list, dict)):
                                                        context[dec_name] = dec_value
                                                    elif isinstance(dec_value, types.ModuleType):
                                                        context[dec_name] = dec_value
                                                    # Also capture any objects from decorator's globals
                                                    elif hasattr(dec_value, "__module__"):
                                                        context[dec_name] = dec_value

                                        # Handle closure variables
                                        if hasattr(decorator_func, "__closure__") and decorator_func.__closure__:
                                            freevars = decorator_func.__code__.co_freevars
                                            closure_defs = []
                                            for k, var_name in enumerate(freevars):
                                                if (
                                                    k < len(decorator_func.__closure__)
                                                    and decorator_func.__closure__[k] is not None
                                                ):
                                                    try:
                                                        closure_value = decorator_func.__closure__[k].cell_contents
                                                        closure_defs.append(f"{var_name} = {repr(closure_value)}")
                                                        context[var_name] = closure_value
                                                    except ValueError:
                                                        pass
                                            if closure_defs:
                                                decorator_source = "\n".join(closure_defs) + "\n\n" + decorator_source

                                        source = _clean_decorator_source(decorator_source) + "\n\n" + source

                                except (TypeError, OSError):
                                    # Can't get decorator source, continue with function object
                                    pass

                        # Enhanced handling for locally-defined decorators
                        missing_decorators = [name for name in decorator_matches if name not in func.__globals__]
                        if missing_decorators:
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

                                                    # CRITICAL: Capture annotation context from local decorator too
                                                    self._capture_annotation_context(decorator_func, context)

                                                    # Handle closure variables
                                                    closure_defs = []
                                                    if hasattr(decorator_func, "__closure__") and decorator_func.__closure__:
                                                        freevars = decorator_func.__code__.co_freevars
                                                        for k, var_name in enumerate(freevars):
                                                            if (
                                                                k < len(decorator_func.__closure__)
                                                                and decorator_func.__closure__[k] is not None
                                                            ):
                                                                try:
                                                                    closure_value = decorator_func.__closure__[k].cell_contents
                                                                    closure_defs.append(f"{var_name} = {repr(closure_value)}")
                                                                    context[var_name] = closure_value
                                                                except ValueError:
                                                                    pass

                                                    if closure_defs:
                                                        decorator_source = "\n".join(closure_defs) + "\n\n" + decorator_source

                                                    source = _clean_decorator_source(decorator_source) + "\n\n" + source

                                                except (TypeError, OSError) as e:
                                                    print(f"DEBUG: Could not capture decorator {decorator_name}: {e}")

                                    frame = frame.f_back
                            finally:
                                del frame

                    else:
                        context = {}
                except (TypeError, OSError):
                    source = self._create_dynamic_wrapper(func)
                    context = {}
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
            func = new_func
        self.tools.append(schema)
        self.function_map[func.__name__] = func

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
        if hasattr(module, "__file__"):
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
        
        # Extract existing import statements from the source using AST
        try:
            tree = ast.parse(source)
            
            for node in ast.walk(tree):
                if isinstance(node, ast.Import):
                    for alias in node.names:
                        if alias.asname:
                            imports_needed.append(f"import {alias.name} as {alias.asname}")
                        else:
                            imports_needed.append(f"import {alias.name}")
                            
                elif isinstance(node, ast.ImportFrom):
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
            # Fallback: use regex to extract import statements
            import_patterns = [
                r'^import\s+[\w\.,\s]+',
                r'^from\s+[\w\.]+\s+import\s+[\w\.,\s\*]+',
            ]
            
            for line in source.split('\n'):
                line = line.strip()
                for pattern in import_patterns:
                    if re.match(pattern, line):
                        imports_needed.append(line)
                        break
        # CRITICAL FIX: Add imports for typing objects used in type hints
        # This fixes the issue where Callable, Any, etc. are used but not imported
        try:
            tree = ast.parse(source)
            
            # Find all names used in type annotations
            annotation_names = set()
            
            class AnnotationVisitor(ast.NodeVisitor):
                def visit_FunctionDef(self, node):
                    # Check function annotations
                    if node.returns:
                        self._extract_names_from_annotation(node.returns, annotation_names)
                    
                    for arg in node.args.args:
                        if arg.annotation:
                            self._extract_names_from_annotation(arg.annotation, annotation_names)
                    
                    self.generic_visit(node)
                
                def visit_AsyncFunctionDef(self, node):
                    # Same as FunctionDef but for async functions
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
                        # For things like typing.Optional
                        if isinstance(annotation.value, ast.Name):
                            names_set.add(annotation.value.id)
                    elif isinstance(annotation, ast.Subscript):
                        # For things like List[str], Optional[int]
                        self._extract_names_from_annotation(annotation.value, names_set)
                        if hasattr(annotation, 'slice'):
                            if isinstance(annotation.slice, ast.Name):
                                names_set.add(annotation.slice.id)
                            elif hasattr(annotation.slice, 'elts'):  # Tuple of types
                                for elt in annotation.slice.elts:
                                    self._extract_names_from_annotation(elt, names_set)
                            else:
                                self._extract_names_from_annotation(annotation.slice, names_set)
            
            visitor = AnnotationVisitor()
            visitor.visit(tree)
            
            # Now check if any of these annotation names are typing objects in the namespace
            if hasattr(module_context, 'namespace') and hasattr(module_context.namespace, '__dict__'):
                namespace_dict = module_context.namespace.__dict__
                
                # Common typing imports that need to be handled
                typing_imports = []
                
                for name in annotation_names:
                    if name in namespace_dict:
                        value = namespace_dict[name]
                        
                        # Check if this is a typing object
                        if hasattr(value, '__module__') and value.__module__ == 'typing':
                            typing_imports.append(name)
                
                # Add typing imports if we found any
                if typing_imports:
                    typing_import = f"from typing import {', '.join(sorted(typing_imports))}"
                    imports_needed.append(typing_import)
                    
                # ADDITIONAL FIX: Also check for other common module imports (like functools.wraps)
                # Look for any names used in the code that exist in the namespace
                all_names_used = set()
                
                # Collect all names used in the source (not just annotations)
                class NameCollector(ast.NodeVisitor):
                    def visit_Name(self, node):
                        if isinstance(node.ctx, ast.Load):
                            all_names_used.add(node.id)
                        self.generic_visit(node)
                
                name_collector = NameCollector()
                name_collector.visit(tree)
                
                # Group imports by module
                module_imports = {}
                
                for name in all_names_used:
                    if name in namespace_dict:
                        value = namespace_dict[name]
                        
                        # Check if this has a module and it's a standard library or common module
                        if hasattr(value, '__module__') and value.__module__:
                            module_name = value.__module__
                            
                            # Only handle common modules to avoid importing everything
                            if module_name in ['functools', 'itertools', 'collections', 'operator', 're', 'math', 'datetime']:
                                if module_name not in module_imports:
                                    module_imports[module_name] = []
                                module_imports[module_name].append(name)
                
                # Add the module imports
                for module_name, names in module_imports.items():
                    if names:
                        module_import = f"from {module_name} import {', '.join(sorted(names))}"
                        imports_needed.append(module_import)
                    
        except Exception as e:
            # If annotation analysis fails, continue without it
            # This ensures we don't break existing functionality
            pass

        
        # Remove duplicates while preserving order
        unique_imports = []
        seen = set()
        for imp in imports_needed:
            if imp not in seen:
                unique_imports.append(imp)
                seen.add(imp)
        
        # Add imports to source if any were found
        if unique_imports:
            import_block = '\n'.join(unique_imports) + '\n\n'
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
            # CRITICAL: Use the enhanced source with imports when saving
            enhanced_source = self._add_imports_to_source(module_context)

            module_details[file_path] = {
                "name": module_context.name,
                "source": enhanced_source,  # Save the enhanced source, not the original
                "file_path": module_context.file_path,
                "code_hash": self._get_code_hash(enhanced_source),  # Hash the enhanced source
                "globals": self._serialize_globals(module_context.namespace.__dict__),
            }

        for name, func in self.function_map.items():
            module_context = getattr(func, "__module_context__", None)
            if module_context:
                function_paths[name] = module_context.file_path
            else:
                function_paths[name] = "dynamic"

        return {
            "class": f"{self.__class__.__module__}.{self.__class__.__name__}",
            "tools": self.tools.copy(),
            "requests": self.requests.copy(),
            "results": self.results.copy(),
            "modules": module_details,
            "function_paths": function_paths,
        }
    def _serialize_globals(self, namespace_dict: dict) -> dict:
        """Serialize globals including modules and other necessary objects."""
        import types
        serialized = {}
        
        for k, v in namespace_dict.items():
            if k.startswith("__"):
                continue
                
            # Include basic types
            if isinstance(v, (int, float, str, bool, list, dict)):
                serialized[k] = v
            # Include modules - store their import information
            elif isinstance(v, types.ModuleType):
                # Store module info for reconstruction
                serialized[k] = {
                    "__module_type__": True,
                    "name": v.__name__,
                    "spec": getattr(v, "__spec__", None) and v.__spec__.name
                }
            # Include other serializable objects that might be needed
            elif hasattr(v, "__module__") and hasattr(v, "__name__"):
                # This covers classes and other importable objects
                pass  # For now, skip these - they're complex to serialize
                
        return serialized


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

                # Get detailed traceback information
                exc_type, exc_value, exc_traceback = sys.exc_info()
                if exc_traceback:
                    tb_frame = exc_traceback.tb_frame
                    tb_lineno = exc_traceback.tb_lineno
                    print(f"  Location: {tb_frame.f_code.co_filename}:{tb_lineno}")
                    print(f"  Function: {tb_frame.f_code.co_name}")

                    # Get local variables at the point of failure
                    if tb_frame.f_locals:
                        relevant_locals = {
                            k: v for k, v in tb_frame.f_locals.items() if not k.startswith("__") and not callable(v)
                        }
                        if relevant_locals:
                            print(f"  Local variables: {relevant_locals}")

                # Show the full stack trace for debugging
                tb_lines = traceback.format_tb(exc_traceback)
                if tb_lines:
                    print("  Full stack trace:")
                    for i, line in enumerate(tb_lines):
                        print(f"    Frame {i}: {line.strip()}")

                # Show the source code around the error if possible
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

        return handler
    @staticmethod
    def _deserialize_globals(module_dict: dict, serialized_globals: dict):
        """Deserialize globals including module reconstruction."""
        import types
        import importlib
        
        for k, v in serialized_globals.items():
            if isinstance(v, dict) and v.get("__module_type__"):
                # This is a serialized module - reconstruct it
                module_name = v["name"]
                try:
                    # Import the module
                    imported_module = importlib.import_module(module_name)
                    module_dict[k] = imported_module
                except ImportError as e:
                    print(f"Warning: Could not import module {module_name}: {e}")
                    # Continue without this module - function might still work
                    pass
            else:
                # Regular value - just assign it
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

# max_tokens and temperature because those were the two
# sliders on the first openai playground and I found them
# very useful at the time. Eventually this will change to 
# a general config file
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
        conversation: Optional[ConversationNode] = (ConversationNode._create_empty()),
        tool_handler: Optional[ToolHandler] = None,
        mailbox: Optional[Mailbox] = None,
        autosave: bool = True,
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
        self.conversation = self.conversation._add_reply(content=prompt, role=role)
        if self.autosave:
            self.save(f"{self.name}")
        reply, _ = self._cvsn_respond()
        if self.autosave:
            self.save(f"{self.name}")
        return reply

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
        try:
            self.tool_handler.clear()
            response = self.mailbox.send_message(self)
            _ = self.tool_handler.extract_requests(response)
            text, role, data = self.mailbox.process_response(response, self)
            self.conversation = self.conversation._add_reply(content=text, role=role, **data)
            self.conversation._add_tool_calls(self.tool_handler.requests)
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
                bot.conversation = bot.conversation.replies[0]
        return bot

    def save(self, filename: Optional[str] = None) -> str:
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

        Returns:
            str: Path to the saved file

        Example:
            ```python
            # Save with generated name
            path = bot.save()  # e.g., "MyBot@2024-01-20_15-30-45.bot"

            # Save with specific name
            path = bot.save("code_review_bot")  # saves as "code_review_bot.bot"
            ```

        Note:
            - API keys are not saved for security
            - Creates directories in path if they don't exist
            - Maintains complete tool context for restoration
        """
        if filename is None:
            now = formatted_datetime()
            filename = f"{self.name}@{now}.bot"
        elif not filename.endswith(".bot"):
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
        if self.tool_handler:
            data["tool_handler"] = self.tool_handler.to_dict()
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                data[key] = str(value)
        with open(filename, "w") as file:
            json.dump(data, file, indent=1)
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
                    content,
                    width=available_width,
                    initial_indent=indent + "│ ",
                    subsequent_indent=indent + "│ ",
                )
            )
            tool_info = []
            if hasattr(node, "tool_calls") and node.tool_calls:
                tool_info.append(f"{indent}│ Tool Calls:")
                for call in node.tool_calls:
                    if isinstance(call, dict):
                        tool_info.append(f"{indent}│   - {call.get('name', 'unknown')}")
            if hasattr(node, "tool_results") and node.tool_results:
                tool_info.append(f"{indent}│ Tool Results:")
                for result in node.tool_results:
                    if isinstance(result, dict):
                        tool_info.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
            if hasattr(node, "pending_results") and node.pending_results:
                tool_info.append(f"{indent}│ Pending Results:")
                for result in node.pending_results:
                    if isinstance(result, dict):
                        tool_info.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
                    else:
                        raise ValueError()
            messages.append(f"{indent}├─ {name_display}")
            messages.append(wrapped_content)
            if hasattr(node, "tool_calls") and node.tool_calls:
                messages.append(f"{indent}│ Tool Calls:")
                for call in node.tool_calls:
                    if isinstance(call, dict):
                        messages.append(f"{indent}│   - {call.get('name', 'unknown')}")
            if hasattr(node, "tool_results") and node.tool_results:
                messages.append(f"{indent}│ Tool Results:")
                for result in node.tool_results:
                    if isinstance(result, dict):
                        messages.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
            if hasattr(node, "pending_results") and node.pending_results:
                messages.append(f"{indent}│ Pending Results:")
                for result in node.pending_results:
                    if isinstance(result, dict):
                        messages.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
            messages.append(f"{indent}└" + "─" * 40)
            if hasattr(node, "replies") and node.replies:
                for reply in node.replies:
                    messages.extend(format_conversation(reply, level + 1))
            return messages

        lines = []
        lines.append("╔" + "═" * 12)
        lines.append(f"║ {self.name}")
        lines.append(f"║ Role: {self.role}")
        lines.append(f"║ Model: {self.model_engine.value}")
        if self.tool_handler:
            tool_count = len(self.tool_handler.tools)
            lines.append(f"║ Tools Available: {tool_count}")
        lines.append("╚" + "═" * 78 + "╝\n")
        if self.conversation:
            root = self.conversation
            while hasattr(root, "parent") and root.parent:
                if root.parent._is_empty() and len(root.parent.replies) == 1:
                    break
                root = root.parent
            lines.extend(format_conversation(root))
        return "\n".join(lines)
