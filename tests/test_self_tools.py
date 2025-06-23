import io
import sys
import tempfile
import unittest
from unittest.mock import patch
import bots.tools.self_tools as self_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines

class TestSelfTools(unittest.TestCase):
    """Test suite for self_tools module functionality.

    This test suite verifies the behavior of self-introspection and branching
    tools, with particular focus on the debug printing functionality added
    to the branch_self function.

    Attributes:
        temp_dir (str): Temporary directory path for test file operations
        bot (AnthropicBot): Test bot instance with Claude 3.5 Sonnet configuration
    """

    def setUp(self) -> None:
        """Set up test environment before each test.

        Creates a temporary directory and initializes a test AnthropicBot instance
        with Claude 3.5 Sonnet configuration and self_tools loaded.
        """
        self.temp_dir = tempfile.mkdtemp()
        self.bot = AnthropicBot(name="TestBot", model_engine=Engines.CLAUDE35_SONNET_20240620)
        self.bot.add_tools(self_tools)

    def tearDown(self) -> None:
        """Clean up test environment after each test."""
        import shutil
        try:
            shutil.rmtree(self.temp_dir)
        except Exception as e:
            print(f"Warning: Could not clean up temp directory: {e}")

    def test_get_own_info(self) -> None:
        """Test that get_own_info returns valid bot information."""
        response = self.bot.respond("Please use get_own_info to tell me about yourself")
        # Should not contain error about not finding calling bot
        self.assertNotIn("Error: Could not find calling bot", response)
        # Should contain bot information
        self.assertIn("name", response.lower())
        self.assertIn("TestBot", response)

    def test_branch_self_basic_functionality(self) -> None:
        """Test that branch_self function works correctly when called as a tool."""
        response = self.bot.respond("Please create 2 branches with prompts ['Hello world', 'Goodbye world'] using branch_self")
        # Should not contain error about not finding calling bot
        self.assertNotIn("Error: Could not find calling bot", response)
        # Should indicate successful branching
        self.assertIn("branch", response.lower())
        self.assertIn("2", response)

    def test_branch_self_debug_printing(self) -> None:
        """Test that branch_self produces debug output when branching."""
        # Capture stdout to verify debug printing
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            response = self.bot.respond("Use branch_self with prompts ['Test prompt 1', 'Test prompt 2']")
        # Get the captured output
        debug_output = captured_output.getvalue()
        # Verify debug output contains expected elements
        self.assertIn("=== BRANCH", debug_output)
        self.assertIn("DEBUG ===", debug_output)
        self.assertIn("PROMPT:", debug_output)
        self.assertIn("RESPONSE:", debug_output)
        self.assertIn("Test prompt 1", debug_output)
        self.assertIn("Test prompt 2", debug_output)
        # Should have debug output for both branches
        self.assertIn("BRANCH 0", debug_output)
        self.assertIn("BRANCH 1", debug_output)

    def test_branch_self_method_restoration(self) -> None:
        """Test that the original respond method is properly restored after branching."""
        # Store reference to original respond method
        original_respond = self.bot.respond
        # Execute branch_self
        response = self.bot.respond("Use branch_self with prompts ['Test restoration']")
        # Verify the respond method is the same object as before
        self.assertIs(self.bot.respond, original_respond)
        # Verify normal operation still works
        normal_response = self.bot.respond("Hello, how are you?")
        self.assertIsInstance(normal_response, str)
        self.assertGreater(len(normal_response), 0)

    def test_branch_self_with_allow_work_true(self) -> None:
        """Test branch_self with allow_work=True parameter."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            # Note: This test might take longer as allow_work=True lets branches use tools
            response = self.bot.respond("Use branch_self with prompts ['Simple task'] and allow_work='True'")
        debug_output = captured_output.getvalue()
        # Should still have debug output
        self.assertIn("=== BRANCH", debug_output)
        self.assertIn("PROMPT:", debug_output)
        self.assertIn("RESPONSE:", debug_output)

    def test_branch_self_error_handling(self) -> None:
        """Test branch_self error handling with invalid input."""
        response = self.bot.respond("Use branch_self with invalid prompts: 'not a list'")
        # Should handle the error gracefully
        self.assertIn("Error", response)

    def test_branch_self_empty_prompts(self) -> None:
        """Test branch_self with empty prompt list."""
        response = self.bot.respond("Use branch_self with prompts []")
        # Should handle empty list gracefully
        self.assertIn("Error", response)

    def test_debug_output_format(self) -> None:
        """Test that debug output follows the expected format."""
        captured_output = io.StringIO()
        with patch('sys.stdout', captured_output):
            self.bot.respond("Use branch_self with prompts ['Format test']")
        debug_output = captured_output.getvalue()
        lines = debug_output.split('\n')
        # Find debug sections
        debug_start_lines = [i for i, line in enumerate(lines) if "=== BRANCH" in line and "DEBUG ===" in line]
        debug_end_lines = [i for i, line in enumerate(lines) if "=== END BRANCH" in line and "DEBUG ===" in line]
        # Should have matching start and end markers
        self.assertEqual(len(debug_start_lines), len(debug_end_lines))
        # Each debug section should be properly formatted
        for start_idx, end_idx in zip(debug_start_lines, debug_end_lines):
            section = lines[start_idx:end_idx + 1]
            section_text = '\n'.join(section)
            # Should contain required elements
            self.assertIn("PROMPT:", section_text)
            self.assertIn("RESPONSE:", section_text)
            self.assertIn("=" * 50, section_text)  # Separator line
if __name__ == '__main__':
    unittest.main()