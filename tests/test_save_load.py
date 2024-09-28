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
    return int(x) + int(y)

class TestSaveLoad(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.openai_bot = ChatGPT_Bot(name="TestGPT", model_engine=Engines.GPT35TURBO)
        self.anthropic_bot = AnthropicBot(name="TestClaude", model_engine=Engines.CLAUDE35_SONNET)
        return self

    def tearDown(self):
        for file in os.listdir(self.temp_dir):
            os.remove(os.path.join(self.temp_dir, file))
        os.rmdir(self.temp_dir)

    def test_basic_save_load(self):
        bots = [self.openai_bot, self.anthropic_bot]
        for original_bot in bots:
            save_path = os.path.join(self.temp_dir, f"{original_bot.name}.bot")
            original_bot.save(save_path)
            loaded_bot = Bot.load(save_path)
            self.assertEqual(original_bot.name, loaded_bot.name)
            self.assertEqual(original_bot.model_engine, loaded_bot.model_engine)
            self.assertEqual(original_bot.max_tokens, loaded_bot.max_tokens)
            self.assertEqual(original_bot.temperature, loaded_bot.temperature)
            self.assertEqual(original_bot.role, loaded_bot.role)
            self.assertEqual(original_bot.role_description, loaded_bot.role_description)

    def test_save_load_after_conversation(self):
        bot = self.openai_bot
        bot.respond("Hello, how are you?")
        bot.respond("What's the weather like today?")
        bot.respond("Thank you for the information.")
        save_path = os.path.join(self.temp_dir, "convo_bot.bot")
        bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(bot.conversation.node_count(), loaded_bot.conversation.node_count())
        self.assertEqual(bot.conversation.content, loaded_bot.conversation.content)

    def test_save_load_with_file_tools(self):
        bot = self.openai_bot
        tool_file_path = "bots/tools/python_tools.py"
        bot.add_tools(tool_file_path)
        save_path = os.path.join(self.temp_dir, "file_tool_bot.bot")
        bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertEqual(bot.tool_handler.tools, loaded_bot.tool_handler.tools)

    def test_save_load_with_module_tools(self):
        bot = self.anthropic_bot
        bot.add_tools(python_tools)
        save_path = os.path.join(self.temp_dir, "module_tool_bot.bot")
        bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(len(bot.tool_handler.tools), len(loaded_bot.tool_handler.tools))
        self.assertEqual(bot.tool_handler.tools, loaded_bot.tool_handler.tools)

    def test_save_load_with_system_message(self):
        original_bot = self.openai_bot
        system_message = "You are a helpful assistant specialized in Python programming."
        original_bot.set_system_message(system_message)
        save_path = os.path.join(self.temp_dir, "system_msg_bot.bot")
        original_bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertEqual(original_bot.system_message, loaded_bot.system_message)

    def test_api_key_handling(self):
        original_bot = self.openai_bot
        save_path = os.path.join(self.temp_dir, "api_key_bot.bot")
        original_bot.save(save_path)
        loaded_bot = Bot.load(save_path)
        self.assertIsNone(loaded_bot.api_key)
        new_api_key = "new_test_api_key"
        loaded_bot_with_key = Bot.load(save_path, api_key=new_api_key)
        self.assertEqual(loaded_bot_with_key.api_key, new_api_key)

    def test_tool_execution_results(self):
        bot = self.openai_bot
        
        bot.add_tool(simple_addition)
        bot.respond("What is 2 + 3?")
        
        self.assertEqual(len(bot.tool_handler.get_results()), 1)
        self.assertEqual(int(bot.tool_handler.get_results()[0]['content']), 5)
        
        save_path = os.path.join(self.temp_dir, "tool_exec_bot.bot")
        bot.save(save_path)
        
        loaded_bot = Bot.load(save_path)
        
        self.assertEqual(bot.tool_handler.get_results(), loaded_bot.tool_handler.get_results())

    def test_custom_attributes(self):
        original_bot = self.openai_bot
        
        original_bot.custom_attr1 = "Test Value"
        original_bot.custom_attr2 = 42
        original_bot.custom_attr3 = {"key": "value"}
        
        save_path = os.path.join(self.temp_dir, "custom_attr_bot.bot")
        original_bot.save(save_path)
        
        loaded_bot = Bot.load(save_path)
        
        self.assertEqual(original_bot.custom_attr1, loaded_bot.custom_attr1)
        self.assertEqual(original_bot.custom_attr2, loaded_bot.custom_attr2)
        self.assertEqual(original_bot.custom_attr3, loaded_bot.custom_attr3)
        
        self.assertIsInstance(loaded_bot.custom_attr1, str)
        self.assertIsInstance(loaded_bot.custom_attr2, int)
        self.assertIsInstance(loaded_bot.custom_attr3, dict)

        with self.assertRaises(AttributeError):
            _ = loaded_bot.non_existent_attr

from debug_on_error import debug_on_error as dbstoperror

@dbstoperror
def main():
    tests = TestSaveLoad().setUp()
    tests.test_save_load_with_file_tools()
    tests.test_save_load_with_module_tools()
    tests.test_tool_execution_results()
    tests.test_save_load_after_conversation()


if __name__ == '__main__':
    unittest.main()
    #main()