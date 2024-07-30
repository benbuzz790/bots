# anthropic_bot.py

from src.base import Bot, Mailbox, ConversationNode, Engines, ToolHandler
import src.base as base
from typing import Optional, Dict, Any, List, Callable
import anthropic
import os
import inspect
import json
from typing import Union

class AnthropicNode(ConversationNode):
    def __init__(self, **kwargs):
        super().__init__(role=kwargs.get('role'), content=kwargs.get('content'))
        self.tool_use = kwargs.get('tool_use', [])
        self.tool_result = kwargs.get('tool_result', [])

    def add_tool_use(self, tool_use):
        self.tool_use = tool_use
    
    def add_tool_result(self, result):
        self.tool_result = result
    
    def get_message_list(self) -> List[Dict[str, Union[str, List[Dict[str, Any]]]]]:
        """
        Converts the conversation node and its replies to a list of dictionaries.
        """
        if self.is_empty():
            return []

        content: Union[str, List[Dict[str, Any]]]
        if not self.tool_result and not self.tool_use:
            content = self.content
        else:
            content = []
            if self.tool_use or self.tool_result:
                if self.tool_use:
                    for item in self.tool_use:
                        content.append(item)
                if self.tool_result:
                    for item in self.tool_result:
                        content.append(item)

        conversation_dict = [{"role": self.role, "content": content}]

        if self.parent is not None:
            parent_dict = self.parent.get_message_list()
            conversation_dict = parent_dict + conversation_dict
        return conversation_dict

class AnthropicToolHandler(ToolHandler):
    def __init__(self):
        super().__init__()

    def generate_tool_schema(self, func: Callable):
        sig = inspect.signature(func)
        doc = inspect.getdoc(func) or "No description provided."
        
        tool = {
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

    def handle_tool_use(self, response):

        for block in response.content:
            if hasattr(block, 'type') and block.type == 'tool_use':
                tool_use_id = getattr(block, 'id', 'unknown_id')
                tool_name = getattr(block, 'name', 'unknown_tool')
                tool_input = getattr(block, 'input', {})
                
                request = {attr: getattr(block, attr) for attr in ['type', 'id', 'name', 'input']}
                self.add_request(request)

                tool_function = next((tool for tool in self.tools if tool['name'] == tool_name), None)
                if not tool_function:
                    self.add_result({
                        "type": 'tool_result',
                        "tool_use_id": tool_use_id,
                        "content": f"Error: Tool '{tool_name}' not found.",
                    })
                    continue
                try:
                    result = self.function_map[tool_name](**tool_input)
                    self.add_result({
                        "type": 'tool_result',
                        "tool_use_id": tool_use_id,
                        "content": result
                    })
                except Exception as e:
                    result = f"Error executing tool '{tool_name}': {str(e)}"
                    self.add_result({
                        "type": 'tool_result',
                        "tool_use_id": tool_use_id,
                        "content": f"Error executing tool '{tool_name}': {str(e)}",
                    })
                
        return result

class AnthropicMailbox(Mailbox):
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False, tool_handler: AnthropicToolHandler=None):
        super().__init__(verbose)
        self.tool_handler = tool_handler
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided.")

    def set_tool_handler(self, tool_handler):
        self.tool_handler = tool_handler

    def _send_message_implementation(self, conversation: AnthropicNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        client = anthropic.Anthropic(api_key=api_key)

        # Add tool requests to the parent conversation node, if they exist:
        if self.tool_handler.requests:
            conversation.parent.add_tool_use(self.tool_handler.requests)

        # Add tool results to the current conversation node, if they exist:
        if self.tool_handler.results:
            conversation.add_tool_result(self.tool_handler.results)

        # Clear the tool handler's requests and results    
        self.tool_handler.clear()       

        # Send tools, if they exist
        tools = None
        if(self.tool_handler.tools):
            tools = self.tool_handler.tools


        messages = conversation.get_message_list()

        
        # Prepare kwargs for create method
        kwargs = {
            "model": model,
            "max_tokens": max_tokens,
            "temperature": temperature,
            "messages": messages,
        }
        
        if system_message:
            kwargs["system"] = system_message
        
        if tools:
            kwargs["tools"] = tools
        
        try:
            response = client.messages.create(**kwargs)
        except Exception as e:
            print('\n\n\n ---debug---\n')
            print(kwargs)
            print('\n---debug---\n\n\n')
            raise e
        return response

    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
        tool_results = []
        if response.stop_reason == 'tool_use':
            self.tool_handler.handle_tool_use(response)
            tool_results = self.tool_handler.get_results()

        response_role = response.role
        response_text = ""
        for block in response.content:
            if block.type == 'text':
                response_text += block.text
        
        return response_text, response_role, tool_results

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
        tool_handler: Optional[AnthropicToolHandler] = None,
        tool_path: Optional[str] = None ):

        conversation = AnthropicNode.create_empty()
        super().__init__(api_key, model_engine, max_tokens, temperature, name, role, role_description, conversation=conversation)
        
        self.mailbox = AnthropicMailbox(api_key=api_key, verbose=True, tool_handler=tool_handler)
        self.tool_handler = tool_handler
        self.tool_path = tool_path
        if self.tool_path and self.tool_handler:
            self.add_tools(self.tool_path)

    def add_tools(self, filepath):
        self.tool_path = filepath
        if self.tool_handler is None:
            self.tool_handler = AnthropicToolHandler()
        self.tool_handler.add_tools_from_file(filepath)
        self.mailbox.set_tool_handler(self.tool_handler)