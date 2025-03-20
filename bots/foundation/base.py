"""Base classes and utilities for bot functionality."""
import os, sys, json, ast, inspect, hashlib, importlib, textwrap, copy
from abc import ABC, abstractmethod
from enum import Enum
from typing import Optional, Type, Dict, Any, List, Callable, Tuple
from types import ModuleType
from dataclasses import dataclass
from bots.utils.helpers import formatted_datetime, _clean

def load(filepath: str) -> 'Bot':
    """Loads a bot"""
    return Bot.load(filepath)

class Engines(str, Enum):
    """Enum class representing different AI model engines."""
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
    CLAUDE3_HAIKU = 'claude-3-haiku-20240307'
    CLAUDE3_SONNET = 'claude-3-sonnet-20240229'
    CLAUDE3_OPUS = 'claude-3-opus-20240229'
    CLAUDE35_SONNET_20240620 = 'claude-3-5-sonnet-20240620'
    CLAUDE35_SONNET_20241022 = 'claude-3-5-sonnet-20241022'
    CLAUDE37_SONNET_20250224 = 'claude-3-7-sonnet-20250224'

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

    @staticmethod
    def get_conversation_node_class(class_name: str) -> Type['ConversationNode']:
        """Returns the conversation node class based on the class name."""
        from bots.foundation.openai_bots import OpenAINode
        from bots.foundation.anthropic_bots import AnthropicNode
        NODE_CLASS_MAP = {'OpenAINode': OpenAINode, 'AnthropicNode': AnthropicNode}
        node_class = NODE_CLASS_MAP.get(class_name)
        if node_class is None:
            raise ValueError(f'Unsupported conversation node type: {class_name}')
        return node_class

class ConversationNode:
    """Base class for conversation nodes that store message history and tool interactions."""

    def __init__(self, content: str, role: str, tool_calls: List[Dict]=None, tool_results: List[Dict]=None, pending_results: List[Dict]=None, **kwargs):
        self.role = role
        self.content = content
        self.parent: ConversationNode = None
        self.replies: list[ConversationNode] = []
        self.tool_calls = tool_calls or []
        self.tool_results = tool_results or []
        self.pending_results = pending_results or []
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def _create_empty(cls=None) -> 'ConversationNode':
        if cls:
            return cls(role='empty', content='')
        return ConversationNode(role='empty', content='')

    def _is_empty(self) -> bool:
        return self.role == 'empty' and self.content == ''

    def _add_reply(self, **kwargs) -> 'ConversationNode':
        reply = type(self)(**kwargs)
        reply.parent = self
        self.replies.append(reply)
        if self.pending_results:
            reply.tool_results = self.pending_results.copy()
            self.pending_results = []
        reply._sync_tool_context()
        return reply

    def _sync_tool_context(self) -> None:
        """Synchronize tool context between all siblings by taking the union of their tool results."""
        if self.parent and self.parent.replies:
            all_tool_results = []
            for sibling in self.parent.replies:
                for result in sibling.tool_results:
                    if result not in all_tool_results:
                        all_tool_results.append(result)
            for sibling in self.parent.replies:
                sibling.tool_results = all_tool_results.copy()

    def _add_tool_calls(self, calls):
        self.tool_calls.extend(calls)

    def _add_tool_results(self, results):
        self.tool_results.extend(results)
        self._sync_tool_context()

    def _find_root(self) -> 'ConversationNode':
        """Navigate to the root of the conversation tree."""
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def _root_dict(self) -> Dict:
        """Convert the conversation tree starting from the root to a dictionary."""
        root = self._find_root()
        return root._to_dict_recursive()

    def _to_dict_recursive(self) -> Dict:
        """Recursively convert this node and its replies to a dictionary."""
        result = self._to_dict_self()
        if self.replies:
            result['replies'] = [reply._to_dict_recursive() for reply in self.replies]
        return result

    def _to_dict_self(self) -> Dict:
        """
        Convert this node to a dictionary, omitting replies, parent, callables.
        """
        result = {}
        for k in dir(self):
            if not k.startswith('_') and k not in {'parent', 'replies'} and (not callable(getattr(self, k))):
                value = getattr(self, k)
                if isinstance(value, (str, int, float, bool, list, dict, type(None))):
                    result[k] = value
                else:
                    result[k] = str(value)
        result['node_class'] = self.__class__.__name__
        return result

    def _build_messages(self) -> List[Dict[str, str]]:
        node = self
        if node._is_empty():
            return []
        conversation_list_dict = []
        while node:
            if not node._is_empty():
                entry = {'role': node.role, 'content': node.content}
                if node.tool_calls is not None:
                    entry['tool_calls'] = node.tool_calls
                if node.tool_results is not None:
                    entry['tool_results'] = node.tool_results
                conversation_list_dict = [entry] + conversation_list_dict
            node = node.parent
        return conversation_list_dict

    @classmethod
    def _from_dict(cls, data: Dict[str, Any]) -> 'ConversationNode':
        reply_data = data.pop('replies', [])
        node_class = Engines.get_conversation_node_class(data.pop('node_class', cls.__name__))
        node = node_class(**data)
        for reply in reply_data:
            reply_node = cls._from_dict(reply)
            reply_node.parent = node
            node.replies.append(reply_node)
        return node

    def _node_count(self) -> int:
        """
        Recursively count the total number of nodes in the conversation,
        starting from the root.
        """
        root = self._find_root()

        def count_recursive(current_node):
            count = 1
            for reply in current_node.replies:
                count += count_recursive(reply)
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
        raise NotImplementedError('You must implement this method in a subclass')

    @abstractmethod
    def generate_request_schema(self, response: Any) -> List[Dict[str, Any]]:
        """
        Generate request schema from response.

        Args:
            response: Raw response from LLM service

        Returns:
            List of request schemas (multiple requests may be in one message)
        """
        raise NotImplementedError('You must implement this method in a subclass')

    @abstractmethod
    def tool_name_and_input(self, request_schema: Dict[str, Any]) -> Tuple[Optional[str], Dict[str, Any]]:
        """
        Extract tool name and input from request.

        Args:
            request_schema: The request schema to parse

        Returns:
            Tuple of (tool name, input kwargs). Tool name may be None if request should be skipped.
        """
        raise NotImplementedError('You must implement this method in a subclass')

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
        raise NotImplementedError('You must implement this method in a subclass')

    @abstractmethod
    def generate_error_schema(self, request_schema: Dict[str, Any], error_msg: str) -> Dict[str, Any]:
        """
        Generate an error response schema matching the format expected by this handler.
        
        Args:
            error_msg: The error message to include
            request_schema: Optional original request schema that caused the error
            
        Returns:
            Dict containing the error in the correct schema format for this handler
        """
        raise NotImplementedError('You must implement this method in a subclass')

    def extract_requests(self, response: Any) -> List[Dict[str, Any]]:
        """
        Extract tool requests from an LLM response.
        
        Args:
            response: The raw response from the LLM service
            
        Returns:
            List of request schemas

        Side effect:
            Cl`ears self.requests and sets to return value
        """
        self.requests = self.generate_request_schema(response)
        return self.requests

    def exec_requests(self) -> List[Dict[str, Any]]:
        """
        Execute tool requests and generate results.
        
        Args:
            requests: List of requests as request schemas to execute
            
        Returns:
            List of result schemas
            
        Side effects:
            - Executes tools and produces any tool use side effects
        """
        results = []
        requests = self.requests
        for request_schema in requests:
            tool_name, input_kwargs = self.tool_name_and_input(request_schema)
            if tool_name is None:
                continue
            try:
                if tool_name not in self.function_map:
                    raise ToolNotFoundError(f"Tool '{tool_name}' not found in function map")
                func = self.function_map[tool_name]
                output_kwargs = func(**input_kwargs)
                response_schema = self.generate_response_schema(request_schema, output_kwargs)
            except ToolNotFoundError as e:
                error_msg = 'Error: Tool not found.\n\n' + str(e)
                response_schema = self.generate_error_schema(request_schema, error_msg)
            except TypeError as e:
                error_msg = f"Invalid arguments for tool '{tool_name}': {str(e)}"
                response_schema = self.generate_error_schema(request_schema, error_msg)
            except Exception as e:
                error_msg = f"Unexpected error while executing tool '{tool_name}': {str(e)}"
                response_schema = self.generate_error_schema(request_schema, error_msg)
            self.results.append(response_schema)
            results.append(response_schema)
        return results

    def _create_builtin_wrapper(self, func):
        """Create a wrapper function for built-in functions"""
        source = f'def {func.__name__}(x):\n    """Wrapper for built-in function {func.__name__} from {func.__module__}"""\n    import {func.__module__}\n    return {func.__module__}.{func.__name__}(float(x))\n'
        return source

    def _create_dynamic_wrapper(self, func):
        """Create a wrapper for dynamic functions"""
        source = f'def {func.__name__}{inspect.signature(func)}:\n'
        if func.__doc__:
            source += f'    """{func.__doc__}"""\n'
        if hasattr(func, '__code__'):
            try:
                body = inspect.getsource(func).split('\n', 1)[1]
                source += body
            except:
                source += f'    return func(*args, **kwargs)\n'
        else:
            source += '    pass\n'
        return source

    def add_tool(self, func: Callable) -> None:
        """
        Add a single function as a tool.
        Creates a dynamic module context if none exists.
        """
        schema = self.generate_tool_schema(func)
        if not schema:
            raise ValueError('Schema undefined. ToolHandler.generate_tool_schema() may not be implemented.')
        if not hasattr(func, '__module_context__'):
            if inspect.isbuiltin(func) or inspect.ismethoddescriptor(func):
                source = self._create_builtin_wrapper(func)
                context = {}
            else:
                try:
                    source = inspect.getsource(func)
                    if hasattr(func, '__globals__'):
                        code = func.__code__
                        names = code.co_names
                        context = {name: func.__globals__[name] for name in names if name in func.__globals__}
                    else:
                        context = {}
                except (TypeError, OSError):
                    source = self._create_dynamic_wrapper(func)
                    context = {}
            source = _clean(source)
            module_name = f'dynamic_module_{hash(source)}'
            file_path = f'dynamic_module_{hash(str(func))}'
            module = ModuleType(module_name)
            module.__file__ = file_path
            module.__dict__.update(context)
            module_context = ModuleContext(name=module_name, source=source, file_path=file_path, namespace=module, code_hash=self._get_code_hash(source))
            exec(source, module.__dict__)
            new_func = module.__dict__[func.__name__]
            new_func.__module_context__ = module_context
            self.modules[file_path] = module_context
            func = new_func
        self.tools.append(schema)
        self.function_map[func.__name__] = func

    def _add_tools_from_file(self, filepath: str) -> None:
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
        module_name = f'dynamic_module_{hashlib.md5(abs_file_path.encode()).hexdigest()}'
        try:
            with open(abs_file_path, 'r') as file:
                source = file.read()
            module = ModuleType(module_name)
            module.__file__ = abs_file_path
            tree = ast.parse(source)
            function_nodes = [node for node in ast.walk(tree) if isinstance(node, ast.FunctionDef)]
            sys.path.insert(0, os.path.dirname(abs_file_path))
            try:
                exec(source, module.__dict__)
            finally:
                sys.path.pop(0)
            module_context = ModuleContext(name=module_name, source=source, file_path=abs_file_path, namespace=module, code_hash=self._get_code_hash(source))
            self.modules[abs_file_path] = module_context
            for node in function_nodes:
                if not node.name.startswith('_'):
                    func = module.__dict__.get(node.name)
                    if func:
                        func.__module_context__ = module_context
                        self.add_tool(func)
        except Exception as e:
            raise ModuleLoadError(f'Error loading module from {filepath}: {str(e)}') from e

    def _add_tools_from_module(self, module: ModuleType) -> None:
        """
        Add all non-private functions from a module as tools.
        Module must have either a __file__ attribute or a __source__ attribute.

        Args:
            module: Module containing the tools to add

        Raises:
            ModuleLoadError: If module has neither __file__ nor __source__ attribute
        """
        if hasattr(module, '__file__'):
            self._add_tools_from_file(module.__file__)
        elif hasattr(module, '__source__'):
            source = module.__source__
            module_name = f'dynamic_module_{hashlib.md5(module.__name__.encode()).hexdigest()}'
            try:
                dynamic_module = ModuleType(module_name)
                dynamic_module.__file__ = f'dynamic_module_{hash(source)}'
                exec(source, dynamic_module.__dict__)
                module_context = ModuleContext(name=module_name, source=source, file_path=dynamic_module.__file__, namespace=dynamic_module, code_hash=self._get_code_hash(source))
                self.modules[dynamic_module.__file__] = module_context
                for name, func in inspect.getmembers(dynamic_module, inspect.isfunction):
                    if not name.startswith('_'):
                        func.__module_context__ = module_context
                        self.add_tool(func)
            except Exception as e:
                raise ModuleLoadError(f'Error loading module {module.__name__}: {str(e)}') from e
        else:
            raise ModuleLoadError(f'Module {module.__name__} has neither file path nor source. Cannot load.')

    def to_dict(self) -> Dict[str, Any]:
        """
        Serialize the ToolHandler state to a dictionary.
        """
        module_details = {}
        function_paths = {}
        for file_path, module_context in self.modules.items():
            module_details[file_path] = {'name': module_context.name, 'source': module_context.source, 'file_path': module_context.file_path, 'code_hash': module_context.code_hash, 'globals': {k: str(v) for k, v in module_context.namespace.__dict__.items() if not k.startswith('__')}}
        for name, func in self.function_map.items():
            module_context = getattr(func, '__module_context__', None)
            if module_context:
                function_paths[name] = module_context.file_path
            else:
                function_paths[name] = 'dynamic'
        return {'class': f'{self.__class__.__module__}.{self.__class__.__name__}', 'tools': self.tools.copy(), 'requests': self.requests.copy(), 'results': self.results.copy(), 'modules': module_details, 'function_paths': function_paths}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'ToolHandler':
        """
        Reconstruct a ToolHandler instance from a serialized state.
        Only restores functions that were explicitly registered as tools.
        Requests and Results are conserverved.
        """
        handler = cls()
        handler.results = data.get('results', [])
        handler.requests = data.get('requests', [])
        handler.tools = data.get('tools', []).copy()
        function_paths = data.get('function_paths', {})
        for file_path, module_data in data.get('modules', {}).items():
            current_code_hash = cls._get_code_hash(module_data['source'])
            if current_code_hash != module_data['code_hash']:
                print(f'Warning: Code hash mismatch for module {file_path}. Skipping.')
                continue
            try:
                module = ModuleType(module_data['name'])
                module.__file__ = file_path
                source = module_data['source']
                if 'globals' in module_data:
                    module.__dict__.update(module_data['globals'])
                exec(source, module.__dict__)
                module_context = ModuleContext(name=module_data['name'], source=source, file_path=module_data['file_path'], namespace=module, code_hash=current_code_hash)
                handler.modules[module_data['file_path']] = module_context
                for func_name, path in function_paths.items():
                    if path == module_data['file_path'] and func_name in module.__dict__:
                        func = module.__dict__[func_name]
                        if callable(func):
                            func.__module_context__ = module_context
                            handler.function_map[func_name] = func
            except Exception as e:
                print(f'Warning: Failed to load module {file_path}: {str(e)}')
                continue
        return handler

    def get_tools_json(self) -> str:
        """Return a JSON string representation of all tools."""
        return json.dumps(self.tools, indent=1)

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

    @staticmethod
    def _get_code_hash(code: str) -> str:
        """Generate MD5 hash of code string."""
        return hashlib.md5(code.encode()).hexdigest()

    def __str__(self) -> str:
        """String representation showing number of tools and modules."""
        return f'ToolHandler with {len(self.tools)} tools and {len(self.modules)} modules'

    def __repr__(self) -> str:
        """Detailed representation including tool names."""
        tool_names = list(self.function_map.keys())
        return f'ToolHandler(tools={tool_names}, modules={list(self.modules.keys())})'

class Mailbox(ABC):

    def __init__(self):
        self.log_file = 'data\\mailbox_log.txt'

    def log_message(self, message: str, direction: str) -> None:
        timestamp = formatted_datetime()
        log_entry = f'[{timestamp}] {direction.upper()}:\n{message}\n\n'
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

    @abstractmethod
    def send_message(self, bot: 'Bot') -> Dict[str, Any]:
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
        raise NotImplemented('You must implement this method in a subclass')
        pass

    @abstractmethod
    def process_response(self, response: Dict[str, Any], bot: 'Bot'=None) -> Tuple[str, str, Dict[str, Any]]:
        """
        Process the raw response from the AI service into a standardized format.

        This method should extract the relevant information from the AI's response
        and return it in a consistent format across different AI services.

        Note that if tool_handler has been implemented, extract_requests and results
        have already been called and are available in the tool_handler.

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
        raise NotImplemented('You must implement this method in a subclass')

    def _log_outgoing(self, conversation: ConversationNode, model: Engines, max_tokens, temperature):
        log_message = {'date': formatted_datetime(), 'messages': conversation._build_messages(), 'max_tokens': max_tokens, 'temperature': temperature, 'model': model}
        self._log_message(json.dumps(log_message, indent=1), 'OUTGOING')

    def _log_incoming(self, processed_response):
        log_message = {'date': formatted_datetime(), 'response': processed_response}
        self._log_message(json.dumps(log_message, indent=1), 'INCOMING')

    def _log_message(self, message: str, direction: str) -> None:
        timestamp = formatted_datetime()
        log_entry = f'[{timestamp}] {direction.upper()}:\n{message}\n\n'
        with open(self.log_file, 'a', encoding='utf-8') as file:
            file.write(log_entry)

class Bot(ABC):
    """Abstract base class for all bot implementations."""

    def __init__(self, api_key: Optional[str], model_engine: Engines, max_tokens: int, temperature: float, name: str, role: str, role_description: str, conversation: Optional[ConversationNode]=ConversationNode._create_empty(), tool_handler: Optional[ToolHandler]=None, mailbox: Optional[Mailbox]=None, autosave: bool=True):
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
        self.autosave = autosave
        if isinstance(self.model_engine, str):
            self.model_engine = Engines.get(self.model_engine)

    def respond(self, prompt: str, role: str='user') -> str:
        """
        Sends 'prompt' to the Bot and returns the text response
        Allows tool use
        """
        self.conversation = self.conversation._add_reply(content=prompt, role=role)
        if self.autosave:
            self.save(f'{self.name}')
        reply, _ = self._cvsn_respond()
        if self.autosave:
            self.save(f'{self.name}')
        return reply

    def add_tools(self, *args) -> None:
        """Adds top level functions from a python file or module 
        to the bot's toolkit. Docstring for the functions are 
        sent as tool descriptions

        Allowable args:
        1. Single or multiple file paths (str)
        2. Single or multiple modules
        3. Mixed list of files and modules
        4. Single functions
        5. Lists/tuples of any of the above

        Examples:
            # Single file
            bot.add_tools("path/to/tools.py")

            # Multiple files
            bot.add_tools("tools1.py", "tools2.py")

            # Multiple modules (after import)
            bot.add_tools(code_tools, python_tools, terminal_tools)

            # Mixed files and modules
            bot.add_tools("tools1.py", code_tools, "tools2.py", terminal_tools)

            # Single function
            bot.add_tools(my_function)

            # List of any supported type
            bot.add_tools([code_tools, "tools1.py", my_function])

        Args:
            *args: Variable number of arguments that can be:
                - str: Filepath to Python file containing tools
                - ModuleType: Module object containing tools
                - Callable: Single function to add as tool
                - List/Tuple: Collection of any of the above

        Raises:
            TypeError: If an argument is not a supported type
            FileNotFoundError: If a specified file path doesn't exist
            ModuleLoadError: If there's an error loading a module
    """

        def process_item(item):
            if isinstance(item, str):
                self.tool_handler._add_tools_from_file(item)
            elif isinstance(item, ModuleType):
                self.tool_handler._add_tools_from_module(item)
            elif isinstance(item, Callable):
                self.tool_handler.add_tool(item)
            elif isinstance(item, (list, tuple)):
                for subitem in item:
                    process_item(subitem)
            else:
                raise TypeError(f'Unsupported type for tool addition: {type(item)}')
        for arg in args:
            process_item(arg)

    def _cvsn_respond(self) -> Tuple[str, ConversationNode]:
        """
        1) Requests a response based on the current conversation using send_message
        2) Extracts tool requests if tool_handler exists
        3) Processes the response using process_response
        4) Creates a new conversation node from the response and adds it to the conversation history
        5) Executes tools if any requests exist and updates node with results
        6) Returns the text of the response and the new conversation node
        """
        try:
            self.tool_handler.clear()
            response = self.mailbox.send_message(self)
            requests = []
            results = []
            requests = self.tool_handler.extract_requests(response)
            text, role, data = self.mailbox.process_response(response, self)
            self.conversation = self.conversation._add_reply(content=text, role=role, **data)
            self.conversation._add_tool_calls(requests)
            results = self.tool_handler.exec_requests()
            self.conversation._add_tool_results(results)
            return (text, self.conversation)
        except Exception as e:
            raise e

    def set_system_message(self, message: str) -> None:
        self.system_message = message

    @classmethod
    def load(cls, filepath: str, api_key=None) -> 'Bot':
        with open(filepath, 'r') as file:
            data = json.load(file)
        bot_class = Engines.get_bot_class(Engines(data['model_engine']))
        init_params = inspect.signature(bot_class.__init__).parameters
        constructor_args = {k: v for k, v in data.items() if k in init_params}
        bot = bot_class(**constructor_args)
        bot.api_key = api_key if api_key is not None else None
        if 'tool_handler' in data:
            tool_handler_class = data['tool_handler']['class']
            module_name, class_name = tool_handler_class.rsplit('.', 1)
            module = importlib.import_module(module_name)
            actual_class = getattr(module, class_name)
            bot.tool_handler = actual_class().from_dict(data['tool_handler'])
        for key, value in data.items():
            if key not in constructor_args and key not in ('conversation', 'tool_handler', 'tools'):
                setattr(bot, key, value)
        if 'conversation' in data and data['conversation']:
            node_class = Engines.get_conversation_node_class(data['conversation']['node_class'])
            bot.conversation = node_class._from_dict(data['conversation'])
            while bot.conversation.replies:
                bot.conversation = bot.conversation.replies[0]
        return bot

    def save(self, filename: Optional[str]=None) -> str:
        if filename is None:
            now = formatted_datetime()
            filename = f'{self.name}@{now}.bot'
        elif not filename.endswith('.bot'):
            filename = filename + '.bot'
        directory = os.path.dirname(filename)
        if directory and (not os.path.exists(directory)):
            os.makedirs(directory)
        data = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        data.pop('api_key', None)
        data.pop('mailbox', None)
        data['bot_class'] = self.__class__.__name__
        data['model_engine'] = self.model_engine.value
        data['conversation'] = self.conversation._root_dict()
        if self.tool_handler:
            data['tool_handler'] = self.tool_handler.to_dict()
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool, list, dict, type(None))):
                data[key] = str(value)
        with open(filename, 'w') as file:
            json.dump(data, file, indent=1)
        return filename

    def chat(self):
        separator = '\n---\n'
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
            if self.tool_handler:
                for request in self.tool_handler.get_requests():
                    tool_name, _ = self.tool_handler.tool_name_and_input(request)
                    print(f'Used Tool: {tool_name}')
                    print(separator)

    def __mul__(self, other):
        if isinstance(other, int):
            return [copy.deepcopy(self) for _ in range(other)]
        return NotImplemented

    def __str__(self) -> str:
        """Returns a formatted string representation of the Bot instance.
        
        Displays:
        1. Bot metadata (name, role, model)
        2. Conversation history with indentation
        3. Tool information if available
        """

        def format_conversation(node, level=0):
            display_level = min(level, 5)
            indent_size = 1
            marker_size = 4
            indent = ' ' * indent_size * display_level
            available_width = max(40, 80 - display_level * indent_size - marker_size)
            messages = []
            if hasattr(node, 'role'):
                if node.role == 'user':
                    base_name = 'You'
                elif node.role == 'assistant':
                    base_name = self.name
                else:
                    base_name = node.role.title()
            else:
                base_name = 'System'
            if level > display_level:
                hidden_levels = level - display_level
                if hidden_levels <= 3:
                    depth_indicator = '>' * hidden_levels
                else:
                    depth_indicator = f'>>>({hidden_levels})'
                name_display = f'{depth_indicator} {base_name}'
            else:
                name_display = base_name
            content = node.content if hasattr(node, 'content') else str(node)
            wrapped_content = '\n'.join(textwrap.wrap(content, width=available_width, initial_indent=indent + '│ ', subsequent_indent=indent + '│ '))
            tool_info = []
            if hasattr(node, 'tool_calls') and node.tool_calls:
                tool_info.append(f'{indent}│ Tool Calls:')
                for call in node.tool_calls:
                    if isinstance(call, dict):
                        tool_info.append(f"{indent}│   - {call.get('name', 'unknown')}")
            if hasattr(node, 'tool_results') and node.tool_results:
                tool_info.append(f'{indent}│ Tool Results:')
                for result in node.tool_results:
                    if isinstance(result, dict):
                        tool_info.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
            if hasattr(node, 'pending_results') and node.pending_results:
                tool_info.append(f'{indent}│ Pending Results:')
                for result in node.pending_results:
                    if isinstance(result, dict):
                        tool_info.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
                    else:
                        raise ValueError()
            tool_info_str = '\n'.join(tool_info) if tool_info else ''
            messages.append(f'{indent}┌─ {name_display}')
            messages.append(wrapped_content)
            if hasattr(node, 'tool_calls') and node.tool_calls:
                messages.append(f'{indent}│ Tool Calls:')
                for call in node.tool_calls:
                    if isinstance(call, dict):
                        messages.append(f"{indent}│   - {call.get('name', 'unknown')}")
            if hasattr(node, 'tool_results') and node.tool_results:
                messages.append(f'{indent}│ Tool Results:')
                for result in node.tool_results:
                    if isinstance(result, dict):
                        messages.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
            if hasattr(node, 'pending_results') and node.pending_results:
                messages.append(f'{indent}│ Pending Results:')
                for result in node.pending_results:
                    if isinstance(result, dict):
                        messages.append(f"{indent}│   - {str(result.get('content', ''))[:available_width]}")
            messages.append(f'{indent}└' + '─' * 40)
            if hasattr(node, 'replies') and node.replies:
                for reply in node.replies:
                    messages.extend(format_conversation(reply, level + 1))
            return messages
        lines = []
        lines.append('╔' + '═' * 12)
        lines.append(f'║ {self.name}')
        lines.append(f'║ Role: {self.role}')
        lines.append(f'║ Model: {self.model_engine.value}')
        if self.tool_handler:
            tool_count = len(self.tool_handler.tools)
            lines.append(f'║ Tools Available: {tool_count}')
        lines.append('╚' + '═' * 78 + '╝\n')
        if self.conversation:
            root = self.conversation
            while hasattr(root, 'parent') and root.parent:
                if root.parent._is_empty() and len(root.parent.replies) == 1:
                    break
                root = root.parent
            lines.extend(format_conversation(root))
        return '\n'.join(lines)
