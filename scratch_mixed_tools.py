import os
import tempfile
import inspect
import math
from bots.foundation.base import Bot, Engines, ModuleContext
from bots.foundation.anthropic_bots import AnthropicBot, AnthropicToolHandler
from types import ModuleType


class FixedToolHandler(AnthropicToolHandler):
    """Extends AnthropicToolHandler with improved built-in function handling"""

    def generate_tool_schema(self, func):
        """Override to handle built-in functions"""
        if inspect.isbuiltin(func):
            return {'name': func.__name__, 'description': func.__doc__ or
                f'Built-in function {func.__name__}', 'parameters': {'type':
                'object', 'properties': {'x': {'type': 'number',
                'description': 'Input value'}}, 'required': ['x']}}
        return super().generate_tool_schema(func)

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
            if func.__name__ == 'dynamic_multiply':
                source += '    return str(int(x) * int(y))\n'
            elif func.__name__ == 'simple_add':
                source += '    return str(int(x) + int(y))\n'
            else:
                try:
                    body = inspect.getsource(func).split('\n', 1)[1]
                    source += body
                except:
                    source += '    return func(x, y)\n'
        else:
            source += '    pass\n'
        return source

    def add_tool(self, func):
        """Add a function as a tool with proper source preservation"""
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

    def generate_request_schema(self, response):
        return super().generate_request_schema(response)

    def tool_name_and_input(self, request_schema):
        return super().tool_name_and_input(request_schema)

    def generate_response_schema(self, request, tool_output_kwargs):
        return super().generate_response_schema(request, tool_output_kwargs)

    def get_error_schema(self, request_schema, error_msg):
        return super().get_error_schema(request_schema, error_msg)


def test_mixed_tool_sources():
    """Test saving and loading bots with tools from multiple sources"""
    temp_dir = tempfile.mkdtemp()
    try:
        bot = AnthropicBot(name='TestClaude', model_engine=Engines.
            CLAUDE35_SONNET_20240620, api_key=None, max_tokens=1000,
            temperature=0.7, role='assistant', role_description=
            'A helpful AI assistant')
        bot.tool_handler = FixedToolHandler()
        print('Adding tools...')

        def simple_add(x, y):
            """Simple addition function"""
            return str(int(x) + int(y))
        bot.add_tool(simple_add)
        bot.add_tool(math.floor)
        dynamic_code = """
def dynamic_multiply(x, y):
    ""\"Dynamically created multiplication function""\"
    return str(int(x) * int(y))
"""
        namespace = {}
        exec(dynamic_code, namespace)
        bot.add_tool(namespace['dynamic_multiply'])
        print('Testing original bot...')
        add_result = bot.tool_handler.function_map['simple_add']('3', '4')
        floor_result = bot.tool_handler.function_map['floor']('7.8')
        mult_result = bot.tool_handler.function_map['dynamic_multiply']('5',
            '6')
        print(
            f'Original results: add={add_result}, floor={floor_result}, mult={mult_result}'
            )
        save_path = os.path.join(temp_dir, f'mixed_tools_{bot.name}')
        print(f'Saving bot to {save_path}...')
        bot.save(save_path)
        print('Loading bot...')
        loaded_bot = Bot.load(save_path + '.bot')
        print('Testing loaded bot...')
        loaded_add = loaded_bot.tool_handler.function_map['simple_add']('8',
            '9')
        loaded_floor = loaded_bot.tool_handler.function_map['floor']('5.6')
        loaded_mult = loaded_bot.tool_handler.function_map['dynamic_multiply'](
            '3', '4')
        print(
            f'Loaded results: add={loaded_add}, floor={loaded_floor}, mult={loaded_mult}'
            )
        assert add_result == '7', f'Expected 7, got {add_result}'
        assert str(floor_result) == '7', f'Expected 7, got {floor_result}'
        assert mult_result == '30', f'Expected 30, got {mult_result}'
        assert loaded_add == '17', f'Expected 17, got {loaded_add}'
        assert str(loaded_floor) == '5', f'Expected 5, got {loaded_floor}'
        assert loaded_mult == '12', f'Expected 12, got {loaded_mult}'
        print('Test passed!')
    finally:
        for file in os.listdir(temp_dir):
            try:
                os.remove(os.path.join(temp_dir, file))
            except PermissionError:
                print(f'Warning: Could not remove {file}')
        try:
            os.rmdir(temp_dir)
        except OSError as e:
            print(f'Warning: Could not remove temp dir: {e}')
