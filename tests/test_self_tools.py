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
        follow_up = self.bot.respond("What information did you get about yourself?")
        self.assertNotIn("Error: Could not find calling bot", response)
        self.assertIn("name", follow_up.lower())
        self.assertIn("TestBot", follow_up)

    def test_branch_self_basic_functionality(self) -> None:
        """Test that branch_self function works correctly when called as a tool."""
        response = self.bot.respond("Please create 2 branches with prompts ['Hello world', 'Goodbye world'] using branch_self")
        self.assertNotIn("Error: Could not find calling bot", response)
        self.assertIn("branch", response.lower())
        self.assertIn("two", response.lower())
        follow_up = self.bot.respond("What happened with the branching?")
        self.assertIn("branch", follow_up.lower())

    def test_branch_self_debug_printing(self) -> None:
        """Test that branch_self function works correctly with multiple prompts."""
        response = self.bot.respond("Please create 2 branches with prompts ['Test prompt 1', 'Test prompt 2'] using branch_self")
        self.assertIn("branch", response.lower())

    def test_branch_self_method_restoration(self) -> None:
        """Test that the original respond method is properly restored after branching."""
        # Store the original method's underlying function and instance
        original_func = self.bot.respond.__func__
        original_self = self.bot.respond.__self__
        
        # Execute branch_self which should temporarily overwrite respond method
        response = self.bot.respond("Use branch_self with prompts ['Test restoration']")
        
        # Verify the respond method was restored to the original
        self.assertIs(self.bot.respond.__func__, original_func,
                    "respond method function was not properly restored after branch_self")
        self.assertIs(self.bot.respond.__self__, original_self,
                    "respond method instance was not properly restored after branch_self")

    def test_branch_self_with_allow_work_true(self) -> None:
        """Test branch_self with allow_work=True parameter."""
        response = self.bot.respond("Please create 1 branch with prompts ['Simple task'] using branch_self with allow_work=True")
        self.assertIn("branch", response.lower())

    def test_branch_self_error_handling(self) -> None:
        """Test branch_self error handling with invalid input."""
        response = self.bot.respond("Use branch_self with invalid prompts: 'not a list'")
        self.assertIn("invalid", response.lower())

    def test_branch_self_empty_prompts(self) -> None:
        """Test branch_self with empty prompt list."""
        response = self.bot.respond("Use branch_self with prompts []")
        self.assertIn("empty", response.lower())

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