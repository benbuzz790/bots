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

# Add the parent directory to the path
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


class TestCLIRealTerminalTimeouts(DetailedTestCase):
    """Integration tests with REAL bot calls to reproduce terminal tool timeouts."""

    def setUp(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        self.timeout_occurred = False
        self.command_duration = 0

    def tearDown(self):
        """Clean up test environment."""
        os.chdir(self.original_cwd)
        # Clean up temp files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

    def _create_cli_with_timeout_monitoring(self):
        """Create CLI instance with terminal tools and timeout monitoring."""
        cli = cli_module.CLI()
        cli.context.bot_instance = AnthropicBot()
        # Only add terminal tools to isolate the issue
        cli.context.bot_instance.add_tools(bots.tools.terminal_tools)
        return cli

    @patch("builtins.input")
    def test_simple_file_creation_real_bot(self, mock_input):
        """Test bot creating simple file - should work quickly."""
        mock_input.side_effect = [
            "Create a simple text file called hello.txt with the content " '"Hello World" using echo command',
            "/exit",
        ]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()

        self.command_duration = time.time() - start_time
        print("\\n=== SIMPLE FILE CREATION TEST ===")
        print(f"Duration: {self.command_duration:.2f} seconds")
        print(f"Output: {output[-500:]}")  # Last 500 chars

        # Should complete quickly
        self.assertLess(self.command_duration, 30, "Simple file creation should not timeout")
        # Check if file was created
        if os.path.exists("hello.txt"):
            print("✅ File created successfully")
        else:
            print("❌ File was not created")

    @patch("builtins.input")
    def test_powershell_here_string_real_bot(self, mock_input):
        """Test bot using PowerShell here-strings - potential timeout pattern."""
        mock_input.side_effect = [
            "Create a Python file called test_script.py using PowerShell "
            "here-strings. The file should contain a function that imports "
            "subprocess and json, with f-strings and encoding parameters "
            'like encoding="utf-8"',
            "/exit",
        ]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()

        self.command_duration = time.time() - start_time
        print("\\n=== POWERSHELL HERE-STRING TEST ===")
        print(f"Duration: {self.command_duration:.2f} seconds")
        print(f"Output: {output[-500:]}")

        # Check for timeout pattern
        if self.command_duration > 60:
            print("🚨 TIMEOUT DETECTED - This matches the original issue!")
            self.timeout_occurred = True
        # Look for timeout indicators in output
        timeout_found = "timeout" in output.lower() or "timed out" in output.lower()
        if timeout_found:
            print("🚨 TIMEOUT MESSAGE FOUND in output")
        # Check if file was created despite timeout
        if os.path.exists("test_script.py"):
            print("✅ File created successfully")
            with open("test_script.py", "r") as f:
                content = f.read()
                print(f"File content preview: {content[:200]}...")
        else:
            print("❌ File was not created")

    @patch("builtins.input")
    def test_complex_python_file_real_bot(self, mock_input):
        """Test bot creating complex Python file with all problematic patterns."""
        complex_prompt = (
            "Create a Python file called complex_script.py using PowerShell. "
            "The file should contain:\n"
            "1. A function with type hints and string defaults like: "
            'func(repo: str = "promptfoo/promptfoo")\n'
            "2. F-strings with complex variables like: "
            'f"repos/{repo}/pulls/{pr_id}/reviews"\n'
            "3. Subprocess calls with encoding='utf-8' and errors='replace'\n"
            "4. Docstrings with quotes inside them\n"
            "5. Import statements for subprocess, json, and re\n"
            "Make it a substantial file, not just a snippet."
        )
        mock_input.side_effect = [
            complex_prompt,
            "/exit",
        ]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()

        self.command_duration = time.time() - start_time
        print("\\n=== COMPLEX PYTHON FILE TEST ===")
        print(f"Duration: {self.command_duration:.2f} seconds")
        print(f"Output: {output[-500:]}")

        # This is the most likely to reproduce the original timeout
        if self.command_duration > 60:
            print("🚨 COMPLEX FILE TIMEOUT - Reproduced the issue!")
            self.timeout_occurred = True
        # Analyze what the bot actually tried to do
        if "function_calls" in output.lower():
            print("✅ Bot attempted to use tools")
        if "@'" in output or "'@" in output:
            print("🎯 Bot used here-strings (potential timeout trigger)")
        if "out-file" in output.lower():
            print("🎯 Bot used Out-File command")
        if "encoding utf8" in output.lower():
            print("🎯 Bot used UTF8 encoding parameter")

    @patch("builtins.input")
    def test_file_creation_progression(self, mock_input):
        """Test increasingly complex file creation to find the breaking point."""
        test_cases = [
            'Create a file with just "hello" using echo',
            "Create a Python file with a simple print statement using PowerShell",
            "Create a Python file with imports and a function using PowerShell here-strings",
            "Create a complex Python file with subprocess, f-strings, and type hints using PowerShell",
        ]
        # We'll test each one and see where it breaks
        for i, prompt in enumerate(test_cases):
            mock_input.side_effect = [prompt, "/exit"]
            start_time = time.time()
            with StringIO() as buf, redirect_stdout(buf):
                try:
                    cli = self._create_cli_with_timeout_monitoring()
                    cli.run()
                except SystemExit:
                    pass
                _ = buf.getvalue()

            duration = time.time() - start_time
            print(f"=== PROGRESSION TEST {i+1} ===")
            print(f"Prompt: {prompt[:60]}...")
            print(f"Duration: {duration:.2f} seconds")
            if duration > 60:
                print(f"🚨 TIMEOUT at test case {i+1}")
                print(f"Breaking point prompt: {prompt}")
                break
            else:
                print(f"✅ Test case {i+1} completed successfully")

    @patch("builtins.input")
    def test_bot_tool_usage_analysis(self, mock_input):
        """Analyze exactly what terminal tool commands the bot generates."""
        mock_input.side_effect = [
            "Show me how to create a Python file with subprocess imports " "using PowerShell, but explain your approach first",
            "/exit",
        ]
        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()
        duration = time.time() - start_time
        print("=== BOT TOOL ANALYSIS TEST ===")
        print(f"Duration: {duration:.2f} seconds")
        print(f"Full output:\n{output}")
        # Extract and analyze the actual PowerShell commands the bot tries to use
        if "execute_powershell" in output:
            print("🔍 Bot used execute_powershell tool")
            # Try to extract the command parameter
            lines = output.split("\n")
            for i, line in enumerate(lines):
                if 'parameter name="command"' in line.lower():
                    # Try to get the next few lines to see the command
                    command_lines = lines[i : i + 10]
                    command_text = chr(10).join(command_lines)
                    print(f"Command being executed:\n{command_text}")
                    break


if __name__ == "__main__":
    # Run with high verbosity to see all the diagnostic output
    unittest.main(verbosity=2)
