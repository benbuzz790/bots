import os
import sys
import tempfile
import time
from contextlib import redirect_stdout
from io import StringIO

import pytest

import bots.dev.cli as cli_module
import bots.tools.terminal_tools
from bots import AnthropicBot

pytestmark = pytest.mark.e2e

# Add the parent directory to the path
current_dir = os.path.dirname(os.path.abspath(__file__))
parent_dir = os.path.dirname(current_dir)
sys.path.insert(0, parent_dir)

# Removed - no longer needed after converting to pytest-style


class TestCLIRealTerminalTimeouts:
    """Integration tests with REAL bot calls to reproduce terminal tool timeouts."""

    @pytest.fixture(autouse=True)
    def setup(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)
        self.timeout_occurred = False
        self.command_duration = 0

        yield

        # Teardown
        from tests.unit.test_helpers import cleanup_leaked_files

        # Restore original directory
        os.chdir(self.original_cwd)

        # Clean up temp files
        import shutil

        shutil.rmtree(self.temp_dir, ignore_errors=True)

        # Safety cleanup: remove any files that leaked into original CWD
        leaked_files = [
            "hello.txt",
            "test_script.py",
            "complex_script.py",
            "minimal.py",
            "task_manager.py",
            "subprocess_example.py",
            "problematic_code.py",
            "encoding_test_*.py",
            "bom_test_*.txt",
            "test_utf8.txt",
            "test_accented_chars.txt",
            "test_arrows_and_boxes.txt",
            "test_ascii_quotes.txt",
            "test_smart_quotes.txt",
            "test_symbols.txt",
            "test_python_code_chars.txt",
        ]

        cleanup_leaked_files(self.original_cwd, leaked_files)

    def _create_cli_with_timeout_monitoring(self):
        """Create CLI instance with terminal tools and timeout monitoring."""
        cli = cli_module.CLI()
        cli.context.bot_instance = AnthropicBot()
        # Only add terminal tools to isolate the issue
        cli.context.bot_instance.add_tools(bots.tools.terminal_tools)
        return cli

    def test_simple_file_creation_real_bot(self, monkeypatch):
        """Test bot creating simple file - should work quickly."""
        inputs = iter(
            [
                "Create a simple text file called hello.txt with the content " '"Hello World" using echo command',
                "/exit",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(inputs, "/exit"))

        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()

        self.command_duration = time.time() - start_time
        print("\n=== SIMPLE FILE CREATION TEST ===")
        print(f"Duration: {self.command_duration:.2f} seconds")
        print(f"Output: {output[-500:]}")  # Last 500 chars

        # Should complete quickly
        assert self.command_duration < 30, "Simple file creation should not timeout"
        # Check if file was created
        if os.path.exists("hello.txt"):
            print("File created successfully")
        else:
            print("File was not created")

    def test_powershell_here_string_real_bot(self, monkeypatch):
        """Test bot using PowerShell here-strings - potential timeout pattern."""
        inputs = iter(
            [
                "Create a Python file called test_script.py using PowerShell "
                "here-strings. The file should contain a function that imports "
                "subprocess and json, with f-strings and encoding parameters "
                'like encoding="utf-8"',
                "/exit",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(inputs, "/exit"))

        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()

        self.command_duration = time.time() - start_time
        print("\n=== POWERSHELL HERE-STRING TEST ===")
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
            print("File created successfully")
            with open("test_script.py", "r") as f:
                content = f.read()
                print(f"File content preview: {content[:200]}...")
        else:
            print("File was not created")

    def test_complex_python_file_real_bot(self, monkeypatch):
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
        inputs = iter([complex_prompt, "/exit"])
        monkeypatch.setattr("builtins.input", lambda _: next(inputs, "/exit"))

        start_time = time.time()
        with StringIO() as buf, redirect_stdout(buf):
            try:
                cli = self._create_cli_with_timeout_monitoring()
                cli.run()
            except SystemExit:
                pass
            output = buf.getvalue()

        self.command_duration = time.time() - start_time
        print("\n=== COMPLEX PYTHON FILE TEST ===")
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

    def test_bot_tool_usage_analysis(self, monkeypatch):
        """Analyze exactly what terminal tool commands the bot generates."""
        inputs = iter(
            [
                "Show me how to create a Python file with subprocess imports "
                "using PowerShell, but explain your approach first",
                "/exit",
            ]
        )
        monkeypatch.setattr("builtins.input", lambda _: next(inputs, "/exit"))

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
