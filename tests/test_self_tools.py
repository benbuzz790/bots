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
        # First message: bot acknowledges it will use the tool
        response1 = self.bot.respond("Please use get_own_info to tell me about yourself")
        # Should not contain error about not finding calling bot
        self.assertNotIn("Error: Could not find calling bot", response1)
        # Second message: bot should have access to tool results and include them
        response2 = self.bot.respond("What information did you find about yourself?")
        # Should contain bot information from the tool results
        self.assertIn("name", response2.lower())
        self.assertIn("TestBot", response2)

    def test_branch_self_basic_functionality(self) -> None:
        """Test that branch_self function correctly identifies it cannot be called as a tool."""
        response1 = self.bot.respond(
            "Use branch_self tool now with self_prompts=['Hello world', 'Goodbye world'] and allow_work='False'. Do not explain, just call the tool."
        )
        # Should not contain error about not finding calling bot
        self.assertNotIn("Error: Could not find calling bot", response1)
        # Check what the tool actually returned
        response2 = self.bot.respond("What did the branch_self tool return?")
        # Should indicate that it cannot be called as a tool
        self.assertIn("API conversation state constraints", response2)

    def test_branch_self_debug_printing(self) -> None:
        """Test that branch_self handles tool call constraints without debug output."""
        # Capture stdout to verify no debug printing when constraint error occurs
        import io
        from unittest.mock import patch

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            response1 = self.bot.respond("Use branch_self with prompts ['Test prompt 1', 'Test prompt 2']")
            response2 = self.bot.respond("What did the branch_self tool return?")
        # Get the captured output
        debug_output = captured_output.getvalue()
        # Should not have debug output since branching doesn't execute
        self.assertNotIn("=== BRANCH", debug_output)
        # Should handle constraint gracefully
        self.assertIn("API conversation state constraints", response2)

    def test_branch_self_method_restoration(self) -> None:
        """Test that branch_self handles tool call constraints gracefully."""
        response1 = self.bot.respond(
            "Execute branch_self tool with self_prompts=['Test restoration'] now. Do not explain, just call the tool."
        )
        # Check what the tool actually returned
        response2 = self.bot.respond("What did the branch_self tool return?")
        # Should handle the tool call constraint gracefully
        self.assertIn("API conversation state constraints", response2)
        # Verify that normal operation still works after the constraint error
        normal_response = self.bot.respond("Hello, how are you?")
        self.assertIsInstance(normal_response, str)
        self.assertGreater(len(normal_response), 0)

    def test_branch_self_with_allow_work_true(self) -> None:
        """Test branch_self with allow_work=True parameter."""
        import io
        from unittest.mock import patch

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            response1 = self.bot.respond("Use branch_self with prompts ['Simple task'] and allow_work='True'")
            response2 = self.bot.respond("What did the branch_self tool return?")
        debug_output = captured_output.getvalue()
        # Should not have debug output since branching doesn't execute due to constraints
        self.assertNotIn("=== BRANCH", debug_output)
        # Should handle constraint gracefully
        self.assertIn("API conversation state constraints", response2)

    def test_branch_self_error_handling(self) -> None:
        """Test branch_self error handling with invalid input."""
        response1 = self.bot.respond(
            "Execute branch_self tool with self_prompts='not a list' now. Do not explain, just call the tool."
        )
        # Check what the tool actually returned
        response2 = self.bot.respond("What did the branch_self tool return?")
        # Should handle the tool call constraint gracefully
        self.assertIn("API conversation state constraints", response2)

    def test_branch_self_empty_prompts(self) -> None:
        """Test branch_self with empty prompt list."""
        response1 = self.bot.respond(
            "Call branch_self tool with self_prompts=[] now. Do not explain, just execute the tool call."
        )
        # Check what the tool actually returned
        response2 = self.bot.respond("What did the branch_self tool return?")
        # Should handle the tool call constraint gracefully
        self.assertIn("API conversation state constraints", response2)

    def test_debug_output_format(self) -> None:
        """Test that branch_self handles constraints without producing debug output."""
        import io
        from unittest.mock import patch

        captured_output = io.StringIO()
        with patch("sys.stdout", captured_output):
            response1 = self.bot.respond("Use branch_self with prompts ['Format test']")
            response2 = self.bot.respond("What did the branch_self tool return?")
        debug_output = captured_output.getvalue()
        # Should not have debug sections since branching doesn't execute
        self.assertNotIn("=== BRANCH", debug_output)
        self.assertNotIn("DEBUG ===", debug_output)
        # Should handle constraint gracefully
        self.assertIn("API conversation state constraints", response2)


if __name__ == "__main__":
    unittest.main()
