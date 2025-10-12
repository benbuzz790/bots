"""
Integration tests for web_tool with bot framework.

Tests the complete flow of:
1. Adding web_search tool to bots
2. Verifying tool registration and execution
3. Testing real bot usage scenarios
4. Manual inspection helpers for correct behavior validation
"""

import os
import tempfile
import unittest
from unittest.mock import Mock, patch

from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines
from bots.tools.web_tool import web_search


class TestWebToolIntegration(unittest.TestCase):
    """Integration tests for web_tool with the bot framework."""

    def setUp(self):
        """Set up test environment with bot."""
        self.bot = AnthropicBot(
            api_key=None,  # No actual API calls needed for most tests
            model_engine=Engines.CLAUDE4_SONNET,
            max_tokens=1000,
            temperature=0,
            name="WebToolIntegrationTestBot",
            autosave=False,
        )

        # Create temp directory for test files
        self.test_dir = tempfile.mkdtemp()

    def test_add_web_search_tool_to_bot(self):
        """Test that web_search tool can be added to bot."""
        # Add web_search tool to bot
        self.bot.add_tools(web_search)

        # Verify tool is registered
        tool_names = list(self.bot.tool_handler.function_map.keys())
        self.assertIn("web_search", tool_names)

        # Verify tool schema is generated
        self.assertEqual(len(self.bot.tool_handler.tools), 1)

        # Verify tool schema has correct structure
        tool_schema = self.bot.tool_handler.tools[0]
        self.assertIn("name", tool_schema)
        self.assertIn("description", tool_schema)
        self.assertIn("input_schema", tool_schema)
        self.assertEqual(tool_schema["name"], "web_search")

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("bots.tools.web_tool.anthropic.Anthropic")
    def test_web_search_tool_execution_through_bot(self, mock_anthropic_class):
        """Test web_search tool execution through bot's tool handler."""
        # Add tool to bot
        self.bot.add_tools(web_search)

        # Setup mock for the web_search function
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Mocked search results")]
        mock_response.__str__ = Mock(return_value="Mocked raw API response")
        mock_client.messages.create.return_value = mock_response

        # Execute tool through bot's tool handler
        web_search_func = self.bot.tool_handler.function_map["web_search"]
        result = web_search_func("Python programming tutorials")

        # Verify result is a string (toolified behavior)
        self.assertIsInstance(result, str)
        self.assertIn("=== WEB SEARCH RESULTS ===", result)
        self.assertIn("Python programming tutorials", result)

    def test_web_search_tool_with_multiple_tools(self):
        """Test web_search tool alongside other tools."""
        # Create additional test tools
        from bots.dev.decorators import toolify

        @toolify("Add two numbers")
        def add_numbers(x: int, y: int) -> int:
            return x + y

        @toolify("Convert text to uppercase")
        def make_uppercase(text: str) -> str:
            return text.upper()

        # Add multiple tools including web_search
        self.bot.add_tools(web_search, add_numbers, make_uppercase)

        # Verify all tools are registered
        tool_names = list(self.bot.tool_handler.function_map.keys())
        self.assertIn("web_search", tool_names)
        self.assertIn("add_numbers", tool_names)
        self.assertIn("make_uppercase", tool_names)

        # Test that each tool works correctly
        add_result = self.bot.tool_handler.function_map["add_numbers"]("10", "5")
        self.assertEqual(add_result, "15")

        upper_result = self.bot.tool_handler.function_map["make_uppercase"]("test")
        self.assertEqual(upper_result, "TEST")

        # Test web_search tool (mocked)
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("bots.tools.web_tool.anthropic.Anthropic") as mock_anthropic_class:
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client

                mock_response = Mock()
                mock_response.content = [Mock(text="Search results")]
                mock_response.__str__ = Mock(return_value="Raw response")
                mock_client.messages.create.return_value = mock_response

                web_result = self.bot.tool_handler.function_map["web_search"]("test query")
                self.assertIsInstance(web_result, str)
                self.assertIn("=== WEB SEARCH RESULTS ===", web_result)

    def test_web_search_tool_error_handling_integration(self):
        """Test web_search tool error handling in bot context."""
        # Add tool to bot
        self.bot.add_tools(web_search)

        # Test with missing API key
        with patch.dict(os.environ, {}, clear=True):
            web_search_func = self.bot.tool_handler.function_map["web_search"]
            result = web_search_func("test query")

            # Verify error is handled gracefully
            self.assertIsInstance(result, str)
            self.assertIn("ANTHROPIC_API_KEY environment variable not set", result)

        # Test with API exception
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            with patch("bots.tools.web_tool.anthropic.Anthropic") as mock_anthropic_class:
                mock_client = Mock()
                mock_anthropic_class.return_value = mock_client
                mock_client.messages.create.side_effect = Exception("Connection failed")

                web_search_func = self.bot.tool_handler.function_map["web_search"]
                result = web_search_func("test query")

                # Verify error is handled gracefully
                self.assertIsInstance(result, str)
                self.assertIn("Web search failed:", result)
                self.assertIn("Connection failed", result)

    def test_web_search_tool_docstring_and_schema(self):
        """Test web_search tool has proper docstring and schema for LLM."""
        # Add tool to bot
        self.bot.add_tools(web_search)

        # Check tool function docstring (comes from @toolify decorator)
        web_search_func = self.bot.tool_handler.function_map["web_search"]
        self.assertIn("agentic web search", web_search_func.__doc__)
        self.assertIn("Claude's internal web search", web_search_func.__doc__)

        # Check tool schema
        tool_schema = self.bot.tool_handler.tools[0]
        self.assertEqual(tool_schema["name"], "web_search")
        self.assertIn("agentic web search", tool_schema["description"])

        # Check input schema
        input_schema = tool_schema["input_schema"]
        self.assertIn("properties", input_schema)
        self.assertIn("question", input_schema["properties"])
        self.assertIn("required", input_schema)
        self.assertIn("question", input_schema["required"])

    def tearDown(self):
        """Clean up test files and directories."""
        import shutil

        try:
            shutil.rmtree(self.test_dir, ignore_errors=True)
        except Exception as e:
            print(f"Warning: Could not clean up test directory: {e}")


class TestWebToolManualInspection(unittest.TestCase):
    """Tests for manual inspection of web_tool behavior."""

    def setUp(self):
        """Set up for manual inspection tests."""
        self.inspection_results = {}

    @unittest.skip("Manual inspection test - run separately with real API key")
    def test_manual_web_search_inspection(self):
        """Manual test to inspect actual web search behavior.

        This test is skipped by default. To run it:
        1. Ensure ANTHROPIC_API_KEY environment variable is set
        2. Remove the @unittest.skip decorator
        3. Run this test individually
        4. Manually inspect the output for correctness
        """
        # This performs a real web search for manual inspection
        result = web_search("latest Python 3.12 features")

        print("\n" + "=" * 80)
        print("MANUAL INSPECTION: Web Search Results")
        print("=" * 80)
        print("Query: latest Python 3.12 features")
        print(f"Result length: {len(result)} characters")
        print("\nResult preview (first 500 chars):")
        print(result[:500])
        print("\n" + "=" * 80)

        # Store for potential automated checks after manual inspection
        self.inspection_results["web_search"] = {
            "query": "latest Python 3.12 features",
            "result_length": len(result),
            "contains_raw_response": "=== WEB SEARCH RESULTS ===" in result,
            "contains_processed_response": "Search performed:" in result,
            "result_preview": result[:200],
        }

        # Basic automated checks based on expected structure
        self.assertIsInstance(result, str)
        self.assertGreater(len(result), 50)  # Should have substantial content
        self.assertIn("=== WEB SEARCH RESULTS ===", result)
        self.assertIn("Search performed:", result)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("bots.tools.web_tool.anthropic.Anthropic")
    def test_web_search_result_structure_expectations(self, mock_anthropic_class):
        """Test expected structure of web_search results (mocked)."""
        # Create a realistic mock response structure
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Create mock response that mimics real web search structure
        mock_response = Mock()
        mock_response.content = [
            Mock(text="I'll search for information about Python tutorials.", type="text"),
            Mock(text=None, type="server_tool_use", name="web_search"),
            Mock(
                text=None,
                type="web_search_tool_result",
                content=[
                    {"type": "web_search_result", "title": "Python Tutorial", "url": "https://example.com"},
                    {"type": "web_search_result", "title": "Advanced Python", "url": "https://example2.com"},
                ],
            ),
            Mock(text="Based on the search results, I found 2 relevant tutorials...", type="text"),
        ]
        mock_response.__str__ = Mock(
            return_value=str(
                {
                    "search_results": [
                        {"title": "Python Tutorial", "url": "https://example.com", "snippet": "Learn Python..."},
                        {"title": "Advanced Python", "url": "https://example2.com", "snippet": "Advanced concepts..."},
                    ],
                    "query": "Python tutorials",
                    "total_results": 2,
                }
            )
        )
        mock_client.messages.create.return_value = mock_response

        result = web_search("Python tutorials")

        # Test expected structure
        self.assertIn("=== WEB SEARCH RESULTS ===", result)
        self.assertIn("Search performed:", result)
        self.assertIn("=== CLAUDE'S ANALYSIS ===", result)

        # Test that raw response data is preserved
        self.assertIn("Python Tutorial", result)
        self.assertIn("https://example.com", result)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("bots.tools.web_tool.anthropic.Anthropic")
    def test_web_search_with_citations(self, mock_anthropic_class):
        """Test web_search handles responses with citations."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        # Mock response with citations (like real Claude responses)
        mock_response = Mock()
        mock_response.content = [
            Mock(text="Based on the search results:", type="text"),
            Mock(
                text="Python 3.12 includes many new features",
                citations=[{"url": "https://python.org", "title": "Python 3.12 Release"}],
            ),
        ]
        mock_response.__str__ = Mock(return_value="Response with citations")
        mock_client.messages.create.return_value = mock_response

        result = web_search("Python 3.12 features")

        # Should handle citations gracefully
        self.assertIsInstance(result, str)
        self.assertIn("=== WEB SEARCH RESULTS ===", result)
        self.assertIn("Based on the search results:", result)
        self.assertIn("=== WEB SEARCH RESULTS ===", result)


class TestWebToolRealWorldScenarios(unittest.TestCase):
    """Test web_tool in realistic usage scenarios."""

    def setUp(self):
        """Set up realistic test scenarios."""
        self.bot = AnthropicBot(
            api_key=None,
            model_engine=Engines.CLAUDE4_SONNET,
            max_tokens=1000,
            temperature=0,
            name="RealWorldTestBot",
            autosave=False,
        )

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("bots.tools.web_tool.anthropic.Anthropic")
    def test_web_search_for_current_events(self, mock_anthropic_class):
        """Test web_search for current events queries."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Here are the latest news about AI developments...")]
        mock_response.__str__ = Mock(return_value="Current events response")
        mock_client.messages.create.return_value = mock_response

        result = web_search("latest AI developments 2024")

        self.assertIsInstance(result, str)
        self.assertIn("=== WEB SEARCH RESULTS ===", result)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("bots.tools.web_tool.anthropic.Anthropic")
    def test_web_search_for_technical_documentation(self, mock_anthropic_class):
        """Test web_search for technical documentation queries."""
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Here's the documentation for the Python requests library...")]
        mock_response.__str__ = Mock(return_value="Technical docs response")
        mock_client.messages.create.return_value = mock_response

        result = web_search("Python requests library documentation")

        self.assertIsInstance(result, str)
        self.assertIn("Python requests library", result)

    @patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"})
    @patch("bots.tools.web_tool.anthropic.Anthropic")
    def test_web_search_integration_with_bot_workflow(self, mock_anthropic_class):
        """Test web_search as part of a larger bot workflow."""
        # Add web_search and other tools to bot
        from bots.dev.decorators import toolify

        @toolify("Summarize text")
        def summarize_text(text: str) -> str:
            return f"Summary: {text[:100]}..."

        self.bot.add_tools(web_search, summarize_text)

        # Mock web search
        mock_client = Mock()
        mock_anthropic_class.return_value = mock_client

        mock_response = Mock()
        mock_response.content = [Mock(text="Detailed information about machine learning...")]
        mock_response.__str__ = Mock(return_value="ML search response")
        mock_client.messages.create.return_value = mock_response

        # Test workflow: search then summarize
        search_result = self.bot.tool_handler.function_map["web_search"]("machine learning basics")
        summary_result = self.bot.tool_handler.function_map["summarize_text"](search_result)

        self.assertIsInstance(search_result, str)
        self.assertIsInstance(summary_result, str)
        self.assertIn("Summary:", summary_result)


if __name__ == "__main__":
    # Run tests with verbose output for better inspection
    unittest.main(verbosity=2)
