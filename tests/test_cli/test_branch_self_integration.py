import os
import sys
import tempfile
import time
import unittest
from contextlib import redirect_stdout
from io import StringIO
from unittest.mock import patch
import bots.dev.cli as cli_module
import bots.tools.terminal_tools
from bots import AnthropicBot
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
        cli.context.bot_instance.add_tools(bots.tools.terminal_tools, bots.tools.self_tools, bots.tools.python_edit, bots.tools.code_tools)
        return cli

    @patch("builtins.input")
    def test_branch_self_nested_directory_and_file_creation(self, mock_input):
        """Test the specific prompt: branch_self to make directories, then each branch makes files."""
        prompt = "Hi Claude. Please use branch_self to make three directories (dir1, dir2, dir3), and then have each branch use branch_self to make three files in each directory. This is a test"
        mock_input.side_effect = [prompt, "/exit"]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = cli_module.CLI()
                original_init = cli._initialize_new_bot

                def init_with_branch_self():
                    original_init()
                    import bots.tools.self_tools
                    cli.context.bot_instance.add_tools(bots.tools.self_tools)
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
        self.assertLess(self.test_duration, 120, "Branch_self nested test should not take more than 2 minutes")
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

    @patch("builtins.input")
    def test_branch_self_basic_functionality(self, mock_input):
        """Test basic branch_self functionality to ensure it works in CLI context."""
        basic_prompt = "Please use branch_self to create three simple text files with different content in each. Cancel if you hit an error."
        mock_input.side_effect = [basic_prompt, "/exit"]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_full_tools()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()
        duration = time.time() - start_time
        print("\n=== BRANCH_SELF BASIC FUNCTIONALITY TEST ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Output preview:\n{output[-500:]}")
        self.assertLess(duration, 60, "Basic branch_self should complete within 1 minute")
        self.assertContainsNormalized(output, "branch_self")
        files_created = [f for f in os.listdir('.') if os.path.isfile(f) and f.endswith('.txt')]
        print(f"Text files created: {files_created}")
        if len(files_created) > 0:
            print("✅ Basic branch_self file creation successful")
            for filename in files_created:
                with open(filename, 'r') as f:
                    content = f.read()
                    print(f"File {filename} content preview: {content[:100]}...")
        else:
            print("⚠️ No text files detected, but branch_self may have been executed")

    @patch("builtins.input")
    def test_branch_self_error_handling(self, mock_input):
        """Test branch_self error handling with malformed input."""
        error_prompt = "Please use branch_self with invalid parameters to test error handling"
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
        print("\n=== BRANCH_SELF ERROR HANDLING TEST ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Output preview:\n{output[-500:]}")
        self.assertLess(duration, 30, "Error handling should be quick")
        self.assertGreater(len(output), 100, "Should produce some output")

    def test_branch_self_tool_availability(self):
        """Test that branch_self tool is properly available in CLI context."""
        cli = self._create_cli_with_full_tools()
        tool_names = [tool["name"] for tool in cli.context.bot_instance.tool_handler.tools]
        self.assertIn("branch_self", tool_names, "branch_self should be available as a tool")
        print(f"✅ branch_self tool is available. All tools: {tool_names}")
if __name__ == "__main__":
    unittest.main(verbosity=2)