# anthropic_bot.py

from src.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
import src.base as base
from typing import Optional, Dict, Any, List, Callable, Tuple
import anthropic
import os
import inspect


class AnthropicNode(ConversationNode):
    def __init__(self, **kwargs: Any) -> None:
        super().__init__(role=kwargs.pop('role'), content=kwargs.pop('content'))
        for key, value in kwargs.items():
            self.content += f"{key}: {value}"


class AnthropicToolHandler(ToolHandler):
    def __init__(self) -> None:
        super().__init__()

    def generate_tool_schema(self, func: Callable) -> None:
        sig: inspect.Signature = inspect.signature(func)
        doc: str = inspect.getdoc(func) or "No description provided."

        tool: Dict[str, Any] = {
            "name": func.__name__,
            "description": doc,
            "input_schema": {
                "type": "object",
                "properties": {},
                "required": []
            }
        }

        for param_name, param in sig.parameters.items():
            tool["input_schema"]["properties"][param_name] = {"type": "string"}
            if param.default == inspect.Parameter.empty:
                tool["input_schema"]["required"].append(param_name)

        self.tools.append(tool)
        self.function_map[func.__name__] = func

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """
        Generate request schema from response
        Return list of schemas (multiple requests may be in one message)
        """
        requests: List[Dict[str, Any]] = []
        for block in response.content:
            if block.type == 'tool_use':
                request = {attr: getattr(block, attr) for attr in ['type', 'id', 'name', 'input']}
                requests.append(request)
        return requests

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        tool_name: str = request_schema['name']
        tool_input: Dict[str, Any] = request_schema['input']
        return tool_name, tool_input

    def generate_response_schema(self, request: Dict[str, Any],
                                 tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        response: Dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": request.get("id", "unknown id"),
            "content": tool_output_kwargs
        }

        return response


class AnthropicMailbox(Mailbox):
    def __init__(self, verbose: bool = False, tool_handler: Optional[AnthropicToolHandler] = None):
        super().__init__()
        self.tool_handler: Optional[AnthropicToolHandler] = tool_handler

    def set_tool_handler(self, tool_handler: AnthropicToolHandler) -> None:
        self.tool_handler = tool_handler

    def _send_message_implementation(self, conversation: AnthropicNode, model: str, max_tokens: int,
                                     temperature: float, api_key: Optional[str] = None,
                                     system_message: Optional[str] = None) -> Dict[str, Any]:

        if not api_key:
            try:
                api_key = os.getenv("ANTHROPIC_API_KEY")
            except:
                raise ValueError("Anthropic API key not found. Set up 'ANTHROPIC_API_KEY' environment variable.")
        client: anthropic.Anthropic = anthropic.Anthropic(api_key=api_key)

        # Anthropic expects tool requests and results in the messages block,
        # so they need to be added to the conversation nodes, so that they
        # are present when build_messages() is called.

        if self.tool_handler and self.tool_handler.requests:
            if isinstance(conversation.parent.content, str):
                conversation.parent.content = [{'type': 'text', 'text': conversation.parent.content}]
            conversation.parent.content.extend(self.tool_handler.requests)

        if self.tool_handler and self.tool_handler.results:
            if isinstance(conversation.content, str):
                conversation.content = [{'type': 'text', 'text': conversation.content}]
            conversation.content = self.tool_handler.results + conversation.content
        if self.tool_handler:
            self.tool_handler.clear()

        # Send tools, if they exist
        tools: Optional[List[Dict[str, Any]]] = None
        if self.tool_handler and self.tool_handler.tools:
            tools = self.tool_handler.tools

        messages: List[Dict[str, Any]] = conversation.build_messages()

        # Prepare dict for create method. Model params do not go in the messages block
        create_dict: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        # System message and tools do not go in the messages block either
        if system_message:
            create_dict["system"] = system_message

        if tools:
            create_dict["tools"] = tools

        try:
            response: Dict[str, Any] = client.messages.create(**create_dict)
        except Exception as e:
            print('\n\n\n ---debug---\n')
            print(create_dict)
            print('\n---debug---\n\n\n')
            raise e
        return response

    def _process_response(self, response: Dict[str, Any]) -> Tuple[str, str, Dict[str, Any]]:
        tool_results: List[Dict[str, Any]] = []
        if response.stop_reason == 'tool_use':
            tool_requests, tool_results = self.tool_handler.handle_response(response)
            extra_data: Dict[str, Any] = {"requests": tool_requests, "results": tool_results}
        else:
            extra_data = {}

        response_role: str = response.role
        response_text: str = ""
        for block in response.content:
            if block.type == 'text':
                response_text += block.text

        return response_text, response_role, extra_data


class AnthropicBot(Bot):
    def __init__(
            self,
            api_key: Optional[str] = None,
            model_engine: Engines = Engines.CLAUDE35,
            max_tokens: int = 4096,
            temperature: float = 0.3,
            name: str = "Claude",
            role: str = "assistant",
            role_description: str = "a friendly AI assistant",
    ) -> None:

        super().__init__(api_key,
                         model_engine,
                         max_tokens,
                         temperature,
                         name,
                         role,
                         role_description,
                         conversation=AnthropicNode.create_empty(),
                         tool_handler=AnthropicToolHandler(),
                         mailbox=AnthropicMailbox())

        self.mailbox.tool_handler = self.tool_handler