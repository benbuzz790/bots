"""
Unit tests for bots.observability.callbacks module.

Tests the callback system including:
- BotCallbacks abstract base class
- OpenTelemetryCallbacks integration with tracing
- ProgressCallbacks CLI output
- Error handling and graceful degradation
"""

import io
from unittest.mock import MagicMock, Mock, patch

import pytest

from bots.observability.callbacks import (
    TRACING_AVAILABLE,
    BotCallbacks,
    OpenTelemetryCallbacks,
    ProgressCallbacks,
)


class TestBotCallbacks:
    """Test the BotCallbacks abstract base class."""

    def test_bot_callbacks_is_abstract(self):
        """Test that BotCallbacks can be instantiated (all methods have defaults)."""
        # BotCallbacks has default implementations, so it can be instantiated
        callbacks = BotCallbacks()
        assert callbacks is not None

    def test_all_methods_are_no_ops_by_default(self):
        """Test that all callback methods do nothing by default."""
        callbacks = BotCallbacks()

        # Should not raise any exceptions
        callbacks.on_respond_start("test prompt")
        callbacks.on_respond_complete("test response")
        callbacks.on_respond_error(Exception("test"))
        callbacks.on_api_call_start()
        callbacks.on_api_call_complete()
        callbacks.on_api_call_error(Exception("test"))
        callbacks.on_tool_start("test_tool")
        callbacks.on_tool_complete("test_tool", "result")
        callbacks.on_tool_error("test_tool", Exception("test"))
        callbacks.on_step_start("test_step")
        callbacks.on_step_complete("test_step")
        callbacks.on_step_error("test_step", Exception("test"))

    def test_custom_callback_implementation(self):
        """Test that custom callbacks can override methods."""

        class CustomCallbacks(BotCallbacks):
            def __init__(self):
                self.calls = []

            def on_respond_start(self, prompt, metadata=None):
                self.calls.append(("respond_start", prompt))

            def on_tool_start(self, tool_name, metadata=None):
                self.calls.append(("tool_start", tool_name))

        callbacks = CustomCallbacks()
        callbacks.on_respond_start("hello")
        callbacks.on_tool_start("my_tool")

        assert len(callbacks.calls) == 2
        assert callbacks.calls[0] == ("respond_start", "hello")
        assert callbacks.calls[1] == ("tool_start", "my_tool")


class TestOpenTelemetryCallbacks:
    """Test the OpenTelemetryCallbacks implementation."""

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_on_respond_start_adds_event(self):
        """Test that on_respond_start adds an event to the span."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()
            callbacks.on_respond_start("test prompt", {"bot": "test_bot"})

            mock_span.add_event.assert_called_once()
            call_args = mock_span.add_event.call_args
            assert call_args[0][0] == "respond.start"
            assert "prompt.length" in call_args[0][1]
            assert call_args[0][1]["prompt.length"] == 11

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_on_respond_complete_adds_event(self):
        """Test that on_respond_complete adds an event to the span."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()
            callbacks.on_respond_complete("test response", {"duration": 2.5})

            mock_span.add_event.assert_called_once()
            call_args = mock_span.add_event.call_args
            assert call_args[0][0] == "respond.complete"
            assert "response.length" in call_args[0][1]

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_on_respond_error_records_exception(self):
        """Test that on_respond_error records the exception."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()
            error = ValueError("test error")
            callbacks.on_respond_error(error, {"context": "test"})

            mock_span.record_exception.assert_called_once_with(error)
            mock_span.set_attribute.assert_called()

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_on_api_call_complete_sets_attributes(self):
        """Test that on_api_call_complete sets important attributes."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()
            metadata = {"input_tokens": 100, "output_tokens": 50, "cost_usd": 0.015}
            callbacks.on_api_call_complete(metadata)

            # Should add event and set attributes
            mock_span.add_event.assert_called_once()
            assert mock_span.set_attribute.call_count == 3

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_on_tool_start_adds_event(self):
        """Test that on_tool_start adds an event with tool name."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()
            callbacks.on_tool_start("my_tool", {"args": "test"})

            mock_span.add_event.assert_called_once()
            call_args = mock_span.add_event.call_args
            assert call_args[0][0] == "tool.start"
            assert call_args[0][1]["tool.name"] == "my_tool"

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_graceful_degradation_no_span(self):
        """Test that callbacks work gracefully when no span is active."""
        with patch("bots.observability.callbacks.trace.get_current_span", return_value=None):
            callbacks = OpenTelemetryCallbacks()

            # Should not raise exceptions
            callbacks.on_respond_start("test")
            callbacks.on_api_call_complete()
            callbacks.on_tool_start("tool")

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_graceful_degradation_span_not_recording(self):
        """Test that callbacks work gracefully when span is not recording."""
        mock_span = Mock()
        mock_span.is_recording.return_value = False

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()

            # Should not call span methods
            callbacks.on_respond_start("test")
            mock_span.add_event.assert_not_called()


class TestProgressCallbacks:
    """Test the ProgressCallbacks implementation."""

    def test_non_verbose_mode_shows_dots(self):
        """Test that non-verbose mode shows dots."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=False, file=output)

        callbacks.on_respond_start("test")
        callbacks.on_api_call_start()
        callbacks.on_api_call_complete()
        callbacks.on_respond_complete("response")

        result = output.getvalue()
        assert "." in result
        assert result.count(".") == 4

    def test_verbose_mode_shows_details(self):
        """Test that verbose mode shows operation details."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=True, file=output)

        callbacks.on_respond_start("test")
        callbacks.on_api_call_start({"provider": "anthropic"})
        callbacks.on_api_call_complete()
        callbacks.on_respond_complete("response")

        result = output.getvalue()
        assert "[Responding" in result
        assert "anthropic" in result
        assert "✓" in result

    def test_tool_execution_indicators(self):
        """Test that tool execution shows indicators."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=True, file=output)

        callbacks.on_tool_start("my_tool")
        callbacks.on_tool_complete("my_tool", "result")

        result = output.getvalue()
        assert "my_tool" in result
        assert "✓" in result

    def test_step_indicators(self):
        """Test that step execution shows indicators."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=True, file=output)

        callbacks.on_step_start("build_messages")
        callbacks.on_step_complete("build_messages")

        result = output.getvalue()
        assert "build_messages" in result

    def test_non_verbose_tool_shows_dots(self):
        """Test that non-verbose tool execution shows dots."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=False, file=output)

        callbacks.on_tool_start("tool1")
        callbacks.on_tool_complete("tool1", "result")

        result = output.getvalue()
        assert result.count(".") == 2
        assert "tool1" not in result

    def test_metadata_handling(self):
        """Test that callbacks handle metadata gracefully."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=True, file=output)

        # With metadata
        callbacks.on_api_call_start({"provider": "openai", "model": "gpt-4"})
        result = output.getvalue()
        assert "openai" in result

        # Without metadata
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=True, file=output)
        callbacks.on_api_call_start()
        result = output.getvalue()
        assert "API" in result  # Default provider name


class TestCallbackErrorHandling:
    """Test error handling in callbacks."""

    def test_callbacks_dont_break_on_none_metadata(self):
        """Test that callbacks handle None metadata gracefully."""
        callbacks = BotCallbacks()

        # Should not raise
        callbacks.on_respond_start("test", None)
        callbacks.on_api_call_complete(None)
        callbacks.on_tool_start("tool", None)

    @pytest.mark.skipif(not TRACING_AVAILABLE, reason="OpenTelemetry not available")
    def test_otel_callbacks_handle_missing_metadata_keys(self):
        """Test that OpenTelemetryCallbacks handles missing metadata keys."""
        mock_span = Mock()
        mock_span.is_recording.return_value = True

        with patch("bots.observability.callbacks.trace.get_current_span", return_value=mock_span):
            callbacks = OpenTelemetryCallbacks()

            # Metadata without expected keys
            callbacks.on_api_call_complete({"some_other_key": "value"})

            # Should still work
            mock_span.add_event.assert_called_once()

    def test_progress_callbacks_handle_none_result(self):
        """Test that ProgressCallbacks handles None tool results."""
        output = io.StringIO()
        callbacks = ProgressCallbacks(verbose=True, file=output)

        # Should not raise
        callbacks.on_tool_complete("tool", None)
        result = output.getvalue()
        assert "✓" in result
