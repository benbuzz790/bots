from bots.foundation.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
from typing import Optional, Dict, Any, Tuple, Callable, List
import inspect
from openai import OpenAI
from openai.types.chat.chat_completion_message import ChatCompletionMessage
import os
import json

class OpenAINode(ConversationNode):

    def __init__(self, **kwargs: Any) -> None:
        super().__init__(**kwargs)
        
    def _build_messages(self):
        """Build message list for OpenAI API, properly handling empty nodes and tool calls"""
        node = self
        conversation_dict = []
        while node:
            if node._is_empty():
                node = node.parent
                continue

            if node.role == 'user':
                conversation_dict = [{'role': 'user', 'content': node.content}] + conversation_dict
            
            if node.role == 'assistant':
                
                if not (node.tool_calls or node.tool_results):
                    assistant_msg = {'role': 'assistant', 'content': node.content}
                    conversation_dict = [assistant_msg] + conversation_dict
                    node = node.parent
                    continue
                
                for result in node.tool_results:
                    conversation_dict = [result] + conversation_dict

                if node.tool_calls:
                    assistant_msg = {'role': 'assistant', 'content': node.content, 'tool_calls': node.tool_calls}
                    conversation_dict = [assistant_msg] + conversation_dict

            node = node.parent
        return conversation_dict

class OpenAIToolHandler(ToolHandler):

    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """Generate OpenAI-compatible function definitions."""
        schema = {'type': 'function', 'function': {'name': func.__name__, 'description': func.__doc__ or 'No description provided.', 'parameters': {'type': 'object', 'properties': {}, 'required': []}}}
        sig = inspect.signature(func)
        for param_name, param in sig.parameters.items():
            schema['function']['parameters']['properties'][param_name] = {'type': 'string', 'description': f'Parameter: {param_name}'}
            if param.default == inspect.Parameter.empty:
                schema['function']['parameters']['required'].append(param_name)
        return schema

    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """Extract tool calls from OpenAI responses."""
        if hasattr(response.choices[0].message, 'tool_calls') and response.choices[0].message.tool_calls is not None:
            return [{'id': tool_call.id, 'type': tool_call.type, 'function': {'name': tool_call.function.name, 'arguments': tool_call.function.arguments}} for tool_call in response.choices[0].message.tool_calls]
        return []

    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[str, Dict[str, Any]]:
        """Parse OpenAI's function call format."""
        if not request_schema:
            return (None, None)
        return (request_schema['function']['name'], json.loads(request_schema['function']['arguments']))

    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """Format tool results for OpenAI."""
        return {'role': 'tool', 'content': str(tool_output_kwargs), 'tool_call_id': request['id']}

    def generate_error_schema(self, request_schema: Optional[Dict[str, Any]], error_msg: str) -> Dict[str, Any]:
        """
        Generate an error response schema matching the format expected by this handler.

        Args:
            request_schema: Optional original request schema that caused the error
            error_msg: The error message to include

        Returns:
            Dict containing the error in the correct schema format for this handler
        """
        return {'role': 'tool', 'content': error_msg, 'tool_call_id': request_schema['id'] if request_schema else 'unknown'}

class OpenAIMailbox(Mailbox):

    def __init__(self, api_key: Optional[str]=None):
        super().__init__()
        self.api_key = api_key or os.getenv('OPENAI_API_KEY')
        if not self.api_key:
            raise ValueError('OpenAI API key not provided.')
        self.client = OpenAI(api_key=self.api_key)

    def send_message(self, bot) -> Dict[str, Any]:
        system_message = bot.system_message
        messages = bot.conversation._build_messages()
        try:
            self._log_message(json.dumps({'messages': messages}, indent=2), 'OUTGOING')
        except FileNotFoundError:
            pass
        if system_message:
            messages.insert(0, {'role': 'system', 'content': system_message})
        tools = bot.tool_handler.tools if bot.tool_handler else None
        model = bot.model_engine
        max_tokens = bot.max_tokens
        temperature = bot.temperature
        try:
            if tools:
                response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature, tools=tools, tool_choice='auto')
            else:
                response = self.client.chat.completions.create(model=model, messages=messages, max_tokens=max_tokens, temperature=temperature)
            try:
                self._log_message(json.dumps({'response': response.model_dump()}, indent=2), 'INCOMING')
            except FileNotFoundError:
                pass
            return response
        except Exception as e:
            raise e

    def process_response(self, response: Dict[str, Any], bot: Bot) -> Tuple[str, str, Dict[str, Any]]:
        """Process the raw response and handle tool calls until no more are left."""
        message: ChatCompletionMessage = response.choices[0].message
        
        if not message.tool_calls: # base case
            return (message.content or '~', message.role, {})
        
        while message.tool_calls: # recursive case
            bot.conversation = bot.conversation._add_reply(role='assistant', content=message.content or '~')
            bot.conversation._add_tool_calls(calls=bot.tool_handler.requests)
            bot.conversation._add_tool_results(results=bot.tool_handler.exec_requests())
            bot.tool_handler.clear()
            return self.process_response(bot.mailbox.send_message(bot), bot)

class ChatGPT_Bot(Bot):
    """
    A bot implementation using the OpenAI GPT API.
    """

    def __init__(self, api_key: Optional[str]=None, model_engine: Engines=Engines.GPT4, max_tokens: int=4096, temperature: float=0.3, name: str='bot', role: str='assistant', role_description: str='a friendly AI assistant', autosave: bool=True):
        super().__init__(api_key=api_key, model_engine=model_engine, max_tokens=max_tokens, temperature=temperature, name=name, role=role, role_description=role_description, tool_handler=OpenAIToolHandler(), conversation=OpenAINode._create_empty(OpenAINode), mailbox=OpenAIMailbox(), autosave=autosave)
