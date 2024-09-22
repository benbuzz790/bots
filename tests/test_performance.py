import unittest
import time
import sys
import os

# Add the parent directory to the Python path to import the bot modules


from bots import AnthropicBot
from bots import ChatGPT_Bot

@unittest.skip("Takes too long, not relevant yet")
class TestBotPerformance(unittest.TestCase):
    def setUp(self):
        self.anthropic_bot = AnthropicBot()
        self.gpt_bot = ChatGPT_Bot()

    def test_response_time(self):
        prompt = "Explain the theory of relativity in one sentence."
        max_response_time = 10  # seconds
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            start_time = time.time()
            response = bot.respond(prompt)
            end_time = time.time()
            
            response_time = end_time - start_time
            print(f"{bot.__class__.__name__} response time: {response_time:.2f} seconds")
            
            self.assertLess(response_time, max_response_time, 
                            f"{bot.__class__.__name__} took too long to respond")
            self.assertTrue(len(response) > 0)

    def test_long_conversation_performance(self):
        prompts = [
            "Let's discuss the history of computing.",
            "Who invented the first computer?",
            "What was the ENIAC?",
            "How did computing evolve in the 1960s and 1970s?",
            "Tell me about the personal computer revolution.",
            "How has cloud computing changed the industry?",
            "What are some future trends in computing?",
        ]
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            start_time = time.time()
            for prompt in prompts:
                response = bot.respond(prompt)
                self.assertIsInstance(response, str)
                self.assertTrue(len(response) > 0)
            total_time = time.time() - start_time
            
            print(f"{bot.__class__.__name__} long conversation time: {total_time:.2f} seconds")
            self.assertLess(total_time, 60, f"{bot.__class__.__name__} took too long for a long conversation")

    def test_memory_usage(self):
        import psutil
        import os

        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss

        long_conversation = ["Tell me about " + topic for topic in [
            "artificial intelligence", "quantum computing", "blockchain",
            "virtual reality", "augmented reality", "internet of things",
            "5G networks", "cybersecurity", "cloud computing", "edge computing"
        ]]

        for bot in [self.anthropic_bot, self.gpt_bot]:
            for prompt in long_conversation:
                bot.respond(prompt)

        final_memory = process.memory_info().rss
        memory_increase = final_memory - initial_memory

        max_memory_increase = 100 * 1024 * 1024  # 100 MB
        self.assertLess(memory_increase, max_memory_increase, 
                        "Memory usage increased too much during the conversation")
        print(f"Memory usage increase: {memory_increase / 1024 / 1024:.2f} MB")

if __name__ == '__main__':
    unittest.main()

