import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from openai import OpenAI
from datetime import datetime
import anthropic
from anthropic.types import ToolUseBlock
from abc import ABC, abstractmethod
import src.conversation_node as CN
from typing import Optional, Dict, Any
import threading
import inspect
import json
from typing import List, Callable
import ast

# TODO separate the singleton object - isolate it from ToolBuilder

class BaseMailbox(ABC):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log_file = r"data\mailbox_log.txt"

    def log_message(self, message: str, direction: str) -> None:
        timestamp = self.__formatted_datetime__()
        log_entry = f"[{timestamp}] {direction.upper()}:\n{message}\n\n"
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

    def __formatted_datetime__(self) -> str:
        now = datetime.now()
        return now.strftime("%Y-%m-%d %H:%M:%S")

    def send_message(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> tuple[str, str, Dict[str, Any]]:
        log_message = {
            "date": self.__formatted_datetime__(),
            "messages": conversation.to_dict(),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model,
        }
        self.log_message(json.dumps(log_message, indent=2), "OUTGOING")
        try:
            response = self._send_message_implementation(conversation, model, max_tokens, temperature, api_key, system_message)
        except Exception as e:
            raise e
        response_text, response_role = self._process_response(response)
        log_message = {
            "date": self.__formatted_datetime__(),
            "role": response_role,
            "content": response_text,
        }
        self.log_message(json.dumps(log_message, indent=2), "INCOMING")
        return response_text, response_role

    @abstractmethod
    def _send_message_implementation(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        pass

    @abstractmethod
    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str]:
        pass

    def batch_send(self, conversations, model, max_tokens, temperature, api_key, system_message=None):
        threads = []
        results = [None] * len(conversations)
        
        def send_thread(index, conv):
            result = self.send_message(conv, model, max_tokens, temperature, api_key, system_message)
            results[index] = result
        
        for i, conversation in enumerate(conversations):
            thread = threading.Thread(target=send_thread, args=(i, conversation))
            threads.append(thread)
            thread.start()
        
        for thread in threads:
            thread.join()
        
        return results

class OpenAIMailbox(BaseMailbox):
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.api_key = api_key or os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API key not provided.")

    def _send_message_implementation(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        client = OpenAI(api_key=api_key)
        messages = conversation.to_dict()
        if system_message:
            messages.insert(0, {"role": "system", "content": system_message})
        return client.chat.completions.create(
            messages=messages,
            max_tokens=max_tokens,
            temperature=temperature,
            model=model,
        )

    def _process_response(self, response: Dict[str, Any]) -> tuple:
        response_text = response.choices[0].message.content
        response_role = response.choices[0].message.role
        return response_text, response_role

class AnthropicMailbox(BaseMailbox):
    def __init__(self, api_key: Optional[str] = None, verbose: bool = False):
        super().__init__(verbose)
        self.tool_builder = AnthropicToolHandler()
        self.api_key = api_key or os.getenv("ANTHROPIC_API_KEY")
        if not self.api_key:
            raise ValueError("Anthropic API key not provided.")

    def _send_message_implementation(self, conversation: CN.ConversationNode, model: str, max_tokens: int, temperature: float, api_key: str, system_message: Optional[str] = None) -> Dict[str, Any]:
        client = anthropic.Anthropic(api_key=api_key)
        messages = self._fix_messages(conversation)
        
        # Prepare tools
        tools = self.tool_builder.tools if hasattr(self.tool_builder, 'tools') and self.tool_builder.tools else None
        
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
            print(f"System message: {system_message}")
            print(f"Messages: {messages}")
            print(f"Tools: {json.dumps(tools, indent=2) if tools else 'None'}")
            print('\n---debug---\n\n\n')
            raise e
        return response

    def _fix_messages(self, csvn: CN.ConversationNode) -> list[dict[str, str]]:
        messages = csvn.to_dict()
        return [msg for msg in messages if msg['role'] != 'system']

    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str]:
        if response.stop_reason == 'tool_use':
            tool_results = self.tool_builder.handle_tool_use(response)
            
            if tool_results:
                self.tool_builder.results.extend(tool_results)

        response_role = response.role
        match response.content[0].type:
            case 'text':
                response_text = response.content[0].text
            #case {'type': 'image', 'source': {'type': 'base64', 'media_type': _, 'data': data}}:
                #response_text = f"[Image data: {data[:20]}...]"
            case 'tool_use':
                response_text = f"[Tool use: {response.content[0].name} with input {response.content[0].input}]"
            case _:
                Warning("response.content[0].type does not match 'text' or 'tool_use'")
                response_text = str(response.content[0])
    
        if hasattr(self.tool_builder, 'results') and self.tool_builder.results:
            response_text += "\n\nTool Results:\n"
            for result in self.tool_builder.results:
                response_text += f"\n\n Tool: {result['function_name']}\n"
                response_text += f"  Result: {result['output']}\n\n"
            
            self.tool_builder.results = []
        
        return response_text, response_role

    def add_tools_from_py(self, filename):
        """Adds tools and tool processing for all top level python functions in the file"""
        self.tool_builder.add_tools(filename)

class AnthropicToolHandler:
        def __init__(self):
            self.tools = []
            self.function_map = {}
            self.results = []

        def add_python_function_tool(self, func: Callable):
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


        def tool_msg(self, *tool_functions: Callable) -> str:
            """
            Construct the tool portion of the api message string for Claude.
            """
            for func in tool_functions:
                self.add_python_function_tool(func)
            return json.dumps(self.tools, indent=2)
        
        def extract_functions(self, file_path: str):
            if not os.path.exists(file_path):
                raise FileNotFoundError(f"File '{file_path}' not found.")

            with open(file_path, 'r') as file:
                content = file.read()

            module = ast.parse(content)
            
            functions = []
            for node in module.body:
                if isinstance(node, ast.FunctionDef):
                    func_name = node.name
                    func_code = ast.get_source_segment(content, node)
                    
                    # Create a new module and execute the function definition
                    mod = ast.Module(body=[node], type_ignores=[])
                    compiled = compile(mod, filename="<ast>", mode="exec")
                    local_env = {}
                    exec(compiled, local_env)
                    
                    # Append only the function we just defined
                    functions.append(local_env[func_name])
            
            return functions
        
        def add_tools(self, file_path: str):
            """
            Extract all first-level functions from a file and add them as tools.

            Args:
            file_path (str): The path to the Python file.

            Returns:
            None.
            """
            functions = self.extract_functions(file_path)
            
            for func in functions:
                self.add_python_function_tool(func)
                    
        def handle_tool_use(self, response):
            tool_results = []

            for content in response.content:
                if hasattr(content, 'type') and content.type == 'tool_use':
                    tool_use_id = getattr(content, 'id', 'unknown_id')
                    tool_name = getattr(content, 'name', 'unknown_tool')
                    tool_input = getattr(content, 'input', {})

                    tool_function = next((tool for tool in self.tools if tool['name'] == tool_name), None)

                    if not tool_function:
                        tool_results.append({
                            "type": 'tool_result',
                            "function_name": 'unknown',
                            "tool_call_id": tool_use_id,
                            "output": f"Error: Tool '{tool_name}' not found.",
                        })
                        continue

                    try:
                        # Use the stored function in the tool dictionary
                        result = self.function_map[tool_name](**tool_input)
                        tool_results.append({
                            "type": 'tool_result',
                            "function_name": tool_name,
                            "tool_call_id": tool_use_id,
                            "output": str(result)
                        })
                    except Exception as e:
                        tool_results.append({
                            "type": 'tool_result',
                            "function_name": tool_name,
                            "tool_call_id": tool_use_id,
                            "output": f"Error executing tool '{tool_name}': {str(e)}",
                        })

            return tool_results if tool_results else None

"""Notes:
General structure for handling tool use responses

response = client.messages.create(
    model="claude-3-opus-20240229",
    max_tokens=1024,
    messages=[{"role": "user", "content": "Your message here"}],
    tools=[{
        "name": "your_tool_name",
        "description": "Your tool description",
        "input_schema": {
            "type": "object",
            "properties": {
                # Your tool's properties here
            },
            "required": ["required_property"]
        }
    }]
)

"""