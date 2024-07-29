# base.py

import os
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Union, Type, Dict, Any, List, Callable
import datetime as DT
import json
import re
import ast
from types import ModuleType
import threading
import inspect
import hashlib

# Utility Functions
def remove_code_blocks(text: str) -> tuple[List[str], List[str]]:
    pattern = r'```(\w*)\s*([\s\S]*?)```'
    matches = re.findall(pattern, text)
    code_blocks = [match[1].strip() for match in matches]
    labels = [match[0].strip() for match in matches]
    text = re.sub(pattern, '', text)
    return code_blocks, labels

def load(filepath: str) -> "Bot":
    return Bot.load(filepath)

def formatted_datetime() -> str:
    now = DT.datetime.now()
    return now.strftime("%Y-%m-%d_%H-%M-%S")

class Engines(Enum):
    """Enum class representing different AI model engines."""
    GPT4 = "gpt-4"
    GPT432k = "gpt-4-32k"
    GPT35 = "gpt-3.5-turbo"
    CLAUDE3OPUS = "claude-3-opus-20240229"
    CLAUDE3SONNET = "claude-3-sonnet-20240229"
    CLAUDE35 = "claude-3-5-sonnet-20240620"

    @staticmethod
    def get_bot_class(model_engine: "Engines") -> Type["Bot"]:
        """Returns the bot class based on the model engine. Bit of a kluge for now"""
        if model_engine in [Engines.GPT4, Engines.GPT35, Engines.GPT432k]:
            from src.openai_bots import GPTBot
            return GPTBot
        elif model_engine in [Engines.CLAUDE3OPUS, Engines.CLAUDE3SONNET, Engines.CLAUDE35]:
            from src.anthropic_bots import AnthropicBot
            return AnthropicBot
        else:
            raise ValueError(f"Unsupported model engine: {model_engine}")

class ConversationNode:
          
    def __init__(self, content, role, **kwargs):
        self.attributes = kwargs
        self.role = role
        self.content = content
        self.replies: List["ConversationNode"] = []
        self.parent: Optional["ConversationNode"] = None

    def copy(self):
        new_node = self.__class__(**self.attributes)
        new_node.replies = [reply.copy() for reply in self.replies]
        return new_node

    def add_reply(self, **kwargs) -> "ConversationNode":
        reply = self.__class__(**kwargs, parent=self)
        self.replies.append(reply)
        return reply
    
    @classmethod
    def create_empty(cls) -> 'ConversationNode':
        return cls(role="empty", content="")

    def is_empty(self) -> bool:
        return self.role == "empty" and self.content == ""

    def add_reply(self, **kwargs) -> 'ConversationNode':
        if self.is_empty():
            # If this node is empty, update it instead of adding a reply
            self.__init__(**kwargs)
            return self
        else:
            reply = self.__class__(**kwargs)
            reply.parent = self
            self.replies.append(reply)
            return reply
    
    def get_message_list(self) -> List[Dict[str, str]]:
        """
        Converts the conversation node and its replies to a list of dictionaries.
        """
        node = self
        if node.is_empty():
            return []
        conversation_dict = [{"role": node.role, "content": node.content}]
        if node.parent is not None:
            parent_dict = node.parent.get_message_list()
            conversation_dict = parent_dict + conversation_dict
        return conversation_dict
    
    def to_dict(self) -> Dict[str, Any]:
        result = {k: v for k, v in self.attributes.items() if k != 'parent'}
        if self.replies:
            result['replies'] = [reply.to_dict() for reply in self.replies]
        return result
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "ConversationNode":
        node = cls(**{k: v for k, v in data.items() if k != 'replies'})
        for reply_data in data.get("replies", []):
            reply_node = cls.from_dict(reply_data)
            reply_node.parent = node
            node.replies.append(reply_node)
        return node
    
    @classmethod
    def create_empty(cls):
        return cls(role="empty", content="")



class Mailbox(ABC):
    def __init__(self, verbose: bool = False):
        self.verbose = verbose
        self.log_file = r"data\mailbox_log.txt"

    def log_message(self, message: str, direction: str) -> None:
        timestamp = formatted_datetime()
        log_entry = f"[{timestamp}] {direction.upper()}:\n{message}\n\n"
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

    def send_message(self, 
            conversation: ConversationNode, 
            model: str, 
            max_tokens: int, 
            temperature: float, 
            api_key: str, 
            system_message: Optional[str] = None
            ) -> tuple[str, str, Dict[str, Any]]:
        self._log_outgoing(conversation, model, max_tokens, temperature)
        try:
            response = self._send_message_implementation(conversation, model, max_tokens, temperature, api_key, system_message)
            processed_response = self._process_response(response)
        except Exception as e:
            raise e
        self._log_incoming(processed_response)
        return processed_response

    @abstractmethod
    def _send_message_implementation(self, 
            conversation: ConversationNode, 
            model: str, 
            max_tokens: int, 
            temperature: float, 
            api_key: str, 
            system_message: Optional[str] = None
            ) -> Dict[str, Any]:
        """
        Implement the actual message sending logic for a specific AI service.

        This method should handle the API call to the AI service and return the raw response.

        Parameters:
        - conversation (ConversationNode): The conversation history.
        - model (str): The name or identifier of the AI model to use.
        - max_tokens (int): The maximum number of tokens the AI should generate.
        - temperature (float): The sampling temperature to use for generation.
        - api_key (str): The API key for the AI service.
        - system_message (Optional[str]): An optional system message to guide the AI's behavior.

        Returns:
        Dict[str, Any]: The raw response from the AI service.

        Raises:
        Exception: If there's an error in sending the message or receiving the response.
        """
        pass

    @abstractmethod
    def _process_response(self, response: Dict[str, Any]) -> tuple[str, str, Dict[str, Any]]:
        """
        Process the raw response from the AI service into a standardized format.

        This method should extract the relevant information from the AI's response
        and return it in a consistent format across different AI services.

        Parameters:
        - response (Dict[str, Any]): The raw response from the AI service.

        Returns:
        tuple[str, str, Dict[str, Any]]: A tuple containing:
            - The response text (str)
            - The role of the responder (str, e.g., "assistant")
            - Additional metadata or parsed information (Dict[str, Any])

        Note:
        The exact structure of the returned tuple may vary depending on the specific 
        requirements of your application, but it should be consistent across all 
        implementations of this method.
        """
        pass

    def _log_outgoing(self, conversation:ConversationNode, model, max_tokens, temperature):
        log_message = {
            "date": formatted_datetime(),
            "messages": conversation.get_message_list(),
            "max_tokens": max_tokens,
            "temperature": temperature,
            "model": model,
        }
        self._log_message(json.dumps(log_message, indent=2), "OUTGOING")

    def _log_incoming(self, processed_response):
        log_message = {
            "date": formatted_datetime(),
            "response": processed_response,
        }
        self._log_message(json.dumps(log_message, indent=2), "INCOMING")

    def _log_message(self, message: str, direction: str) -> None:
        timestamp = formatted_datetime()
        log_entry = f"[{timestamp}] {direction.upper()}:\n{message}\n\n"
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

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

class Bot(ABC):
    def __init__(
        self,
        api_key: Optional[str],
        model_engine: Engines,
        max_tokens: int,
        temperature: float,
        name: str,
        role: str,
        role_description: str,
        conversation: Optional[ConversationNode] = ConversationNode.create_empty()
    ):
        self.api_key = api_key
        self.name = name
        self.model_engine = model_engine
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.role = role
        self.role_description = role_description
        self.conversation = conversation
        self.system_message = ""
        self.mailbox: Mailbox

    def respond(self, content: str, role: str = "user") -> str:
        reply, self.conversation = self._cvsn_respond(
            text=content, cvsn=self.conversation, role=role
        )
        return reply

    def _cvsn_respond(
        self,
        text: Optional[str] = None,
        cvsn: Optional[ConversationNode] = None,
        role: str = "user",
    ) -> tuple[str, ConversationNode]:
        if cvsn is None and text is None:
            raise ValueError("Invalid input: both text and cvsn are None")

        if cvsn is None:
            cvsn = self.__class__(role=role, content=text)
        elif text is not None:
            cvsn = cvsn.add_reply(content=text, role=role)

        try:
            response_text, response_role, extra_data = self.mailbox.send_message(
                cvsn,
                self.model_engine.value, 
                max_tokens=self.max_tokens, 
                temperature=self.temperature,
                api_key=self.api_key,
                system_message=self.system_message or ''
            )

            cvsn = cvsn.add_reply(content=response_text, role=response_role, data=extra_data)

            return response_text, cvsn

        except Exception as e:
            raise e

    def _handle_extra_data(self, cvsn: ConversationNode, extra_data: Any) -> None:
        """
        Handle any extra data returned by the mailbox.
        This method can be overridden by subclasses to handle specific data types.
        """
        pass

    def set_system_message(self, message: str) -> None:
        self.system_message = message

    @classmethod
    def load(cls, filepath: str) -> "Bot":
        with open(filepath, "r") as file:
            data = json.load(file)

        bot_class = Engines.get_bot_class(Engines(data["model_engine"]))
        
        # Get the constructor parameters
        init_params = inspect.signature(bot_class.__init__).parameters
        
        # Filter the data to only include parameters accepted by the constructor
        constructor_args = {k: v for k, v in data.items() if k in init_params}
        
        # Handle special cases
        if 'tool_handler' in constructor_args:
            constructor_args['tool_handler'] = bot_class.ToolHandlerClass.from_dict(constructor_args['tool_handler'])
        
        # Create the bot instance
        bot = bot_class(**constructor_args)
        
        # Set additional attributes that are not part of the constructor
        for key, value in data.items():
            if key not in constructor_args and key != "conversation":
                if key == 'tool_handler':
                    setattr(bot, key, bot_class.ToolHandlerClass.from_dict(value))
                else:
                    setattr(bot, key, value)

        # Handle conversation separately
        if 'conversation' in data and data['conversation']:
            bot.conversation = ConversationNode.from_dict(data["conversation"])
        return bot

    def save(self, filename: Optional[str] = None) -> str:
        now = formatted_datetime()
        if filename is None:
            filename = f"{self.name}@{now}.bot"
        
        # Get all attributes of the bot
        data = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        
        # Handle special cases
        data["bot_class"] = self.__class__.__name__
        data["model_engine"] = self.model_engine.value
        data["conversation"] = self.conversation.to_dict() if self.conversation else None
        
        if 'tool_handler' in data:
            data['tool_handler'] = data['tool_handler'].to_dict()

        # Handle non-serializable objects
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                data[key] = str(value)

        with open(filename, "w") as file:
            json.dump(data, file)
        
        return filename

class ToolHandler(ABC):
    def __init__(self):
        self.tools: List[Dict[str, Any]] = []
        self.function_map: Dict[str, Callable] = {}
        self.requests: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.sent = False

    @abstractmethod
    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        pass

    @abstractmethod
    def handle_tool_use(self, response: Any) -> List[Dict[str, Any]]:
        """Add requests to self.requests, add results to self.results, use correct schema"""
        pass

    def add_tool(self, func: Callable) -> None:
        schema = self.generate_tool_schema(func)
        if schema:  # Only add the tool if a valid schema was generated
            self.tools.append(schema)
            self.function_map[func.__name__] = func
        self.sent = False

    def add_tools_from_file(self, filepath: str) -> None:
        functions = self.extract_functions(filepath)
        for func in functions:
            self.add_tool(func)

    def extract_functions(self, file_path: str) -> List[Callable]:
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"File '{file_path}' not found.")

        abs_file_path = os.path.abspath(file_path)
        file_dir = os.path.dirname(abs_file_path)

        sys.path.insert(0, file_dir)

        try:
            with open(abs_file_path, 'r') as file:
                content = file.read()

            module = ast.parse(content)
            
            imports = []
            functions = []
            for node in module.body:
                if isinstance(node, (ast.Import, ast.ImportFrom)):
                    imports.append(node)
                elif isinstance(node, ast.FunctionDef):
                    functions.append(node)

            new_module = ast.Module(body=imports + functions, type_ignores=[])
            compiled = compile(new_module, filename=abs_file_path, mode="exec")
            
            namespace = ModuleType("dynamic_module")
            namespace.__file__ = abs_file_path
            exec(compiled, namespace.__dict__)
            
            extracted_functions = []
            for func in functions:
                if func.name in namespace.__dict__ and not func.name.startswith('_'):
                    extracted_functions.append(namespace.__dict__[func.name])

            return extracted_functions

        finally:
            sys.path.pop(0)

    def get_tools_json(self) -> str:
        """Return a JSON string representation of all tools."""
        return json.dumps(self.tools, indent=2)

    def clear(self) -> None:
        """Clear the stored results and requests."""
        self.results = []
        self.requests = []
    
    def add_request(self, request: Dict[str, Any]) -> None:
        """Add a request to the stored requests."""
        self.requests.append(request)

    def add_result(self, result: Dict[str, Any]) -> None:
        """Add a result to the stored results."""
        self.results.append(result)

    def get_results(self) -> List[Dict[str, Any]]:
        """Get all stored results."""
        return self.results
    
    def get_requests(self) -> List[Dict[str, Any]]:
        """Get all stored requests"""
        return self.requests

    def to_dict(self) -> Dict[str, Any]:
        return {
            'tools': self.tools,
            'function_map': {
                k: {
                    'name': v.__name__,
                    'code': inspect.getsource(v),
                    'file_path': inspect.getfile(v),
                    'file_hash': self._get_file_hash(inspect.getfile(v))
                } for k, v in self.function_map.items()
            },
            'requests': self.requests,
            'results': self.results,
            'sent': self.sent
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolHandler':
        handler = cls()
        handler.tools = data['tools']
        handler.results = data['results']
        
        for func_name, func_data in data['function_map'].items():
            if os.path.exists(func_data['file_path']):
                current_hash = handler._get_file_hash(func_data['file_path'])
                if current_hash == func_data['file_hash']:
                    # File exists and hasn't changed, load function from file
                    handler.add_tools_from_file(func_data['file_path'])
                    continue
            
            # File doesn't exist or has changed, load from stored code
            exec(func_data['code'], globals())
            func = globals()[func_data['name']]
            handler.add_tool(func)

        return handler

    def _get_file_hash(self, file_path: str) -> str:
        with open(file_path, 'rb') as f:
            return hashlib.md5(f.read()).hexdigest()

