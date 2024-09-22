import unittest
import os
from unittest.mock import patch
from bots import AnthropicBot
from bots import ChatGPT_Bot

class TestBotIntegration(unittest.TestCase):
    def setUp(self):
        self.anthropic_bot = AnthropicBot()
        self.gpt_bot = ChatGPT_Bot()

    def test_tool_integration(self):
        def simple_calculator(operation: str, x: str, y: str) -> str:
            """Perform simple arithmetic operations, 'add', 'subtract', 'multiply', and 'divide'"""
            x = float(x)
            y = float(y)
            if operation == "add":
                return str(x + y)
            elif operation == "subtract":
                return str(x - y)
            elif operation == "multiply":
                return str(x * y)
            elif operation == "divide":
                return str(x / y)
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
            response = bot.respond("This is a unittest. Please use faulty_tool with input 5.")
            # Test passes if this does not cause an error

            # Test recovery and continued conversation
            response = bot.respond("Okay, let's forget about that tool. What's the capital of France?")
            self.assertIn("Paris", response)

if __name__ == '__main__':
    unittest.main()

