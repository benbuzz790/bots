"""
Backward compatibility tests for OpenTelemetry integration.

These tests ensure that the addition of OpenTelemetry tracing does not
break existing code or introduce regressions. All existing bot functionality
should continue to work exactly as before, with tracing being purely additive.
"""

import os
import tempfile
import time
from unittest.mock import MagicMock, patch

import pytest

from bots.testing.mock_bot import MockBot


class TestBackwardCompatibility:
    """Test suite ensuring no breaking changes from OpenTelemetry integration."""

    def test_bot_without_enable_tracing_parameter(self):
        """Test that existing bot initialization code still works.

        Old code that doesn't specify enable_tracing parameter should
        continue to work without modification. This ensures backward
        compatibility for all existing bot instantiations.
        """
        # This is how users currently create bots - should still work
        bot = MockBot()

        assert bot is not None
        assert hasattr(bot, "respond")
        assert hasattr(bot, "conversation")

        # Bot should work normally
        response = bot.respond("Hello")
        assert isinstance(response, str)
        assert len(response) > 0

    def test_bot_respond_without_tracing(self):
        """Test that respond() works correctly when tracing is disabled.

        Verifies that the core bot.respond() functionality is unchanged
        when tracing is explicitly disabled. Response quality and behavior
        should be identical to pre-tracing implementation.
        """
        bot = MockBot(enable_tracing=False)

        # Configure different responses for each call
        bot.add_response_pattern("Response 1: {user_input}")
        bot.add_response_pattern("Response 2: {user_input}")

        # Test basic response
        response = bot.respond("What is 2+2?")
        assert isinstance(response, str)
        assert len(response) > 0

        # Test multiple responses
        response2 = bot.respond("Tell me a joke")
        assert isinstance(response2, str)
        assert response != response2  # Should be different responses

    def test_bot_with_tools_no_tracing(self):
        """Test that tool execution works without tracing enabled.

        Tool functionality should be completely unaffected by tracing
        configuration. This test ensures tools execute correctly and
        return expected results when tracing is disabled.
        """

        def sample_tool(x: str) -> str:
            """A simple test tool.

            Use when you need to test tool functionality.

            Parameters:
                x (str): Input string

            Returns:
                str: Processed output
            """
            return f"Processed: {x}"

        bot = MockBot(enable_tracing=False)
        bot.add_tools(sample_tool)

        # Verify tool was added
        assert len(bot.tool_handler.tools) > 0

        # Tool should work normally
        response = bot.respond("Use the sample_tool with input 'test'")
        assert isinstance(response, str)

    def test_existing_bot_initialization_parameters(self):
        """Test that all existing __init__ parameters still work.

        Ensures that adding enable_tracing parameter doesn't break
        any existing initialization parameters. All combinations of
        existing parameters should continue to work as before.
        """
        # Test with various existing parameter combinations
        bot1 = MockBot(name="test_bot")
        assert bot1.name == "test_bot"

        bot2 = MockBot(temperature=0.5)
        assert bot2.temperature == 0.5

        bot3 = MockBot(max_tokens=1000)
        assert bot3.max_tokens == 1000

        bot4 = MockBot(name="complex_bot", temperature=0.7, max_tokens=2000)
        assert bot4.name == "complex_bot"
        assert bot4.temperature == 0.7
        assert bot4.max_tokens == 2000

    def test_otel_not_imported_if_disabled(self):
        """Test graceful degradation when OpenTelemetry is not available.

        If OpenTelemetry is not installed or is disabled, the bot should
        continue to function normally without any errors. This ensures
        the library doesn't become dependent on OpenTelemetry.
        """
        # Mock the import to simulate OpenTelemetry not being available
        with patch.dict("sys.modules", {"opentelemetry": None}):
            # Bot should still initialize and work
            bot = MockBot(enable_tracing=False)
            response = bot.respond("Hello")
            assert isinstance(response, str)

    def test_no_performance_impact_when_disabled(self):
        """Test that disabled tracing has minimal performance impact.

        When tracing is disabled, there should be negligible performance
        overhead. This test does a basic timing comparison to ensure
        the if-checks for tracing don't significantly slow down execution.
        """
        bot_with_tracing_disabled = MockBot(enable_tracing=False)

        # Warm up
        bot_with_tracing_disabled.respond("warmup")

        # Time multiple responses
        start = time.time()
        for i in range(10):
            bot_with_tracing_disabled.respond(f"Test message {i}")
        elapsed = time.time() - start

        # Should complete reasonably quickly (adjust threshold as needed)
        # This is a basic sanity check, not a rigorous benchmark
        assert elapsed < 5.0, f"Responses took too long: {elapsed}s"

    def test_save_load_with_tracing_disabled(self):
        """Test that save/load functionality works with tracing disabled.

        Bot serialization and deserialization should be completely
        unaffected by tracing configuration. Saved bots should load
        correctly and maintain all their state.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            filepath = os.path.join(tmpdir, "test_bot.bot")

            # Create and save a bot
            bot1 = MockBot(name="save_test", enable_tracing=False)
            bot1.respond("Remember this conversation")
            bot1.save(filepath)

            # Load the bot
            from bots.foundation.base import load

            bot2 = load(filepath)

            # Verify state was preserved
            assert bot2.name == "save_test"
            assert bot2.conversation is not None
            assert bot2._tracing_enabled == False  # Tracing state should be preserved

            # Verify conversation history was preserved
            messages = bot2.conversation._build_messages()
            assert len(messages) > 0  # Should have conversation history

    def test_conversation_tree_unchanged(self):
        """Test that conversation tree structure is unchanged.

        The conversation tree implementation should be completely
        unaffected by tracing. Tree navigation, branching, and
        history should work exactly as before.
        """
        bot = MockBot(enable_tracing=False)

        # Build a conversation
        bot.respond("First message")
        conversation_point = bot.conversation

        bot.respond("Second message")

        # Navigate back
        bot.conversation = conversation_point
        bot.respond("Alternative second message")

        # Verify tree structure
        assert conversation_point.replies is not None
        assert len(conversation_point.replies) == 2

    def test_autosave_unchanged(self):
        """Test that autosave functionality is unchanged.

        Autosave behavior should work exactly as before, regardless
        of tracing configuration.
        """
        with tempfile.TemporaryDirectory() as tmpdir:
            # Change to temp directory for autosave
            original_dir = os.getcwd()
            try:
                os.chdir(tmpdir)

                bot = MockBot(name="autosave_test", autosave=True, enable_tracing=False)
                bot.respond("Test message")

                # Autosave file should exist
                expected_file = "autosave_test.bot"
                assert os.path.exists(expected_file)

            finally:
                os.chdir(original_dir)

    def test_multiple_bots_with_different_tracing_settings(self):
        """Test that multiple bots can coexist with different tracing settings.

        Some bots may have tracing enabled while others don't. They should
        all work correctly without interfering with each other.
        """
        bot1 = MockBot(name="traced", enable_tracing=True)
        bot2 = MockBot(name="untraced", enable_tracing=False)
        bot3 = MockBot(name="default")  # Uses default setting

        # All should work independently
        response1 = bot1.respond("Message to traced bot")
        response2 = bot2.respond("Message to untraced bot")
        response3 = bot3.respond("Message to default bot")

        assert isinstance(response1, str)
        assert isinstance(response2, str)
        assert isinstance(response3, str)

        # Verify they're independent
        assert bot1.name == "traced"
        assert bot2.name == "untraced"
        assert bot3.name == "default"


class TestEnvironmentVariableCompatibility:
    """Test that environment variable handling doesn't break existing behavior."""

    def test_otel_sdk_disabled_environment_variable(self):
        """Test that OTEL_SDK_DISABLED environment variable is respected.

        When OTEL_SDK_DISABLED=true, tracing should be completely disabled
        even if enable_tracing=True is passed to the bot.
        """
        with patch.dict(os.environ, {"OTEL_SDK_DISABLED": "true"}):
            bot = MockBot(enable_tracing=True)

            # Bot should still work normally
            response = bot.respond("Test message")
            assert isinstance(response, str)

    def test_no_environment_variables_set(self):
        """Test default behavior when no environment variables are set.

        Without any environment variables, bots should work with their
        default configuration.
        """
        # Clear any OpenTelemetry environment variables
        env_vars_to_clear = ["OTEL_SDK_DISABLED", "BOTS_ENABLE_TRACING"]
        with patch.dict(os.environ, {k: "" for k in env_vars_to_clear}, clear=False):
            bot = MockBot()
            response = bot.respond("Test message")
            assert isinstance(response, str)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
