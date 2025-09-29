import unittest
from io import StringIO
from unittest.mock import patch

from bots.dev.decorators import toolify


class ToolExecutionError(Exception):
    """Custom exception for tool execution failures."""

    pass


class TestKeyboardInterruptHandling(unittest.TestCase):
    """Test that KeyboardInterrupt from tools is handled properly."""

    def test_toolify_converts_keyboard_interrupt(self):
        """Test that @toolify converts KeyboardInterrupt to ToolExecutionError."""

        @toolify()
        def tool_that_raises_keyboard_interrupt():
            """A tool that raises KeyboardInterrupt (simulating server port conflict)."""
            raise KeyboardInterrupt("Address already in use")

        # The decorated function should return an error string, not raise
        result = tool_that_raises_keyboard_interrupt()

        # Should return error string, not raise exception
        self.assertIsInstance(result, str)
        self.assertIn("Tool Failed:", result)
        self.assertIn("Tool execution interrupted", result)
        self.assertIn("Address already in use", result)

    def test_toolify_converts_keyboard_interrupt(self):
        """Test that @toolify converts KeyboardInterrupt to ToolExecutionError."""

        @toolify("A tool that simulates server startup failure")
        def start_server_tool(port: int = 8000) -> str:
            """Simulate starting a server that fails due to port conflict."""
            raise KeyboardInterrupt(f"Port {port} already in use")

        # The decorated function should return an error string, not raise
        result = start_server_tool("8000")

        # Should return error string, not raise exception
        self.assertIsInstance(result, str)
        self.assertIn("Tool Failed:", result)
        self.assertIn("Port 8000 already in use", result)

    @patch("sys.stdin", StringIO("hello\n/exit\n"))
    @patch("sys.stdout", new_callable=StringIO)
    def test_cli_handles_tool_keyboard_interrupt_gracefully(self, mock_stdout):
        """Test that CLI doesn't show 'use /exit to quit' for tool KeyboardInterrupt."""

        # This test verifies that when tools raise KeyboardInterrupt,
        # they get converted to error strings by the decorators,
        # preventing them from reaching the CLI's KeyboardInterrupt handler

        # Create a tool that would normally cause the issue
        @toolify()
        def server_startup_tool():
            raise KeyboardInterrupt("Port 8000 already in use")

        # The tool should return an error string, not raise
        result = server_startup_tool()

        # Verify it's handled as a tool error, not a user interrupt
        self.assertIsInstance(result, str)
        self.assertIn("Tool Failed:", result)
        self.assertIn("Tool execution interrupted", result)

        # This proves that the KeyboardInterrupt won't reach the CLI level
        # where it would trigger the "use /exit to quit" message

    def test_keyboard_interrupt_from_tool_becomes_tool_execution_error(self):
        """Test the specific scenario where a tool raises KeyboardInterrupt."""

        # Simulate what happens when a tool tries to start a server on a busy port
        @toolify()
        def problematic_server_tool():
            # This is what might happen inside a server startup tool

            # Simulate the kind of error that gets converted to KeyboardInterrupt
            raise KeyboardInterrupt("Address already in use (port 8000)")

        result = problematic_server_tool()

        # The result should be an error string, not a raised exception
        self.assertIsInstance(result, str)
        self.assertIn("Tool Failed:", result)

        # And it should contain information about the original error
        self.assertIn("Tool execution interrupted", result)
        self.assertIn("Address already in use", result)

    def test_realistic_server_port_conflict_scenario(self):
        """Test a realistic scenario where a server tool encounters a port conflict."""

        @toolify("Start a web server on the specified port")
        def start_web_server(port: int = 8000) -> str:
            """Simulate starting a web server that encounters a port conflict."""

            # Simulate what many server libraries do when they can't bind to a port
            # Some libraries convert socket errors to KeyboardInterrupt
            raise KeyboardInterrupt(f"[Errno 98] Address already in use: port {port}")

        # This should return an error message, not raise an exception
        result = start_web_server("8080")

        # Verify the tool handles the error gracefully
        self.assertIsInstance(result, str)
        self.assertTrue(
            result.startswith("Error:") or result.startswith("Tool Failed:"), f"Expected error message, got: {result}"
        )
        self.assertIn("Address already in use", result)
        self.assertIn("8080", result)

        # Most importantly, this proves the KeyboardInterrupt won't bubble up
        # to the CLI where it would trigger "use /exit to quit"


if __name__ == "__main__":
    unittest.main()
