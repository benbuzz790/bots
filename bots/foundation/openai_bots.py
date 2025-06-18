"""OpenAI-specific implementations of the bot framework components.
Use when you need to create and manage bots that interface with OpenAI's
chat completion API.
This module provides OpenAI-specific implementations of conversation nodes,
tool handling, message processing, and the main bot class.
Key Components:
    - OpenAINode: Manages conversation history in OpenAI's expected format
    - OpenAIToolHandler: Handles function calling with OpenAI's schema
    - OpenAIMailbox: Manages API communication with OpenAI
    - ChatGPT_Bot: Main bot implementation for OpenAI models
"""

import inspect
import json
import os
from typing import Any, Callable, Dict, List, Optional, Tuple

from openai import OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage

from bots.foundation.base import (
    Bot,
    ConversationNode,
    Engines,
    Mailbox,
    ToolHandler,
)


class OpenAINode(ConversationNode):
    """A conversation node implementation specific to OpenAI's chat format.
    Use when you need to manage conversation history in a format compatible
    with OpenAI's chat API.
    Handles proper formatting of messages, tool calls, and tool results in
    the conversation tree.
    Inherits from:
        ConversationNode: Base class for conversation tree nodes
    Attributes:
        content (str): The message content for this node
        role (str): The role of the message sender ('user', 'assistant', or
            'tool')
        parent (Optional[ConversationNode]): Reference to the parent node in
            conversation tree
        children (List[ConversationNode]): List of child nodes in
            conversation tree
        tool_calls (Optional[List[Dict]]): List of tool calls made in this
            node
        tool_results (Optional[List[Dict]]): List of results from tool
            executions
    """

    def __init__(self, **kwargs: Any) -> None:
        """Initialize an OpenAINode.
        Parameters:
            **kwargs: Arbitrary keyword arguments passed to parent class
        """
        super().__init__(**kwargs)

    def _build_messages(self) -> List[Dict[str, Any]]:
        """Build message list for OpenAI API, properly handling empty nodes
        and tool calls.
        Use when you need to convert the conversation tree into OpenAI's
        expected message format.
        Traverses the conversation tree from current node to root, building a
        properly formatted message list that includes all relevant context,
        tool calls, and tool results.
        Returns:
            List[Dict[str, Any]]: List of messages in OpenAI chat format,
            where each message is a dictionary containing 'role' and 'content'
            keys, and optionally 'tool_calls' for assistant messages or
            'tool_call_id' for tool response messages.
        """
        conversation_dict = []
        node = self
        while node:
            if node._is_empty():
                node = node.parent
                continue
            if node.role == "user":
                conversation_dict = [{"role": "user", "content": node.content}] + conversation_dict
            if node.role == "assistant":
                if not (node.tool_calls or node.tool_results):
                    assistant_msg = {"role": "assistant", "content": node.content}
                    conversation_dict = [assistant_msg] + conversation_dict
                    node = node.parent
                    continue
                for result in node.tool_results:
                    conversation_dict = [result] + conversation_dict
                if node.tool_calls:
                    assistant_msg = {
                        "role": "assistant",
                        "content": node.content,
                        "tool_calls": node.tool_calls,
                    }
                    conversation_dict = [assistant_msg] + conversation_dict
            node = node.parent
        return conversation_dict


class OpenAIToolHandler(ToolHandler):
    """Tool handler implementation specific to OpenAI's function calling
    format.
    Use when you need to manage tool/function definitions and executions for
    OpenAI chat models.
    Handles conversion between Python functions and OpenAI's function calling
    schema, including proper formatting of function definitions, calls, and
    results.
    Inherits from:
        ToolHandler: Base class for managing tool operations
    Attributes:
        tools (List[Dict[str, Any]]): List of tool definitions in OpenAI
            function format
        requests (List[Dict[str, Any]]): Current list of pending tool/function
            calls
        results (List[Dict[str, Any]]): Results from the most recent tool
            executions
    """

    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate OpenAI-compatible function definitions from Python
        functions.
        Use when you need to convert a Python function into OpenAI's function
        definition format.
        Extracts function name, docstring, and signature to create a schema
        that OpenAI can understand and use for function calling.
        Parameters:
            func (Callable): The Python function to convert into a tool
                schema. Should have a proper docstring and type hints for best
                results.
        Returns:
            Dict[str, Any]: OpenAI-compatible function definition containing:
                - type: Always 'function'
                - function: Dict containing:
                    - name: The function name
                    - description: Function's docstring or default text
                    - parameters: Object describing required and optional
                        parameters
        """
        schema = {
            "type": "function",
            "function": {
                "name": func.__name__,
                "description": func.__doc__ or "No description provided.",
                "parameters": {"type": "object", "properties": {}, "required": []},
            },
        }
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            schema["function"]["parameters"]["properties"][param_name] = {
                "type": "string",
                "description": f"Parameter: {param_name}",
            }
            if param.default == inspect.Parameter.empty:
                schema["function"]["parameters"]["required"].append(param_name)
        return schema

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI API responses.
        Use when you need to parse tool/function calls from an OpenAI chat
        completion response.
        Handles both single and multiple function calls in the response.
        Parameters:
            response (Any): The raw response from OpenAI's chat completion
                API, typically containing a 'choices' field with message and
                potential tool calls
        Returns:
            List[Dict[str, Any]]: List of tool calls, each containing:
                - id: The unique tool call ID
                - type: The type of tool call (typically 'function')
                - function: Dict containing:
                    - name: The function name to call
                    - arguments: JSON string of function arguments
        """
        if hasattr(response.choices[0].message, "tool_calls") and response.choices[0].message.tool_calls is not None:
            return [
                {
                    "id": tool_call.id,
                    "type": tool_call.type,
                    "function": {
                        "name": tool_call.function.name,
                        "arguments": tool_call.function.arguments,
                    },
                }
                for tool_call in response.choices[0].message.tool_calls
            ]
        return []

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Parse OpenAI's function call format into tool name and arguments.
        Use when you need to extract the function name and arguments from an
        OpenAI function call.
        Handles JSON parsing of the arguments string into a Python dictionary.
        Parameters:
            request_schema (Dict[str, Any]): The function call schema from
                OpenAI, containing function name and arguments as a JSON string
        Returns:
            Tuple[str, Dict[str, Any]]: A tuple containing:
                - The function name (str)
                - Dictionary of parsed arguments (Dict[str, Any])
                Returns (None, None) if request_schema is empty
        """
        if not request_schema:
            return (None, None)
        return (
            request_schema["function"]["name"],
            json.loads(request_schema["function"]["arguments"]),
        )

    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool execution results for OpenAI's expected format.
        Use when you need to format a tool's output for OpenAI's function
        calling API.
        Converts Python function outputs into the message format OpenAI
        expects for tool results.
        Parameters:
            request (Dict[str, Any]): The original function call request
                containing the tool_call_id
            tool_output_kwargs (Dict[str, Any]): The output from the tool
                execution
        Returns:
            Dict[str, Any]: OpenAI-compatible tool response containing:
                - role: Always 'tool'
                - content: String representation of the tool output
                - tool_call_id: ID from the original request
        """
        return {
            "role": "tool",
            "content": str(tool_output_kwargs),
            "tool_call_id": request["id"],
        }

    def generate_error_schema(self, request_schema: Optional[Dict[str, Any]], error_msg: str) -> Dict[str, Any]:
        """Generate an error response in OpenAI's expected format.
        Use when you need to format an error that occurred during tool
        execution.
        Creates a properly formatted error message that can be included in the
        conversation.
        Parameters:
            request_schema (Optional[Dict[str, Any]]): The original request
                that caused the error, containing the tool_call_id if available
            error_msg (str): The error message to include in the response
        Returns:
            Dict[str, Any]: OpenAI-compatible error response containing:
                - role: Always 'tool'
                - content: The error message
                - tool_call_id: ID from the original request or 'unknown'
        """
        return {
            "role": "tool",
            "content": error_msg,
            "tool_call_id": (request_schema["id"] if request_schema else "unknown"),
        }


class OpenAIMailbox(Mailbox):
    """Mailbox implementation for handling OpenAI API communication.
    Use when you need to manage message sending and receiving with OpenAI's
    chat completion API.
    Handles API key management, message formatting, and response processing
    including tool calls.
    Provides logging of API interactions for debugging purposes.
    Inherits from:
        Mailbox: Base class for API communication
    Attributes:
        api_key (str): OpenAI API key used for authentication
        client (OpenAI): Initialized OpenAI client instance for API calls
    """

    def __init__(self, api_key: Optional[str] = None):
        """Initialize OpenAI API client.
        Use when you need to create a new OpenAI API communication channel.
        Handles API key validation and client initialization.
        Parameters:
            api_key (Optional[str]): OpenAI API key. If not provided, attempts
                to read from OPENAI_API_KEY environment variable.
        Raises:
            ValueError: If no API key is provided and none is found in
                environment variables.
        """
        super().__init__()
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")
        self.client = OpenAI(api_key=self.api_key)

    def send_message(self, bot: Bot) -> Dict[str, Any]:
        """Send a message to OpenAI's chat completion API.
        Use when you need to send a conversation to OpenAI and get a
        completion response.
        Handles message formatting, system messages, tool definitions, and API
        parameters.
        Includes logging of both outgoing messages and incoming responses.
        Parameters:
            bot (Bot): The bot instance containing:
                - conversation history
                - system message
                - tool definitions
                - model configuration (engine, tokens, temperature)
        Returns:
            Dict[str, Any]: Raw response from OpenAI's chat completion API
                containing:
                - choices: List of completion choices
                - usage: Token usage statistics
                - model: Model used for completion
                - id: Response ID
        Raises:
            Exception: Any error from the OpenAI API is re-raised for proper
                handling
        """
        system_message = bot.system_message
        messages = bot.conversation._build_messages()
        try:
            self._log_message(json.dumps({"messages": messages}, indent=2), "OUTGOING")
        except FileNotFoundError:
            pass
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})
        tools = bot.tool_handler.tools if bot.tool_handler else None
        model = bot.model_engine
        max_tokens = bot.max_tokens
        temperature = bot.temperature
        try:
            if tools:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                    tools=tools,
                    tool_choice="auto",
                )
            else:
                response = self.client.chat.completions.create(
                    model=model,
                    messages=messages,
                    max_tokens=max_tokens,
                    temperature=temperature,
                )
            try:
                self._log_message(
                    json.dumps({"response": response.model_dump()}, indent=2),
                    "INCOMING",
                )
            except FileNotFoundError:
                pass
            return response
        except Exception as e:
            raise e

    def process_response(self, response: Dict[str, Any], bot: Bot) -> Tuple[str, str, Dict[str, Any]]:
        """Process OpenAI's response and handle any tool calls recursively.
        Use when you need to extract the final response content after handling
        any tool calls.
        Manages the recursive process of executing tool calls and getting
        follow-up responses until a final text response is received.
        Parameters:
            response (Dict[str, Any]): Raw response from OpenAI's chat
                completion API containing the message content and any tool
                calls
            bot (Bot): The bot instance for handling tool calls and maintaining
                conversation state
        Returns:
            Tuple[str, str, Dict[str, Any]]: A tuple containing:
                - The final response content (str)
                - The role of the message (str)
                - Additional metadata dictionary (Dict[str, Any])
        """
        message: ChatCompletionMessage = response.choices[0].message
        if not message.tool_calls:  # base case
            return (message.content or "~", message.role, {})
        while message.tool_calls:  # recursive case
            bot.conversation = bot.conversation._add_reply(role="assistant", content=message.content or "~")
            bot.conversation._add_tool_calls(calls=bot.tool_handler.requests)
            bot.conversation._add_tool_results(results=bot.tool_handler.exec_requests())
            bot.tool_handler.clear()
            return self.process_response(bot.mailbox.send_message(bot), bot)


class ChatGPT_Bot(Bot):
    """A bot implementation using the OpenAI GPT API.
    Use when you need to create a bot that interfaces with OpenAI's chat
    completion models.
    Provides a complete implementation with OpenAI-specific conversation
    management, tool handling, and message processing. Supports both simple
    chat interactions and complex tool-using conversations.
    Inherits from:
        Bot: Base class for all bot implementations, providing core
            conversation and tool management
    Attributes:
        api_key (str): OpenAI API key for authentication
        model_engine (Engines): The OpenAI model being used (e.g., GPT4)
        max_tokens (int): Maximum tokens allowed in completion responses
        temperature (float): Response randomness factor (0-1)
        name (str): Instance name for identification
        role (str): Bot's role identifier
        role_description (str): Detailed description of bot's role/personality
        system_message (str): System-level instructions for the bot
        tool_handler (OpenAIToolHandler): Manages function calling capabilities
        conversation (OpenAINode): Manages conversation history
        mailbox (OpenAIMailbox): Handles API communication
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
        model_engine: Engines = Engines.GPT4,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        name: str = "bot",
        role: str = "assistant",
        role_description: str = "a friendly AI assistant",
        autosave: bool = True,
    ):
        """Initialize a ChatGPT bot with OpenAI-specific components.
        Use when you need to create a new OpenAI-based bot instance with
        specific configuration.
        Sets up all necessary components for OpenAI interaction including
        conversation management, tool handling, and API communication.
        Parameters:
            api_key (Optional[str]): OpenAI API key. If not provided, attempts
                to read from OPENAI_API_KEY environment variable
            model_engine (Engines): The OpenAI model to use, defaults to GPT-4.
                Determines capabilities and pricing
            max_tokens (int): Maximum tokens in completion response, defaults
                to 4096. Affects response length and API costs
            temperature (float): Response randomness (0-1), defaults to 0.3.
                Higher values make responses more creative but less focused
            name (str): Name of the bot instance, defaults to 'bot'. Used for
                identification in logs and saved states
            role (str): Role identifier for the bot, defaults to 'assistant'.
                Used in message formatting
            role_description (str): Description of the bot's role/personality,
                defaults to 'a friendly AI assistant'. Guides bot behavior
            autosave (bool): Whether to automatically save conversation state,
                defaults to True. Enables conversation recovery
        Note:
            The bot is initialized with OpenAI-specific implementations of:
            - OpenAIToolHandler for function calling
            - OpenAINode for conversation management
            - OpenAIMailbox for API communication
        """
        super().__init__(
            api_key=api_key,
            model_engine=model_engine,
            max_tokens=max_tokens,
            temperature=temperature,
            name=name,
            role=role,
            role_description=role_description,
            tool_handler=OpenAIToolHandler(),
            conversation=OpenAINode._create_empty(OpenAINode),
            mailbox=OpenAIMailbox(),
            autosave=autosave,
        )
