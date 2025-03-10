import unittest
import os
import json
from unittest.mock import patch
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
import bots.tools.python_editing_tools as python_editing_tools


def simple_addition(x, y) ->str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))


class TestSaveLoad(unittest.TestCase):

    def setUp(self):
        self.temp_dir = os.path.join('benbuzz790', 'private_tests', 'temp')
        os.makedirs(self.temp_dir, exist_ok=True)
        self.bots = {'anthropic': AnthropicBot(name='TestClaude',
            model_engine=Engines.CLAUDE35_SONNET_20240620)}
        return self

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f'Warning: Could not clean up {self.temp_dir}: {e}')

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
            self.assertEqual(bot.conversation._node_count(), loaded_bot.
                conversation._node_count())
            self.assertEqual(bot.conversation.content, loaded_bot.
                conversation.content)
        self.run_test_for_both_bots(_test)

    def test_save_load_with_file_tools(self):

        def _test(bot):
            tool_file_path = 'bots/tools/python_editing_tools.py'
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
            bot.add_tools(python_editing_tools)
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
        """Test that tool results are properly saved in conversation nodes"""

        def _test(bot):
            bot.add_tools(simple_addition)
            bot.respond('What is 2 + 3?')
            tool_results = bot.conversation.tool_results[0].values(
                ) if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values(
                ) if bot.conversation.pending_results else []
            self.assertTrue(any('5' in str(v) for v in tool_results) or any
                ('5' in str(v) for v in pending_results))
            save_path = os.path.join(self.temp_dir, f'tool_exec_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            loaded_tool_results = loaded_bot.conversation.tool_results[0
                ].values() if loaded_bot.conversation.tool_results else []
            loaded_pending_results = loaded_bot.conversation.pending_results[0
                ].values() if loaded_bot.conversation.pending_results else []
            self.assertTrue(any('5' in str(v) for v in loaded_tool_results) or
                any('5' in str(v) for v in loaded_pending_results))
        self.run_test_for_both_bots(_test)

    def test_save_load_with_tool_use(self):
        """Test that tool results are properly maintained in individual conversation nodes"""

        def _test(bot: Bot):
            bot.add_tools(simple_addition)
            interactions = ['What is 5 + 3?', 'Can you add 10 and 20?',
                'Please add 7 and 15']
            for query in interactions:
                _ = bot.respond(query)
            tool_results = bot.conversation.tool_results[0].values(
                ) if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values(
                ) if bot.conversation.pending_results else []
            self.assertTrue(any('22' in str(v) for v in tool_results) or
                any('22' in str(v) for v in pending_results))
            save_path = os.path.join(self.temp_dir, f'tool_use_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            loaded_bot.save(save_path + '2')
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.
                tool_handler.tools))
            loaded_tool_results = loaded_bot.conversation.tool_results[0
                ].values() if loaded_bot.conversation.tool_results else []
            loaded_pending_results = loaded_bot.conversation.pending_results[0
                ].values() if loaded_bot.conversation.pending_results else []
            self.assertTrue(any('22' in str(v) for v in loaded_tool_results
                ) or any('22' in str(v) for v in loaded_pending_results))
            new_response = loaded_bot.respond('What is 25 + 17?')
            self.assertIsNotNone(new_response)
            loaded_tool_results = loaded_bot.conversation.tool_results[0
                ].values() if loaded_bot.conversation.tool_results else []
            loaded_pending_results = loaded_bot.conversation.pending_results[0
                ].values() if loaded_bot.conversation.pending_results else []
            self.assertTrue(any('42' in str(v) for v in loaded_tool_results
                ) or any('42' in str(v) for v in loaded_pending_results))
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
            bot.add_tools(simple_addition)
            original_tool_count = len(bot.tool_handler.tools)
            save_path1 = os.path.join(self.temp_dir, f'cycle1_{bot.name}')
            bot.respond('What is 5 + 3?')
            tool_results = bot.conversation.tool_results[0].values(
                ) if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values(
                ) if bot.conversation.pending_results else []
            self.assertTrue(any('8' in str(v) for v in tool_results) or any
                ('8' in str(v) for v in pending_results))
            bot.save(save_path1)
            loaded1 = Bot.load(save_path1 + '.bot')
            loaded_tool_results = loaded1.conversation.tool_results[0].values(
                ) if loaded1.conversation.tool_results else []
            loaded_pending_results = loaded1.conversation.pending_results[0
                ].values() if loaded1.conversation.pending_results else []
            self.assertTrue(any('8' in str(v) for v in loaded_tool_results) or
                any('8' in str(v) for v in loaded_pending_results))
            save_path2 = os.path.join(self.temp_dir, f'cycle2_{bot.name}')
            loaded1.respond('What is 10 + 15?')
            loaded_tool_results = loaded1.conversation.tool_results[0].values(
                ) if loaded1.conversation.tool_results else []
            loaded_pending_results = loaded1.conversation.pending_results[0
                ].values() if loaded1.conversation.pending_results else []
            self.assertTrue(any('25' in str(v) for v in loaded_tool_results
                ) or any('25' in str(v) for v in loaded_pending_results))
            loaded1.save(save_path2)
            loaded2 = Bot.load(save_path2 + '.bot')
            self.assertEqual(original_tool_count, len(loaded2.tool_handler.
                tools))
            self.assertEqual(loaded2.conversation._node_count(), 5)
            loaded2.respond('What is 12 + 13?')
            loaded_tool_results = loaded2.conversation.tool_results[0].values(
                ) if loaded2.conversation.tool_results else []
            loaded_pending_results = loaded2.conversation.pending_results[0
                ].values() if loaded2.conversation.pending_results else []
            self.assertTrue(any('25' in str(v) for v in loaded_tool_results
                ) or any('25' in str(v) for v in loaded_pending_results))
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
            self.assertEqual(bot.conversation._node_count(), loaded_bot.
                conversation._node_count())
            response = loaded_bot.respond('Can you still respond?')
            self.assertIsNotNone(response)
            self.assertTrue(len(response) > 0)
        self.run_test_for_both_bots(_test)

    def test_working_directory_independence(self):
        """Test that bots can be saved and loaded from different working directories
    while maintaining proper tool results state"""

        def _test(bot):
            subdir = os.path.join(self.temp_dir, 'subdir')
            os.makedirs(subdir, exist_ok=True)
            bot.add_tools(simple_addition)
            original_path = os.path.join(self.temp_dir, f'original_{bot.name}')
            bot.save(original_path)
            original_cwd = os.getcwd()
            try:
                os.chdir(subdir)
                loaded_bot = Bot.load(os.path.join('..',
                    f'original_{bot.name}.bot'))
                loaded_bot.respond('What is 7 + 8?')
                loaded_tool_results = loaded_bot.conversation.tool_results[0
                    ].values() if loaded_bot.conversation.tool_results else []
                loaded_pending_results = (loaded_bot.conversation.
                    pending_results[0].values() if loaded_bot.conversation.
                    pending_results else [])
                self.assertTrue(any('15' in str(v) for v in
                    loaded_tool_results) or any('15' in str(v) for v in
                    loaded_pending_results))
                new_path = os.path.join('..', f'from_subdir_{bot.name}')
                loaded_bot.save(new_path)
            finally:
                os.chdir(original_cwd)
        self.run_test_for_both_bots(_test)

    @unittest.skip('Kinda works')
    def test_dynamic_function_rejection(self):
        """Test that dynamic functions are properly rejected"""

        def _test(bot):
            dynamic_code = """
def dynamic_add(x, y):
    ""\"Dynamically created addition function""\"
    return str(int(x) + int(y))
"""
            namespace = {}
            exec(dynamic_code, namespace)
            dynamic_func = namespace['dynamic_add']
            with self.assertRaises(ValueError) as context:
                bot.add_tools(dynamic_func)
            self.assertIn('Dynamic functions cannot be used as tools', str(
                context.exception))
        self.run_test_for_both_bots(_test)

    def test_mixed_tool_sources(self):
        """Test saving and loading bots with tools from multiple sources"""

        def floor_str(x) ->str:
            """Returns floor of x as a string"""
            import math
            return str(math.floor(float(x)))

        def _test(bot):
            bot.add_tools(simple_addition)
            bot.add_tools(floor_str)
            bot.respond('What is 3 + 4?')
            bot.respond('What is the floor of 7.8?')
            original_results = bot.tool_handler.get_results()
            save_path = os.path.join(self.temp_dir, f'mixed_tools_{bot.name}')
            bot.save(save_path)
            loaded_bot = Bot.load(save_path + '.bot')
            loaded_bot.respond('What is 8 + 9?')
            loaded_bot.respond('What is the floor of 5.6?')
            loaded_results = loaded_bot.tool_handler.get_results()
            self.assertEqual('7', original_results[0]['content'])
            self.assertEqual('7', original_results[1]['content'])
            self.assertEqual('17', loaded_results[2]['content'])
            self.assertEqual('5', loaded_results[3]['content'])


import sys
import traceback
from functools import wraps
from typing import Any, Callable
import shutil
from bots.tools.python_editing_tools import replace_function


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
    test.test_multiple_save_load_cycles()


if __name__ == '__main__':
    unittest.main()
    #main()