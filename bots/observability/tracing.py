"""
OpenTelemetry tracing setup and utilities.

Provides:
- Tracer initialization with configurable exporters
- Environment-based configuration (OTEL_SDK_DISABLED)
- Helper functions for common tracing patterns
"""

import os
from typing import Optional

from opentelemetry import trace
from opentelemetry.sdk.resources import SERVICE_NAME, Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import (
    BatchSpanProcessor,
    ConsoleSpanExporter,
    SimpleSpanProcessor,
    SpanExporter,
)

from bots.observability.config import ObservabilityConfig, load_config_from_env

# Global state
_tracer_provider: Optional[TracerProvider] = None
_initialized: bool = False


def is_tracing_enabled() -> bool:
    """Check if OpenTelemetry tracing is enabled.

    This function reloads the configuration from environment variables
    to ensure it reflects the current state.

    Returns:
        bool: True if tracing is enabled, False otherwise
    """
    # Reload config from environment to catch any changes
    config = load_config_from_env()
    return config.tracing_enabled


def get_default_tracing_preference() -> bool:
    """Get the default tracing preference from environment.

    Checks BOTS_ENABLE_TRACING environment variable (not OTEL_SDK_DISABLED).
    This is used by Bot.__init__ to determine the default tracing state.

    Returns:
        bool: True if tracing should be enabled by default, False otherwise
    """
    return os.getenv("BOTS_ENABLE_TRACING", "true").lower() == "true"


def setup_tracing(config: Optional[ObservabilityConfig] = None, exporter: Optional[SpanExporter] = None) -> None:
    """Initialize OpenTelemetry tracing.

    This function should be called once at application startup.
    It's safe to call multiple times - subsequent calls are no-ops.

    Args:
        config: Optional configuration. If None, uses config from environment.
        exporter: Optional custom exporter. If provided, overrides config.exporter_type.
                 Pass None explicitly to enable tracing without exporting.
    """
    global _tracer_provider, _initialized

    if _initialized:
        return

    if config is None:
        config = load_config_from_env()

    if not config.tracing_enabled:
        # Use NoOp tracer provider (zero overhead)
        _initialized = True
        return

    # Create resource with service name
    resource = Resource(attributes={SERVICE_NAME: config.service_name})

    # Create tracer provider
    _tracer_provider = TracerProvider(resource=resource)

    # Configure exporter based on what was provided
    if exporter is not None:
        # Custom exporter provided - use it
        processor = SimpleSpanProcessor(exporter)
        _tracer_provider.add_span_processor(processor)
    elif config.exporter_type == "console":
        # Console exporter for development
        exp = ConsoleSpanExporter()
        processor = SimpleSpanProcessor(exp)
        _tracer_provider.add_span_processor(processor)
    elif config.exporter_type == "otlp":
        # OTLP exporter for production (requires opentelemetry-exporter-otlp)
        try:
            from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

            exp = OTLPSpanExporter(endpoint=config.otlp_endpoint)
            processor = BatchSpanProcessor(exp)
            _tracer_provider.add_span_processor(processor)
        except ImportError:
            # Fall back to console if OTLP not installed
            exp = ConsoleSpanExporter()
            processor = SimpleSpanProcessor(exp)
            _tracer_provider.add_span_processor(processor)
    elif config.exporter_type == "none":
        # No exporter - tracing is enabled but not exported
        pass

    # Set as global tracer provider
    trace.set_tracer_provider(_tracer_provider)

    _initialized = True


def get_tracer(name: str) -> trace.Tracer:
    """Get a tracer for the given module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        Tracer: OpenTelemetry tracer instance
    """
    # Ensure tracing is set up
    if not _initialized:
        setup_tracing()

    return trace.get_tracer(name)


def configure_exporter(exporter_type: str = None, exporter: SpanExporter = None, **kwargs) -> None:
    """Configure the trace exporter.

    This allows runtime configuration of the exporter.
    Must be called before any tracing occurs.

    Args:
        exporter_type: Type of exporter ('console', 'otlp', 'none')
        exporter: Custom exporter instance (overrides exporter_type)
        **kwargs: Additional arguments for the exporter
    """
    global _initialized, _tracer_provider

    # Reset initialization
    _initialized = False
    _tracer_provider = None

    # Reset the global tracer provider
    trace._TRACER_PROVIDER = None
    trace._TRACER_PROVIDER_SET_ONCE = trace.Once()

    if exporter is not None:
        # Use custom exporter
        setup_tracing(exporter=exporter)
    else:
        # Create new config
        current_config = load_config_from_env()
        config = ObservabilityConfig(
            tracing_enabled=current_config.tracing_enabled,
            exporter_type=exporter_type or current_config.exporter_type,
            otlp_endpoint=kwargs.get("endpoint", current_config.otlp_endpoint),
            service_name=kwargs.get("service_name", current_config.service_name),
        )

        # Re-initialize with new config
        setup_tracing(config)


# Auto-initialize on import (lazy initialization)
# This ensures tracing is ready when first tracer is requested
# If OTEL_SDK_DISABLED=true, this becomes a no-op
