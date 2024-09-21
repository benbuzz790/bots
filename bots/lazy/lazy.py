import inspect
import os
import ast
import logging
from typing import Callable, Optional, Any
from bots.foundation.base import remove_code_blocks, Bot
from bots import AnthropicBot
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
                context_content = get_context(func, context)
                instructions: str = (
                    '''Please fill out the following function definition according 
                    to the following requirements. Respond only with the code in a 
                    single code block. Include all import statements inside the 
                    function definition. Remove the lazy decorator. Respond only
                    with the function definition, including any new decorators and
                    docstring. Include 'gen by @lazy' in the docstring. Use PEP8 
                    convention with type hints for all variables.'''
                    )
                complete_prompt: str = f"""{instructions}

{prompt}

{context_content}

{function_name}{str(inspect.signature(func))}"""
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


def get_context(func: Callable, context_level: str) ->str:
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
                    f'Interface of {filename}:\n{get_py_interface(file_path)}\n\n'
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


def get_py_interface(file_path: str) ->str:

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


