import io
import os
import sys
import tempfile
import time
import unittest

import pytest

from bots import AnthropicBot
from bots.foundation.base import Engines
from bots.tools.self_tools import branch_self

pytestmark = pytest.mark.e2e

current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)


class DetailedTestCase(unittest.TestCase):
    """Base test case with enhanced assertion methods."""

    def assertContainsNormalized(self, text: str, substring: str) -> None:
        """Check if normalized text contains normalized substring."""
        text_norm = " ".join(text.split())
        substring_norm = " ".join(substring.split())
        self.assertIn(substring_norm.lower(), text_norm.lower())


class TestBranchSelfIntegration(DetailedTestCase):
    """Integration tests for branch_self functionality."""

    def setUp(self):
        """Set up test environment."""
        self.original_dir = os.getcwd()
        self.temp_dir = tempfile.mkdtemp()
        os.chdir(self.temp_dir)
        print("\n=== TEST ENVIRONMENT ===")
        print("Working directory: {}".format(self.temp_dir))

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_dir)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def test_branch_self_basic_functionality(self):
        """Test basic branch_self functionality with file creation."""
        print("\n" + "=" * 50)
        print("STARTING BRANCH_SELF BASIC FUNCTIONALITY TEST")
        print("=" * 50)
        bot = AnthropicBot(
            name="TestBot",
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=10000,
        )
        bot.add_tools(branch_self)
        start_time = time.time()
        with io.StringIO() as buf:
            sys.stdout = buf
            try:
                bot.respond(
                    "Use branch_self to create 3 branches. "
                    "Each branch should create a text file: "
                    'Branch 1 creates "file1.txt" with content '
                    '"This is the first file. It contains '
                    'information about branch 1.", '
                    'Branch 2 creates "file2.txt" with content '
                    '"This is the second file. It contains '
                    'information about branch 2.", '
                    'Branch 3 creates "file3.txt" with content '
                    '"This is the third file. It contains '
                    'information about branch 3."'
                )
            finally:
                sys.stdout = sys.__stdout__
                output = buf.getvalue()
        duration = time.time() - start_time
        print("\n=== BRANCH_SELF BASIC FUNCTIONALITY TEST ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Output preview:\n{output[-500:]}")
        self.assertLess(duration, 120, "Basic branch_self should complete within 2 minutes")
        self.assertContainsNormalized(output, "branch_self")
        files_created = [f for f in os.listdir(".") if os.path.isfile(f) and f.endswith(".txt")]
        print(f"Text files created: {files_created}")
        if len(files_created) > 0:
            print("✅ Basic branch_self file creation successful")

    def test_branch_self_error_handling(self):
        """Test branch_self error handling with invalid input."""
        print("\n" + "=" * 50)
        print("STARTING BRANCH_SELF ERROR HANDLING TEST")
        print("=" * 50)
        bot = AnthropicBot(
            name="TestBot",
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=10000,
        )
        bot.add_tools(branch_self)
        start_time = time.time()
        with io.StringIO() as buf:
            sys.stdout = buf
            try:
                bot.respond('Call branch_self with self_prompts="invalid" ' "(should be a list)")
            finally:
                sys.stdout = sys.__stdout__
                output = buf.getvalue()
        duration = time.time() - start_time
        print("=" * 50)
        print("BRANCH_SELF ERROR HANDLING TEST")
        print("=" * 50)
        print(f"Duration: {duration:.2f} seconds")
        print(f"Output length: {len(output)} characters")
        self.assertLess(duration, 60, "Error handling should complete within 1 minute")
        self.assertGreater(len(output), 100, "Should produce some output")
        # Test passes as long as it completes without crashing

    def test_branch_self_tool_availability(self):
        """Test that branch_self tool is properly available in CLI context."""
        bot = AnthropicBot(
            name="TestBot",
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=1000,
        )
        bot.add_tools(branch_self)
        tool_names = list(bot.tool_handler.function_map.keys())
        self.assertIn("branch_self", tool_names, "branch_self should be available as a tool")
        print(f"✅ branch_self tool is available. All tools: {tool_names}")

    def test_branch_self_nested_directory_and_file_creation(self):
        """Test branch_self with nested directory and file creation."""
        print("\n" + "=" * 50)
        print("STARTING NESTED DIRECTORY TEST")
        print("=" * 50)
        bot = AnthropicBot(
            name="TestBot",
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=10000,
        )
        bot.add_tools(branch_self)
        with io.StringIO() as buf:
            sys.stdout = buf
            try:
                bot.respond(
                    "Use branch_self to create 2 branches. "
                    "Branch 1: Create directory 'dir1' and "
                    "file 'dir1/test1.txt' with content 'Test 1'. "
                    "Branch 2: Create directory 'dir2' and "
                    "file 'dir2/test2.txt' with content 'Test 2'."
                )
            finally:
                sys.stdout = sys.__stdout__
        dirs_created = [d for d in os.listdir(".") if os.path.isdir(d)]
        print(f"Directories created: {dirs_created}")
        if "dir1" in dirs_created and os.path.exists("dir1/test1.txt"):
            print("✅ Nested directory and file creation successful")


if __name__ == "__main__":
    unittest.main(verbosity=2)
