# anthropic_bot.py

from bots.foundation.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
from typing import Optional, Dict, Any, List, Callable, Tuple
import anthropic
import os
import inspect
import random
import time


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

    def generate_response_schema(
        self,
        request: Dict[str, Any],
        tool_output_kwargs: Dict[str, Any]
    ) -> Dict[str, Any]:
        response: Dict[str, Any] = {
            "type": "tool_result",
            "tool_use_id": request.get("id", "unknown id"),
            "content": tool_output_kwargs
        }

        return response

class AnthropicMailbox(Mailbox):
    def __init__(self, verbose: bool = False):
        super().__init__()
        self.last_message: Optional[Dict[str, Any]] = None
        self.client: Optional[anthropic.Anthropic] = None

    def send_message(self, bot: 'AnthropicBot') -> Dict[str, Any]:
        """Sends a bot message using the Anthropic API"""

        # Check API Key
        api_key: Optional[str] = bot.api_key
        if not api_key:
            try:
                api_key = os.getenv("ANTHROPIC_API_KEY")
            except:
                raise ValueError("Anthropic API key not found. Set up 'ANTHROPIC_API_KEY' environment variable.")
        self.client = anthropic.Anthropic(api_key=api_key)

        # Update conversation based on tool calls and results
        conversation: AnthropicNode = bot.conversation
        if bot.tool_handler and bot.tool_handler.requests:
            if isinstance(conversation.parent.content, str):
                conversation.parent.content = [{'type': 'text', 'text': conversation.parent.content}]
            conversation.parent.content.extend(bot.tool_handler.requests)

        if bot.tool_handler and bot.tool_handler.results:
            if isinstance(conversation.content, str):
                conversation.content = [{'type': 'text', 'text': conversation.content}]
            conversation.content = bot.tool_handler.results + conversation.content
        
        # Clear old tool calls and results
        if bot.tool_handler:
            bot.tool_handler.clear()

        # Build tools block
        tools: Optional[List[Dict[str, Any]]] = None
        if bot.tool_handler and bot.tool_handler.tools:
            tools = bot.tool_handler.tools

        # Build messages block
        messages: List[Dict[str, Any]] = conversation.build_messages()

        # Build API package
        model: Engines = bot.model_engine
        max_tokens: int = bot.max_tokens
        temperature: float = bot.temperature
        create_dict: Dict[str, Any] = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }

        # Add optional blocks
        system_message: Optional[str] = bot.system_message
        if system_message:
            create_dict["system"] = system_message
        if tools:
            create_dict["tools"] = tools

        # Send message, automatically handling rate limits and server errors
        max_retries: int = 25
        base_delay: float = 1
        for attempt in range(max_retries):
            try:
                response: Dict[str, Any] = self.client.messages.create(**create_dict)
                return response
            except (anthropic.InternalServerError, anthropic.RateLimitError) as e:
                if attempt == max_retries - 1:
                    print('\n\n\n ---debug---\n')
                    print(create_dict)
                    print('\n---debug---\n\n\n')
                    raise e
                delay: float = base_delay * (2 ** attempt) + random.uniform(0, 1)
                print(f"Attempt {attempt + 1} failed with {e.__class__.__name__}. "
                      f"Retrying in {delay:.2f} seconds...")
                time.sleep(delay)

        raise Exception("Max retries reached. Unable to send message.")

    def merge_content(self, existing_content: Any, new_content: Any) -> Any:
        if isinstance(existing_content, str) and isinstance(new_content, str):
            return (existing_content + new_content).strip()
        
        elif isinstance(existing_content, str) and isinstance(new_content, list):
            if new_content and new_content[0]['type'] == 'text':
                return ([{'type': 'text', 'text': (existing_content + new_content[0]['text']).strip()}] +
                        new_content[1:])
            else:
                return [{'type': 'text', 'text': existing_content.strip()}] + new_content
        
        elif isinstance(existing_content, list) and isinstance(new_content, list):
            return new_content  # new_content contains all of old_content
        
        elif isinstance(existing_content, list) and isinstance(new_content, str):
            if existing_content and existing_content[-1]['type'] == 'text':
                existing_content[-1]['text'] = (existing_content[-1]['text'] + new_content).strip()
            else:
                existing_content.append({'type': 'text', 'text': new_content.strip()})
            return existing_content
        else:
            raise ValueError("Unexpected content types")


    def process_response(self,
                        response: Dict[str, Any],
                        bot: Optional['AnthropicBot'] = None
                        ) -> Tuple[str, str, Dict[str, Any]]:
        
        # If the stop reason was max tokens, request continuation
        # Continuation is not allowed with tool calls

        def should_continue(response):
            return response.stop_reason == 'max_tokens' and not 'tool_calls' in response

        message = bot.conversation.build_messages()
        while should_continue(response):
            message.append({'role': response.role, 'content':response.content[0].text})
            response = self.client.messages.create(**message)
            
        response_role: str = response.role
        response_text: str = response.content[0].text

        # Incorporate tool use via extra_data
        if response.stop_reason == 'tool_calls':
            requests = bot.tool_handler.get_requests()
            results = bot.tool_handler.get_results()
            extra_data: Dict[str, Any] = {"requests": requests, "results": results}
        else:
            extra_data = {}
        return response_text, response_role, extra_data


class AnthropicBot(Bot):
    """
    A bot implementation using the Anthropic API.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_engine: Engines = Engines.CLAUDE35_SONNET,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        name: str = "Claude",
        role: str = "assistant",
        role_description: str = "a friendly AI assistant",
    ) -> None:

        super().__init__(
            api_key,
            model_engine,
            max_tokens,
            temperature,
            name,
            role,
            role_description,
            conversation=AnthropicNode.create_empty(AnthropicNode),
            tool_handler=AnthropicToolHandler(),
            mailbox=AnthropicMailbox()
        )


