"""Base classes and utilities for bot functionality."""
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
    def get_bot_class(model_engine: 'Engines') ->Type['Bot']:
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
    def get_conversation_node_class(class_name: str) ->Type['ConversationNode'
        ]:
        """Returns the conversation node class based on the class name."""
        from bots.foundation.openai_bots import OpenAINode
        from bots.foundation.anthropic_bots import AnthropicNode
        NODE_CLASS_MAP = {'OpenAINode': OpenAINode, 'AnthropicNode':
            AnthropicNode}
        node_class = NODE_CLASS_MAP.get(class_name)
        if node_class is None:
            raise ValueError(
                f'Unsupported conversation node type: {class_name}')
        return node_class


class ConversationNode:
    """Base class for conversation nodes that store message history and tool interactions."""

    def __init__(self, content: str, role: str, tool_calls: Optional[Any]=
        None, tool_results: Optional[Any]=None, **kwargs):
        self.role = role
        self.content = content
        self.tool_calls = tool_calls
        self.tool_results = tool_results
        self.replies: list[ConversationNode] = []
        self.parent: ConversationNode = None
        for key, value in kwargs.items():
            setattr(self, key, value)

    @staticmethod
    def create_empty(cls=None) ->'ConversationNode':
        if cls:
            return cls(role='empty', content='')
        return ConversationNode(role='empty', content='')

    def is_empty(self) ->bool:
        return self.role == 'empty' and self.content == ''

    def add_reply(self, **kwargs) ->'ConversationNode':
        if (self.replies and 'tool_calls' not in kwargs and 'tool_results'
             not in kwargs):
            first_sibling = self.replies[0]
            kwargs['tool_calls'] = first_sibling.tool_calls
            kwargs['tool_results'] = first_sibling.tool_results
        reply = type(self)(**kwargs)
        reply.parent = self
        self.replies.append(reply)
        return reply

    def sync_tool_context(self) ->None:
        """Synchronize tool context between all siblings."""
        if self.parent and self.parent.replies:
            first_sibling = self.parent.replies[0]
            for sibling in self.parent.replies[1:]:
                sibling.tool_calls = first_sibling.tool_calls
                sibling.tool_results = first_sibling.tool_results

    def add_child(self, node: 'ConversationNode') ->None:
        if self.is_empty():
            raise NotImplementedError(
                'Cannot add a child node to an empty node')
        else:
            node.parent = self
            self.replies.append(node)

    def find_root(self) ->'ConversationNode':
        """Navigate to the root of the conversation tree."""
        current = self
        while current.parent is not None:
            current = current.parent
        return current

    def root_dict(self) ->Dict:
        """Convert the conversation tree starting from the root to a dictionary."""
        root = self.find_root()
        return root._to_dict_recursive()

    def _to_dict_recursive(self) ->Dict:
        """Recursively convert this node and its replies to a dictionary."""
        result = self._to_dict_self()
        if self.replies:
            result['replies'] = [reply._to_dict_recursive() for reply in
                self.replies]
        return result

    def _to_dict_self(self) ->Dict:
        """
        Convert this node to a dictionary, omitting replies, parent, callables,
        and private attributes.
        """
        result = {}
        for k in dir(self):
            if not k.startswith('_') and k not in {'parent', 'replies'
                } and not callable(getattr(self, k)):
                value = getattr(self, k)
                if isinstance(value, (str, int, float, bool, list, dict,
                    type(None))):
                    result[k] = value
                else:
                    result[k] = str(value)
        result['node_class'] = self.__class__.__name__
        return result

    def build_messages(self) ->List[Dict[str, str]]:
        print('base class')
        node = self
        if node.is_empty():
            return []
        conversation_list_dict = []
        while node:
            if not node.is_empty():
                entry = {'role': node.role, 'content': node.content}
                if node.tool_calls is not None:
                    entry['tool_calls'] = node.tool_calls
                if node.tool_results is not None:
                    entry['tool_results'] = node.tool_results
                conversation_list_dict = [entry] + conversation_list_dict
            node = node.parent
        return conversation_list_dict

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) ->'ConversationNode':
        node_data = {k: v for k, v in data.items() if k != 'replies'}
        node_class = Engines.get_conversation_node_class(data.get(
            'node_class', cls.__name__))
        node = node_class(**node_data)
        for reply_data in data.get('replies', []):
            reply_node = cls.from_dict(reply_data)
            reply_node.parent = node
            node.replies.append(reply_node)
        return node

    def node_count(self) ->int:
        """
        Recursively count the total number of nodes in the conversation,
        starting from the root.
        """
        root = self.find_root()

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
    def generate_tool_schema(self, func: Callable) ->Dict[str, Any]:
        """
        Generate tool schema from callable function.

        Args:
            func: The function to generate schema for

        Returns:
            Dictionary containing the tool's schema
        """
        raise NotImplementedError(
            'You must implement this method in a subclass')

    @abstractmethod
    def generate_request_schema(self, response: Any) ->List[Dict[str, Any]]:
        """
        Generate request schema from response.

        Args:
            response: Raw response from LLM service

        Returns:
            List of request schemas (multiple requests may be in one message)
        """
        raise NotImplementedError(
            'You must implement this method in a subclass')

    @abstractmethod
    def tool_name_and_input(self, request_schema: Dict[str, Any]) ->Tuple[
        Optional[str], Dict[str, Any]]:
        """
        Extract tool name and input from request.

        Args:
            request_schema: The request schema to parse

        Returns:
            Tuple of (tool name, input kwargs). Tool name may be None if request should be skipped.
        """
        raise NotImplementedError(
            'You must implement this method in a subclass')

    @abstractmethod
    def generate_response_schema(self, request: Dict[str, Any],
        tool_output_kwargs: Dict[str, Any]) ->Dict[str, Any]:
        """
        Generate response schema from request and tool output.

        Args:
            request: The original request schema
            tool_output_kwargs: The output from tool execution

        Returns:
            Response schema dictionary
        """
        raise NotImplementedError(
            'You must implement this method in a subclass')

    @abstractmethod
    def generate_error_schema(self, request_schema: Dict[str, Any], error_msg: str
        ) ->Dict[str, Any]:
        """
        Generate an error response schema matching the format expected by this handler.
        
        Args:
            error_msg: The error message to include
            request_schema: Optional original request schema that caused the error
            
        Returns:
            Dict containing the error in the correct schema format for this handler
        """
        raise NotImplementedError(
            'You must implement this method in a subclass')

    def clean_source(self, source):
        """Helper function to ensure source is handled consistently"""
        return textwrap.dedent(source).strip()

    def handle_response(self, response: Any) ->Tuple[List[Dict[str, Any]],
        List[Dict[str, Any]]]:
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
                    raise ToolNotFoundError(
                        f"Tool '{tool_name}' not found in function map")
                func = self.function_map[tool_name]
                output_kwargs = func(**input_kwargs)
                response_schema = self.generate_response_schema(request_schema,
                    output_kwargs)
            except ToolNotFoundError as e:
                error_msg = 'Error: Tool not found.\n\n' + str(e)
                response_schema = self.generate_error_schema(request_schema,
                    error_msg)
            except TypeError as e:
                error_msg = (
                    f"Invalid arguments for tool '{tool_name}': {str(e)}")
                response_schema = self.generate_error_schema(request_schema,
                    error_msg)
            except Exception as e:
                error_msg = (
                    f"Unexpected error while executing tool '{tool_name}': {str(e)}"
                    )
                response_schema = self.generate_error_schema(request_schema,
                    error_msg)
            self.requests.append(request_schema)
            self.results.append(response_schema)
        return self.requests, self.results

    def _create_builtin_wrapper(self, func):
        """Create a wrapper function for built-in functions"""
        source = f"""def {func.__name__}(x):
    ""\"Wrapper for built-in function {func.__name__} from {func.__module__}""\"
    import {func.__module__}
    return {func.__module__}.{func.__name__}(float(x))
"""
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

    def add_tool(self, func: Callable) ->None:
        """
        Add a single function as a tool.
        Creates a dynamic module context if none exists.
        """
        schema = self.generate_tool_schema(func)
        if not schema:
            raise ValueError(
                'Schema undefined. ToolHandler.generate_tool_schema() may not be implemented.'
                )
        if not hasattr(func, '__module_context__'):
            if inspect.isbuiltin(func) or inspect.ismethoddescriptor(func):
                source = self._create_builtin_wrapper(func)
            else:
                try:
                    source = inspect.getsource(func)
                except (TypeError, OSError):
                    source = self._create_dynamic_wrapper(func)
            file_path = f'dynamic_module_{hash(str(func))}'
            source = self.clean_source(source)
            module_name = f'dynamic_module_{hash(source)}'
            module = ModuleType(module_name)
            module.__file__ = file_path
            module_context = ModuleContext(name=module_name, source=source,
                file_path=file_path, namespace=module, code_hash=self.
                _get_code_hash(source))
            exec(source, module.__dict__)
            new_func = module.__dict__[func.__name__]
            new_func.__module_context__ = module_context
            self.modules[file_path] = module_context
            func = new_func
        self.tools.append(schema)
        self.function_map[func.__name__] = func

    def add_tools_from_file(self, filepath: str) ->None:
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
        module_name = (
            f'dynamic_module_{hashlib.md5(abs_file_path.encode()).hexdigest()}'
            )
        try:
            with open(abs_file_path, 'r') as file:
                source = file.read()
            module = ModuleType(module_name)
            module.__file__ = abs_file_path
            tree = ast.parse(source)
            function_nodes = [node for node in ast.walk(tree) if isinstance
                (node, ast.FunctionDef)]
            sys.path.insert(0, os.path.dirname(abs_file_path))
            try:
                exec(source, module.__dict__)
            finally:
                sys.path.pop(0)
            module_context = ModuleContext(name=module_name, source=source,
                file_path=abs_file_path, namespace=module, code_hash=self.
                _get_code_hash(source))
            self.modules[abs_file_path] = module_context
            for node in function_nodes:
                if not node.name.startswith('_'):
                    func = module.__dict__.get(node.name)
                    if func:
                        func.__module_context__ = module_context
                        self.add_tool(func)
        except Exception as e:
            raise ModuleLoadError(
                f'Error loading module from {filepath}: {str(e)}') from e

    def add_tools_from_module(self, module: ModuleType) ->None:
        """
        Add all non-private functions from a module as tools.
        """
        try:
            try:
                source = getattr(module, '__source__', None
                    ) or inspect.getsource(module)
            except Exception:
                functions = inspect.getmembers(module, inspect.isfunction)
                source_parts = []
                for name, func in functions:
                    if not name.startswith('_'):
                        try:
                            func_source = inspect.getsource(func)
                        except Exception:
                            raise ValueError('function source code not found')
                            func_source = f"""def {name}{inspect.signature(func)}:
    {func.__doc__ or ''}
    return None"""
                        source_parts.append(textwrap.dedent(func_source))
                source = '\n\n'.join(source_parts)
            source = self.clean_source(source)
            module_context = ModuleContext(name=module.__name__, source=
                source, file_path=getattr(module, '__file__',
                f'dynamic_module_{hashlib.md5(module.__name__.encode()).hexdigest()}'
                ), namespace=module, code_hash=self._get_code_hash(source))
            self.modules[module_context.file_path] = module_context
            for name, func in inspect.getmembers(module, inspect.isfunction):
                if not name.startswith('_'):
                    func.__module_context__ = module_context
                    self.add_tool(func)
        except Exception as e:
            raise ModuleLoadError(
                f'Error loading module {module.__name__}: {str(e)}') from e

    def to_dict(self) ->Dict[str, Any]:
        """
        Serialize the ToolHandler state to a dictionary.
        """
        module_details = {}
        function_paths = {}
        for file_path, module_context in self.modules.items():
            module_details[file_path] = {'name': module_context.name,
                'source': module_context.source, 'file_path':
                module_context.file_path, 'code_hash': module_context.code_hash
                }
        for name, func in self.function_map.items():
            module_context = getattr(func, '__module_context__', None)
            if module_context:
                function_paths[name] = module_context.file_path
            else:
                function_paths[name] = 'dynamic'
        return {'class':
            f'{self.__class__.__module__}.{self.__class__.__name__}',
            'tools': self.tools.copy(), 'requests': self.requests.copy(),
            'results': self.results.copy(), 'modules': module_details,
            'function_paths': function_paths}

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) ->'ToolHandler':
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
                print(
                    f'Warning: Code hash mismatch for module {file_path}. Skipping.'
                    )
                continue
            try:
                module = ModuleType(module_data['name'])
                module.__file__ = file_path
                source = textwrap.dedent(module_data['source']).strip()
                exec(source, module.__dict__)
                module_context = ModuleContext(name=module_data['name'],
                    source=source, file_path=module_data['file_path'],
                    namespace=module, code_hash=current_code_hash)
                handler.modules[module_data['file_path']] = module_context
                for func_name, path in function_paths.items():
                    if path == module_data['file_path'
                        ] and func_name in module.__dict__:
                        func = module.__dict__[func_name]
                        if callable(func):
                            func.__module_context__ = module_context
                            handler.function_map[func_name] = func
            except Exception as e:
                print(f'Warning: Failed to load module {file_path}: {str(e)}')
                continue
        for func_name, path in function_paths.items():
            if path == 'dynamic' and func_name not in handler.function_map:
                print(
                    f"Warning: Dynamic function '{func_name}' cannot be restored without source."
                    )
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
    def _get_code_hash(code: str) ->str:
        """Generate MD5 hash of code string."""
        return hashlib.md5(code.encode()).hexdigest()

    def __str__(self) ->str:
        """String representation showing number of tools and modules."""
        return (
            f'ToolHandler with {len(self.tools)} tools and {len(self.modules)} modules'
            )

    def __repr__(self) ->str:
        """Detailed representation including tool names."""
        tool_names = list(self.function_map.keys())
        return (
            f'ToolHandler(tools={tool_names}, modules={list(self.modules.keys())})'
            )


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
        raise NotImplemented('You must implement this method in a subclass')
        pass

    @abstractmethod
    def process_response(self, response: Dict[str, Any], bot: 'Bot'=None
        ) ->Tuple[str, str, Dict[str, Any]]:
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
        raise NotImplemented('You must implement this method in a subclass')
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
        ]=None, mailbox: Optional[Mailbox]=None, autosave: bool=True):
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

    def respond(self, prompt: str, role: str='user') ->str:
        """
        Sends 'prompt' to the Bot and returns the text response
        Allows tool use
        """
        self.conversation = self.conversation.add_reply(content=prompt,
            role=role)
        reply, _ = self._cvsn_respond()
        if self.autosave:
            self.save(f'{self.name}')
        return reply

    def _cvsn_respond(self) ->Tuple[str, ConversationNode]:
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
            if self.tool_handler:
                self.tool_handler.handle_response(response)
            text, role, data = self.mailbox.process_response(response, self)
            node = self.conversation.add_reply(content=text, role=role, **data)
            self.conversation = node
            return text, node
        except Exception as e:
            raise e

    def add_tool(self, func: Callable):
        self.tool_handler.add_tool(func)

    def add_tools(self, path_or_module: Union[str, ModuleType]) ->None:
        """Adds top level functions from a python file or module to the bot's toolkit."""
        if isinstance(path_or_module, str):
            self.tool_path = path_or_module
            self.tool_handler.add_tools_from_file(path_or_module)
        elif isinstance(path_or_module, ModuleType):
            self.tool_handler.add_tools_from_module(path_or_module)
            self.tool_path = str(path_or_module)
        else:
            raise TypeError('path_or_module must be a string or module object')

    def set_system_message(self, message: str) ->None:
        self.system_message = message

    @classmethod
    def load(cls, filepath: str, api_key=None) ->'Bot':
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
            # Create handler instance first, then restore its state
            bot.tool_handler = actual_class().from_dict(data['tool_handler'])
        for key, value in data.items():
            if key not in constructor_args and key not in ('conversation',
                'tool_handler', 'tools'):
                setattr(bot, key, value)
        if 'conversation' in data and data['conversation']:
            node_class = Engines.get_conversation_node_class(data[
                'conversation']['node_class'])
            bot.conversation = node_class.from_dict(data['conversation'])
            while bot.conversation.replies:
                bot.conversation = bot.conversation.replies[0]
        return bot

    def save(self, filename: Optional[str]=None) ->str:
        if filename is None:
            now = formatted_datetime()
            filename = f'{self.name}@{now}.bot'
        elif not filename.endswith('.bot'):
            filename = filename + '.bot'
        data = {key: value for key, value in self.__dict__.items() if not key.startswith('_')}
        data.pop('api_key', None)
        data.pop('mailbox', None)
        data['bot_class'] = self.__class__.__name__
        data['model_engine'] = self.model_engine.value
        data['conversation'] = self.conversation.root_dict()
        if self.tool_handler:
            data['tool_handler'] = self.tool_handler.to_dict()
        for key, value in data.items():
            if not isinstance(value, (str, int, float, bool, list, dict,
                type(None))):
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
                    tool_name, _ = self.tool_handler.tool_name_and_input(
                        request)
                    print(f'Used Tool: {tool_name}')
                    print(separator)

    def __str__(self) ->str:
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
            available_width = max(40, 80 - display_level * indent_size -
                marker_size)
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
            wrapped_content = '\n'.join(textwrap.wrap(content, width=
                available_width, initial_indent=indent + '│ ',
                subsequent_indent=indent + '│ '))
            messages.append(f'{indent}┌─ {name_display}')
            messages.append(wrapped_content)
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
                root = root.parent
            lines.extend(format_conversation(root))
        return '\n'.join(lines)
