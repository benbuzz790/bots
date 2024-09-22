import unittest
from bots import AnthropicBot
from bots import ChatGPT_Bot
from bots.foundation.base import Engines

class TestAnthropicBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot()

    def test_initialization(self):
        self.assertIsInstance(self.bot, AnthropicBot)
        self.assertEqual(self.bot.model_engine, Engines.CLAUDE35)
        self.assertEqual(self.bot.max_tokens, 4096)
        self.assertEqual(self.bot.temperature, 0.3)
        self.assertEqual(self.bot.name, "Claude")

    def test_custom_initialization(self):
        custom_bot = AnthropicBot(
            model_engine=Engines.CLAUDE3OPUS,
            max_tokens=1000,
            temperature=0.7,
            name="CustomClaude",
            role="expert",
            role_description="an AI language expert"
        )
        self.assertEqual(custom_bot.model_engine, Engines.CLAUDE3OPUS)
        self.assertEqual(custom_bot.max_tokens, 1000)
        self.assertEqual(custom_bot.temperature, 0.7)
        self.assertEqual(custom_bot.name, "CustomClaude")
        self.assertEqual(custom_bot.role, "expert")
        self.assertEqual(custom_bot.role_description, "an AI language expert")

    def test_basic_conversation(self):
        response = self.bot.respond("Hello, how are you?")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_multiple_turns(self):
        response1 = self.bot.respond("What's the capital of France?")
        self.assertIn("Paris", response1)
        response2 = self.bot.respond("What's its population?")
        self.assertIn("million", response2.lower())

class TestGPTBot(unittest.TestCase):
    def setUp(self):
        self.bot = ChatGPT_Bot()

    def test_initialization(self):
        self.assertIsInstance(self.bot, ChatGPT_Bot)
        self.assertEqual(self.bot.model_engine, Engines.GPT4)
        self.assertEqual(self.bot.max_tokens, 4096)
        self.assertEqual(self.bot.temperature, 0.3)
        self.assertEqual(self.bot.name, "bot")

    def test_custom_initialization(self):
        custom_bot = ChatGPT_Bot(
            model_engine=Engines.GPT35,
            max_tokens=2000,
            temperature=0.5,
            name="CustomGPT",
            role="assistant",
            role_description="a helpful AI assistant"
        )
        self.assertEqual(custom_bot.model_engine, Engines.GPT35)
        self.assertEqual(custom_bot.max_tokens, 2000)
        self.assertEqual(custom_bot.temperature, 0.5)
        self.assertEqual(custom_bot.name, "CustomGPT")
        self.assertEqual(custom_bot.role, "assistant")
        self.assertEqual(custom_bot.role_description, "a helpful AI assistant")

    def test_basic_conversation(self):
        response = self.bot.respond("Hello, how are you?")
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_multiple_turns(self):
        response1 = self.bot.respond("What's the capital of France?")
        self.assertIn("Paris", response1)
        response2 = self.bot.respond("What's its population?")
        self.assertIn("million", response2.lower())

if __name__ == '__main__':
    unittest.main()

