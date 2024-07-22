import os
import sys
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
import unittest
from src.bot_mailbox import BaseMailbox, OpenAIMailbox, AnthropicMailbox
import src.conversation_node as CN
import json
from openai.types.chat import ChatCompletionMessage

class TestBaseMailbox(unittest.TestCase):
    def setUp(self):
        self.test_mb = OpenAIMailbox()

    def test_log_message(self):
        self.test_mb.log_message("Test message", "OUTGOING")
        with open('data\\mailbox_log.txt', 'r', encoding='utf-8') as file:
            log_content = file.read()
        self.assertIn("Test message", log_content)
        self.assertIn("OUTGOING", log_content)

    def test_send_message(self):
        conversation = CN.ConversationNode("user", "Test message")
        result = self.test_mb.send_message(conversation, "gpt-3.5-turbo", 100, 0.7, api_key=self.test_mb.api_key)
        self.assertEqual(result[1], 'assistant')

class TestOpenAIMailbox(unittest.TestCase):
    def setUp(self):
        self.openai_mailbox = OpenAIMailbox()

    def test_send_message_implementation(self):
        conversation = CN.ConversationNode("user", "What is the capital of France?")
        response = self.openai_mailbox._send_message_implementation(
            conversation, "gpt-3.5-turbo", 100, 0.7, os.getenv("OPENAI_API_KEY")
        )
        self.assertIsInstance(response.choices[0].message, ChatCompletionMessage)

    def test_process_response(self):
        conversation = CN.ConversationNode("user", "What is the capital of France?")
        response = self.openai_mailbox._send_message_implementation(
            conversation, "gpt-3.5-turbo", 100, 0.7, os.getenv("OPENAI_API_KEY")
        )
        result = self.openai_mailbox._process_response(response)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn("Paris", result[0])
        self.assertEqual(result[1], 'assistant')

class TestAnthropicMailbox(unittest.TestCase):
    def setUp(self):
        self.anthropic_mailbox = AnthropicMailbox()
        
        # Create src directory if it doesn't exist
        if not os.path.exists('src'):
            os.makedirs('src')
        
        # Create a simple tools.py file for testing
        with open('src/tools.py', 'w') as f:
            f.write("""
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers together.\"\"\"
    return int(a) + int(b)

def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a.\"\"\"
    return int(a) - int(b)
            """)

    def tearDown(self):
        # Remove the tools.py file after tests
        if os.path.exists('src/tools.py'):
            os.remove('src/tools.py')

    def test_send_message_implementation(self):
        conversation = CN.ConversationNode("user", "What is the capital of France?")
        response = self.anthropic_mailbox._send_message_implementation(
            conversation, "claude-3-haiku-20240307", 100, 0.7, os.getenv("ANTHROPIC_API_KEY")
        )
        #self.assertIsInstance(response.content[0], ContentBlock)
        self.assertEqual(response.content[0].type, 'text')
    
    def test_process_response_regular(self):
        conversation = CN.ConversationNode("user", "What is the capital of France?")
        response = self.anthropic_mailbox._send_message_implementation(
            conversation, "claude-3-haiku-20240307", 100, 0.7, os.getenv("ANTHROPIC_API_KEY")
        )
        result = self.anthropic_mailbox._process_response(response)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn("Paris", result[0])
        self.assertEqual(result[1], 'assistant')

    def test_process_response_tool_use(self):
        self.anthropic_mailbox.add_tools_from_py('src/tools.py')
        conversation = CN.ConversationNode("user", "What is 15 + 27?")
        response = self.anthropic_mailbox._send_message_implementation(
            conversation, "claude-3-haiku-20240307", 100, 0.7, os.getenv("ANTHROPIC_API_KEY")
        )
        result = self.anthropic_mailbox._process_response(response)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 2)
        self.assertIn("42", result[0])
        self.assertIn("Tool Results:", result[0])

if __name__ == '__main__':
    unittest.main()