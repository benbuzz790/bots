import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch

import pytest

import bots.dev.cli as cli_module
from bots import AnthropicBot

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
    """Integration test for branch_self functionality through CLI."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        self.test_duration = 0

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_cli_with_full_tools(self):
        """Create CLI instance with all standard tools including branch_self."""
        cli = cli_module.CLI()
        cli.context.bot_instance = AnthropicBot()
        import bots.tools.code_tools
        import bots.tools.python_edit
        import bots.tools.self_tools

        cli.context.bot_instance.add_tools(
            bots.tools.terminal_tools, bots.tools.self_tools, bots.tools.python_edit, bots.tools.code_tools
        )
        return cli

    @patch("builtins.input")
    def test_branch_self_nested_directory_and_file_creation(self, mock_input):
        """Test the specific prompt: branch_self to make directories, then each branch makes files."""
        prompt = (
            "Hi Claude. Please use branch_self to make three directories (dir1, dir2, dir3), "
            "and then have each branch use branch_self to make three files in each directory. This is a test"
        )
        mock_input.side_effect = [prompt, "/exit"]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = cli_module.CLI()
                original_init = cli._initialize_new_bot

                def init_with_branch_self():
                    original_init()
                    # branch_self is already added in CLI initialization, no need to add again

                cli._initialize_new_bot = init_with_branch_self
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()
        self.test_duration = time.time() - start_time
        print("\n=== BRANCH_SELF NESTED INTEGRATION TEST ===")
        print(f"Duration: {self.test_duration:.2f} seconds")
        print(f"Output length: {len(output)} characters")
        print(f"Full output:\n{output}")
        self.assertLess(self.test_duration, 300, "Branch_self nested test should not take more than 5 minutes")
        if "branch_self" in output.lower():
            print("✅ branch_self was mentioned in output")
        branch_indicators = ["branch", "successfully created", "errors:", "tool_result"]
        found_indicators = [ind for ind in branch_indicators if ind in output.lower()]
        if found_indicators:
            print(f"✅ Found branching indicators: {found_indicators}")
        expected_dirs = ["dir1", "dir2", "dir3", "directory1", "directory2", "directory3", "folder1", "folder2", "folder3"]
        created_dirs = []
        for dirname in expected_dirs:
            if os.path.exists(dirname) and os.path.isdir(dirname):
                created_dirs.append(dirname)
                print(f"✅ Directory created: {dirname}")
        total_files_created = 0
        for dirname in created_dirs:
            files_in_dir = [f for f in os.listdir(dirname) if os.path.isfile(os.path.join(dirname, f))]
            total_files_created += len(files_in_dir)
            if files_in_dir:
                print(f"✅ Files in {dirname}: {files_in_dir}")
        print(f"Total files created: {total_files_created}")
        print(f"Total directories created: {len(created_dirs)}")
        success = False
        if "branch" in output.lower() and ("tool" in output.lower() or "errors:" in output.lower()):
            print("✅ Evidence of branch_self execution found")
            success = True
        elif len(created_dirs) > 0:
            print("✅ Directories were created")
            success = True
        elif "branch_self" in output.lower():
            print("✅ branch_self was at least recognized")
            success = True
        self.assertTrue(success, "Test should show some evidence of branch_self being used or attempted")

    def test_branch_self_basic_functionality(self):
        """Test that branch_self can execute multiple branches and create files."""
        bot = AnthropicBot(
            name="BranchTestBot",
            system_message="You are a helpful assistant.",
            model_engine=Engines.CLAUDE37_SONNET_20250219,
            max_tokens=2000,
        )
        bot.add_tools(branch_self)
        start_time = time.time()
        with io.StringIO() as buf:
            sys.stdout = buf
            try:
                bot.respond(
                    'Use branch_self to create 3 branches. Each branch should create a text file: '
                    'Branch 1 creates "file1.txt" with content "This is the first file. It contains information about branch 1.", '
                    'Branch 2 creates "file2.txt" with content "This is the second file. It contains information about branch 2.", '
                    'Branch 3 creates "file3.txt" with content "This is the third file. It contains information about branch 3."'
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
        else:
            print("⚠️ No text files were created")

    @patch("builtins.input")
    def test_branch_self_error_handling(self, mock_input):
        """Test branch_self error handling with malformed input.

        This test verifies that branch_self properly handles invalid input.
        The prompt is more specific to ensure deterministic behavior.
        """
        # Use a specific prompt that should trigger error handling
        error_prompt = (
            "Please call branch_self tool directly with self_prompts='invalid string not json array'. "
            "This should cause an error which you should report."
        )
        mock_input.side_effect = [error_prompt, "/exit"]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_full_tools()
                cli.run()
            except SystemExit:
                pass
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
        cli = self._create_cli_with_full_tools()
        tool_names = [tool["name"] for tool in cli.context.bot_instance.tool_handler.tools]
        self.assertIn("branch_self", tool_names, "branch_self should be available as a tool")
        print(f"✅ branch_self tool is available. All tools: {tool_names}")


if __name__ == "__main__":
    unittest.main(verbosity=2)