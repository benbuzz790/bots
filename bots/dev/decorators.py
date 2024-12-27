import os, sys, json, inspect, functools, ast, logging, traceback, textwrap
from typing import Callable, Optional, Any, Dict
from bots.foundation.base import remove_code_blocks, Bot
from bots.flows.flows import create_issue_flow, BotFlow
import bots.flows.functional_prompts as fp
from bots import AnthropicBot
from bots.events import BotEventSystem


# Set up logging
logging.basicConfig(level=logging.WARNING, format=
    '%(asctime)s - %(name)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)
logger.setLevel(logging.DEBUG)
class NoHTTPFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) ->bool:
        return 'response' not in record.name.lower()
logger.addFilter(NoHTTPFilter())


def lazy(prompt: Optional[str]=None, bot: Optional[Bot]=None, context:
    Optional[str]=None) ->Callable:

    def decorator(func: Callable) ->Callable:
        nonlocal bot, prompt, context
        if bot is None:
            bot = AnthropicBot(name='Claude')
        if prompt is None:
            prompt = ''
        if context is None:
            context = 'None'

        def wrapper(*args: Any, **kwargs: Any) ->Any:
            nonlocal func
            if not hasattr(wrapper, 'initialized') or not wrapper.initialized:
                function_name: str = func.__name__
                logger.debug(f'Initializing lazy function: {function_name}')
                context_content = _get_context(func, context)
                instructions: str = textwrap.dedent("""Please fill out the following 
                    function definition according to the following requirements. 
                    Respond only with the code in a single code block. Include all 
                    import statements inside the function definition. Remove the lazy 
                    decorator. Respond only with the function definition, including 
                    any new decorators and docstring. Include 'gen by @lazy' in the 
                    docstring. Use PEP8 convention with type hints for all variables.""")
                complete_prompt: str = textwrap.dedent(f"""
                    {instructions}

                    {prompt}

                    {context_content}

                    {function_name}{str(inspect.signature(func))}""")
                response: str = bot.respond(complete_prompt)
                function_code, _ = remove_code_blocks(response)
                function_code = function_code[0]
                logger.debug(f'Generated function code:\n{function_code}')
                source_file: str = inspect.getfile(func)
                logger.debug(f'Source file: {source_file}')
                with open(source_file, 'r') as file:
                    source_lines: str = file.read()
                logger.debug(f'Original source file content:\n{source_lines}')
                source_tree: ast.AST = ast.parse(source_lines)


                class FunctionReplacer(ast.NodeTransformer):

                    def __init__(self, function_name: str, new_code: str):
                        self.function_name = function_name
                        self.new_code = new_code

                    def visit_FunctionDef(self, node: ast.FunctionDef
                        ) ->ast.AST:
                        if node.name == self.function_name:
                            logger.debug(
                                f'Replacing function: {self.function_name}')
                            new_node: ast.AST = ast.parse(self.new_code).body[0
                                ]
                            return new_node
                        return node
                function_replacer = FunctionReplacer(function_name,
                    function_code)
                new_tree: ast.AST = function_replacer.visit(source_tree)
                ast.fix_missing_locations(new_tree)
                new_source_lines: str = ast.unparse(new_tree)
                logger.debug(f'New source file content:\n{new_source_lines}')
                with open(source_file, 'w') as file:
                    file.write(new_source_lines)
                logger.debug('Updated source file written')
                exec(function_code, globals())
                func = globals()[function_name]
                wrapper.initialized = True
                logger.debug(f'Lazy function {function_name} initialized')
            return func(*args, **kwargs)
        wrapper.initialized = False
        return wrapper
    return decorator

# Helper function for lazy
def _get_context(func: Callable, context_level: str) ->str:
    if context_level == 'None':
        return ''
    source_file = inspect.getfile(func)
    source_dir = os.path.dirname(source_file)
    if context_level == 'low':
        source_code = inspect.getsource(inspect.getmodule(func))
        tree = ast.parse(source_code)
        for node in ast.walk(tree):
            if isinstance(node, ast.ClassDef):
                for sub_node in node.body:
                    if isinstance(sub_node, ast.FunctionDef
                        ) and sub_node.name == func.__name__:
                        return ast.unparse(node)
        return ''
    elif context_level == 'medium':
        with open(source_file, 'r') as file:
            return file.read()
    elif context_level == 'high':
        context = ''
        with open(source_file, 'r') as file:
            context += (
                f'Current file ({os.path.basename(source_file)}):\n{file.read()}\n\n'
                )
        for filename in os.listdir(source_dir):
            if filename.endswith('.py') and filename != os.path.basename(
                source_file):
                file_path = os.path.join(source_dir, filename)
                context += (
                    f'Interface of {filename}:\n{_get_py_interface(file_path)}\n\n'
                    )
        return context
    elif context_level == 'very high':
        context = ''
        for filename in os.listdir(source_dir):
            if filename.endswith('.py'):
                file_path = os.path.join(source_dir, filename)
                with open(file_path, 'r') as file:
                    context += f'File: {filename}\n{file.read()}\n\n'
        return context
    else:
        raise ValueError(f'Invalid context level: {context_level}')

# Helper function for lazy
def _get_py_interface(file_path: str) ->str:

    def get_docstring(node):
        return ast.get_docstring(node) or ''

    def format_function(node):
        return (
            f'def {node.name}{ast.unparse(node.args)}:\n    """{get_docstring(node)}"""\n'
            )

    def format_class(node):
        class_str = f'class {node.name}'
        if node.bases:
            class_str += (
                f"({', '.join(ast.unparse(base) for base in node.bases)})")
        class_str += f':\n    """{get_docstring(node)}"""\n'
        for item in node.body:
            if isinstance(item, ast.FunctionDef):
                class_str += f'    {format_function(item)}\n'
        return class_str
    with open(file_path, 'r') as file:
        tree = ast.parse(file.read())
    interface = ''
    for node in tree.body:
        if isinstance(node, ast.ClassDef):
            interface += format_class(node) + '\n'
        elif isinstance(node, ast.FunctionDef):
            interface += format_function(node) + '\n'
    return interface.strip()

def create_issues(repo: str, include_args: bool=True):
    """
    A decorator that creates GitHub issues asynchronously when decorated functions raise exceptions.
    Uses BotFlow and BotEventSystem to handle issue creation in the background.

    Parameters:
    - repo (str): The target repository in format "owner/repo" where issues will be created
    - include_args (bool): Whether to include function arguments in the issue (default True)

    Returns:
    - Callable: The decorator function

    Example:
    @create_issues(repo="owner/repo")
    def my_function():
        # This will create an issue asynchronously if it raises an exception
        pass
    """

    def decorator(func: Callable) ->Callable:

        bot = AnthropicBot(name='issue_tracker_bot', autosave=False)
        bot_flow = BotFlow(bot, create_issue_flow)
        event_system = BotEventSystem()
        event_system.listener.subscribe('error_occurred', bot_flow.handle)
        event_system.start()

        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                exc_type, exc_value, exc_tb = sys.exc_info()
                tb_str = ''.join(traceback.format_tb(exc_tb))
                title = f'Error in {func.__name__}: {str(e)}'
                body_parts = [
                    f'An error occurred in function `{func.__name__}`',
                    '',
                    '### Error Details', 
                    f'- **Type**: {exc_type.__name__}',
                    f'- **Message**: {str(e)}', 
                    '',
                    '### Traceback',
                    '```python', 
                    tb_str, 
                    '```'
                    ]
                if include_args:
                    sig = inspect.signature(func)
                    body_parts.extend([
                        '', 
                        '### Function Details',
                        f'- **Signature**: `{func.__name__}{sig}`',
                        '- **Arguments**:', 
                        '```python', 
                        f'args: {args}',
                        f'kwargs: {kwargs}', 
                        '```'
                        ])
                try:
                    source = inspect.getsource(func)
                    body_parts.extend(['', '### Source Code', '```python', source, '```'])
                except Exception:
                    body_parts.extend(['', '### Source Code','*Source code not available*'])
                
                body = '\n'.join(body_parts)
                error_info = {
                    'repo': repo,
                    'title': title, 
                    'body': body, 
                    'function': func.__name__, 
                    'error_type': exc_type.__name__,
                    'error_message': str(e)
                    }
                event_system.listener.emit('error_occurred', {'error_info':error_info})
                logger.info(f'Error event emitted for async issue creation: {title}')
                raise
        return wrapper
    return decorator

import sys
import traceback
from functools import wraps
from typing import Any, Callable

def debug_on_error(func: Callable) -> Callable:
    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        try:
            return func(*args, **kwargs)
        except Exception:
            type, value, tb = sys.exc_info()
            traceback.print_exception(type, value, tb)
            print("\n--- Entering post-mortem debugging ---")
            import pdb
            pdb.post_mortem(tb)
    return wrapper
