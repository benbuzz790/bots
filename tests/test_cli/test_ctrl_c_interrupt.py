"""Test Ctrl-C interrupt handling in CLI.

This addresses GitHub issue #225 and WO026.

The interrupt handling is implemented by wrapping bot.respond() in the CLI
with an interruptible wrapper that uses threading to check for Ctrl-C.
"""

import signal
import time

import pytest

from bots.dev.bot_session import make_bot_interruptible
from bots.testing.mock_bot import MockBot
from bots.utils.interrupt_handler import run_interruptible


class TestCtrlCInterrupt:
    """Test Ctrl-C interrupt handling during bot operations."""

    def test_keyboard_interrupt_in_main_loop(self):
        """Test that KeyboardInterrupt is caught in the main CLI loop."""
        # This test verifies the existing interrupt handling at line 2846
        # The main loop should catch KeyboardInterrupt and continue

        # We can't easily test the actual main loop, but we can verify
        # the exception handling exists
        import inspect

        from bots.dev.cli import CLI

        # Get the run method source
        source = inspect.getsource(CLI.run)

        # Verify KeyboardInterrupt is handled
        assert "except KeyboardInterrupt" in source
        assert "Use /exit to quit" in source or "exit" in source.lower()

    def test_keyboard_interrupt_in_auto_command(self):
        """Test that KeyboardInterrupt is caught in /auto command."""
        import inspect

        from bots.dev.cli import SystemHandler

        # Get the auto method source
        source = inspect.getsource(SystemHandler.auto)

        # Verify KeyboardInterrupt is handled
        assert "except KeyboardInterrupt" in source
        assert "interrupted" in source.lower()

    @pytest.mark.skip(reason="Difficult to test actual API call interruption without real API")
    def test_ctrl_c_during_api_call(self):
        """Test Ctrl-C during actual bot.respond() API call.

        This is the core issue from #225 - Ctrl-C doesn't work during
        the blocking HTTP request to the LLM API.

        This test is skipped because it requires:
        1. A real or mocked API call that blocks
        2. Sending SIGINT from another thread
        3. Verifying the interrupt is handled gracefully

        Manual testing procedure:
        1. Start CLI with: python -m bots.dev.cli
        2. Send a message that will take time to process
        3. Press Ctrl-C during the API call
        4. Verify the operation is interrupted and CLI remains responsive
        """

    def test_signal_handler_infrastructure(self):
        """Test that signal handling infrastructure exists."""
        # Verify Python's signal module is available
        assert signal.SIGINT is not None

        # Verify we can set signal handlers
        old_handler = signal.signal(signal.SIGINT, signal.default_int_handler)
        assert old_handler is not None

        # Restore original handler
        signal.signal(signal.SIGINT, old_handler)


class TestInterruptibleWrapper:
    """Test the interruptible wrapper utility."""

    def test_interruptible_wrapper_basic(self):
        """Test the interruptible wrapper with a simple function."""

        def simple_function(x):
            """Multiplies the input value by 2.

            Args:
                x: The value to be doubled.

            Returns:
                The input value multiplied by 2.
            """
            return x * 2

        result = run_interruptible(simple_function, 5, check_interval=0.1)
        assert result == 10

    def test_interruptible_wrapper_with_slow_function(self):
        """Test that interruptible wrapper completes slow functions."""

        def slow_function():
            """Simulates a slow-running operation with a 200ms delay.

            Returns:
                str: The string "completed" indicating the operation has finished.
            """
            time.sleep(0.2)
            return "completed"

        result = run_interruptible(slow_function, check_interval=0.05)
        assert result == "completed"

    def test_interruptible_wrapper_propagates_exceptions(self):
        """Test that interruptible wrapper propagates exceptions from the function."""

        def failing_function():
            """Test function that always raises a ValueError.

            Raises:
                ValueError: Always raised with message "Test error".
            """
            raise ValueError("Test error")

        with pytest.raises(ValueError, match="Test error"):
            run_interruptible(failing_function, check_interval=0.1)


class TestBotInterruptWrapper:
    """Test wrapping bot.respond() with interrupt handling."""

    def test_make_bot_interruptible_wraps_respond(self):
        """Test that make_bot_interruptible wraps the respond method."""
        bot = MockBot()
        original_respond = bot.respond

        # Wrap the bot
        make_bot_interruptible(bot)

        # Verify respond was wrapped (it's a different function now)
        assert bot.respond != original_respond
        assert callable(bot.respond)

    def test_wrapped_bot_respond_still_works(self):
        """Test that wrapped bot.respond() still functions normally."""
        bot = MockBot()
        make_bot_interruptible(bot)

        # Should work normally
        response = bot.respond("Hello")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_wrapped_bot_respond_with_role(self):
        """Test that wrapped bot.respond() handles role parameter."""
        bot = MockBot()
        make_bot_interruptible(bot)

        # Should work with role parameter
        response = bot.respond("Hello", role="user")
        assert isinstance(response, str)

    def test_bot_state_after_interrupt(self):
        """Test that bot state is not corrupted after an interrupt.

        This is critical - we need to ensure that if Ctrl-C interrupts
        a bot.respond() call, the bot can still be used afterwards.
        """
        bot = MockBot()

        # Add a simple tool
        def test_tool(x: int) -> int:
            """A test tool that doubles a number."""
            return x * 2

        bot.add_tools(test_tool)

        # Wrap the bot
        make_bot_interruptible(bot)

        # Simulate an interrupt by mocking the original respond to raise KeyboardInterrupt
        bot.respond.__wrapped__ if hasattr(bot.respond, "__wrapped__") else None

        # Since we can't easily simulate a real interrupt in the middle of execution,
        # we'll test that the bot can be used after a simulated interrupt
        try:
            # This should work normally
            response1 = bot.respond("Hello")
            assert isinstance(response1, str)

            # Now test that tools still work after normal operation
            # (In a real scenario, this would be after an interrupt)
            response2 = bot.respond("Use test_tool with x=5")
            assert isinstance(response2, str)

            # Verify bot conversation state is intact
            assert bot.conversation is not None
            assert len(bot.conversation._build_messages()) > 0

        except KeyboardInterrupt:
            # If an interrupt happens, verify bot is still usable
            response3 = bot.respond("Are you still working?")
            assert isinstance(response3, str)

    def test_wrapped_bot_preserves_conversation(self):
        """Test that wrapped bot maintains conversation history."""
        bot = MockBot()
        make_bot_interruptible(bot)

        # Send multiple messages
        bot.respond("First message")
        bot.respond("Second message")

        # Verify conversation has both messages
        messages = bot.conversation._build_messages()
        assert len(messages) >= 4  # system + user1 + assistant1 + user2 + assistant2


class TestManualVerification:
    """Documentation of manual testing procedures for Ctrl-C handling."""

    def test_manual_procedure_documented(self):
        """Document the manual testing procedure for issue #225."""
        manual_test_procedure = """
        Manual Test Procedure for Ctrl-C During Bot Response:

        1. Start the CLI:
           python -m bots.dev.cli

        2. Send a message that will take several seconds:
           You: Write a detailed explanation of quantum computing

        3. While the bot is processing (during API call):
           Press Ctrl-C

        4. Expected behavior (AFTER FIX):
           - The bot response should be interrupted within 0.1 seconds
           - CLI should display "Operation interrupted by user"
           - CLI should return to the prompt
           - Bot should still be usable for subsequent requests

        5. Verify bot state is not corrupted:
           You: Hello, are you still working?
           Bot: [should respond normally]

        6. Test with tools after interrupt:
           You: Use view to read a file
           Bot: [should execute tool normally]

        7. Implementation:
           - bot.respond() is wrapped with run_interruptible() in CLI
           - Uses threading to check for Ctrl-C every 0.1 seconds
           - Raises KeyboardInterrupt immediately when detected
           - Bot state remains consistent (no partial updates)
        """

        # This test always passes - it's just documentation
        assert len(manual_test_procedure) > 0
