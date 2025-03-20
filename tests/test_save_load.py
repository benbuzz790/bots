import unittest
import os
import json
from unittest.mock import patch
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
import bots.tools.python_editing_tools as python_editing_tools

def simple_addition(x, y) -> str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))

class TestSaveLoad(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bots = {'anthropic': AnthropicBot(name='TestClaude', model_engine=Engines.CLAUDE35_SONNET_20240620)}
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
            self.assertEqual(original_bot.model_engine, loaded_bot.model_engine)
            self.assertEqual(original_bot.max_tokens, loaded_bot.max_tokens)
            self.assertEqual(original_bot.temperature, loaded_bot.temperature)
            self.assertEqual(original_bot.role, loaded_bot.role)
            self.assertEqual(original_bot.role_description, loaded_bot.role_description)
        self.run_test_for_both_bots(_test)

    def test_save_load_after_conversation(self):

        def _test(bot):
            bot.respond('Hello, how are you?')
            bot.respond("What's the weather like today?")
            bot.respond('Thank you for the information.')
            save_path = os.path.join(self.temp_dir, f'convo_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.conversation._node_count(), loaded_bot.conversation._node_count())
            self.assertEqual(bot.conversation.content, loaded_bot.conversation.content)
        self.run_test_for_both_bots(_test)

    def test_save_load_with_file_tools(self):

        def _test(bot):
            tool_file_path = 'bots/tools/python_editing_tools.py'
            bot.add_tools(tool_file_path)
            save_path = os.path.join(self.temp_dir, f'file_tool_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
            for original_tool, loaded_tool in zip(bot.tool_handler.tools, loaded_bot.tool_handler.tools):
                self.assertEqual(original_tool.get('name'), loaded_tool.get('name'))
                self.assertEqual(original_tool.get('parameters'), loaded_tool.get('parameters'))
                self.assertEqual(original_tool.get('returns', {}).get('type'), loaded_tool.get('returns', {}).get('type'))
                self.assertEqual(original_tool.get('type'), loaded_tool.get('type'))
                if 'function' in original_tool and 'function' in loaded_tool:
                    self.assertEqual(type(original_tool['function']), type(loaded_tool['function']))
        self.run_test_for_both_bots(_test)

    def test_save_load_with_module_tools(self):

        def _test(bot):
            bot.add_tools(python_editing_tools)
            save_path = os.path.join(self.temp_dir, f'module_tool_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
            for original_tool, loaded_tool in zip(bot.tool_handler.tools, loaded_bot.tool_handler.tools):
                self.assertEqual(original_tool.get('name'), loaded_tool.get('name'))
                self.assertEqual(original_tool.get('parameters'), loaded_tool.get('parameters'))
                self.assertEqual(original_tool.get('returns', {}).get('type'), loaded_tool.get('returns', {}).get('type'))
                self.assertEqual(original_tool.get('type'), loaded_tool.get('type'))
        self.run_test_for_both_bots(_test)

    def test_save_load_with_system_message(self):

        def _test(bot):
            system_message = 'You are a helpful assistant specialized in Python programming.'
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
            tool_results = bot.conversation.tool_results[0].values() if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values() if bot.conversation.pending_results else []
            self.assertTrue(any(('5' in str(v) for v in tool_results)) or any(('5' in str(v) for v in pending_results)))
            save_path = os.path.join(self.temp_dir, f'tool_exec_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
            loaded_pending_results = loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
            self.assertTrue(any(('5' in str(v) for v in loaded_tool_results)) or any(('5' in str(v) for v in loaded_pending_results)))
        self.run_test_for_both_bots(_test)

    def test_save_load_with_tool_use(self):
        """Test that tool results are properly maintained in individual conversation nodes"""

        def _test(bot: Bot):
            bot.add_tools(simple_addition)
            interactions = ['What is 5 + 3?', 'Can you add 10 and 20?', 'Please add 7 and 15']
            for query in interactions:
                _ = bot.respond(query)
            tool_results = bot.conversation.tool_results[0].values() if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values() if bot.conversation.pending_results else []
            self.assertTrue(any(('22' in str(v) for v in tool_results)) or any(('22' in str(v) for v in pending_results)))
            save_path = os.path.join(self.temp_dir, f'tool_use_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            loaded_bot.save(save_path + '2')
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
            loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
            loaded_pending_results = loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
            self.assertTrue(any(('22' in str(v) for v in loaded_tool_results)) or any(('22' in str(v) for v in loaded_pending_results)))
            new_response = loaded_bot.respond('What is 25 + 17?')
            self.assertIsNotNone(new_response)
            loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
            loaded_pending_results = loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
            self.assertTrue(any(('42' in str(v) for v in loaded_tool_results)) or any(('42' in str(v) for v in loaded_pending_results)))
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
            save_path = os.path.join(self.temp_dir, f'corrupted_{bot.name}.bot')
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
            tool_results = bot.conversation.tool_results[0].values() if bot.conversation.tool_results else []
            pending_results = bot.conversation.pending_results[0].values() if bot.conversation.pending_results else []
            self.assertTrue(any(('8' in str(v) for v in tool_results)) or any(('8' in str(v) for v in pending_results)))
            bot.save(save_path1)
            loaded1 = Bot.load(save_path1 + '.bot')
            loaded_tool_results = loaded1.conversation.tool_results[0].values() if loaded1.conversation.tool_results else []
            loaded_pending_results = loaded1.conversation.pending_results[0].values() if loaded1.conversation.pending_results else []
            self.assertTrue(any(('8' in str(v) for v in loaded_tool_results)) or any(('8' in str(v) for v in loaded_pending_results)))
            save_path2 = os.path.join(self.temp_dir, f'cycle2_{bot.name}')
            loaded1.respond('What is 10 + 15?')
            loaded_tool_results = loaded1.conversation.tool_results[0].values() if loaded1.conversation.tool_results else []
            loaded_pending_results = loaded1.conversation.pending_results[0].values() if loaded1.conversation.pending_results else []
            self.assertTrue(any(('25' in str(v) for v in loaded_tool_results)) or any(('25' in str(v) for v in loaded_pending_results)))
            loaded1.save(save_path2)
            loaded2 = Bot.load(save_path2 + '.bot')
            self.assertEqual(original_tool_count, len(loaded2.tool_handler.tools))
            self.assertEqual(loaded2.conversation._node_count(), 5)
            loaded2.respond('What is 12 + 13?')
            loaded_tool_results = loaded2.conversation.tool_results[0].values() if loaded2.conversation.tool_results else []
            loaded_pending_results = loaded2.conversation.pending_results[0].values() if loaded2.conversation.pending_results else []
            self.assertTrue(any(('25' in str(v) for v in loaded_tool_results)) or any(('25' in str(v) for v in loaded_pending_results)))
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
            self.assertEqual(bot.conversation._node_count(), loaded_bot.conversation._node_count())
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
                loaded_bot = Bot.load(os.path.join('..', f'original_{bot.name}.bot'))
                loaded_bot.respond('What is 7 + 8?')
                loaded_tool_results = loaded_bot.conversation.tool_results[0].values() if loaded_bot.conversation.tool_results else []
                loaded_pending_results = loaded_bot.conversation.pending_results[0].values() if loaded_bot.conversation.pending_results else []
                self.assertTrue(any(('15' in str(v) for v in loaded_tool_results)) or any(('15' in str(v) for v in loaded_pending_results)))
                new_path = os.path.join('..', f'from_subdir_{bot.name}')
                loaded_bot.save(new_path)
            finally:
                os.chdir(original_cwd)
        self.run_test_for_both_bots(_test)

    def test_conversation_node_content_preservation(self):
        """Test that conversation node content is properly preserved during save/load"""

        def _test(bot):
            bot.conversation = bot.conversation._add_reply(content='', role='empty')
            self.assertEqual(bot.conversation.content, '')
            bot.conversation = bot.conversation._add_reply(content='Hello', role='user')
            self.assertEqual(bot.conversation.content, 'Hello')
            save_path = os.path.join(self.temp_dir, f'content_preservation_{bot.name}')
            save_path = bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(loaded_bot.conversation.content, 'Hello')
            root = loaded_bot.conversation._find_root()
            self.assertEqual(root.content, '')
            self.assertIn('node_class', root._to_dict_self())
            self.assertEqual(root.content, '')
            loaded_bot.conversation = loaded_bot.conversation._add_reply(content='Test content', role='user')
            self.assertEqual(loaded_bot.conversation.content, 'Test content')
            save_path2 = os.path.join(self.temp_dir, f'content_preservation2_{bot.name}')
            save_path2 = loaded_bot.save(save_path2)
            loaded_bot2 = Bot.load(save_path2)
            self.assertEqual(loaded_bot2.conversation.content, 'Test content')
        self.run_test_for_both_bots(_test)

    def test_mixed_tool_sources(self):
        """Test saving and loading bots with tools from multiple sources"""

        def floor_str(x) -> str:
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

    def test_module_tool_persistence(self):
        """Test that module tools persist correctly through multiple save/load cycles"""
        import bots.tools.code_tools as code_tools

        def compare_sources(source1, source2, context=''):
            """Compare two sources and print detailed differences"""
            print(f'\n=== Source Comparison {context} ===')
            print(f'Source1 length: {len(source1)}')
            print(f'Source2 length: {len(source2)}')
            if source1 == source2:
                print('Sources are identical!')
                return
            print('Sources differ!')
            print('\nFirst 50 chars of each:')
            print(f'Source1: {repr(source1[:50])}')
            print(f'Source2: {repr(source2[:50])}')
            for i, (c1, c2) in enumerate(zip(source1, source2)):
                if c1 != c2:
                    start = max(0, i - 20)
                    end = min(len(source1), i + 20)
                    print(f'\nFirst difference at position {i}:')
                    print(f'Source1 context: {repr(source1[start:end])}')
                    print(f'Source2 context: {repr(source2[start:end])}')
                    print(f'Different chars: {repr(c1)} vs {repr(c2)}')
                    break
            lines1 = source1.splitlines()
            lines2 = source2.splitlines()
            print(f'\nLine counts: {len(lines1)} vs {len(lines2)}')
            for i, (line1, line2) in enumerate(zip(lines1, lines2), 1):
                if line1 != line2:
                    print(f'\nFirst different line {i}:')
                    print(f'Source1: {repr(line1)}')
                    print(f'Source2: {repr(line2)}')
                    break

        def _test(bot):
            bot.add_tools(code_tools)
            initial_tool_count = len(bot.tool_handler.tools)
            initial_function_names = set(bot.tool_handler.function_map.keys())
            initial_modules = bot.tool_handler.modules
            print('\n=== Initial State ===')
            for file_path, module_context in initial_modules.items():
                print(f'\nModule: {file_path}')
                print(f'Initial Hash: {module_context.code_hash}')
                initial_source = module_context.source
                computed_hash = bot.tool_handler._get_code_hash(initial_source)
                print(f'Initial Source Hash: {computed_hash}')
                print('Source preview:', initial_source[:100].replace('\n', '\\n'))
            save_path1 = os.path.join(self.temp_dir, f'module_tools_1_{bot.name}')
            bot.save(save_path1)
            print('\n=== Saved File Content ===')
            with open(save_path1 + '.bot', 'r') as f:
                save_data = json.load(f)
                if 'tool_handler' in save_data and 'modules' in save_data['tool_handler']:
                    for file_path, module_data in save_data['tool_handler']['modules'].items():
                        print(f'\nModule in save file: {file_path}')
                        saved_hash = module_data['code_hash']
                        saved_source = module_data['source']
                        print(f'Saved Hash: {saved_hash}')
                        computed_hash = bot.tool_handler._get_code_hash(saved_source)
                        print(f'Computed Hash of Saved Source: {computed_hash}')
                        print('Source preview:', saved_source[:100].replace('\n', '\\n'))
                        if saved_hash != computed_hash:
                            print('\n!!! Hash mismatch in saved file !!!')
                            compare_sources(initial_source, saved_source, 'Initial vs Saved')
            loaded_bot1 = Bot.load(save_path1 + '.bot')
            print('\n=== After First Load ===')
            for file_path, module_context in loaded_bot1.tool_handler.modules.items():
                print(f'\nModule: {file_path}')
                loaded_hash = module_context.code_hash
                loaded_source = module_context.source
                print(f'Loaded Hash: {loaded_hash}')
                computed_hash = loaded_bot1.tool_handler._get_code_hash(loaded_source)
                print(f'Computed Hash of Loaded Source: {computed_hash}')
                print('Source preview:', loaded_source[:100].replace('\n', '\\n'))
                if file_path in initial_modules:
                    if initial_modules[file_path].code_hash != loaded_hash:
                        print('\n!!! Hash mismatch with initial !!!')
                        print(f'Initial hash: {initial_modules[file_path].code_hash}')
                        print(f'Loaded hash:  {loaded_hash}')
                        compare_sources(initial_source, loaded_source, 'Initial vs Loaded')
                    if loaded_hash != computed_hash:
                        print('\n!!! Hash mismatch in loaded code !!!')
                        compare_sources(saved_source, loaded_source, 'Saved vs Loaded')
            self.assertEqual(initial_tool_count, len(loaded_bot1.tool_handler.tools))
            self.assertEqual(initial_function_names, set(loaded_bot1.tool_handler.function_map.keys()))
            save_path2 = os.path.join(self.temp_dir, f'module_tools_2_{bot.name}')
            loaded_bot1.save(save_path2)
            print('\n=== Second Save Content ===')
            with open(save_path2 + '.bot', 'r') as f:
                save_data = json.load(f)
                if 'tool_handler' in save_data and 'modules' in save_data['tool_handler']:
                    for file_path, module_data in save_data['tool_handler']['modules'].items():
                        print(f'\nModule in second save: {file_path}')
                        saved_hash = module_data['code_hash']
                        saved_source = module_data['source']
                        print(f'Saved Hash: {saved_hash}')
                        computed_hash = bot.tool_handler._get_code_hash(saved_source)
                        print(f'Computed Hash of Saved Source: {computed_hash}')
                        print('Source preview:', saved_source[:100].replace('\n', '\\n'))
                        if saved_hash != computed_hash:
                            print('\n!!! Hash mismatch in second save !!!')
                            compare_sources(loaded_source, saved_source, 'Loaded vs Second Save')
            loaded_bot2 = Bot.load(save_path2 + '.bot')
            print('\n=== After Second Load ===')
            for file_path, module_context in loaded_bot2.tool_handler.modules.items():
                print(f'\nModule: {file_path}')
                final_hash = module_context.code_hash
                final_source = module_context.source
                print(f'Final Loaded Hash: {final_hash}')
                computed_hash = loaded_bot2.tool_handler._get_code_hash(final_source)
                print(f'Computed Hash of Final Source: {computed_hash}')
                print('Source preview:', final_source[:100].replace('\n', '\\n'))
                if file_path in initial_modules:
                    if initial_modules[file_path].code_hash != final_hash:
                        print('\n!!! Hash mismatch with initial !!!')
                        print(f'Initial hash: {initial_modules[file_path].code_hash}')
                        print(f'Final hash:   {final_hash}')
                        compare_sources(initial_source, final_source, 'Initial vs Final')
            self.assertEqual(initial_tool_count, len(loaded_bot2.tool_handler.tools))
            self.assertEqual(initial_function_names, set(loaded_bot2.tool_handler.function_map.keys()))
            for func_name in initial_function_names:
                self.assertTrue(callable(loaded_bot2.tool_handler.function_map[func_name]), f'Function {func_name} is not callable after two save/load cycles')
        self.run_test_for_both_bots(_test)

    def test_save_load_empty_bot(self):
        """Test saving and loading a bot that has no conversation history"""

        def _test(bot_type):
            if bot_type == 'anthropic':
                fresh_bot = AnthropicBot(name='TestClaude', model_engine=Engines.CLAUDE35_SONNET_20240620)
            save_path = os.path.join(self.temp_dir, f'empty_{fresh_bot.name}')
            save_path = fresh_bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertIsNotNone(loaded_bot.conversation)
            self.assertEqual(loaded_bot.conversation._node_count(), 1, 'Expected only root node initially')
            root = loaded_bot.conversation._find_root()
            self.assertEqual(root.role, 'empty')
            self.assertEqual(root.content, '')
            self.assertEqual(len(root.replies), 0)
            response = loaded_bot.respond('Hello!')
            self.assertIsNotNone(response)
            self.assertTrue(len(response) > 0)
            self.assertEqual(loaded_bot.conversation._node_count(), 3, 'Expected root node + user message + assistant response (3 nodes total)')
            root = loaded_bot.conversation._find_root()
            self.assertEqual(len(root.replies), 1, 'Root should have one reply')
            user_message = root.replies[0]
            self.assertEqual(user_message.role, 'user')
            self.assertEqual(user_message.content, 'Hello!')
            self.assertEqual(len(user_message.replies), 1, 'User message should have one reply')
            assistant_response = user_message.replies[0]
            self.assertEqual(assistant_response.role, 'assistant')
            self.assertTrue(len(assistant_response.content) > 0)
        for bot_type in self.bots.keys():
            with self.subTest(bot_type=bot_type):
                _test(bot_type)
import sys
import traceback
from functools import wraps
from typing import Any, Callable
import shutil
from bots.tools.python_editing_tools import replace_function
import tempfile

def debug_on_error(func: Callable) -> Callable:

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
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
    main()