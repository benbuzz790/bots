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
        # Extract required fields
        role = kwargs.pop('role', None)
        content = kwargs.pop('content', None)
        tool_calls = kwargs.pop('tool_calls', None)
        tool_results = kwargs.pop('tool_results', None)
        
        super().__init__(
            role=role,
            content=content,
            tool_calls=tool_calls,
            tool_results=tool_results,
            **kwargs
        )

    def build_messages(self) -> List[Dict[str, Any]]:
        node = self
        if node.is_empty():
            return []
        
        conversation_dict = []
        while node:
            # Create base message structure
            entry = {'role': node.role}
            
            # Build content list in Anthropic format
            content_list = [{'type': 'text', 'text': node.content}]
            
            #    Add tool calls if present
            if node.tool_calls:
                for call in node.tool_calls:
                    ent = {'type': 'tool_use', **call}
                    content_list.insert(-1, ent) 

            # Add tool results if present
            if node.tool_results:
                for result in node.tool_results:
                    ent = {'type': 'tool_result', **result}  
                    content_list.insert(0, ent)  


            entry['content'] = content_list
            conversation_dict = [entry] + conversation_dict
            node = node.parent
            
        return conversation_dict

class AnthropicToolHandler(ToolHandler):
    def __init__(self) -> None:
        super().__init__()

    def generate_tool_schema(self, func: Callable):         
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

        return tool

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

        # # Update conversation based on tool calls and results
        conversation: AnthropicNode = bot.conversation
        if bot.tool_handler and bot.tool_handler.requests and bot.tool_handler.results:
            conversation.parent.tool_calls = bot.tool_handler.requests
            conversation.tool_results = bot.tool_handler.results
        
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
        messages = cc.manage_cache_controls(messages, 1.0)

        # Add optional blocks to create_dict
        create_dict: Dict[str, Any] = {}
        system_message: Optional[str] = bot.system_message
        if tools:
            create_dict["tools"] = tools
        if system_message:
            create_dict["system"] = system_message


        # Create non-optional blocks and update create_dict
        model: Engines = bot.model_engine.value
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

    def process_response(self,
                        response: Dict[str, Any],
                        bot: Optional['AnthropicBot'] = None
                        ) -> Tuple[str, str, Dict[str, Any]]:
        
        # How should we handle responses from claude which are malformed?

        try:
            # For long outputs without tool use, we can prompt over and over rather
            # than ending mid-sentence.
            # If the stop reason was max tokens, request a continuation
            # Continuation is not allowed with tool calls

            def should_continue(response):
                return response.stop_reason == 'max_tokens' and not 'tool_calls' in response

            while should_continue(response):
                bot.conversation.add_reply(role= 'assistant', content=response.content[0].text)
                messages = bot.conversation.build_messages()
                response = self.send_message(bot)
                
            response_role: str = response.role
            response_text: str = getattr(response.content[0], 'text', '~')
            # The last line uses '~' if claude responds without a text block. Claude can do this,
            # but the API doesn't like it when you send that back. So I need to add a text block
            # here with some kind of indication that it contains nothing. '~' seems to do the 
            # trick.

            # Incorporate tool use via extra_data
            if response.stop_reason == 'tool_calls':
                requests = bot.tool_handler.get_requests()
                results = bot.tool_handler.get_results()
                extra_data: Dict[str, Any] = {"tool_calls": requests, "tool_results": results}
            else:
                extra_data = {}
        except anthropic.BadRequestError as e:
            print("--------------------------------------------")
            print("BAD REQUEST RUINED YOUR DAY AGAIN HAHAHAHAHA")
            print("--------------------------------------------")
            if e.status_code == 400:
                # determine if claude was responsible or if I was responsible:
                    # claude: tool params missing, tools not in toolmap,
                    # ben: default
                pass
            raise e


        return response_text, response_role, extra_data


class AnthropicBot(Bot):
    """
    A bot implementation using the Anthropic API.
    """
    def __init__(
        self,
        api_key: Optional[str] = None,
        model_engine: Engines = Engines.CLAUDE35_SONNET_20241022,
        max_tokens: int = 4096,
        temperature: float = 0.3,
        name: str = "Claude",
        role: str = "assistant",
        role_description: str = "a friendly AI assistant",
        autosave: bool = True
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
            mailbox=AnthropicMailbox(),
            autosave = autosave,
        )

class CacheController:
    def find_cache_control_positions(self, messages: List[Dict[str, Any]]) -> List[int]:
        positions = []
        for idx, msg in enumerate(messages):
            # Check content
            content = msg.get('content', None)
            if isinstance(content, list):
                for item in content:
                    if isinstance(item, dict) and 'cache_control' in item:
                        positions.append(idx)
                        break
            elif isinstance(content, dict) and 'cache_control' in content:
                positions.append(idx)
            
            # Check tool_calls
            tool_calls = msg.get('tool_calls', None)
            if tool_calls:
                for tool_call in tool_calls:
                    if isinstance(tool_call, dict) and tool_call.get('cache_control'):
                        positions.append(idx)
                        break
        
        return sorted(list(set(positions)))  # Remove duplicates and sort

    def should_add_cache_control(self, total_messages: int, last_control_pos: int, threshold: float = 1.0) -> bool:
        required_length = last_control_pos * (1 + threshold)
        return total_messages >= math.ceil(required_length)

    def shift_cache_control_out_of_tool_block(self, messages: List[Dict[str, Any]], position: int) -> int:
        """
        Moves cache control out of tool blocks and returns the new position where it was placed.
        """
        if position >= len(messages):
            return position

        msg = messages[position]
        content = msg.get('content', None)
        has_tool_block = False

        # Check if we're in a tool block
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and item.get('type') in ['tool_call', 'tool_result']:
                    has_tool_block = True
                    break
        elif isinstance(content, dict) and content.get('type') in ['tool_call', 'tool_result']:
            has_tool_block = True

        if has_tool_block:
            # Find the next non-tool message
            new_position = position + 1
            while new_position < len(messages):
                next_content = messages[new_position].get('content', None)
                is_tool = False
                
                if isinstance(next_content, list):
                    is_tool = any(isinstance(item, dict) and 
                                item.get('type') in ['tool_call', 'tool_result'] 
                                for item in next_content)
                elif isinstance(next_content, dict):
                    is_tool = next_content.get('type') in ['tool_call', 'tool_result']
                
                if not is_tool:
                    # Move cache control here
                    self.remove_cache_control_at_position(messages, position)
                    self.insert_cache_control(messages, new_position)
                    return new_position
                new_position += 1
            
            # If we couldn't find a non-tool message after, try to place it before
            new_position = position - 1
            while new_position >= 0:
                prev_content = messages[new_position].get('content', None)
                is_tool = False
                
                if isinstance(prev_content, list):
                    is_tool = any(isinstance(item, dict) and 
                                item.get('type') in ['tool_call', 'tool_result'] 
                                for item in prev_content)
                elif isinstance(prev_content, dict):
                    is_tool = prev_content.get('type') in ['tool_call', 'tool_result']
                
                if not is_tool:
                    # Move cache control here
                    self.remove_cache_control_at_position(messages, position)
                    self.insert_cache_control(messages, new_position)
                    return new_position
                new_position -= 1
                
        return position

    def insert_cache_control(self, messages: List[Dict[str, Any]], position: int) -> None:
        if position < 0 or position > len(messages):
            position = len(messages) - 1

        msg = messages[position]
        content = msg.get('content', None)

        # Handle content cache control
        if isinstance(content, str):
            msg['content'] = [{
                'type': 'text',
                'text': content,
                'cache_control': {"type": "ephemeral"}
            }]
        elif isinstance(content, list):
            if not any('cache_control' in item for item in content if isinstance(item, dict)):
                for item in content:
                    if isinstance(item, dict) and 'type' in item:
                        if item['type'] not in ['tool_call', 'tool_result']:
                            item['cache_control'] = {"type": "ephemeral"}
                            break
        elif isinstance(content, dict) and 'cache_control' not in content:
            if content.get('type') not in ['tool_call', 'tool_result']:
                content['cache_control'] = {"type": "ephemeral"}

        # Handle tool_calls cache control
        tool_calls = msg.get('tool_calls', None)
        if tool_calls:
            # Remove any existing cache_control from tool_calls
            for tool_call in tool_calls:
                if isinstance(tool_call, dict):
                    tool_call.pop('cache_control', None)

    def remove_cache_control_at_position(self, messages: List[Dict[str, Any]], position: int) -> None:
        if position < 0 or position >= len(messages):
            return

        msg = messages[position]
        
        # Remove from content
        content = msg.get('content', None)
        if isinstance(content, list):
            for item in content:
                if isinstance(item, dict) and 'cache_control' in item:
                    del item['cache_control']
        elif isinstance(content, dict) and 'cache_control' in content:
            del content['cache_control']
        
        # Remove from tool_calls
        tool_calls = msg.get('tool_calls', None)
        if tool_calls:
            for tool_call in tool_calls:
                if isinstance(tool_call, dict) and 'cache_control' in tool_call:
                    del tool_call['cache_control']

    def manage_cache_controls(self, messages: List[Dict[str, Any]], threshold: float = 1.0) -> List[Dict[str, Any]]:
        # Find existing cache_control positions
        cache_control_positions = self.find_cache_control_positions(messages)

        if not cache_control_positions:
            # No existing cache_control, add one at 75% position
            initial_position = math.ceil(len(messages) * 0.75) - 1
            self.insert_cache_control(messages, initial_position)
            initial_position = self.shift_cache_control_out_of_tool_block(messages, initial_position)
            cache_control_positions = [initial_position]
        elif len(cache_control_positions) == 1:
            # Only one cache_control exists, check if we need to add the second one
            last_control_pos = cache_control_positions[0]
            # First, ensure existing cache control is not in a tool block
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
            # Two or more cache_control blocks exist
            # First ensure existing cache controls are not in tool blocks
            updated_positions = []
            for pos in cache_control_positions:
                new_pos = self.shift_cache_control_out_of_tool_block(messages, pos)
                if new_pos not in updated_positions:
                    updated_positions.append(new_pos)
            cache_control_positions = sorted(updated_positions)
            
            last_control_pos = max(cache_control_positions)
            if self.should_add_cache_control(len(messages), last_control_pos, threshold):
                # Add new cache_control at the new position
                new_position = math.ceil(len(messages) * threshold) - 1
                self.insert_cache_control(messages, new_position)
                new_position = self.shift_cache_control_out_of_tool_block(messages, new_position)
                
                # Move the older cache_control to the front
                if cache_control_positions[0] != 0:
                    self.remove_cache_control_at_position(messages, cache_control_positions[0])
                    self.insert_cache_control(messages, 0)
                    self.shift_cache_control_out_of_tool_block(messages, 0)
                
                # Clean up any extra cache_controls
                cache_control_positions = self.find_cache_control_positions(messages)
                if len(cache_control_positions) > 2:
                    for pos in cache_control_positions[2:]:
                        self.remove_cache_control_at_position(messages, pos)

        return messages