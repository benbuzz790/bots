import unittest
from unittest.mock import patch, MagicMock, mock_open
from bot_mailbox import BaseMailbox, OpenAIMailbox, AnthropicMailbox
import conversation_node as CN
import os

class ConcreteBaseMailbox(BaseMailbox):
    def _send_message_implementation(self, conversation, model, max_tokens, temperature, api_key, system_message=None):
        return {'test': 'response'}

    def _process_response(self, response):
        return 'test_text', 'test_role'

class TestBaseMailbox(unittest.TestCase):
    def setUp(self):
        self.base_mailbox = ConcreteBaseMailbox()

    def test_log_message(self):
        with patch('builtins.open', mock_open()) as mock_file:
            self.base_mailbox.log_message("Test message", "OUTGOING")
            mock_file.assert_called_once_with('mailbox_log.txt', 'a', encoding='utf-8')
            mock_file().write.assert_called_once()

class TestOpenAIMailbox(unittest.TestCase):
    def setUp(self):
        self.patcher = patch('bot_mailbox.OpenAI')
        self.mock_openai = self.patcher.start()
        self.mock_client = MagicMock()
        self.mock_openai.return_value = self.mock_client
        self.openai_mailbox = OpenAIMailbox()

    def tearDown(self):
        self.patcher.stop()

    def test_send_message_implementation(self):
        mock_response = MagicMock()
        mock_response.choices = [MagicMock(message=MagicMock(content='Test response', role='assistant'))]
        self.mock_client.chat.completions.create.return_value = mock_response

        conversation = CN.ConversationNode("user", "Test message")
        response = self.openai_mailbox._send_message_implementation(
            conversation, "gpt-3.5-turbo", 100, 0.7, os.getenv('OPENAI_API_KEY')
        )

        print(f"Mock client called: {self.mock_client.chat.completions.create.called}")
        print(f"Mock client call count: {self.mock_client.chat.completions.create.call_count}")
        print(f"Mock client call args: {self.mock_client.chat.completions.create.call_args}")

        self.mock_client.chat.completions.create.assert_called_once()
        self.assertIsInstance(response, MagicMock)

if __name__ == '__main__':
    unittest.main()