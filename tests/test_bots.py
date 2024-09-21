import unittest
from bots import AnthropicBot
from bots import ChatGPT_Bot
from bots.foundation.base import Bot, Engines

#TODO - fill in a pile of GPT and Anthropic tests


class TestBaseBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestBot", role="assistant", role_description="Test bot")

    # Todo - teardown - remove all bots named TestBot@... from the local directory

    def test_respond(self):
        response = self.bot.respond("Hello")
        verification_prompt = f"Is the following a greeting?\n\n{response}"
        #self.assertTrue(BaseBot.load(r'data\TrueFalse@2024.07.16-18.27.57.bot').respond(verification_prompt))
        self.assertIsInstance(response, str)

    @unittest.skip(reason="Not Implemented")
    def test_batch_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

    def test_save_and_load(self):
        self.bot.respond("Please respond with exactly and only ~")
        self.bot.respond("Once more please")
        filename = self.bot.save()
        loaded_bot = Bot.load(filename)
        self.assertEqual(loaded_bot.name, self.bot.name)
        self.assertEqual(loaded_bot.conversation.root_dict(), self.bot.conversation.root_dict(), msg=f"Expected:{self.bot.conversation.content}\n\nActual:{loaded_bot.conversation.content}")

class TestGPTBot(unittest.TestCase):
    def setUp(self):
        self.bot = ChatGPT_Bot(api_key=None, model_engine=Engines.GPT4, max_tokens=100, temperature=0.7, name="TestGPTBot", role="assistant", role_description="Test bot")

    @unittest.skip(reason="Not Implemented")
    def test_batch_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

class TestAnthropicBot(unittest.TestCase):
    def setUp(self):
        self.bot = AnthropicBot(api_key=None, model_engine=Engines.CLAUDE35, max_tokens=100, temperature=0.7, name="TestAnthropicBot")
    
    @unittest.skip(reason="Not Implemented")
    def test_parallel_respond(self):
        responses = self.bot.parallel_respond("Hello", num_responses=3)
        self.assertEqual(responses, ["Mock response", "Mock response", "Mock response"])
        self.assertEqual(len(self.bot.conversation.replies), 3)

if __name__ == '__main__':
    unittest.main()


