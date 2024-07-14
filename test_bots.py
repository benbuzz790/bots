import unittest
from bots import BaseBot, GPTBot, AnthropicBot, RolloverBot, Engines
import conversation_node as CN

class MockMailbox:
    def send_message(self, cvsn, model_engine, max_tokens, temperature, api_key, system_message=None):
        return "Mock response", "assistant", {}

    def batch_send(self, conversations, model_engine, max_tokens, temperature, api_key, system_message=None):
        return [("Mock response", "assistant", {}) for _ in conversations]

class TestBaseBot(unittest.TestCase):
    def setUp(self):
        self.bot = GPTBot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestBot", role="assistant", role_description="Test bot")
        self.bot.mailbox = MockMailbox()

    def test_respond(self):
        response = self.bot.respond("Hello")
        self.assertEqual(response, "Mock response")

    def test_batch_respond(self):
        responses = self.bot.batch_respond("Hello", num_responses=3)
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
        response, role, _ = self.bot._send_message(cvsn)
        self.assertEqual(response, "Mock response")
        self.assertEqual(role, "assistant")

    def test_batch_respond(self):
        responses = self.bot.batch_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

class TestAnthropicBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestAnthropicBot")
        self.bot.mailbox = MockMailbox()

    def test_send_message(self):
        cvsn = CN.ConversationNode(role="user", content="Test message")
        response, role, _ = self.bot._send_message(cvsn)
        self.assertEqual(response, "Mock response")
        self.assertEqual(role, "assistant")

    def test_batch_respond(self):
        responses = self.bot.batch_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

    def test_rollover_bot_truncate_conversation(self):
        rollover_bot = RolloverBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestRolloverBot", role="assistant", role_description="Test bot", max_conversation_length=100)
        rollover_bot.mailbox = MockMailbox()

        # Add some replies to the conversation
        for i in range(10):
            rollover_bot.conversation = rollover_bot.conversation.add_reply(f"User message {i}", "user")
            rollover_bot.conversation = rollover_bot.conversation.add_reply(f"Assistant response {i}", "assistant")

        # Check if the conversation is truncated correctly
        truncated_conversation = rollover_bot._truncate_conversation(rollover_bot.conversation)
        self.assertLessEqual(len(truncated_conversation.to_string()), rollover_bot.max_conversation_length)

    def test_rollover_bot_respond(self):
        rollover_bot = RolloverBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestRolloverBot", role="assistant", role_description="Test bot", max_conversation_length=100)
        rollover_bot.mailbox = MockMailbox()

        # Add some replies to the conversation
        for i in range(10):
            rollover_bot.respond(f"User message {i}")

        # Check if the conversation is truncated correctly after responding
        self.assertLessEqual(len(rollover_bot.conversation.to_string()), rollover_bot.max_conversation_length)


if __name__ == '__main__':
    unittest.main()
