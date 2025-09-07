"""
Gemini-specific implementations of the bot framework components.

This module provides Gemini-specific implementations of conversation nodes,
tool handling, message processing, and the main bot class.

Key Components:
    - GeminiNode: Manages conversation history in Gemini's expected format
    - GeminiToolHandler: Handles function calling with Gemini's schema
    - GeminiMailbox: Manages API communication with Gemini
    - GeminiBot: Main bot implementation for Gemini models
"""

from typing import Any, Callable, Dict, List, Optional, Tuple
from google import genai
from google.genai import types
import os
import json

from bots.foundation.base import (
    Bot,
    ConversationNode,
    Engines,
    Mailbox,
    ToolHandler,
)

class GeminiNode(ConversationNode):
    """
    Conversation node implementation for Gemini's chat format.
    """
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)

    def _build_messages(self) -> List[Any]:
        # Gemini expects a list of content strings or dicts
        # We'll traverse from root to current node, collecting messages
        messages = []
        node = self
        stack = []
        while node:
            if not node._is_empty():
                stack.append(node)
            node = node.parent
        for n in reversed(stack):
            if n.role == "user":
                messages.append(n.content)
            elif n.role == "assistant":
                messages.append(n.content)
            elif n.role == "tool":
                # Gemini may expect tool results as content or as structured part
                messages.append(n.content)
        return messages

class GeminiToolHandler(ToolHandler):
    """
    Tool handler for Gemini's function calling format.
    """
    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        # Generate a JSON Schema for the function
        schema = {
            "name": func.__name__,
            "description": func.__doc__ or "No description provided.",
            "parameters": {
                "type": "object",
                "properties": {},
                "required": [],
            },
        }
        import inspect
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            schema["parameters"]["properties"][param_name] = {
                "type": "string",
                "description": f"Parameter: {param_name}",
            }
            if param.default == inspect.Parameter.empty:
                schema["parameters"]["required"].append(param_name)
        return schema

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        # Extract function calls from Gemini response
        calls = []
        try:
            candidates = response.candidates if hasattr(response, 'candidates') else []
            for cand in candidates:
                parts = cand.content.parts if hasattr(cand.content, 'parts') else []
                for part in parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        calls.append({
                            "name": part.function_call.name,
                            "args": part.function_call.args,
                        })
        except Exception:
            pass
        return calls

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        if not request_schema:
            return (None, {})
        return (
            request_schema.get("name"),
            request_schema.get("args", {}),
        )

    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        # Return a string result for Gemini
        return {
            "role": "tool",
            "content": json.dumps(tool_output_kwargs),
            "tool_call_id": request.get("id", "unknown"),
        }

    def generate_error_schema(self, request_schema: Optional[Dict[str, Any]], error_msg: str) -> Dict[str, Any]:
        return {
            "role": "tool",
            "content": error_msg,
            "tool_call_id": (request_schema.get("id") if request_schema else "unknown"),
        }

class GeminiMailbox(Mailbox):
    """
    Mailbox implementation for Gemini API communication.
    """
    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GOOGLE_API_KEY") or os.getenv("GEMINI_API_KEY")
        if not self.api_key:
            raise ValueError("Google Gemini API key not provided.")
        # Pass api_key directly to Client constructor instead of using configure
        self.client = genai.Client(api_key=self.api_key)

    def send_message(self, bot: Bot) -> Any:
        messages = bot.conversation._build_messages()
        tools = bot.tool_handler.tools if bot.tool_handler else None
        tool_decls = []
        if tools:
            for t in tools:
                if "function" in t:
                    tool_decls.append(t["function"])
                else:
                    tool_decls.append(t)
        config = types.GenerateContentConfig()
        if tool_decls:
            config.tools = [types.Tool(function_declarations=tool_decls)]
        response = self.client.models.generate_content(
            model=bot.model_engine,
            contents=messages,
            config=config,
        )
        return response

    def process_response(self, response: Any, bot: Bot) -> Tuple[str, str, Dict[str, Any]]:
        # If there is a function call, handle it recursively
        handler = bot.tool_handler
        requests = handler.generate_request_schema(response)
        if not requests:
            # Return the first candidate's text as the response
            text = getattr(response, 'text', None)
            if not text:
                # Try to get from parts
                try:
                    text = response.candidates[0].content.parts[0].text
                except Exception:
                    text = "~"
            return (text, "assistant", {})
        # There is at least one tool call
        for req in requests:
            tool_name, tool_args = handler.tool_name_and_input(req)
            if tool_name in handler.function_map:
                tool_func = handler.function_map[tool_name]
                try:
                    result = tool_func(**tool_args)
                except Exception as e:
                    result = str(e)
            else:
                result = f"Tool {tool_name} not found."
            # Add tool result to conversation
            bot.conversation = bot.conversation._add_reply(role="tool", content=json.dumps(result))
        # Recursively send the updated conversation
        return self.process_response(self.send_message(bot), bot)

class GeminiBot(Bot):
    """
    Bot implementation using the Gemini API.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_engine: Engines = Engines.GEMINI25_FLASH,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        name: str = "bot",
        role: str = "assistant",
        role_description: str = "a friendly AI assistant",
        autosave: bool = True,
    ):
        super().__init__(
            api_key=api_key,
            model_engine=model_engine,
            max_tokens=max_tokens,
            temperature=temperature,
            name=name,
            role=role,
            role_description=role_description,
            tool_handler=GeminiToolHandler(),
            conversation=GeminiNode._create_empty(GeminiNode),
            mailbox=GeminiMailbox(api_key=api_key),
            autosave=autosave,
        )