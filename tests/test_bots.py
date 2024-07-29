import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.base import Bot as BaseBot, Engines
from src.anthropic_bots import AnthropicBot
from src.openai_bots import GPTBot 
from src.base import ConversationNode as CNode

#TODO - add sequence_respond test
#TODO - fill in a pile of GPT and Anthropic tests

class MockMailbox:
    def send_message(self, cvsn, model_engine, max_tokens, temperature, api_key, system_message=None):
        return "Mock response", "assistant", []

class TestBaseBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestBot", role="assistant", role_description="Test bot")
        self.bot.mailbox = MockMailbox()

    # Todo - teardown - remove all bots named TestBot@... from the local directory

    def test_respond(self):
        response, _ = self.bot.respond("Hello")
        self.assertEqual(response, "Mock response")

    @unittest.skip(reason="Not Implemented")
    def test_batch_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

    def test_save_and_load(self):
        self.bot.conversation = CNode(role="user", content="Test message")
        filename = self.bot.save()
        loaded_bot = BaseBot.load(filename)
        self.assertEqual(loaded_bot.name, self.bot.name)
        self.assertEqual(loaded_bot.conversation.attributes['content'], self.bot.conversation.attributes['content'])

class TestGPTBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestGPTBot", role="assistant", role_description="Test bot")
        self.bot.mailbox = MockMailbox()

    @unittest.skip(reason="Not Implemented")
    def test_batch_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

class TestAnthropicBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestAnthropicBot")
        self.bot.mailbox = MockMailbox()
    
    @unittest.skip(reason="Not Implemented")
    def test_parallel_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

if __name__ == '__main__':
    unittest.main()
