import unittest
import sys
import os
import io
from unittest.mock import patch

# Add the parent directory to the Python path to import the bot modules
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from src.anthropic_bots import AnthropicBot
from src.openai_bots import GPTBot

class TestBotIntegration(unittest.TestCase):
    def setUp(self):
        self.anthropic_bot = AnthropicBot()
        self.gpt_bot = GPTBot()

    def test_tool_integration(self):
        def simple_calculator(operation: str, x: float, y: float) -> float:
            """Perform simple arithmetic operations, 'add', 'subtract', 'multiply', and 'divide'"""
            if operation == "add":
                return x + y
            elif operation == "subtract":
                return x - y
            elif operation == "multiply":
                return x * y
            elif operation == "divide":
                return x / y
            else:
                raise ValueError("Unsupported operation")

        for bot in [self.anthropic_bot, self.gpt_bot]:
            bot.add_tool(simple_calculator)
            
            response:str = bot.respond("What is 101,101,101 multiplied by 999?")
            if bot == self.anthropic_bot:
                response = bot.respond("What is the result?")
            self.assertTrue(any(expected in response.replace(",", "") for expected in ["100999999899", "100,999,999,899"]))

            response = bot.respond("If I have 537,432,123 apples and a pie takes 17 apples, how many pies can I make?")
            if bot == self.anthropic_bot:
                response = bot.respond("What is the result?")
            self.assertTrue(any(expected in response.replace(",", "") for expected in ["31613654", "31,613,654"]))

    def test_conversation_state_persistence(self):
        for bot in [self.anthropic_bot, self.gpt_bot]:
            bot.respond("My name is Alice and I love chess.")
            
            # Save the bot state
            filepath = bot.save()
            
            # Create a new bot instance and load the state
            new_bot = bot.__class__.load(filepath)
            
            response = new_bot.respond("What's my name and what do I love?")
            self.assertIn("Alice", response)
            self.assertIn("chess", response)

            # Clean up
            os.remove(filepath)

    def test_error_handling_and_recovery(self):
        def faulty_tool(x: int) -> int:
            """A tool that raises an exception"""
            raise ValueError("This tool always fails")

        for bot in [self.anthropic_bot, self.gpt_bot]:
            bot.add_tool(faulty_tool)

            # Test error handling
            response = bot.respond("Please use the faulty_tool with input 5.")
            self.assertIn("error", response.lower())

            # Test recovery and continued conversation
            response = bot.respond("Okay, let's forget about that tool. What's the capital of France?")
            self.assertIn("Paris", response)

    @patch('builtins.input', side_effect=['Hello', 'What is AI?', 'Thank you', '/exit'])
    def test_interactive_chat_with_tool_use(self, mock_input):
        def define_term(term: str) -> str:
            """Defines 'AI' or 'ML'"""
            definitions = {
                "AI": "Artificial Intelligence is the simulation of human intelligence processes by machines, especially computer systems.",
                "ML": "Machine Learning is a subset of AI that enables systems to learn and improve from experience without being explicitly programmed.",
            }
            return definitions.get(term.upper(), f"Sorry, I don't have a definition for {term}.")

        for bot in [self.anthropic_bot, self.gpt_bot]:
            bot.add_tool(define_term)

            with unittest.mock.patch('sys.stdout', new=io.StringIO()) as fake_out:
                bot.chat()
                output = fake_out.getvalue()

                self.assertIn("Hello", output)
                self.assertIn("Artificial Intelligence", output)
                self.assertIn("Thank you", output)

if __name__ == '__main__':
    unittest.main()