# anthropic_bot.py

from bots.foundation.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
from typing import Optional, Dict, Any, List, Callable, Tuple
import anthropic
import os
import inspect
import random
import time
import math


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
            tools[-1]["cache_control"] = {"type": "ephemeral"}

        # Build messages block
        messages: List[Dict[str, Any]] = conversation.build_messages()

        cc = CacheController()
        messages = cc.manage_cache_controls(messages, .25)

        # Add optional blocks to create_dict
        create_dict: Dict[str, Any] = {}
        system_message: Optional[str] = bot.system_message
        if tools:
            create_dict["tools"] = tools
        if system_message:
            create_dict["system"] = system_message


        # Create non-optional blocks and update create_dict
        model: Engines = bot.model_engine
        max_tokens: int = bot.max_tokens
        temperature: float = bot.temperature
        non_optional = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        create_dict.update(**non_optional)

        # Send message, automatically handling rate limits and server errors
        max_retries: int = 25
        base_delay: float = 1
        for attempt in range(max_retries):
            try:
                response = self.client.beta.prompt_caching.messages.create(**create_dict)
                #response: Dict[str, Any] = self.client.messages.create(**create_dict)
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


class CacheController():
    def find_cache_control_positions(self, messages: List[Dict[str, Any]]) -> List[int]:
        positions = []
        for idx, msg in enumerate(messages):
            content = msg.get('content', None)
            if isinstance(content, list):
                for item in content:
                    if 'cache_control' in item:
                        positions.append(idx)
                        break  # Assuming one cache_control per message
            elif isinstance(content, dict):
                if 'cache_control' in content:
                    positions.append(idx)
        return positions

    def should_add_cache_control(self, total_messages: int, last_control_pos: int, threshold: float = 0.25) -> bool:
        required_length = last_control_pos * (1 + threshold)
        return total_messages >= math.ceil(required_length)

    def insert_cache_control(sel, messages: List[Dict[str, Any]], position: int) -> None:
        if position < 0 or position > len(messages):
            position = len(messages) - 1  # Default to last message if out of bounds

        msg = messages[position]
        content = msg.get('content', None)

        if isinstance(content, str):
            # Convert string content to a list of dictionaries
            text = content
            msg['content'] = [{
                'type': 'text',
                'text': text
            }]
            content = msg['content']

        if isinstance(content, list):
            # Add cache_control to the last content block
            last_content = content[-1]
            last_content['cache_control'] = {"type": "ephemeral"}
        elif isinstance(content, dict):
            # Directly add cache_control
            msg['content']['cache_control'] = {"type": "ephemeral"}

    def remove_cache_control_at_position(self, messages: List[Dict[str, Any]], position: int) -> None:
        if position < 0 or position >= len(messages):
            return  # Invalid position

        msg = messages[position]
        content = msg.get('content', None)

        if isinstance(content, list):
            for item in content:
                if 'cache_control' in item:
                    del item['cache_control']
        elif isinstance(content, dict):
            if 'cache_control' in content:
                del content['cache_control']

    def manage_cache_controls(self, messages: Any, threshold: float = 0.25) -> List[Dict[str, Any]]:

        # Find existing cache_control positions
        cache_control_positions = self.find_cache_control_positions(messages)

        if not cache_control_positions:
            # No existing cache_control, add one at 75% position
            initial_position = math.ceil(len(messages) * 0.75) - 1
            self.insert_cache_control(messages, initial_position)
            cache_control_positions.append(initial_position)
        elif len(cache_control_positions) == 1:
            # Only one cache_control exists, check if we need to add the second one
            last_control_pos = cache_control_positions[-1]
            if self.should_add_cache_control(len(messages), last_control_pos, threshold):
                new_position = math.ceil(len(messages) * threshold) - 1
                self.insert_cache_control(messages, new_position)
                cache_control_positions.append(new_position)
        else:
            # Two cache_control blocks exist, check if we need to add a new one
            # Identify the latest cache_control position
            last_control_pos = max(cache_control_positions)
            if self.should_add_cache_control(len(messages), last_control_pos, threshold):
                # Add new cache_control at the new position
                new_position = math.ceil(len(messages) * threshold) - 1
                self.insert_cache_control(messages, new_position)
                
                # Move the older cache_control to the front
                if cache_control_positions[0] != 0:
                    # Remove cache_control from its current position
                    self.remove_cache_control_at_position(messages, cache_control_positions[0])
                    
                    # Insert cache_control at the front (position 0)
                    self.insert_cache_control(messages, 0)
                
                # Update cache_control_positions to keep only the two
                cache_control_positions = self.find_cache_control_positions(messages)
                if len(cache_control_positions) > 2:
                    # Remove any extra cache_controls if present
                    for pos in cache_control_positions[2:]:
                        self.remove_cache_control_at_position(messages, pos)
                    cache_control_positions = cache_control_positions[:2]

        return messages