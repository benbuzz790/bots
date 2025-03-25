import unittest
import os
import tempfile
import shutil
from bots import ChatGPT_Bot
from bots.foundation.base import Engines
from bots.tools.code_tools import view

class TestGPTBot(unittest.TestCase):

    def setUp(self):
        self.temp_dir = tempfile.mkdtemp()
        self.bot = ChatGPT_Bot(model_engine=Engines.GPT4TURBO, max_tokens=1000, temperature=0.7, name='TestBot')
        self.bot.add_tools(view)
        self.test_file_path = os.path.join(self.temp_dir, 'test_file.txt')
        self.test_content = 'This is a test file content.'
        with open(self.test_file_path, 'w') as f:
            f.write(self.test_content)

    def tearDown(self):
        if os.path.exists(self.temp_dir):
            shutil.rmtree(self.temp_dir)

    def test_gptbot_read_file(self):
        response1 = self.bot.respond(f'Please display the contents of the file {self.test_file_path}')
        print(response1)
        self.bot.save(os.path.join(self.temp_dir, 'gpttestresult.bot'))
        self.assertIn(self.test_content, response1)

    def test_tool_call_sequence_save_load(self):
        """Test that tool calls and responses maintain proper sequence through save/load"""

        def simple_addition(x, y) -> str:
            """Returns x + y with appropriate type conversion"""
            return str(int(x) + int(y))
        bot = ChatGPT_Bot(model_engine=Engines.GPT4TURBO, max_tokens=1000, temperature=0.7)
        bot.add_tools(simple_addition)
        response1 = bot.respond('What is 5 + 3?')
        save_path = os.path.join(self.temp_dir, 'tool_test.bot')
        bot.save(save_path)
        loaded_bot = ChatGPT_Bot.load(save_path)
        response2 = loaded_bot.respond('What is 10 + 15?')
        self.assertTrue(any(('8' in str(v) for v in bot.conversation.parent.tool_results[0].values())) if bot.conversation.parent.tool_results else False)
        self.assertTrue(any(('25' in str(v) for v in loaded_bot.conversation.parent.tool_results[0].values())) if loaded_bot.conversation.parent.tool_results else False)

    def test_tool_call_sequence_basic(self):
        """Test that tool calls and responses maintain proper sequence without save/load"""

        def simple_addition(x, y) -> str:
            """Returns x + y with appropriate type conversion"""
            return str(int(x) + int(y))
        
        bot = ChatGPT_Bot(model_engine=Engines.GPT4TURBO, max_tokens=1000, temperature=0.7)
        bot.add_tools(simple_addition)
        response1 = bot.respond('What is 5 + 3?')
        self.assertTrue(any(('8' in str(v) for v in bot.conversation.parent.tool_results[0].values())) if bot.conversation.parent.tool_results else False)
        response2 = bot.respond('What is 10 + 15?')
        self.assertTrue(any(('25' in str(v) for v in bot.conversation.parent.tool_results[0].values())) if bot.conversation.parent.tool_results else False)


from bots.dev.decorators import debug_on_error

#@debug_on_error
def main():
    t = TestGPTBot()
    t.setUp()
    t.test_tool_call_sequence_basic()
    t.tearDown()

    print("Test 2")
    u = TestGPTBot()
    u.setUp()
    u.test_tool_call_sequence_save_load()
    u.tearDown()

if __name__ == '__main__':
    #main()
    unittest.main()