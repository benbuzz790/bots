"""
Pytest fixtures for OpenTelemetry observability tests.

Provides common fixtures for testing tracing functionality including:
- Mock bots with tracing enabled/disabled
- Span capture utilities
- Environment variable management
- OpenTelemetry setup/teardown
"""

import os

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter


@pytest.fixture
def clean_otel_env(monkeypatch):
    """Clean OpenTelemetry environment variables before test.

    Use when you need a clean slate for environment variable testing.
    Removes all OpenTelemetry-related environment variables.
    """
    monkeypatch.delenv("OTEL_SDK_DISABLED", raising=False)
    monkeypatch.delenv("BOTS_OTEL_EXPORTER", raising=False)
    monkeypatch.delenv("OTEL_SERVICE_NAME", raising=False)
    monkeypatch.delenv("OTEL_EXPORTER_OTLP_ENDPOINT", raising=False)
    yield


@pytest.fixture
def otel_disabled(monkeypatch):
    """Set OTEL_SDK_DISABLED=true for testing disabled state.

    Use when you need to test behavior with OpenTelemetry disabled.
    """
    monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
    yield


@pytest.fixture
def capture_spans():
    """Capture spans for validation in tests.

    Use when you need to inspect spans created during a test.

    Returns:
        InMemorySpanExporter: Exporter that stores spans in memory

    Example:
        def test_span_creation(capture_spans):
            # ... create spans ...
            spans = capture_spans.get_finished_spans()
            assert len(spans) == 1
            assert spans[0].name == "test.span"
    """
    # Create a new tracer provider with in-memory exporter
    exporter = InMemorySpanExporter()
    processor = SimpleSpanProcessor(exporter)
    provider = TracerProvider()
    provider.add_span_processor(processor)

    # Set as global provider
    trace.set_tracer_provider(provider)

    yield exporter

    # Cleanup
    exporter.clear()


@pytest.fixture
def mock_bot_with_tracing():
    """Create a MockBot with tracing enabled.

    Use for unit tests that need to verify tracing behavior without API calls.

    Returns:
        MockBot: Bot instance with tracing enabled
    """
    from bots.testing import MockBot

    bot = MockBot(name="test_bot", enable_tracing=True)
    return bot


@pytest.fixture
def mock_bot_without_tracing():
    """Create a MockBot with tracing disabled.

    Use for unit tests that need to verify no-op behavior when tracing is disabled.

    Returns:
        MockBot: Bot instance with tracing disabled
    """
    from bots.testing import MockBot

    bot = MockBot(name="test_bot", enable_tracing=False)
    return bot


@pytest.fixture
def reset_tracing():
    """Reset tracing state between tests.

    Use when tests modify global tracing state and need isolation.
    """
    # Reset before test runs
    try:
        import bots.observability.tracing as tracing_module

        tracing_module._initialized = False
        tracing_module._tracer_provider = None
    except (ImportError, AttributeError):
        pass

    # Reset OpenTelemetry global state
    from opentelemetry import trace
    from opentelemetry.trace import ProxyTracerProvider

    # Create a fresh ProxyTracerProvider
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE._done = False

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
    trace._TRACER_PROVIDER_SET_ONCE._done = False
