from src.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
from typing import Optional, Dict, Any, Tuple, Callable, List
import inspect
from openai import OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
import os
import json

class OpenAINode(ConversationNode):
    def __init__(self, **kwargs: Any) -> None:
        role = kwargs.pop('role')
        content = kwargs.pop('content')
        super().__init__(role=role, content=content, **kwargs)

    def build_messages(self):
        node = self
        if node.is_empty():
            return []
        conversation_dict = []
        while node:

            if hasattr(node, 'tool_calls'):
                entry = node._to_dict_self()
            elif node.role == 'tool':
                entry = {'role': node.role, 'content': node.content, 'tool_call_id': node.tool_call_id}
            else:
                entry = {'role': node.role, 'content': node.content}
            
            conversation_dict = [entry] + conversation_dict
            node = node.parent

        return conversation_dict


class OpenAIToolHandler(ToolHandler):

    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate OpenAI-compatible function definitions."""
        schema = {
            'type': 'function',
            'function': {
                'name': func.__name__,
                'description': func.__doc__ or 'No description provided.',
                'parameters': {'type': 'object', 'properties': {}, 'required': []}
            }
        }
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            schema['function']['parameters']['properties'][param_name] = {
                'type': 'string',
                'description': f'Parameter: {param_name}'
            }
            if param.default == inspect.Parameter.empty:
                schema['function']['parameters']['required'].append(param_name)
        return schema

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI responses."""
        if hasattr(response.choices[0].message, 'tool_calls'):
            return [response.choices[0].message.model_dump()]
        else:
            return []

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Parse OpenAI's function call format."""
        # Precondition - the request schema has a tool call that is not None
        
        if not request_schema:
            return None, None
        
        if not 'tool_calls' in request_schema:
            return None, None
        
        if request_schema['tool_calls'] is None:
            return None, None
        
        request = {}
        tool_call = request_schema['tool_calls'][0]
        request = {
            'id': tool_call['id'],
            'type': tool_call['type'],
            'name': tool_call['function']['name'],
            'arguments': json.loads(tool_call['function']['arguments'])
        }
        self.add_request(request)
        return request['name'], request['arguments']

    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool results for OpenAI."""
        return {
            'role': 'tool',
            'content': json.dumps(tool_output_kwargs),
            'tool_call_id': request['tool_calls'][0]['id']
        }


class OpenAIMailbox(Mailbox):

    def __init__(self, api_key: Optional[str] = None):
        super().__init__()
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OpenAI API key not provided.')
        self.client = OpenAI(api_key=self.api_key)

    def send_message(self, bot) -> Dict[str, Any]:

        system_message = bot.system_message
        messages = bot.conversation.build_messages()
        # Add a system message if one is provided
        if system_message:
            messages.insert(0, {'role': 'system', 'content': system_message})

        # Include tools if available
        tools = bot.tool_handler.tools if bot.tool_handler else None

        # Send the message to the OpenAI API
        model = bot.model_engine
        max_tokens = bot.max_tokens
        temperature = bot.temperature

        if tools:
            response = self.client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens,
                temperature=temperature, tools=tools, tool_choice='auto')
        else:
            response = self.client.chat.completions.create(
                model=model, messages=messages, max_tokens=max_tokens,
                temperature=temperature)
        return response

    def process_response(self, response: Dict[str, Any], bot: Bot
        ) -> Tuple[str, str, Dict[str, Any]]:
        """Process the raw response and handle tool calls until no more are left."""
        
        message: ChatCompletionMessage = response.choices[0].message

        # If there are no tool calls, return the role and content
        if not message.tool_calls:
            response_text = message.content
            response_role = message.role
            extra_data = {}
            return response_text, response_role, extra_data

        # Otherwise, process the tool call
        if message.tool_calls:
            
            requests, results = bot.tool_handler.handle_response(response)           
            bot.conversation = bot.conversation.add_reply(**requests[1]) #TODO why the heck does requests look like this?
            for result in results:
                bot.conversation = bot.conversation.add_reply(**result)
            
            # Send results back to bot
            response = bot.mailbox.send_message(bot)
            
            # Use final message for text
            message = response.choices[0].message
            response_text = message.content
            response_role = message.role
            extra_data = {}
            return response_text, response_role, extra_data


class GPTBot(Bot):

    def __init__(self, 
                 api_key: Optional[str] = None, 
                 model_engine: Engines = Engines.GPT4,
                 max_tokens: int = 4096, 
                 temperature: float = 0.3, 
                 name: str = 'bot',
                 role: str = 'assistant', 
                 role_description: str = 'a friendly AI assistant',
                 ):
        
        super().__init__(api_key=api_key, 
                         model_engine=model_engine, 
                         max_tokens=max_tokens, 
                         temperature=temperature, 
                         name=name, 
                         role=role, 
                         role_description=role_description,
                         tool_handler = OpenAIToolHandler(),
                         conversation = OpenAINode.create_empty(OpenAINode),
                         mailbox = OpenAIMailbox()
                         )