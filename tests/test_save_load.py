import unittest
import os
import tempfile
import json
from unittest.mock import patch
from bots.foundation.base import Bot, Engines
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
import bots.tools.python_tools as python_tools

def simple_addition(x, y) -> str:
    return str(int(x) + int(y))

class TestSaveLoad(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bots = {
            'openai': ChatGPT_Bot(name="TestGPT", model_engine=Engines.GPT35TURBO),
            'anthropic': AnthropicBot(name="TestClaude", model_engine=Engines.CLAUDE35_SONNET_20240620)
        }
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
            save_path = os.path.join(self.temp_dir, f"{original_bot.name}.bot")
            original_bot.save(save_path)
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
            bot.respond("Hello, how are you?")
            bot.respond("What's the weather like today?")
            bot.respond("Thank you for the information.")
            save_path = os.path.join(self.temp_dir, f"convo_{bot.name}.bot")
            bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.conversation.node_count(), loaded_bot.conversation.node_count())
            self.assertEqual(bot.conversation.content, loaded_bot.conversation.content)

        self.run_test_for_both_bots(_test)

    def test_save_load_with_file_tools(self):
        def _test(bot):
            tool_file_path = "bots/tools/python_tools.py"
            bot.add_tools(tool_file_path)
            save_path = os.path.join(self.temp_dir, f"file_tool_{bot.name}.bot")
            bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            
            # Compare essential attributes of each tool while ignoring formatting
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
            for original_tool, loaded_tool in zip(bot.tool_handler.tools, loaded_bot.tool_handler.tools):
                self.assertEqual(original_tool.get('name'), loaded_tool.get('name'))
                self.assertEqual(original_tool.get('parameters'), loaded_tool.get('parameters'))
                self.assertEqual(
                    original_tool.get('returns', {}).get('type'),
                    loaded_tool.get('returns', {}).get('type')
                )
                self.assertEqual(original_tool.get('type'), loaded_tool.get('type'))
                if 'function' in original_tool and 'function' in loaded_tool:
                    self.assertEqual(
                        type(original_tool['function']),
                        type(loaded_tool['function'])
                    )

        self.run_test_for_both_bots(_test)

    def test_save_load_with_module_tools(self):
        def _test(bot):
            bot.add_tools(python_tools)
            save_path = os.path.join(self.temp_dir, f"module_tool_{bot.name}.bot")
            bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
            # Using same tool comparison as file_tools test
            for original_tool, loaded_tool in zip(bot.tool_handler.tools, loaded_bot.tool_handler.tools):
                self.assertEqual(original_tool.get('name'), loaded_tool.get('name'))
                self.assertEqual(original_tool.get('parameters'), loaded_tool.get('parameters'))
                self.assertEqual(
                    original_tool.get('returns', {}).get('type'),
                    loaded_tool.get('returns', {}).get('type')
                )
                self.assertEqual(original_tool.get('type'), loaded_tool.get('type'))

        self.run_test_for_both_bots(_test)

    def test_save_load_with_system_message(self):
        def _test(bot):
            system_message = "You are a helpful assistant specialized in Python programming."
            bot.set_system_message(system_message)
            save_path = os.path.join(self.temp_dir, f"system_msg_{bot.name}.bot")
            bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.system_message, loaded_bot.system_message)

        self.run_test_for_both_bots(_test)

    def test_api_key_handling(self):
        def _test(bot):
            save_path = os.path.join(self.temp_dir, f"api_key_{bot.name}.bot")
            bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertIsNone(loaded_bot.api_key)
            new_api_key = "new_test_api_key"
            loaded_bot_with_key = Bot.load(save_path, api_key=new_api_key)
            self.assertEqual(loaded_bot_with_key.api_key, new_api_key)

        self.run_test_for_both_bots(_test)

    def test_tool_execution_results(self):
        def _test(bot):
            bot.add_tool(simple_addition)
            bot.respond("What is 2 + 3?")
            
            self.assertEqual(len(bot.tool_handler.get_results()), 1)
            self.assertIn('5',bot.tool_handler.get_results()[0]['content'])
            
            save_path = os.path.join(self.temp_dir, f"tool_exec_{bot.name}.bot")
            bot.save(save_path)
            
            loaded_bot = Bot.load(save_path)
            self.assertEqual(bot.tool_handler.get_results(), loaded_bot.tool_handler.get_results())

        self.run_test_for_both_bots(_test)

    def test_save_load_with_tool_use(self):
        def _test(bot):
            bot.add_tool(simple_addition)
            
            interactions = [
                "What is 5 + 3?",
                "Can you add 10 and 20?",
                "Please add 7 and 15"
            ]
            
            original_responses = []
            for query in interactions:
                response = bot.respond(query)
                original_responses.append(response)
            
            original_results = bot.tool_handler.get_results()
            
            save_path = os.path.join(self.temp_dir, f"tool_use_{bot.name}.bot")
            bot.save(save_path)
            
            loaded_bot = Bot.load(save_path)
            
            self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
            
            loaded_results = loaded_bot.tool_handler.get_results()
            self.assertEqual(len(original_results), len(loaded_results))
            
            for original, loaded in zip(original_results, loaded_results):
                self.assertEqual(original['content'], loaded['content'])
            
            new_response = loaded_bot.respond("What is 25 + 17?")
            self.assertIsNotNone(new_response)
            
            updated_results = loaded_bot.tool_handler.get_results()
            latest_result = updated_results[-1]
            self.assertEqual(int(latest_result['content']), 42)

        self.run_test_for_both_bots(_test)

    def test_custom_attributes(self):
        def _test(bot):
            bot.custom_attr1 = "Test Value"
            bot.custom_attr2 = 42
            bot.custom_attr3 = {"key": "value"}
            
            save_path = os.path.join(self.temp_dir, f"custom_attr_{bot.name}.bot")
            bot.save(save_path)
            
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


if __name__ == '__main__':
    unittest.main()