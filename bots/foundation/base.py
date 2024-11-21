import os
import sys
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Union, Type, Dict, Any, List, Callable, Tuple
import datetime as DT
import json
import re
import ast
from types import ModuleType
import threading
import inspect
import hashlib
import importlib
from dataclasses import dataclass
import textwrap

# Some utility functions:

def remove_code_blocks(text: str) ->Tuple[List[str], List[str]]:
    """Extracts code blocks from responses"""
    pattern = '```(\\w*)\\s*([\\s\\S]*?)```'
    matches = re.findall(pattern, text)
    code_blocks = [match[1].strip() for match in matches]
    labels = [match[0].strip() for match in matches]
    text = re.sub(pattern, '', text)
    return code_blocks, labels


def load(filepath: str) ->'Bot':
    """Loads a bot"""
    return Bot.load(filepath)


def formatted_datetime() ->str:
    """Returns 'now' as a formatted string"""
    now = DT.datetime.now()
    return now.strftime('%Y-%m-%d_%H-%M-%S')

class Engines(str, Enum):
    """Enum class representing different AI model engines."""
    # OpenAI models
    GPT4 = 'gpt-4'
    GPT4_0613 = 'gpt-4-0613'
    GPT4_32K = 'gpt-4-32k'
    GPT4_32K_0613 = 'gpt-4-32k-0613'
    GPT4TURBO = 'gpt-4-turbo-preview'
    GPT4TURBO_0125 = 'gpt-4-0125-preview'
    GPT4TURBO_VISION = 'gpt-4-vision-preview'
    GPT35TURBO = 'gpt-3.5-turbo'
    GPT35TURBO_16K = 'gpt-3.5-turbo-16k'
    GPT35TURBO_0125 = 'gpt-3.5-turbo-0125'
    GPT35TURBO_INSTRUCT = 'gpt-3.5-turbo-instruct'
    GPTO1_PREVIEW = 'o1-preview'
    GPTO1_PREVIEW_0912 = 'o1-preview-2024-09-12'
    GPTO1_MINI = 'o1-mini'
    GPTO1_MINI_0912 = 'o1-mini-2024-09-12'
    
    # Anthropic models
    CLAUDE3_HAIKU = 'claude-3-haiku-20240307'
    CLAUDE3_SONNET = 'claude-3-sonnet-20240229'
    CLAUDE3_OPUS = 'claude-3-opus-20240229'
    CLAUDE35_SONNET_20240620 = 'claude-3-5-sonnet-20240620'
    CLAUDE35_SONNET_20241022 = 'claude-3-5-sonnet-20241022'

    @staticmethod
    def get(name):
        """Retrieve an Engines enum member by its value."""
        for engine in Engines:
            if engine.value == name:
                return engine
        return None

    @staticmethod
    def get_bot_class(model_engine: 'Engines') -> Type['Bot']:
        """Returns the bot class based on the model engine."""
        from bots.foundation.openai_bots import ChatGPT_Bot
        from bots.foundation.anthropic_bots import AnthropicBot
        
        if model_engine.value.startswith('gpt'):
            return ChatGPT_Bot
        elif model_engine.value.startswith('claude'):
            return AnthropicBot
        else:
            raise ValueError(f'Unsupported model engine: {model_engine}')

class ConversationNode:

    def __init__(self, content, role, **kwargs):
        for key, value in kwargs.items():
            setattr(self, key, value)
        self.role = role
        self.content = content
        self.replies: list[ConversationNode] = []
        self.parent: ConversationNode = None

    @staticmethod
    def create_empty(cls=None):
        if cls:
            return cls(role="empty", content='')
        return ConversationNode(role='empty', content='')

    def is_empty(self):
        return self.role == 'empty' and self.content == ''

    def add_reply(self, **kwargs):
        if self.is_empty():
            self.__init__(**kwargs)
            return self
        else:
            reply = type(self)(**kwargs)
            reply.parent = self
            self.replies.append(reply)
            return reply

    def add_child(self, node: 'ConversationNode'):
        if self.is_empty():
            raise NotImplementedError("Cannot add a child node to an empty node")
        else:
            node.parent = self
            self.replies.append(node)

    def find_root(self):
        """ Navigate to the root of the conversation tree. """
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def root_dict(self):
        """ Convert the conversation tree starting from the root to a dictionary. """
        root = self.find_root()
        return root._to_dict_recursive()
    
    def _to_dict_recursive(self):
        """ Recursively convert this node and its replies to a dictionary. """
        # Gather all relevant attributes except 'parent'
        result = self._to_dict_self()
        if self.replies:
            result['replies'] = [reply._to_dict_recursive() for reply in self.replies]
        return result

    def _to_dict_self(self):
        """
        Convert this node to a dictionary, omitting replies, parent, callables,
        and private attributes.
        """
        result = {}
        for k in dir(self):
            # Skip private attributes, parent, replies, and callables
            if (not k.startswith('_') and 
                k not in {'parent', 'replies'} and 
                not callable(getattr(self, k))):
                value = getattr(self, k)
                # Handle special cases like tool requests/results that might be complex objects
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    result[k] = value
                else:
                    result[k] = str(value)
        return result
    
    def build_messages(self):
        node = self
        if node.is_empty():
            return []
        conversation_dict = []
        while node:
            entry = {'role': node.role, 'content': node.content}
            conversation_dict = [entry] + conversation_dict
            node = node.parent
        return conversation_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) ->'ConversationNode':
        node = cls(**{k: v for k, v in data.items() if k != 'replies'})
        for reply_data in data.get('replies', []):
            reply_node = cls.from_dict(reply_data)
            reply_node.parent = node
            node.replies.append(reply_node)
        return node
    
    def node_count(self) -> int:
        """
            Recursively count the total number of nodes in the conversation, 
            starting from the root. 
        """
        # First, navigate to the root of the conversation tree
        root = self.find_root()
    
        # Now count all nodes starting from the root
        def count_recursive(current_node):
            count = 1  # Count the current node
            for reply in current_node.replies:
                count += count_recursive(reply)  # Recursively count all replies
            return count
    
        return count_recursive(root)

@dataclass
class ModuleContext:
    """Stores context for a module including its source and execution environment"""
    name: str
    source: str
    file_path: str
    namespace: ModuleType
    code_hash: str

class ToolHandlerError(Exception):
    """Base exception class for ToolHandler errors"""
    pass

class ToolNotFoundError(ToolHandlerError):
    """Raised when a requested tool cannot be found"""
    pass

class ToolExecutionError(ToolHandlerError):
    """Raised when there's an error executing a tool"""
    pass

class ModuleLoadError(ToolHandlerError):
    """Raised when there's an error loading a module"""
    pass

class ToolHandler(ABC):
    """
    Abstract base class for handling tool registration, execution, and persistence.
    Supports module-level preservation of dependencies and function contexts.
    """
    
    def __init__(self):
        self.tools: List[Dict[str, Any]] = []
        self.function_map: Dict[str, Callable] = {}
        self.requests: List[Dict[str, Any]] = []
        self.results: List[Dict[str, Any]] = []
        self.modules: Dict[str, ModuleContext] = {}

    @abstractmethod
    def generate_tool_schema(self, func: Callable) -> Dict[str, Any]:
        """
        Generate tool schema from callable function.
        
        Args:
            func: The function to generate schema for
            
        Returns:
            Dictionary containing the tool's schema
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """
        Generate request schema from response.
        
        Args:
            response: Raw response from LLM service
            
        Returns:
            List of request schemas (multiple requests may be in one message)
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract tool name and input from request.
        
        Args:
            request_schema: The request schema to parse
            
        Returns:
            Tuple of (tool name, input kwargs). Tool name may be None if request should be skipped.
        """
        raise NotImplementedError("You must implement this method in a subclass")

    @abstractmethod
    def generate_response_schema(self, request: Dict[str, Any], tool_output_kwargs: Dict[str, Any]) -> Dict[str, Any]:
        """
        Generate response schema from request and tool output.
        
        Args:
            request: The original request schema
            tool_output_kwargs: The output from tool execution
            
        Returns:
            Response schema dictionary
        """
        raise NotImplementedError("You must implement this method in a subclass")

    def handle_response(self, response: Any) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
        """
        Process an LLM response, execute any requested tools, and generate results.
        
        Args:
            response: The raw response from the LLM service
            
        Returns:
            Tuple of (list of request schemas, list of result schemas)
            
        Side effects:
            - Clears old requests and results
            - Sets new requests and results
            - Executes tools and produces any tool use side effects
        """
        self.clear()
        requests = self.generate_request_schema(response)

        if not requests:
            return self.requests, self.results

        for request_schema in requests:
            tool_name, input_kwargs = self.tool_name_and_input(request_schema)
            
            if tool_name is None:
                continue
                
            try:
                if tool_name not in self.function_map:
                    raise ToolNotFoundError(f"Tool '{tool_name}' not found in function map")
                    
                func = self.function_map[tool_name]
                output_kwargs = func(**input_kwargs)
                
            except ToolNotFoundError as e:
                self.logger.error(f"Tool not found: {str(e)}")
                output_kwargs = {"error": str(e)}
            except TypeError as e:
                self.logger.error(f"Invalid arguments for tool '{tool_name}': {str(e)}")
                output_kwargs = {"error": f"Invalid arguments for tool '{tool_name}': {str(e)}"}
            except Exception as e:
                self.logger.error(f"Unexpected error executing tool '{tool_name}': {str(e)}")
                output_kwargs = {"error": f"Unexpected error while executing tool '{tool_name}': {str(e)}"}

            response_schema = self.generate_response_schema(request_schema, output_kwargs)
            self.requests.append(request_schema)
            self.results.append(response_schema)
        
        return self.requests, self.results

    def add_tool(self, func: Callable) -> None:
        """
        Add a single function as a tool.
        Creates a dynamic module context if none exists.
        """
        schema = self.generate_tool_schema(func)
        if not schema:
            return

        # If function doesn't have a module context, create one
        if not hasattr(func, '__module_context__'):
            try:
                # Try to get source and file info
                source = inspect.getsource(func)
                file_path = inspect.getfile(func) if inspect.getmodule(func) else 'dynamic'
            except Exception:
                # If we can't get source, create minimal version
                source = f"def {func.__name__}{inspect.signature(func)}:\n    {func.__doc__ or ''}\n    return None"
                file_path = 'dynamic'

            # Remove any leading whitespace to avoid indentation issues
            source = textwrap.dedent(source)

            # Create dynamic module
            module_name = f"dynamic_module_{hashlib.md5(source.encode()).hexdigest()}"
            module = ModuleType(module_name)
            module.__file__ = file_path

            # Create module context
            module_context = ModuleContext(
                name=module_name,
                source=source,
                file_path=file_path,
                namespace=module,
                code_hash=self._get_code_hash(source)
            )

            # Execute the function in the module's namespace
            exec(source, module.__dict__)
            
            # Store module context with function
            func.__module_context__ = module_context
            self.modules[file_path] = module_context

        self.tools.append(schema)
        self.function_map[func.__name__] = func

    def add_tools_from_file(self, filepath: str) -> None:
        """
        Add all non-private functions from a file as tools.
        Preserves complete module context including dependencies.
        
        Args:
            filepath: Path to the Python file containing tools
        
        Raises:
            FileNotFoundError: If the specified file doesn't exist
            ModuleLoadError: If there's an error loading the module
        """
        if not os.path.exists(filepath):
            raise FileNotFoundError(f"File '{filepath}' not found.")
            
        abs_file_path = os.path.abspath(filepath)
        module_name = f"dynamic_module_{hashlib.md5(abs_file_path.encode()).hexdigest()}"
        
        try:
            # Read source code
            with open(abs_file_path, 'r') as file:
                source = file.read()
            
            # Create module context
            module = ModuleType(module_name)
            module.__file__ = abs_file_path
            
            # Parse AST to find functions
            tree = ast.parse(source)
            function_nodes = [node for node in ast.walk(tree) 
                            if isinstance(node, ast.FunctionDef)]
            
            # Execute module in its own namespace
            sys.path.insert(0, os.path.dirname(abs_file_path))
            try:
                exec(source, module.__dict__)
            finally:
                sys.path.pop(0)
            
            # Create module context
            module_context = ModuleContext(
                name=module_name,
                source=source,
                file_path=abs_file_path,
                namespace=module,
                code_hash=self._get_code_hash(source)
            )
            
            # Store module context
            self.modules[abs_file_path] = module_context
            
            # Add functions as tools
            for node in function_nodes:
                if not node.name.startswith('_'):
                    func = module.__dict__.get(node.name)
                    if func:
                        func.__module_context__ = module_context
                        self.add_tool(func)
                        
        except Exception as e:
            raise ModuleLoadError(f"Error loading module from {filepath}: {str(e)}") from e

    def add_tools_from_module(self, module: ModuleType) -> None:
        """
        Add all non-private functions from a module as tools.
        """
        try:
            # Get module source
            try:
                source = getattr(module, '__source__', None) or inspect.getsource(module)
            except Exception:
                # If we can't get source, construct it from functions
                functions = inspect.getmembers(module, inspect.isfunction)
                source_parts = []
                for name, func in functions:
                    if not name.startswith('_'):
                        try:
                            func_source = inspect.getsource(func)
                        except Exception:
                            func_source = f"def {name}{inspect.signature(func)}:\n    {func.__doc__ or ''}\n    return None"
                        source_parts.append(textwrap.dedent(func_source))
                source = "\n\n".join(source_parts)

            # Clean up source code
            source = textwrap.dedent(source).strip()

            # Create module context
            module_context = ModuleContext(
                name=module.__name__,
                source=source,
                file_path=getattr(module, '__file__', 'dynamic'),
                namespace=module,
                code_hash=self._get_code_hash(source)
            )
            
            self.modules[module_context.file_path] = module_context
            
            # Add all non-private functions as tools
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if not name.startswith('_'):
                    func.__module_context__ = module_context
                    self.add_tool(func)
                    
        except Exception as e:
            raise ModuleLoadError(f"Error loading module {module.__name__}: {str(e)}") from e

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the ToolHandler state to a dictionary.
        """
        module_details = {}
        function_paths = {}
        
        # Store module details
        for file_path, module_context in self.modules.items():
            module_details[file_path] = {
                'name': module_context.name,
                'source': module_context.source,
                'file_path': file_path,
                'code_hash': module_context.code_hash
            }
        
        # Store function paths
        for name, func in self.function_map.items():
            # Get module context safely
            module_context = getattr(func, '__module_context__', None)
            if module_context:
                function_paths[name] = module_context.file_path
            else:
                print(f"Warning: Function {name} has no module context, using 'dynamic'")
                function_paths[name] = 'dynamic'

        return {
            'class': f"{self.__class__.__module__}.{self.__class__.__name__}",
            'tools': self.tools.copy(),  # Ensure we copy the tools list
            'requests': self.requests.copy(),
            'results': self.results.copy(),
            'modules': module_details,
            'function_map': function_paths
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolHandler':
        """
        Reconstruct a ToolHandler instance from a serialized state.
        """
        handler = cls()
        handler.results = data['results']
        handler.requests = data['requests']
        handler.tools = []  # Ensure we start with empty tools list
        
        # First restore all modules
        for file_path, module_data in data['modules'].items():
            # Verify code hash
            current_code_hash = cls._get_code_hash(module_data['source'])
            if current_code_hash != module_data['code_hash']:
                print(f"Warning: Code hash mismatch for module {file_path}. Skipping.")
                continue
                
            try:
                # Create module
                module = ModuleType(module_data['name'])
                module.__file__ = file_path
                
                # Clean up source code and ensure no leading/trailing whitespace
                source = textwrap.dedent(module_data['source']).strip()
                
                # Create global namespace with module as __name__
                namespace = {'__name__': module_data['name'], '__file__': file_path}
                
                # Execute module code in the namespace
                exec(source, namespace)
                
                # Update module dict with executed namespace
                module.__dict__.update(namespace)
                
                # Create and store module context
                module_context = ModuleContext(
                    name=module_data['name'],
                    source=source,
                    file_path=file_path,
                    namespace=module,
                    code_hash=current_code_hash
                )
                handler.modules[file_path] = module_context
                
                # Register functions from this module
                for func_name, func_path in data['function_map'].items():
                    if func_path == file_path and func_name in namespace:
                        func = namespace[func_name]
                        func.__module_context__ = module_context
                        handler.add_tool(func)
                
            except Exception as e:
                print(f"Warning: Failed to load module {file_path}: {str(e)}")
                import traceback
                print(traceback.format_exc())
                continue
        
        return handler
    
    def get_tools_json(self) ->str:
        """Return a JSON string representation of all tools."""
        return json.dumps(self.tools, indent=1)

    def clear(self) ->None:
        """Clear the stored results and requests."""
        self.results = []
        self.requests = []

    def add_request(self, request: Dict[str, Any]) ->None:
        """Add a request to the stored requests."""
        self.requests.append(request)

    def add_result(self, result: Dict[str, Any]) ->None:
        """Add a result to the stored results."""
        self.results.append(result)

    def get_results(self) ->List[Dict[str, Any]]:
        """Get all stored results."""
        return self.results

    def get_requests(self) ->List[Dict[str, Any]]:
        """Get all stored requests"""
        return self.requests
    
    @staticmethod
    def _get_code_hash(code: str) -> str:
        """Generate MD5 hash of code string."""
        return hashlib.md5(code.encode()).hexdigest()

    def __str__(self) -> str:
        """String representation showing number of tools and modules."""
        return (f"ToolHandler with {len(self.tools)} tools and "
                f"{len(self.modules)} modules")

    def __repr__(self) -> str:
        """Detailed representation including tool names."""
        tool_names = list(self.function_map.keys())
        return (f"ToolHandler(tools={tool_names}, "
                f"modules={list(self.modules.keys())})")

class Mailbox(ABC):

    def __init__(self):
        self.log_file = 'data\\mailbox_log.txt'

    def log_message(self, message: str, direction: str) ->None:
        timestamp = formatted_datetime()
        log_entry = f'[{timestamp}] {direction.upper()}:\n{message}\n\n'
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

    @abstractmethod
    def send_message(self, bot: 'Bot') ->Dict[str, Any]:
        """
        Implement the actual message sending logic for a specific AI service.

        This method should handle the API call to the AI service and return the raw response.
        It *may* also handle any tool results, depending on the api.

        Parameters:
        - bot: a reference to a "Bot" or subclass

        Returns:
        Dict[str, Any]: The raw response from the AI service as a Dict

        Raises:
        Exception: If there's an error in sending the message or receiving the response.
        """
        raise NotImplemented("You must implement this method in a subclass")
        pass

    @abstractmethod
    def process_response(self, 
                         response: Dict[str, Any], 
                         bot: 'Bot' = None
                        ) -> Tuple[str, str, Dict[str, Any]]:
        """
        Process the raw response from the AI service into a standardized format.

        This method should extract the relevant information from the AI's response
        and return it in a consistent format across different AI services.

        Note that if tool_handler has been implemented, handle_response has already
        been called and requests and results can be accessed through bot.tool_handler.

        Parameters:
        - response (Dict[str, Any]): The raw response from the AI service.
        - bot (Bot): A Bot object. This is required in the case that, in processing
            a response, a new message must be sent (such as in the case of openai 
            tool processing)

        Returns:
        tuple[str, str, Dict[str, Any]]: A tuple containing:
            - The response text (str)
            - The role of the responder (str, e.g., "assistant")
            - Additional metadata or parsed information (Dict[str, Any])
                - This additional data will be passed to ConversationNode's kwargs 
                argument directly
                - By default, Conversation Node saves each kwarg as an attribute
        """
        raise NotImplemented("You must implement this method in a subclass")
        pass

    def _log_outgoing(self, conversation: ConversationNode, model: Engines,
        max_tokens, temperature):
        log_message = {'date': formatted_datetime(), 'messages':
            conversation.build_messages(), 'max_tokens': max_tokens,
            'temperature': temperature, 'model': model}
        self._log_message(json.dumps(log_message, indent=1), 'OUTGOING')

    def _log_incoming(self, processed_response):
        log_message = {'date': formatted_datetime(), 'response':
            processed_response}
        self._log_message(json.dumps(log_message, indent=1), 'INCOMING')

    def _log_message(self, message: str, direction: str) ->None:
        timestamp = formatted_datetime()
        log_entry = f'[{timestamp}] {direction.upper()}:\n{message}\n\n'
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

    def batch_send(self, conversations, model, max_tokens, temperature,
        api_key, system_message=None):
        raise NotImplemented
        threads = []
        results = [None] * len(conversations)

        def send_thread(index, conv):
            result = self.send_message(self)
            results[index] = result
        for i, conversation in enumerate(conversations):
            thread = threading.Thread(target=send_thread, args=(i,
                conversation))
            threads.append(thread)
            thread.start()
        for thread in threads:
            thread.join()
        return results


class Bot(ABC):
    """Abstract base class for all bot implementations."""


    def __init__(self, api_key: Optional[str], model_engine: Engines,
        max_tokens: int, temperature: float, name: str, role: str,
        role_description: str, conversation: Optional[ConversationNode]=
        ConversationNode.create_empty(), tool_handler: Optional[ToolHandler
        ]=None, mailbox: Optional[Mailbox]=None):
        self.api_key = api_key
        self.name = name
        self.model_engine = model_engine
        self.max_tokens = max_tokens
        self.temperature = temperature
        self.role = role
        self.role_description = role_description
        self.conversation: ConversationNode = conversation
        self.system_message = ''
        self.tool_handler = tool_handler
        self.mailbox = mailbox
        if isinstance(self.model_engine, str):
            self.model_engine = Engines.get(self.model_engine)

    def respond(self, prompt: str, role: str='user') ->str:
        """
            Sends 'prompt' to the Bot and returns the text response
        """
        self.conversation = self.conversation.add_reply(content=prompt, role=role)
        reply, _ = self._cvsn_respond()
        return reply

    def _cvsn_respond(self) -> Tuple[str, ConversationNode]:
        """
        1) Requests a response based on the current conversation using send_message
        2) Handles tool use with tool_handler.handle_results
        3) Processes the response using process_response
        4) Creates a new conversation node from the response and adds it to 
        the conversation history
        5) Returns the text of the response and the new conversation node
        """
        try:
            response = self.mailbox.send_message(self)
            self.tool_handler.handle_response(response)
            text, role, data = self.mailbox.process_response(response, self)
            node = self.conversation.add_reply(content=text, role=role, **data)
            self.conversation = node
            return text, node
        except Exception as e:
            # Maybe one day I'll implement error handling... one day...
            raise e

    def add_tool(self, func: Callable):
        self.tool_handler.add_tool(func)

    def add_tools(self, path_or_module: Union[str, ModuleType]) -> None:
        """Adds multiple tools from a file to the bot's toolkit."""

        if isinstance(path_or_module, str):
            self.tool_path = path_or_module
            self.tool_handler.add_tools_from_file(path_or_module)
        elif isinstance(path_or_module, ModuleType):
            self.tool_handler.add_tools_from_module(path_or_module)
            self.tool_path = str(path_or_module)
        else:
            raise TypeError("path_or_module must be a string or module object")

    def set_system_message(self, message: str) ->None:
        self.system_message = message

    @classmethod
    def load(cls, filepath: str, api_key=None) ->'Bot':
        # Open file
        with open(filepath, 'r') as file:
            data = json.load(file)
        
        # Start building bot parameters
        bot_class = Engines.get_bot_class(Engines(data['model_engine']))

        # Find the bot's initialization parameters
        init_params = inspect.signature(bot_class.__init__).parameters
        constructor_args = {k: v for k, v in data.items() if k in init_params}
        
        # Initialize Bot
        bot = bot_class(**constructor_args)
        bot.api_key = api_key if api_key is not None else None
        
        # Handle tool handler
        if 'tool_handler' in data:
            tool_handler_class = data['tool_handler']['class'] 
            module_name, class_name = tool_handler_class.rsplit('.', 1)
            module = importlib.import_module(module_name)
            actual_class = getattr(module, class_name)
            handler = actual_class.from_dict(data['tool_handler'])
            bot.tool_handler = handler

        # Set non-initialization parameters
        for key, value in data.items():
            if key not in constructor_args and \
               key not in ('conversation', 'tool_handler', 'tools'):
                setattr(bot, key, value)

        if 'conversation' in data and data['conversation']:
            bot.conversation = ConversationNode.from_dict(data['conversation'])
            while bot.conversation.replies:
                bot.conversation = bot.conversation.replies[0] # default 'continue' point

        return bot

    def save(self, filename: Optional[str]=None) ->str:
        
        # decide name
        if filename is None:
            now = formatted_datetime()
            filename = f'{self.name}@{now}.bot'
        else:
            filename = filename + ".bot"
        
        # collect bot attributes
        data = {key: value for key, value in self.__dict__.items() if not
            key.startswith('_')}
        data.pop('api_key') # never save this
        data.pop('mailbox') # initialized without saved parameters
        
        # set some attributes manually
        data['bot_class'] = self.__class__.__name__
        data['model_engine'] = self.model_engine.value
        data['conversation'] = self.conversation.root_dict()
        if 'tool_handler' in data and data:
            data['tool_handler'] = data['tool_handler'].to_dict()

        # Save as strings
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                data[key] = str(value)
        
        with open(filename, 'w') as file:
            json.dump(data, file, indent=1)
        
        return filename

    def chat(self):
        separator = '\n\n'
        print(separator)
        print('System: Chat started. Type "/exit" to exit.')
        uinput = ''
        while uinput != '/exit':
            print(separator)
            uinput = input('You: ')
            
            if uinput is None or uinput == '/exit':
                break

            print(separator)
            print(f'{self.name}: {self.respond(uinput)}')

            print(separator)
            for request in self.tool_handler.get_requests():
                tool_name, _ = self.tool_handler.tool_name_and_input(request)
                print(f'Used Tool: {tool_name}')
                


