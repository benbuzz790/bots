import unittest
import os
import tempfile
import json
from unittest.mock import patch
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
import bots.tools.python_tools as python_tools


def simple_addition(x, y) ->str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))


class TestSaveLoad(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp(dir=os.path.dirname(__file__))
        self.bots = {'anthropic': AnthropicBot(name='TestClaude',
            model_engine=Engines.CLAUDE35_SONNET_20240620)}
        return self

    def tearDown(self):
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def run_test_for_both_bots(self, test_func):
        """Helper to run a test for both bot types"""
        for bot_type, bot in self.bots.items():
            with self.subTest(bot_type=bot_type):
                test_func(bot)

    def test_basic_save_load(self):

        def _test(original_bot):
            save_path = os.path.join(self.temp_dir, original_bot.name)
            save_path = original_bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(original_bot.name, loaded_bot.name)
            self.assertEqual(original_bot.model_engine, loaded_bot.model_engine
                )
            self.assertEqual(original_bot.max_tokens, loaded_bot.max_tokens)
            self.assertEqual(original_bot.temperature, loaded_bot.temperature)
            self.assertEqual(original_bot.role, loaded_bot.role)
            self.assertEqual(original_bot.role_description, loaded_bot.
                role_description)
        self.run_test_for_both_bots(_test)

    def test_save_load_after_conversation(self):

        def _test(bot):
            bot.respond('Hello, how are you?')
            bot.respond("What's the weather like today?")
            bot.respond('Thank you for the information.')
            save_path = os.path.join(self.temp_dir, f'convo_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.conversation.node_count(), loaded_bot.
                conversation.node_count())
            self.assertEqual(bot.conversation.content, loaded_bot.
                conversation.content)
        self.run_test_for_both_bots(_test)

    def test_save_load_with_file_tools(self):

        def _test(bot):
            tool_file_path = 'bots/tools/python_tools.py'
            bot.add_tools(tool_file_path)
            save_path = os.path.join(self.temp_dir, f'file_tool_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.
                tool_handler.tools))
            for original_tool, loaded_tool in zip(bot.tool_handler.tools,
                loaded_bot.tool_handler.tools):
                self.assertEqual(original_tool.get('name'), loaded_tool.get
                    ('name'))
                self.assertEqual(original_tool.get('parameters'),
                    loaded_tool.get('parameters'))
                self.assertEqual(original_tool.get('returns', {}).get(
                    'type'), loaded_tool.get('returns', {}).get('type'))
                self.assertEqual(original_tool.get('type'), loaded_tool.get
                    ('type'))
                if 'function' in original_tool and 'function' in loaded_tool:
                    self.assertEqual(type(original_tool['function']), type(
                        loaded_tool['function']))
        self.run_test_for_both_bots(_test)

    def test_save_load_with_module_tools(self):

        def _test(bot):
            bot.add_tools(python_tools)
            save_path = os.path.join(self.temp_dir, f'module_tool_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.
                tool_handler.tools))
            for original_tool, loaded_tool in zip(bot.tool_handler.tools,
                loaded_bot.tool_handler.tools):
                self.assertEqual(original_tool.get('name'), loaded_tool.get
                    ('name'))
                self.assertEqual(original_tool.get('parameters'),
                    loaded_tool.get('parameters'))
                self.assertEqual(original_tool.get('returns', {}).get(
                    'type'), loaded_tool.get('returns', {}).get('type'))
                self.assertEqual(original_tool.get('type'), loaded_tool.get
                    ('type'))
        self.run_test_for_both_bots(_test)

    def test_save_load_with_system_message(self):

        def _test(bot):
            system_message = (
                'You are a helpful assistant specialized in Python programming.'
                )
            bot.set_system_message(system_message)
            save_path = os.path.join(self.temp_dir, f'system_msg_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.system_message, loaded_bot.system_message)
        self.run_test_for_both_bots(_test)

    def test_api_key_handling(self):

        def _test(bot):
            save_path = os.path.join(self.temp_dir, f'api_key_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertIsNone(loaded_bot.api_key)
            new_api_key = 'new_test_api_key'
            loaded_bot_with_key = Bot.load(save_path, api_key=new_api_key)
            self.assertEqual(loaded_bot_with_key.api_key, new_api_key)
        self.run_test_for_both_bots(_test)

    def test_tool_execution_results(self):

        def _test(bot):
            bot.add_tool(simple_addition)
            bot.respond('What is 2 + 3?')
            self.assertEqual(len(bot.tool_handler.get_results()), 1)
            self.assertIn('5', bot.tool_handler.get_results()[0]['content'])
            save_path = os.path.join(self.temp_dir, f'tool_exec_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.tool_handler.get_results(), loaded_bot.
                tool_handler.get_results())
        self.run_test_for_both_bots(_test)

    def test_save_load_with_tool_use(self):

        def _test(bot: Bot):
            bot.add_tool(simple_addition)
            interactions = ['What is 5 + 3?', 'Can you add 10 and 20?',
                'Please add 7 and 15']
            original_responses = []
            for query in interactions:
                response = bot.respond(query)
                original_responses.append(response)
            original_results = bot.tool_handler.get_results()
            save_path = os.path.join(self.temp_dir, f'tool_use_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            loaded_bot.save(save_path + '2')
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.
                tool_handler.tools))
            loaded_results = loaded_bot.tool_handler.get_results()
            self.assertEqual(len(original_results), len(loaded_results))
            for original, loaded in zip(original_results, loaded_results):
                self.assertEqual(original['content'], loaded['content'])
            new_response = loaded_bot.respond('What is 25 + 17?')
            self.assertIsNotNone(new_response)
            updated_results = loaded_bot.tool_handler.get_results()
            latest_result = updated_results[-1]
            self.assertEqual(int(latest_result['content']), 42)
        self.run_test_for_both_bots(_test)

    def test_custom_attributes(self):

        def _test(bot):
            bot.custom_attr1 = 'Test Value'
            bot.custom_attr2 = 42
            bot.custom_attr3 = {'key': 'value'}
            save_path = os.path.join(self.temp_dir, f'custom_attr_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.custom_attr1, loaded_bot.custom_attr1)
            self.assertEqual(bot.custom_attr2, loaded_bot.custom_attr2)
            self.assertEqual(bot.custom_attr3, loaded_bot.custom_attr3)
            self.assertIsInstance(loaded_bot.custom_attr1, str)
            self.assertIsInstance(loaded_bot.custom_attr2, int)
            self.assertIsInstance(loaded_bot.custom_attr3, dict)
            with self.assertRaises(AttributeError):
                _ = loaded_bot.non_existent_attr
        self.run_test_for_both_bots(_test)

    def test_file_creation(self):
        """Test that save files are created in the expected location"""

        def _test(bot):
            save_path = os.path.join(self.temp_dir, f'explicit_{bot.name}')
            actual_path = bot.save(save_path)
            self.assertTrue(os.path.exists(actual_path))
            self.assertEqual(actual_path, save_path + '.bot')
            auto_path = bot.save()
            self.assertTrue(os.path.exists(auto_path))
            self.assertTrue(auto_path.endswith('.bot'))
        self.run_test_for_both_bots(_test)

    def test_corrupted_save(self):
        """Test handling of corrupted save files"""

        def _test(bot):
            save_path = os.path.join(self.temp_dir, f'corrupted_{bot.name}.bot'
                )
            bot.save(save_path[:-4])
            with open(save_path, 'w') as f:
                f.write('{"invalid": "json')
            with self.assertRaises(json.JSONDecodeError):
                Bot.load(save_path)
            with open(save_path, 'w') as f:
                f.write('{"name": "test", "model_engine": "invalid-model"}')
            with self.assertRaises(ValueError):
                Bot.load(save_path)
        self.run_test_for_both_bots(_test)

    def test_multiple_save_load_cycles(self):
        """Test multiple save/load cycles with tool usage"""

        def _test(bot):
            bot.add_tool(simple_addition)
            original_tool_count = len(bot.tool_handler.tools)
            save_path1 = os.path.join(self.temp_dir, f'cycle1_{bot.name}')
            bot.respond('What is 5 + 3?')
            bot.save(save_path1)
            loaded1 = Bot.load(save_path1 + '.bot')
            save_path2 = os.path.join(self.temp_dir, f'cycle2_{bot.name}')
            loaded1.respond('What is 10 + 15?')
            loaded1.save(save_path2)
            loaded2 = Bot.load(save_path2 + '.bot')
            self.assertEqual(original_tool_count, len(loaded2.tool_handler.
                tools))
            self.assertEqual(len(bot.tool_handler.get_results()) + 1, len(
                loaded2.tool_handler.get_results()))
            self.assertEqual(loaded2.conversation.node_count(), 4)
        self.run_test_for_both_bots(_test)

    @unittest.skip('too expensive, not necessary')
    def test_large_conversation(self):
        """Test saving and loading large conversations"""

        def _test(bot):
            for i in range(100):
                bot.respond(f'This is test message {i}')
            save_path = os.path.join(self.temp_dir, f'large_{bot.name}')
            actual_path = bot.save(save_path)
            self.assertTrue(os.path.exists(actual_path))
            loaded_bot = Bot.load(actual_path)
            self.assertEqual(bot.conversation.node_count(), loaded_bot.
                conversation.node_count())
            response = loaded_bot.respond('Can you still respond?')
            self.assertIsNotNone(response)
            self.assertTrue(len(response) > 0)
        self.run_test_for_both_bots(_test)

    def test_working_directory_independence(self):
        """Test that bots can be saved and loaded from different working directories"""

        def _test(bot):
            subdir = os.path.join(self.temp_dir, 'subdir')
            os.makedirs(subdir, exist_ok=True)
            bot.add_tool(simple_addition)
            original_path = os.path.join(self.temp_dir, f'original_{bot.name}')
            bot.save(original_path)
            original_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                loaded_bot = Bot.load(os.path.join('..',
                    f'original_{bot.name}.bot'))
                loaded_bot.respond('What is 7 + 8?')
                self.assertIn('15', loaded_bot.tool_handler.get_results()[-
                    1]['content'])
                new_path = os.path.join('..', f'from_subdir_{bot.name}')
                loaded_bot.save(new_path)
            finally:
                os.chdir(original_cwd)
        self.run_test_for_both_bots(_test)

    def test_dynamic_function_persistence(self):
        """Test saving and loading bots with dynamically created functions"""

        def _test(bot):
            dynamic_code = """
def dynamic_add(x, y):
    ""\"Dynamically created addition function""\"
    return str(int(x) + int(y))
"""
            namespace = {}
            exec(dynamic_code, namespace)
            dynamic_func = namespace['dynamic_add']
            bot.add_tool(dynamic_func)
            bot.respond('What is 3 + 4 using the dynamic function?')
            original_result = bot.tool_handler.get_results()[-1]['content']
            save_path = os.path.join(self.temp_dir, f'dynamic_{bot.name}')
            bot.save(save_path)
            loaded_bot = Bot.load(save_path + '.bot')
            loaded_bot.respond('What is 5 + 6 using the dynamic function?')
            new_result = loaded_bot.tool_handler.get_results()[-1]['content']
            self.assertEqual('7', original_result)
            self.assertEqual('11', new_result)
        self.run_test_for_both_bots(_test)

    def test_mixed_tool_sources(self):
        """Test saving and loading bots with tools from multiple sources"""

        def _test(bot):
            bot.add_tool(simple_addition)
            dynamic_code = """
def dynamic_multiply(x, y):
    ""\"Dynamically created multiplication function""\"
    return str(int(x) * int(y))
"""
            namespace = {}
            exec(dynamic_code, namespace)
            bot.add_tool(namespace['dynamic_multiply'])
            import math
            bot.add_tool(math.floor)
            bot.respond('What is 3 + 4?')
            bot.respond('What is 5 * 6?')
            bot.respond('What is the floor of 7.8?')
            original_results = bot.tool_handler.get_results()
            save_path = os.path.join(self.temp_dir, f'mixed_tools_{bot.name}')
            bot.save(save_path)
            loaded_bot = Bot.load(save_path + '.bot')
            loaded_bot.respond('What is 8 + 9?')
            loaded_bot.respond('What is 3 * 4?')
            loaded_bot.respond('What is the floor of 5.6?')
            loaded_results = loaded_bot.tool_handler.get_results()
            self.assertEqual('7', original_results[0]['content'])
            self.assertEqual('30', original_results[1]['content'])
            self.assertEqual('7', original_results[2]['content'])
            self.assertEqual('17', loaded_results[3]['content'])
            self.assertEqual('12', loaded_results[4]['content'])
            self.assertEqual('5', loaded_results[5]['content'])
        self.run_test_for_both_bots(_test)


import sys
import traceback
from functools import wraps
from typing import Any, Callable


def debug_on_error(func: Callable) ->Callable:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) ->Any:
        try:
            return func(*args, **kwargs)
        except Exception:
            type, value, tb = sys.exc_info()
            traceback.print_exception(type, value, tb)
            print('\n--- Entering post-mortem debugging ---')
            import pdb
            pdb.post_mortem(tb)
    return wrapper


@debug_on_error
def main():
    test = TestSaveLoad()
    test.setUp()
    test.test_save_load_with_tool_use()


if __name__ == '__main__':
    unittest.main()
