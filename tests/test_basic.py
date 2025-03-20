import unittest
from bots import AnthropicBot
from bots import ChatGPT_Bot
from bots.foundation.base import Engines


class TestAnthropicBot(unittest.TestCase):

    def setUp(self):
        self.bot = AnthropicBot(autosave=False)

    def test_initialization(self):
        self.assertIsInstance(self.bot, AnthropicBot)
        self.assertEqual(self.bot.model_engine, Engines.CLAUDE37_SONNET_20250219)
        self.assertEqual(self.bot.max_tokens, 4096)
        self.assertEqual(self.bot.temperature, 0.3)
        self.assertEqual(self.bot.name, 'Claude')

    def test_custom_initialization(self):
        custom_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU,
            max_tokens=1000, temperature=0.7, name='CustomClaude', role=
            'expert', role_description='an AI language expert', autosave=False)
        self.assertEqual(custom_bot.model_engine, Engines.CLAUDE3_HAIKU)
        self.assertEqual(custom_bot.max_tokens, 1000)
        self.assertEqual(custom_bot.temperature, 0.7)
        self.assertEqual(custom_bot.name, 'CustomClaude')
        self.assertEqual(custom_bot.role, 'expert')
        self.assertEqual(custom_bot.role_description, 'an AI language expert')

    def test_basic_conversation(self):
        response = self.bot.respond('Hello, how are you?')
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_multiple_turns(self):
        response1 = self.bot.respond("What's the capital of France?")
        self.assertIn('Paris', response1)
        response2 = self.bot.respond("What's its population?")
        self.assertIn('million', response2.lower())


class TestGPTBot(unittest.TestCase):

    def setUp(self):
        self.bot = ChatGPT_Bot()

    def test_initialization(self):
        self.assertIsInstance(self.bot, ChatGPT_Bot)
        self.assertEqual(self.bot.model_engine, Engines.GPT4)
        self.assertEqual(self.bot.max_tokens, 4096)
        self.assertEqual(self.bot.temperature, 0.3)
        self.assertEqual(self.bot.name, 'bot')

    def test_custom_initialization(self):
        custom_bot = ChatGPT_Bot(model_engine=Engines.GPT4, max_tokens=2000,
            temperature=0.5, name='CustomGPT', role='assistant',
            role_description='a helpful AI assistant')
        self.assertEqual(custom_bot.model_engine, Engines.GPT4)
        self.assertEqual(custom_bot.max_tokens, 2000)
        self.assertEqual(custom_bot.temperature, 0.5)
        self.assertEqual(custom_bot.name, 'CustomGPT')
        self.assertEqual(custom_bot.role, 'assistant')
        self.assertEqual(custom_bot.role_description, 'a helpful AI assistant')

    def test_basic_conversation(self):
        response = self.bot.respond('Hello, how are you?')
        self.assertIsInstance(response, str)
        self.assertTrue(len(response) > 0)

    def test_multiple_turns(self):
        response1 = self.bot.respond("What's the capital of France?")
        self.assertIn('Paris', response1)
        response2 = self.bot.respond("What's its population?")
        self.assertIn('million', response2.lower())

def test_bot_multiplication():
    """Test that the __mul__ operator creates proper deep copies of the Bot."""
    bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100,
        temperature=0.7, name='TestBot', role='test', role_description=
        'A test bot', autosave=False)
    bot.conversation = bot.conversation._add_reply(content='Hello', role='user')
    bot.conversation = bot.conversation._add_reply(content='Hi there!', role='assistant')
    bot_copies = bot * 3
    assert len(bot_copies) == 3
    assert all(isinstance(copy, AnthropicBot) for copy in bot_copies)
    assert all(copy is not bot for copy in bot_copies)
    assert all(copy is not bot_copies[0] for copy in bot_copies[1:])
    for copy in bot_copies:
        assert copy.name == bot.name
        assert copy.model_engine == bot.model_engine
        assert copy.max_tokens == bot.max_tokens
        assert copy.temperature == bot.temperature
        assert copy.role == bot.role
        assert copy.role_description == bot.role_description
        assert copy.conversation is not bot.conversation
        assert copy.conversation.content == bot.conversation.content
        assert copy.conversation.role == bot.conversation.role
        assert copy.conversation.parent is not None
        assert copy.conversation.parent is not bot.conversation.parent


if __name__ == '__main__':
    unittest.main()