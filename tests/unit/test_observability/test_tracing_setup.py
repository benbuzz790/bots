"""Tests for the tracing setup module.

This module tests the OpenTelemetry tracing setup functionality,
including initialization, configuration, and environment variable handling.
"""

from unittest.mock import Mock

import pytest
from opentelemetry import trace
from opentelemetry.sdk.trace.export import ConsoleSpanExporter


@pytest.fixture
def reset_tracing():
    """Reset OpenTelemetry tracing state before and after each test.

    This fixture ensures that each test starts with a fresh tracing
    configuration by resetting the global tracer provider and module state.
    """
    # Reset BEFORE the test runs
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE = trace.Once()

    # Reset module-level state in bots.observability.tracing
    import bots.observability.tracing as tracing_module

    tracing_module._initialized = False
    tracing_module._tracer_provider = None

    yield

    # Reset AFTER the test runs (cleanup)
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE = trace.Once()
    tracing_module._initialized = False
    tracing_module._tracer_provider = None


class TestTracingSetup:
    """Test suite for tracing setup functionality."""

    def test_is_tracing_enabled_default(self, clean_otel_env, reset_tracing):
        """Test that tracing is enabled by default.

        When no environment variables are set, tracing should be enabled
        by default to encourage observability best practices.
        """
        from bots.observability.tracing import is_tracing_enabled

        assert is_tracing_enabled() is True

    def test_is_tracing_enabled_when_disabled(self, clean_otel_env, reset_tracing, monkeypatch):
        """Test that tracing respects OTEL_SDK_DISABLED environment variable.

        When OTEL_SDK_DISABLED=true, the tracing should be completely disabled
        following OpenTelemetry standard conventions.
        """
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")

        from bots.observability.tracing import is_tracing_enabled

        assert is_tracing_enabled() is False

    def test_is_tracing_enabled_case_insensitive(self, clean_otel_env, reset_tracing, monkeypatch):
        """Test that OTEL_SDK_DISABLED is case-insensitive.

        The environment variable should work with TRUE, True, true, etc.
        """
        test_cases = ["true", "TRUE", "True", "TrUe"]

        from bots.observability.tracing import is_tracing_enabled

        for value in test_cases:
            monkeypatch.setenv("OTEL_SDK_DISABLED", value)
            assert is_tracing_enabled() is False, f"Failed for value: {value}"

    def test_setup_tracing_idempotent(self, clean_otel_env, reset_tracing):
        """Test that calling setup_tracing() multiple times is safe.

        Multiple calls to setup_tracing() should not cause errors or
        duplicate span processors. This is important for module imports.
        """
        from bots.observability.tracing import setup_tracing

        # Should not raise any exceptions
        setup_tracing()
        setup_tracing()
        setup_tracing()

        # Verify tracer provider is set
        provider = trace.get_tracer_provider()
        assert provider is not None

    def test_setup_tracing_with_console_exporter(self, clean_otel_env, reset_tracing):
        """Test that setup_tracing() configures console exporter by default.

        The default configuration should use ConsoleSpanExporter for
        easy debugging during development.
        """
        from bots.observability.tracing import setup_tracing

        setup_tracing()

        provider = trace.get_tracer_provider()
        # Check for TracerProvider-specific attributes (works with ProxyTracerProvider too)
        assert hasattr(provider, "_active_span_processor") or hasattr(provider, "add_span_processor")

        # Verify that span processors were added (if it's a real TracerProvider)
        if hasattr(provider, "_active_span_processor"):
            assert len(provider._active_span_processor._span_processors) > 0

    def test_setup_tracing_with_none_exporter(self, clean_otel_env, reset_tracing):
        """Test that setup_tracing() can be configured with no exporter.

        When exporter=None is passed, no span processor should be added.
        This is useful for testing or when using external configuration.
        """
        from bots.observability.tracing import setup_tracing

        setup_tracing(exporter=None)

        provider = trace.get_tracer_provider()
        # Check for TracerProvider-specific attributes (works with ProxyTracerProvider too)
        assert hasattr(provider, "_active_span_processor") or hasattr(provider, "add_span_processor")

        # Verify no span processors were added
        if hasattr(provider, "_active_span_processor"):
            assert len(provider._active_span_processor._span_processors) == 0

    def test_setup_tracing_respects_disabled_flag(self, clean_otel_env, reset_tracing, monkeypatch):
        """Test that setup_tracing() respects OTEL_SDK_DISABLED.

        When OTEL_SDK_DISABLED=true, setup_tracing() should return early
        without configuring any providers or exporters.
        """
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")

        from bots.observability.tracing import setup_tracing

        setup_tracing()

        # Should get NoOpTracerProvider when disabled
        provider = trace.get_tracer_provider()
        # NoOpTracerProvider doesn't have _active_span_processor
        assert not hasattr(provider, "_active_span_processor")

    def test_get_tracer_returns_tracer(self, clean_otel_env, reset_tracing):
        """Test that get_tracer() returns a valid tracer instance.

        The get_tracer() function should return a tracer that can be
        used to create spans.
        """
        from bots.observability.tracing import get_tracer, setup_tracing

        setup_tracing()
        tracer = get_tracer("test_module")

        assert tracer is not None
        # Verify we can create a span
        with tracer.start_as_current_span("test_span") as span:
            assert span is not None

    def test_get_tracer_auto_initializes(self, clean_otel_env, reset_tracing):
        """Test that get_tracer() works even without explicit setup_tracing() call.

        For convenience, get_tracer() should work even if setup_tracing()
        was never called, using OpenTelemetry's default configuration.
        """
        from bots.observability.tracing import get_tracer

        # Don't call setup_tracing()
        tracer = get_tracer("test_module")

        assert tracer is not None

    def test_get_tracer_with_disabled_sdk(self, clean_otel_env, reset_tracing, monkeypatch):
        """Test that get_tracer() returns NoOp tracer when SDK is disabled.

        When OTEL_SDK_DISABLED=true, get_tracer() should return a NoOp
        tracer that has zero overhead.
        """
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")

        from bots.observability.tracing import get_tracer

        tracer = get_tracer("test_module")

        # NoOp tracer should still work but not record anything
        with tracer.start_as_current_span("test_span") as span:
            # NoOp span should not raise errors
            span.set_attribute("test", "value")

    def test_get_default_tracing_preference_default(self, clean_otel_env, reset_tracing):
        """Test default tracing preference when no env var is set.

        By default, tracing should be enabled (returns True).
        """
        from bots.observability.tracing import get_default_tracing_preference

        assert get_default_tracing_preference() is True

    def test_get_default_tracing_preference_disabled(self, clean_otel_env, reset_tracing, monkeypatch):
        """Test tracing preference with BOTS_ENABLE_TRACING=false.

        When BOTS_ENABLE_TRACING=false, the default preference should be False.
        """
        monkeypatch.setenv("BOTS_ENABLE_TRACING", "false")

        from bots.observability.tracing import get_default_tracing_preference

        assert get_default_tracing_preference() is False

    def test_get_default_tracing_preference_enabled(self, clean_otel_env, reset_tracing, monkeypatch):
        """Test tracing preference with BOTS_ENABLE_TRACING=true.

        When BOTS_ENABLE_TRACING=true, the default preference should be True.
        """
        monkeypatch.setenv("BOTS_ENABLE_TRACING", "true")

        from bots.observability.tracing import get_default_tracing_preference

        assert get_default_tracing_preference() is True

    def test_configure_exporter_console(self, clean_otel_env, reset_tracing):
        """Test runtime configuration of console exporter.

        Should be able to configure the console exporter at runtime.
        """
        from bots.observability.tracing import setup_tracing

        exporter = ConsoleSpanExporter()
        setup_tracing(exporter=exporter)

        provider = trace.get_tracer_provider()
        # Check for TracerProvider-specific attributes (works with ProxyTracerProvider too)
        assert hasattr(provider, "_active_span_processor") or hasattr(provider, "add_span_processor")

    def test_configure_exporter_custom(self, clean_otel_env, reset_tracing):
        """Test runtime configuration with custom exporter.

        Should be able to pass a custom exporter to setup_tracing().
        """
        from bots.observability.tracing import setup_tracing

        # Create a mock exporter
        mock_exporter = Mock()
        mock_exporter.export = Mock(return_value=None)
        mock_exporter.shutdown = Mock(return_value=None)

        setup_tracing(exporter=mock_exporter)

        provider = trace.get_tracer_provider()
        # Check for TracerProvider-specific attributes (works with ProxyTracerProvider too)
        assert hasattr(provider, "_active_span_processor") or hasattr(provider, "add_span_processor")


class TestTracingIntegration:
    """Integration tests for tracing functionality."""

    def test_span_creation_and_attributes(self, clean_otel_env, reset_tracing):
        """Test that spans can be created and attributes can be set.

        This is an integration test verifying the complete flow of
        creating a span and setting attributes on it.
        """
        from bots.observability.tracing import get_tracer, setup_tracing

        setup_tracing()
        tracer = get_tracer("test_integration")

        with tracer.start_as_current_span("test_operation") as span:
            span.set_attribute("test.attribute", "test_value")
            span.set_attribute("test.number", 42)
            span.set_attribute("test.boolean", True)

            # Nested span
            with tracer.start_as_current_span("nested_operation") as nested_span:
                nested_span.set_attribute("nested.attribute", "nested_value")

    def test_span_events(self, clean_otel_env, reset_tracing):
        """Test that span events can be added.

        Span events are useful for marking important points in time
        during an operation.
        """
        from bots.observability.tracing import get_tracer, setup_tracing

        setup_tracing()
        tracer = get_tracer("test_events")

        with tracer.start_as_current_span("test_operation") as span:
            span.add_event("operation.started")
            span.add_event("operation.checkpoint", {"checkpoint": "halfway"})
            span.add_event("operation.completed")

    def test_multiple_tracers(self, clean_otel_env, reset_tracing):
        """Test that multiple tracers can coexist.

        Different modules should be able to get their own tracers
        without interfering with each other.
        """
        from bots.observability.tracing import get_tracer, setup_tracing

        setup_tracing()

        tracer1 = get_tracer("module1")
        tracer2 = get_tracer("module2")

        assert tracer1 is not None
        assert tracer2 is not None

        # Both should work independently
        with tracer1.start_as_current_span("span1"):
            with tracer2.start_as_current_span("span2"):
                pass
