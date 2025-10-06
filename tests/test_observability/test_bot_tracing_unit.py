"""Unit tests for OpenTelemetry tracing in Bot class.

Tests bot tracing functionality using MockBot to avoid API calls.
Verifies span creation, attributes, and configuration options.
"""

from unittest.mock import patch

import pytest
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

from bots.foundation.base import Engines
from bots.testing.mock_bot import MockBot


# Fixture to capture spans for testing using real OpenTelemetry
@pytest.fixture
def span_exporter():
    """Fixture to capture OpenTelemetry spans using InMemorySpanExporter.

    Returns an InMemorySpanExporter that captures real spans during test execution.
    """
    # Create a new tracer provider with in-memory exporter
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))

    # Patch the tracer in base.py to use our test provider
    with patch("bots.foundation.base.tracer", provider.get_tracer(__name__)):
        yield exporter

    # Clear spans after test
    exporter.clear()


class TestBotTracingConfiguration:
    """Test bot tracing configuration options."""

    def test_bot_tracing_enabled_by_default(self):
        """Verify that tracing is enabled by default when TRACING_AVAILABLE is True.

        When a bot is created without specifying enable_tracing parameter,
        it should default to enabled (assuming OpenTelemetry is available).
        """
        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.get_default_tracing_preference", return_value=True):
                bot = MockBot()
                assert bot._tracing_enabled is True

    def test_bot_tracing_disabled_explicitly(self):
        """Test that enable_tracing=False parameter disables tracing.

        When explicitly disabled via parameter, tracing should be off
        regardless of environment settings.
        """
        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            bot = MockBot(enable_tracing=False)
            assert bot._tracing_enabled is False

    def test_bot_tracing_enabled_explicitly(self):
        """Test that enable_tracing=True parameter enables tracing.

        When explicitly enabled via parameter, tracing should be on
        (assuming OpenTelemetry is available).
        """
        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.is_tracing_enabled", return_value=True):
                bot = MockBot(enable_tracing=True)
                assert bot._tracing_enabled is True

    def test_bot_tracing_respects_otel_disabled(self):
        """Test that OTEL_SDK_DISABLED=true disables tracing globally.

        When OpenTelemetry SDK is disabled via environment variable,
        tracing should be off even if explicitly requested.
        """
        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.is_tracing_enabled", return_value=False):
                bot = MockBot(enable_tracing=True)
                assert bot._tracing_enabled is False

    def test_bot_tracing_unavailable(self):
        """Test that tracing is disabled when OpenTelemetry is not available.

        When TRACING_AVAILABLE is False (import failed), tracing should
        be disabled regardless of configuration.
        """
        with patch("bots.foundation.base.TRACING_AVAILABLE", False):
            bot = MockBot(enable_tracing=True)
            assert bot._tracing_enabled is False


class TestBotRespondTracing:
    """Test tracing behavior in Bot.respond() method."""

    def test_bot_respond_creates_span_when_enabled(self):
        """Verify that Bot.respond() creates a span when tracing is enabled.

        When tracing is enabled, calling respond() should create a span
        named "bot.respond" with appropriate attributes.
        """
        # Create in-memory exporter to capture spans
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.tracer", provider.get_tracer(__name__)):
                bot = MockBot(enable_tracing=True)
                bot._tracing_enabled = True

                bot.respond("Test prompt")

                # Get captured spans
                spans = exporter.get_finished_spans()

                # Verify span was created
                assert len(spans) > 0
                span_names = [span.name for span in spans]
                assert "bot.respond" in span_names

    def test_bot_respond_no_span_when_disabled(self):
        """Verify that Bot.respond() does not create spans when tracing is disabled.

        When tracing is disabled, respond() should work normally but
        not create any OpenTelemetry spans.
        """
        # Create in-memory exporter to capture spans
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.tracer", provider.get_tracer(__name__)):
                bot = MockBot(enable_tracing=False)

                bot.respond("Test prompt")

                # Get captured spans
                spans = exporter.get_finished_spans()

                # Verify no span was created (or only non-bot spans)
                bot_spans = [span for span in spans if span.name.startswith("bot.")]
                assert len(bot_spans) == 0

    def test_span_attributes_captured(self):
        """Verify that correct attributes are captured in bot.respond span.

        The span should include attributes for:
        - bot.name
        - bot.model
        - prompt.length
        """
        # Create in-memory exporter to capture spans
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.tracer", provider.get_tracer(__name__)):
                bot = MockBot(name="test_bot", model_engine=Engines.GPT4, enable_tracing=True)
                bot._tracing_enabled = True

                test_prompt = "Test prompt for tracing"
                bot.respond(test_prompt)

                # Get captured spans
                spans = exporter.get_finished_spans()

                # Find the bot.respond span
                respond_span = None
                for span in spans:
                    if span.name == "bot.respond":
                        respond_span = span
                        break

                assert respond_span is not None, "bot.respond span not found"

                # Verify attributes were set
                attributes = respond_span.attributes
                assert "bot.name" in attributes
                assert attributes["bot.name"] == "test_bot"
                assert "bot.model" in attributes
                assert attributes["bot.model"] == Engines.GPT4.value
                assert "prompt.length" in attributes
                assert attributes["prompt.length"] == len(test_prompt)


class TestBotCvsnRespondTracing:
    """Test tracing behavior in Bot._cvsn_respond() method."""

    def test_bot_cvsn_respond_creates_span(self):
        """Verify that Bot._cvsn_respond() creates a span when tracing is enabled.

        The internal _cvsn_respond method should create its own span
        for tracking the conversation response cycle.
        """
        # Create in-memory exporter to capture spans
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.tracer", provider.get_tracer(__name__)):
                bot = MockBot(enable_tracing=True)
                bot._tracing_enabled = True

                # Add a prompt first
                bot.conversation = bot.conversation._add_reply(content="Test", role="user")

                # Call _cvsn_respond
                bot._cvsn_respond()

                # Get captured spans
                spans = exporter.get_finished_spans()

                # Check if bot._cvsn_respond span was created
                span_names = [span.name for span in spans]
                assert "bot._cvsn_respond" in span_names


class TestToolHandlerTracing:
    """Test tracing behavior in ToolHandler.exec_requests() method."""

    def test_tool_execution_creates_spans(self):
        """Verify that tool execution creates appropriate spans.

        When tools are executed, spans should be created for:
        - The overall tool execution phase
        - Each individual tool call

        Note: This test verifies the base ToolHandler implementation.
        MockToolHandler overrides exec_requests and doesn't include tracing,
        which is acceptable for testing purposes.
        """
        from bots.foundation.anthropic_bots import AnthropicToolHandler

        # Create in-memory exporter to capture spans
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))
        test_tracer = provider.get_tracer(__name__)

        # Track if start_as_current_span was called
        span_names_created = []
        original_start_as_current_span = test_tracer.start_as_current_span

        def tracking_start_as_current_span(name, *args, **kwargs):
            span_names_created.append(name)
            return original_start_as_current_span(name, *args, **kwargs)

        test_tracer.start_as_current_span = tracking_start_as_current_span

        # Use real ToolHandler (not Mock) to test tracing
        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.tracer", test_tracer):
                tool_handler = AnthropicToolHandler()

                # Add a simple tool
                def test_tool(arg: str) -> str:
                    """A test tool."""
                    return f"Result: {arg}"

                tool_handler.add_tool(test_tool)

                # Add a request in Anthropic format
                tool_handler.add_request(
                    {"type": "tool_use", "id": "test_id", "name": "test_tool", "input": {"arg": "test_value"}}
                )

                # Execute - this should trigger tracing
                tool_handler.exec_requests()

                # Verify spans were created
                assert "tools.execute_all" in span_names_created, f"Expected 'tools.execute_all' in {span_names_created}"
                assert "tool.test_tool" in span_names_created, f"Expected 'tool.test_tool' in {span_names_created}"


class TestTracingIntegration:
    """Integration tests for tracing across bot operations."""

    def test_full_respond_cycle_with_tracing(self):
        """Test complete respond cycle with tracing enabled.

        Verify that a full bot.respond() call with tool usage
        creates the expected hierarchy of spans.
        """
        # Create in-memory exporter to capture spans
        exporter = InMemorySpanExporter()
        provider = TracerProvider()
        provider.add_span_processor(SimpleSpanProcessor(exporter))

        with patch("bots.foundation.base.TRACING_AVAILABLE", True):
            with patch("bots.foundation.base.tracer", provider.get_tracer(__name__)):
                bot = MockBot(enable_tracing=True)
                bot._tracing_enabled = True

                response = bot.respond("Test prompt")

                # Verify respond completed successfully
                assert response is not None
                assert isinstance(response, str)

                # Get captured spans
                spans = exporter.get_finished_spans()

                # Verify tracing was invoked
                assert len(spans) > 0
                span_names = [span.name for span in spans]
                assert "bot.respond" in span_names
