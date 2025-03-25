import unittest
import os
import json
import tempfile
import shutil
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot
import bots.tools.python_editing_tools as python_editing_tools

class TestSaveLoadOpenAI(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bot = ChatGPT_Bot(name='TestGPT', model_engine=Engines.GPT4TURBO)
        return self

    def tearDown(self):
        try:
            shutil.rmtree(self.temp_dir, ignore_errors=True)
        except Exception as e:
            print(f'Warning: Could not clean up {self.temp_dir}: {e}')

    def test_basic_save_load(self):
        save_path = os.path.join(self.temp_dir, self.bot.name)
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.name, loaded_bot.name)
        self.assertEqual(self.bot.model_engine, loaded_bot.model_engine)
        self.assertEqual(self.bot.max_tokens, loaded_bot.max_tokens)
        self.assertEqual(self.bot.temperature, loaded_bot.temperature)
        self.assertEqual(self.bot.role, loaded_bot.role)
        self.assertEqual(self.bot.role_description, loaded_bot.role_description)

    def test_save_load_after_conversation(self):
        self.bot.respond('Hello, how are you?')
        self.bot.respond("What's the weather like today?")
        self.bot.respond('Thank you for the information.')
        save_path = os.path.join(self.temp_dir, f'convo_{self.bot.name}')
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.conversation._node_count(), loaded_bot.conversation._node_count())
        self.assertEqual(self.bot.conversation.content, loaded_bot.conversation.content)

    def test_tool_execution_results(self):
        """Test that tool results are properly saved in conversation nodes"""

        def simple_addition(x, y) -> str:
            """Returns x + y with appropriate type conversion"""
            return str(int(x) + int(y))
        self.bot.add_tools(simple_addition)
        self.bot.respond('What is 2 + 3?')
        self.assertTrue(any(('5' in str(v) for v in self.bot.conversation.parent.tool_results[0].values())) if self.bot.conversation.parent.tool_results else False)
        save_path = os.path.join(self.temp_dir, f'tool_exec_{self.bot.name}')
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertTrue(any(('5' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)

    def test_save_load_with_tool_use(self):
        """Test that tool results are properly maintained in individual conversation nodes"""

        def simple_addition(x, y) -> str:
            """Returns x + y with appropriate type conversion"""
            return str(int(x) + int(y))
        self.bot.add_tools(simple_addition)
        interactions = ['What is 5 + 3?', 'Can you add 10 and 20?', 'Please add 7 and 15']
        for query in interactions:
            _ = self.bot.respond(query)
        self.assertTrue(any(('22' in str(v) for v in self.bot.conversation.parent.tool_results[0].values())) if self.bot.conversation.parent.tool_results else False)
        save_path = os.path.join(self.temp_dir, f'tool_use_{self.bot.name}')
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        loaded_bot.save(save_path + '2')
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertTrue(any(('22' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)
        new_response = loaded_bot.respond('What is 25 + 17?')
        self.assertIsNotNone(new_response)
        self.assertTrue(any(('42' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)

    def test_module_tool_persistence(self):
        """Test that module tools persist correctly through multiple save/load cycles"""
        self.bot.add_tools(python_editing_tools)
        initial_tool_count = len(self.bot.tool_handler.tools)
        initial_function_names = set(self.bot.tool_handler.function_map.keys())
        save_path1 = os.path.join(self.temp_dir, f'module_tools_1_{self.bot.name}')
        self.bot.save(save_path1)
        loaded_bot1 = Bot.load(save_path1 + '.bot')
        self.assertEqual(initial_tool_count, len(loaded_bot1.tool_handler.tools))
        self.assertEqual(initial_function_names, set(loaded_bot1.tool_handler.function_map.keys()))
        save_path2 = os.path.join(self.temp_dir, f'module_tools_2_{self.bot.name}')
        loaded_bot1.save(save_path2)
        loaded_bot2 = Bot.load(save_path2 + '.bot')
        self.assertEqual(initial_tool_count, len(loaded_bot2.tool_handler.tools))
        self.assertEqual(initial_function_names, set(loaded_bot2.tool_handler.function_map.keys()))
        for func_name in initial_function_names:
            self.assertTrue(callable(loaded_bot2.tool_handler.function_map[func_name]), f'Function {func_name} is not callable after two save/load cycles')

    def test_save_load_empty_bot(self):
        """Test saving and loading a bot that has no conversation history"""
        fresh_bot = ChatGPT_Bot(name='TestGPT', model_engine=Engines.GPT4TURBO)
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

    def test_save_load_with_file_tools(self):
        tool_file_path = 'bots/tools/python_editing_tools.py'
        self.bot.add_tools(tool_file_path)
        save_path = os.path.join(self.temp_dir, f'file_tool_{self.bot.name}')
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        for original_tool, loaded_tool in zip(self.bot.tool_handler.tools, loaded_bot.tool_handler.tools):
            self.assertEqual(original_tool.get('name'), loaded_tool.get('name'))
            self.assertEqual(original_tool.get('parameters'), loaded_tool.get('parameters'))
            self.assertEqual(original_tool.get('returns', {}).get('type'), loaded_tool.get('returns', {}).get('type'))
            self.assertEqual(original_tool.get('type'), loaded_tool.get('type'))
            if 'function' in original_tool and 'function' in loaded_tool:
                self.assertEqual(type(original_tool['function']), type(loaded_tool['function']))

    def test_save_load_with_module_tools(self):
        self.bot.add_tools(python_editing_tools)
        save_path = os.path.join(self.temp_dir, f'module_tool_{self.bot.name}')
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(len(self.bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        for original_tool, loaded_tool in zip(self.bot.tool_handler.tools, loaded_bot.tool_handler.tools):
            self.assertEqual(original_tool.get('name'), loaded_tool.get('name'))
            self.assertEqual(original_tool.get('parameters'), loaded_tool.get('parameters'))
            self.assertEqual(original_tool.get('returns', {}).get('type'), loaded_tool.get('returns', {}).get('type'))
            self.assertEqual(original_tool.get('type'), loaded_tool.get('type'))

    def test_custom_attributes(self):
        self.bot.custom_attr1 = 'Test Value'
        self.bot.custom_attr2 = 42
        self.bot.custom_attr3 = {'key': 'value'}
        save_path = os.path.join(self.temp_dir, f'custom_attr_{self.bot.name}')
        save_path = self.bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(self.bot.custom_attr1, loaded_bot.custom_attr1)
        self.assertEqual(self.bot.custom_attr2, loaded_bot.custom_attr2)
        self.assertEqual(self.bot.custom_attr3, loaded_bot.custom_attr3)
        self.assertIsInstance(loaded_bot.custom_attr1, str)
        self.assertIsInstance(loaded_bot.custom_attr2, int)
        self.assertIsInstance(loaded_bot.custom_attr3, dict)
        with self.assertRaises(AttributeError):
            _ = loaded_bot.non_existent_attr

    def test_file_creation(self):
        """Test that save files are created in the expected location"""
        save_path = os.path.join(self.temp_dir, f'explicit_{self.bot.name}')
        actual_path = self.bot.save(save_path)
        self.assertTrue(os.path.exists(actual_path))
        self.assertEqual(actual_path, save_path + '.bot')
        auto_path = self.bot.save()
        self.assertTrue(os.path.exists(auto_path))
        self.assertTrue(auto_path.endswith('.bot'))

    def test_corrupted_save(self):
        """Test handling of corrupted save files"""
        save_path = os.path.join(self.temp_dir, f'corrupted_{self.bot.name}.bot')
        self.bot.save(save_path[:-4])
        with open(save_path, 'w') as f:
            f.write('{"invalid": "json')
        with self.assertRaises(json.JSONDecodeError):
            Bot.load(save_path)
        with open(save_path, 'w') as f:
            f.write('{"name": "test", "model_engine": "invalid-model"}')
        with self.assertRaises(ValueError):
            Bot.load(save_path)

    def test_working_directory_independence(self):
        """Test that bots can be saved and loaded from different working directories
    while maintaining proper tool results state"""
        subdir = os.path.join(self.temp_dir, 'subdir')
        os.makedirs(subdir, exist_ok=True)
        self.bot.add_tools(simple_addition)
        original_path = os.path.join(self.temp_dir, f'original_{self.bot.name}')
        self.bot.save(original_path)
        original_cwd = os.getcwd()
        try:
            os.chdir(subdir)
            loaded_bot = Bot.load(os.path.join('..', f'original_{self.bot.name}.bot'))
            loaded_bot.respond('What is 7 + 8?')
            self.assertTrue(any(('15' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)
            new_path = os.path.join('..', f'from_subdir_{self.bot.name}')
            loaded_bot.save(new_path)
        finally:
            os.chdir(original_cwd)

    def test_mixed_tool_sources(self):
        """Test saving and loading bots with tools from multiple sources"""

        def floor_str(x) -> str:
            """Returns floor of x as a string"""
            import math
            return str(math.floor(float(x)))
        
        self.bot.add_tools(simple_addition)
        self.bot.add_tools(floor_str)
        self.bot.add_tools(python_editing_tools)
        self.bot.respond('What is 3 + 4?')
        self.assertTrue(any(('7' in str(v) for v in self.bot.conversation.parent.tool_results[0].values())) if self.bot.conversation.parent.tool_results else False)
        self.bot.respond('What is the floor of 7.8?')
        self.assertTrue(any(('7' in str(v) for v in self.bot.conversation.parent.tool_results[0].values())) if self.bot.conversation.parent.tool_results else False)
        save_path = os.path.join(self.temp_dir, f'mixed_tools_{self.bot.name}')
        self.bot.save(save_path)
        loaded_bot = Bot.load(save_path + '.bot')
        loaded_bot.respond('What is 8 + 9?')
        self.assertTrue(any(('17' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)
        loaded_bot.respond('What is the floor of 5.6?')
        self.assertTrue(any(('5' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)

def simple_addition(x, y) -> str:
    """Returns x + y with appropriate type conversion"""
    return str(int(x) + int(y))