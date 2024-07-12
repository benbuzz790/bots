import unittest
from bots import BaseBot, GPTBot, AnthropicBot, Engines
import conversation_node as CN

class MockMailbox:
    def send_message(self, cvsn, model_engine, max_tokens, temperature, api_key):
        return "Mock response", "assistant", {}

    def batch_send(self, cvsn, model_engine, max_tokens, temperature, api_key, num_messages):
        return ["Mock response"] * num_messages

class TestBaseBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestBot", role="assistant", role_description="Test bot")
        self.bot.mailbox = MockMailbox()

    def test_respond(self):
        response = self.bot.respond("Hello")
        self.assertEqual(response, "Mock response")

    def test_batch_respond(self):
        messages = ["Hello", "How are you?"]
        responses = self.bot.batch_respond(messages)
        self.assertEqual(responses, ["Mock response", "Mock response"])

    def test_save_and_load(self):
        self.bot.conversation = CN.ConversationNode(role="user", content="Test message")
        filename = self.bot.save()
        loaded_bot = BaseBot.load(filename)
        self.assertEqual(loaded_bot.name, self.bot.name)
        self.assertEqual(loaded_bot.conversation.content, self.bot.conversation.content)

class TestGPTBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestGPTBot")
        self.bot.mailbox = MockMailbox()

    def test_send_message(self):
        cvsn = CN.ConversationNode(role="user", content="Test message")
        response, role, _ = self.bot._send_message(cvsn)
        self.assertEqual(response, "Mock response")
        self.assertEqual(role, "assistant")

class TestAnthropicBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestAnthropicBot")
        self.bot.mailbox = MockMailbox()

    def test_send_message(self):
        cvsn = CN.ConversationNode(role="user", content="Test message")
        response, role, _ = self.bot._send_message(cvsn)
        self.assertEqual(response, "Mock response")
        self.assertEqual(role, "assistant")

if __name__ == '__main__':
    unittest.main()
