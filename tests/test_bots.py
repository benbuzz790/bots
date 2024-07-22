import unittest
import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.bots import BaseBot, GPTBot, AnthropicBot, Engines
import src.conversation_node as CN

#TODO - add sequence_respond test

class MockMailbox:
    def send_message(self, cvsn, model_engine, max_tokens, temperature, api_key, system_message=None):
        return "Mock response", "assistant"

    def batch_send(self, conversations, model_engine, max_tokens, temperature, api_key, system_message=None):
        return [("Mock response", "assistant") for _ in conversations]

class TestBaseBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestBot", role="assistant", role_description="Test bot")
        self.bot.mailbox = MockMailbox()

    # Todo - teardown - remove all bots named TestBot@... from the local directory

    def test_respond(self):
        response = self.bot.respond("Hello")
        self.assertEqual(response, "Mock response")

    @unittest.skip(reason="Not Implemented")
    def test_batch_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

    def test_save_and_load(self):
        self.bot.conversation = CN.ConversationNode(role="user", content="Test message")
        filename = self.bot.save()
        loaded_bot = BaseBot.load(filename)
        self.assertEqual(loaded_bot.name, self.bot.name)
        self.assertEqual(loaded_bot.conversation.content, self.bot.conversation.content)

class TestGPTBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestGPTBot", role="assistant", role_description="Test bot")
        self.bot.mailbox = MockMailbox()

    def test_send_message(self):
        cvsn = CN.ConversationNode(role="user", content="Test message")
        response, role = self.bot._send_message(cvsn)
        self.assertEqual(response, "Mock response")
        self.assertEqual(role, "assistant")

    @unittest.skip(reason="Not Implemented")
    def test_batch_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

class TestAnthropicBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestAnthropicBot")
        self.bot.mailbox = MockMailbox()

    def test_send_message(self):
        cvsn = CN.ConversationNode(role="user", content="Test message")
        response, role = self.bot._send_message(cvsn)
        self.assertEqual(response, "Mock response")
        self.assertEqual(role, "assistant")
    
    @unittest.skip(reason="Not Implemented")
    def test_parallel_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

if __name__ == '__main__':
    unittest.main()
