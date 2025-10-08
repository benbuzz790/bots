"""Bot-related fixtures for testing.

Provides both mock and real bot instances for different test scenarios,
including OpenTelemetry observability fixtures.
"""

from unittest.mock import MagicMock, Mock

import pytest


@pytest.fixture
def mock_bot_class():
    """Mock bot class for unit tests.

    Returns a mock bot with common methods (respond, add_tools, save, load).
    Used extensively in unit tests to avoid real API calls.
    """
    mock_bot = Mock()
    mock_bot.respond = Mock(return_value="Mock response")
    mock_bot.add_tools = Mock()
    mock_bot.save = Mock()
    mock_bot.load = Mock()
    mock_bot.conversation = Mock()
    mock_bot.tools = []
    return mock_bot


@pytest.fixture
def mock_anthropic_class():
    """Mock AnthropicBot class for unit tests.

    Returns a mock of the AnthropicBot class itself (not an instance).
    Useful for testing code that instantiates bots.
    """
    mock_class = MagicMock()
    mock_instance = Mock()
    mock_instance.respond = Mock(return_value="Mock Anthropic response")
    mock_instance.conversation = Mock()
    mock_class.return_value = mock_instance
    return mock_class


@pytest.fixture
def real_anthropic_bot():
    """Real AnthropicBot instance for integration tests.

    Creates an actual bot instance that makes real API calls.
    Use sparingly and only in integration tests.
    """
    from bots import AnthropicBot

    return AnthropicBot()


@pytest.fixture
def real_openai_bot():
    """Real OpenAIBot instance for integration tests.

    Creates an actual bot instance that makes real API calls.
    Use sparingly and only in integration tests.
    """
    from bots import OpenAIBot

    return OpenAIBot()


@pytest.fixture
def real_gemini_bot():
    """Real GeminiBot instance for integration tests.

    Creates an actual bot instance that makes real API calls.
    Use sparingly and only in integration tests.
    """
    from bots import GeminiBot

    return GeminiBot()


# OpenTelemetry / Observability Fixtures


@pytest.fixture
def mock_tracer_provider():
    """Create a mock tracer provider with in-memory span exporter.

    Use when you need to capture and inspect spans created during tests.
    Returns a tuple of (provider, exporter) for easy span inspection.
    """
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    return provider, exporter


@pytest.fixture
def reset_tracing():
    """Reset tracing state before and after test.

    Use when tests modify global tracing state and need isolation.
    """
    from opentelemetry import trace

    # Reset before test runs
    try:
        import bots.observability.tracing as tracing_module

        tracing_module._initialized = False
        tracing_module._tracer_provider = None
    except (ImportError, AttributeError):
        pass

    # Reset OpenTelemetry global state
    trace._TRACER_PROVIDER = None
    try:
        trace._TRACER_PROVIDER_SET_ONCE._done = False
    except AttributeError:
        # Handle different OpenTelemetry versions
        trace._TRACER_PROVIDER_SET_ONCE = trace.Once()

    yield

    # Reset after test completes
    try:
        import bots.observability.tracing as tracing_module

        tracing_module._initialized = False
        tracing_module._tracer_provider = None
    except (ImportError, AttributeError):
        pass

    # Reset OpenTelemetry global state again
    trace._TRACER_PROVIDER = None
    try:
        trace._TRACER_PROVIDER_SET_ONCE._done = False
    except AttributeError:
        trace._TRACER_PROVIDER_SET_ONCE = trace.Once()


@pytest.fixture
def captured_spans(mock_tracer_provider, reset_tracing):
    """Fixture that provides access to captured spans.

    Use when you need to verify span creation and attributes in tests.
    Automatically clears spans and resets tracing state after each test.
    """
    from opentelemetry import trace

    provider, exporter = mock_tracer_provider

    # Store original state
    original_provider = trace._TRACER_PROVIDER

    trace.set_tracer_provider(provider)
    yield exporter

    # Clean up
    exporter.clear()

    # Restore original provider
    trace._TRACER_PROVIDER = original_provider
    try:
        trace._TRACER_PROVIDER_SET_ONCE._done = False
    except AttributeError:
        trace._TRACER_PROVIDER_SET_ONCE = trace.Once()


@pytest.fixture
def mock_bot_with_tracing():
    """Create a mock bot with tracing enabled.

    Use when you need a bot instance for testing tracing functionality.
    """
    from bots.testing.mock_bot import MockBot

    bot = MockBot(enable_tracing=True)
    bot._tracing_enabled = True
    return bot


@pytest.fixture
def mock_bot_without_tracing():
    """Create a mock bot with tracing disabled.

    Use when you need to verify behavior with tracing turned off.
    """
    from bots.testing.mock_bot import MockBot

    bot = MockBot(enable_tracing=False)
    return bot


@pytest.fixture
def in_memory_span_exporter():
    """Create an in-memory span exporter for testing.

    Use when you need a simple exporter to capture spans without
    setting up a full tracer provider.
    """
    from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter

    return InMemorySpanExporter()


@pytest.fixture
def simple_tracer_provider(in_memory_span_exporter):
    """Create a simple tracer provider with in-memory exporter.

    Use when you need a basic tracer provider for testing without
    complex configuration.
    """
    from opentelemetry.sdk.trace import TracerProvider
    from opentelemetry.sdk.trace.export import SimpleSpanProcessor

    provider = TracerProvider()
    processor = SimpleSpanProcessor(in_memory_span_exporter)
    provider.add_span_processor(processor)
    return provider
