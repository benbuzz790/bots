import os
import sys
import unittest
from unittest.mock import Mock, patch
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from src.anthropic_bots import AnthropicMailbox, AnthropicToolHandler
from src.openai_bots import OpenAIMailbox
from src.base import ConversationNode, Engines

class TestBaseMailbox(unittest.TestCase):
    def setUp(self):
        self.test_mb = AnthropicMailbox(verbose=True)

    def test_log_message(self):
        with patch('builtins.open', unittest.mock.mock_open()) as mock_file:
            self.test_mb.log_message("Test message", "OUTGOING")
            mock_file().write.assert_called()
            written_content = mock_file().write.call_args[0][0]
            self.assertIn("Test message", written_content)
            self.assertIn("OUTGOING", written_content)

    @patch('src.anthropic_bots.AnthropicMailbox._send_message_implementation')
    @patch('src.anthropic_bots.AnthropicMailbox._process_response')
    def test_send_message(self, mock_process, mock_send):
        mock_send.return_value = {"mock": "response"}
        mock_process.return_value = ("Test response", "assistant", {})
        
        conversation = ConversationNode(role="user", content="Test message")
        result = self.test_mb.send_message(conversation, "gpt-3.5-turbo", 100, 0.7, os.getenv("OPENAI_API_KEY"))
        
        self.assertEqual(result, ("Test response", "assistant", {}))
        mock_send.assert_called_once()
        mock_process.assert_called_once_with({"mock": "response"})

class TestOpenAIMailbox(unittest.TestCase):
    def setUp(self):
        self.openai_mailbox = OpenAIMailbox()

    @unittest.skip(reason="Not Implemented")
    @patch('openai.ChatCompletion.create')
    def test_send_message_implementation(self, mock_create):
       
        conversation = ConversationNode(role="user", content="What is the capital of France?")
        response = self.openai_mailbox._send_message_implementation(
            conversation, "gpt-3.5-turbo", 1024, 0.7, os.getenv("OPENAI_API_KEY")
        )
        
        self.assertIn("Paris", response.choices[0].message.content)
        self.assertEqual(response.choices[0].message.role, "assistant")

    @unittest.skip(reason="Not Implemented")
    def test_process_response(self):
        conversation = ConversationNode(role="user", content="What is the capital of France?")
        response = self.openai_mailbox._send_message_implementation(
            conversation, "gpt-3.5-turbo", 1024, 0.7, os.getenv("OPENAI_API_KEY")
        )
        result = self.openai_mailbox._process_response(response)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertIn("Paris",result[0])
        self.assertEqual(result[1], 'assistant')
        self.assertEqual(result[2], {})

class TestAnthropicMailbox(unittest.TestCase):
    def setUp(self):
        self.anthropic_mailbox = AnthropicMailbox(tool_handler=AnthropicToolHandler())
        self.test_tools_path = 'test_tools.py'
        
        # Create a simple tools file for testing
        with open(self.test_tools_path, 'w') as f:
            f.write("""
def add(a: int, b: int) -> int:
    \"\"\"Add two numbers together.\"\"\"
    return int(a) + int(b)

def subtract(a: int, b: int) -> int:
    \"\"\"Subtract b from a.\"\"\"
    return int(a) - int(b)
            """)

    def tearDown(self):
        # Remove the test tools file after tests
        if os.path.exists(self.test_tools_path):
            os.remove(self.test_tools_path)

    @patch('anthropic.Anthropic')
    def test_send_message_implementation(self, mock_anthropic):
        mock_client = Mock()
        mock_anthropic.return_value = mock_client
        mock_client.messages.create.return_value = Mock(
            content=[Mock(type='text', text="Paris is the capital of France.")],
            role="assistant"
        )

        conversation = ConversationNode(role="user", content="What is the capital of France?")
        response = self.anthropic_mailbox._send_message_implementation(
            conversation, Engines.CLAUDE35.value, 1024, 0.7, os.getenv("ANTHROPIC_API_KEY")
        )

        mock_client.messages.create.assert_called_once()
        self.assertEqual(response.content[0].text, "Paris is the capital of France.")
        self.assertEqual(response.role, "assistant")

    def test_process_response_regular(self):
        mock_response = Mock(
            content=[Mock(type='text', text="Paris is the capital of France.")],
            role="assistant"
        )
        result = self.anthropic_mailbox._process_response(mock_response)
        
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[0], "Paris is the capital of France.")
        self.assertEqual(result[1], 'assistant')
        self.assertEqual(result[2], {})

    def test_process_response_tool_use(self):
        self.anthropic_mailbox.set_tool_handler(AnthropicToolHandler())
        self.anthropic_mailbox.tool_handler.add_tools_from_file(self.test_tools_path)
        conversation = ConversationNode(role="user", content="What is 15 + 27? (use a tool)")
        response = self.anthropic_mailbox._send_message_implementation(
            conversation, Engines.CLAUDE35.value, 1024, 0.7, os.getenv("ANTHROPIC_API_KEY")
        )
        result = self.anthropic_mailbox._process_response(response)
        self.assertIsInstance(result, tuple)
        self.assertEqual(len(result), 3)
        self.assertEqual(result[1], 'assistant')
        self.assertIsInstance(result[2], dict)
        self.assertEqual(result[2]['results'][0]['content'], 42)

if __name__ == '__main__':
    unittest.main()