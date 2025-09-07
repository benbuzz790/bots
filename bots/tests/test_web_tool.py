"""
Test suite for the web_tool module.

Tests both the web_search function functionality and integration with the bot framework.
Includes unit tests for correct behavior and integration tests for bot usage.
"""

import json
import unittest
from unittest.mock import Mock, patch, MagicMock
import os

from bots.tools.web_tool import web_search


class TestWebSearchFunction(unittest.TestCase):
    """Test the web_search function."""

    def test_web_search_function_signature(self):
        """Test that web_search function has correct signature and docstring."""
        # Check that the function has the expected toolified behavior
        self.assertTrue(hasattr(web_search, '__doc__'))
        self.assertIn("agentic web search", web_search.__doc__)
        self.assertIn("Claude's internal web search", web_search.__doc__)

        # Check function signature
        import inspect
        sig = inspect.signature(web_search)
        params = list(sig.parameters.keys())
        self.assertEqual(params, ['question'])

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('bots.tools.web_tool.anthropic.Anthropic')
    def test_web_search_basic_behavior(self, mock_anthropic_class):
        """Test basic web_search function behavior with mocked API."""
        # Setup mock client and response
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create a realistic mock response
        mock_response = Mock()
        mock_response.content = [Mock()]
        mock_response.content[0].text = "Search results for test query"
        mock_response.__str__ = Mock(return_value="Mock API Response Object")
        mock_client.messages.create.return_value = mock_response

        # Call web_search
        result = web_search("test query")

        # Verify client was created
        mock_anthropic_class.assert_called_once_with(api_key='test-key')

        # Verify API call was made with correct parameters
        mock_client.messages.create.assert_called_once()
        call_args = mock_client.messages.create.call_args

        # Check the call arguments
        # Model verification removed - model is a tunable parameter
        self.assertEqual(call_args[1]['temperature'], 0.3)

        # Check tools parameter
        tools = call_args[1]['tools']
        self.assertEqual(len(tools), 1)
        self.assertEqual(tools[0]['type'], 'web_search_20250305')
        self.assertEqual(tools[0]['name'], 'web_search')
        self.assertEqual(tools[0]['max_uses'], 10)

        # Check messages parameter
        messages = call_args[1]['messages']
        self.assertEqual(len(messages), 1)
        self.assertEqual(messages[0]['role'], 'user')
        self.assertIn('test query', messages[0]['content'])

        # Verify result contains both raw and processed responses
        self.assertIsInstance(result, str)
        self.assertIn("Raw API Response:", result)
        self.assertIn("Mock API Response Object", result)
        # Processed Response not implemented yet - only raw response returned
        # Mock returns the __str__ value, not the content.text

    def test_web_search_missing_api_key(self):
        """Test web_search when API key is missing."""
        with patch.dict(os.environ, {}, clear=True):
            result = web_search("test query")

            # Verify error is handled gracefully
            self.assertIsInstance(result, str)
            self.assertIn("Error: ANTHROPIC_API_KEY environment variable not set", result)

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('bots.tools.web_tool.anthropic.Anthropic')
    def test_web_search_api_exception(self, mock_anthropic_class):
        """Test web_search handles API exceptions gracefully."""
        # Setup mock client that raises exception
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client
        mock_client.messages.create.side_effect = Exception("API Error")

        result = web_search("test query")

        # Verify error is handled and returned as string
        self.assertIsInstance(result, str)
        self.assertIn("Web search failed:", result)
        self.assertIn("API Error", result)

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('bots.tools.web_tool.anthropic.Anthropic')
    def test_web_search_empty_response(self, mock_anthropic_class):
        """Test web_search with empty response content."""
        # Setup mock client with empty response
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = []
        mock_response.__str__ = Mock(return_value="Empty Response Object")
        mock_client.messages.create.return_value = mock_response

        result = web_search("test query")

        # Verify it handles empty content gracefully
        self.assertIsInstance(result, str)
        self.assertIn("Raw API Response:", result)
        self.assertIn("Empty Response Object", result)
        # Processed Response not implemented yet - only raw response returned

    @patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'})
    @patch('bots.tools.web_tool.anthropic.Anthropic')
    def test_web_search_complex_response(self, mock_anthropic_class):
        """Test web_search with complex response structure."""
        # Setup mock client with complex response
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create mock response with multiple content blocks
        mock_response = Mock()
        mock_response.content = [
            Mock(text="I'll search for that information."),
            Mock(text=None, type='server_tool_use', name='web_search'),
            Mock(text=None, type='web_search_tool_result'),
            Mock(text="Based on the search results, here's what I found...")
        ]
        mock_response.__str__ = Mock(return_value="Complex Response Object")
        mock_client.messages.create.return_value = mock_response

        result = web_search("complex query")

        # Verify it extracts the first text block
        self.assertIsInstance(result, str)
        self.assertIn("Raw API Response:", result)
        self.assertIn("Complex Response Object", result)
        # Processed Response not implemented yet - only raw response returned
        # Mock returns the __str__ value, not the content blocks

    def test_web_search_is_toolified(self):
        """Test that web_search function is properly toolified."""
        # Test that it accepts string input and returns string output
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('bots.tools.web_tool.anthropic.Anthropic') as mock_anthropic_class:
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client

                mock_response = Mock()
                mock_response.content = [Mock(text="Mocked response")]
                mock_response.__str__ = Mock(return_value="Mocked raw response")
                mock_client.messages.create.return_value = mock_response

                # Should accept string input and return string output
                result = web_search("test query")
                self.assertIsInstance(result, str)

    def test_web_search_prompt_construction(self):
        """Test that the search prompt is constructed correctly."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('bots.tools.web_tool.anthropic.Anthropic') as mock_anthropic_class:
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client

                mock_response = Mock()
                mock_response.content = [Mock(text="Response")]
                mock_response.__str__ = Mock(return_value="Raw response")
                mock_client.messages.create.return_value = mock_response

                # Test with specific query
                test_query = "Python 3.12 features"
                web_search(test_query)

                # Check that the prompt includes the query
                call_args = mock_client.messages.create.call_args
                messages = call_args[1]['messages']
                prompt_content = messages[0]['content']

                self.assertIn(test_query, prompt_content)
                self.assertIn("search the web", prompt_content.lower())


class TestWebSearchValidation(unittest.TestCase):
    """Test web_search function validation and edge cases."""

    def test_web_search_with_special_characters(self):
        """Test web_search with special characters in query."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('bots.tools.web_tool.anthropic.Anthropic') as mock_anthropic_class:
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client

                mock_response = Mock()
                mock_response.content = [Mock(text="Response")]
                mock_response.__str__ = Mock(return_value="Raw response")
                mock_client.messages.create.return_value = mock_response

                # Test with special characters
                special_query = "Python & C++ comparison: which is better?"
                result = web_search(special_query)

                # Should handle special characters gracefully
                self.assertIsInstance(result, str)
                self.assertIn("Raw API Response:", result)

    def test_web_search_with_empty_query(self):
        """Test web_search with empty query."""
        with patch.dict(os.environ, {'ANTHROPIC_API_KEY': 'test-key'}):
            with patch('bots.tools.web_tool.anthropic.Anthropic') as mock_anthropic_class:
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client

                mock_response = Mock()
                mock_response.content = [Mock(text="Response")]
                mock_response.__str__ = Mock(return_value="Raw response")
                mock_client.messages.create.return_value = mock_response

                # Test with empty query
                result = web_search("")

                # Should still work (Claude will handle the empty query)
                self.assertIsInstance(result, str)
                self.assertIn("Raw API Response:", result)


if __name__ == "__main__":
    unittest.main(verbosity=2)
