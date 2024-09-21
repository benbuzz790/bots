import unittest
import sys
import os

# Add the parent directory to the Python path to import the bot modules


from bots import AnthropicBot
from bots import ChatGPT_Bot

@unittest.skip("This hilarious file was written by Claude")
class TestBotAdvancedScenarios(unittest.TestCase):
    def setUp(self):
        self.anthropic_bot = AnthropicBot()
        self.gpt_bot = ChatGPT_Bot()

    def test_multi_turn_conversation(self):
        conversation = [
            "Let's talk about climate change.",
            "What are the main causes of global warming?",
            "How can individuals reduce their carbon footprint?",
            "What are some potential consequences if we don't address climate change?",
            "Can you summarize our conversation about climate change?"
        ]
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            responses = []
            for prompt in conversation:
                response = bot.respond(prompt)
                responses.append(response)
                self.assertIsInstance(response, str)
                self.assertTrue(len(response) > 0)
            
            # Check if the summary contains key points from the conversation
            summary = responses[-1].lower()
            self.assertTrue(all(keyword in summary for keyword in ['climate', 'carbon', 'global warming', 'consequences']))

    def test_language_translation(self):
        languages = ['French', 'Spanish', 'German', 'Italian', 'Japanese']
        text = "Hello, how are you?"
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            for language in languages:
                prompt = f"Translate '{text}' to {language}"
                response = bot.respond(prompt)
                self.assertNotIn(text, response)  # Ensure it's not just repeating the English
                self.assertTrue(len(response) > 0)

    def test_code_generation_and_explanation(self):
        prompt = "Write a Python function to calculate the Fibonacci sequence up to n terms, then explain how it works."
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            response = bot.respond(prompt)
            self.assertIn("def", response)  # Should contain function definition
            self.assertIn("fibonacci", response.lower())
            self.assertIn("explanation", response.lower())

    def test_hypothetical_scenarios(self):
        scenarios = [
            "What would happen if gravity suddenly became twice as strong?",
            "How might society change if teleportation was invented?",
            "What would be the implications if humans could photosynthesize like plants?"
        ]
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            for scenario in scenarios:
                response = bot.respond(scenario)
                self.assertTrue(len(response) > 100)  # Ensure a detailed response
                self.assertIn("would", response.lower())  # Should discuss hypothetical outcomes

    def test_emotional_intelligence(self):
        prompts = [
            "I just lost my job. How should I feel?",
            "My best friend is moving away. What can I do to maintain our friendship?",
            "I'm feeling overwhelmed with my workload. Any advice?"
        ]
        
        for bot in [self.anthropic_bot, self.gpt_bot]:
            for prompt in prompts:
                response = bot.respond(prompt)
                self.assertIn("feel", response.lower())
                self.assertTrue(any(word in response.lower() for word in ["understand", "empathize", "suggest"]))

if __name__ == '__main__':
    unittest.main()

