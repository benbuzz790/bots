"""
Metrics collection for the bots framework.

Provides OpenTelemetry metrics for:
- Performance tracking (response times, durations)
- Usage tracking (API calls, tool calls, tokens)
- Cost tracking (USD per operation)
- Error tracking (failures by type)

Session Tracking:
- Timestamp-based metrics history for tracking cumulative usage within a session
- History resets when a new Python process/CLI instance starts
- Use get_total_tokens(timestamp) and get_total_cost(timestamp) to query metrics since a specific time

Example:
    ```python
    from bots.observability import metrics
    import time

    # Record API call
    metrics.record_api_call(
        duration=2.5,
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        status="success"
    )

    # Record cost
    metrics.record_cost(
        cost=0.015,
        provider="anthropic",
        model="claude-3-5-sonnet-latest"
    )

    # Track session totals
    session_start = time.time()
    # ... make API calls ...
    totals = metrics.get_total_tokens(session_start)
    cost = metrics.get_total_cost(session_start)
    ```
"""

import threading
import time
from typing import Dict, List, Optional, Tuple

from bots.observability.config import load_config_from_env

# Try to import OpenTelemetry with graceful degradation
try:
    from opentelemetry import metrics
    from opentelemetry.sdk.metrics import MeterProvider
    from opentelemetry.sdk.metrics.export import (
        ConsoleMetricExporter,
        PeriodicExportingMetricReader,
    )
    from opentelemetry.sdk.resources import SERVICE_NAME, Resource

    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    metrics = None

# Try to import our custom exporter
try:
    from bots.observability.custom_exporters import SimplifiedConsoleMetricExporter

    CUSTOM_EXPORTER_AVAILABLE = True
except ImportError:
    CUSTOM_EXPORTER_AVAILABLE = False
    SimplifiedConsoleMetricExporter = None

# Global state
_meter_provider: Optional[MeterProvider] = None
_initialized: bool = False
_init_lock = threading.Lock()  # Lock for thread-safe initialization
_custom_exporter: Optional[object] = None  # Store reference to custom exporter

# Track last recorded metrics for CLI display
_last_recorded_metrics = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "cost": 0.0, "duration": 0.0}
_metrics_lock = threading.Lock()  # Lock for thread-safe metrics updates

# Metrics history for session tracking
# Each entry is a tuple: (timestamp, input_tokens, output_tokens, cached_tokens, cost)
# This list resets when a new Python process/CLI instance starts
# Used by get_total_tokens() and get_total_cost() to calculate cumulative totals since a given timestamp
_metrics_history: List[Tuple[float, int, int, int, float]] = []

# Metric instruments (initialized after setup)
_response_time_histogram = None
_api_call_duration_histogram = None
_tool_execution_duration_histogram = None
_message_building_duration_histogram = None
_api_calls_counter = None
_tool_calls_counter = None
_tokens_used_counter = None
_cost_histogram = None
_cost_counter = None
_errors_counter = None
_tool_failures_counter = None


def is_metrics_enabled() -> bool:
    """Check if OpenTelemetry metrics are enabled.

    This function reloads the configuration from environment variables
    to ensure it reflects the current state.

    Returns:
        bool: True if metrics are enabled, False otherwise
    """
    if not METRICS_AVAILABLE:
        return False

    # Reload config from environment to catch any changes
    config = load_config_from_env()
    # Honor metrics_enabled if explicitly set, otherwise fall back to tracing_enabled
    if config.metrics_enabled is not None:
        return config.metrics_enabled
    return config.tracing_enabled


def reset_metrics():
    """Reset metrics state for testing purposes.

    This function should only be used in tests to reset the global metrics state
    between test runs. It allows tests to set up fresh metric providers.

    Warning: This is not thread-safe and should only be used in test environments.
    """
    global _last_recorded_metrics, _metrics_history
    global _meter_provider, _initialized, _custom_exporter
    global _response_time_histogram, _api_call_duration_histogram
    global _tool_execution_duration_histogram, _message_building_duration_histogram
    global _api_calls_counter, _tool_calls_counter, _tokens_used_counter
    global _cost_histogram, _cost_counter, _errors_counter, _tool_failures_counter

    # Shutdown existing meter provider if it exists
    if _meter_provider is not None:
        try:
            _meter_provider.shutdown()
        except Exception:
            pass

    # Reset all global state
    _meter_provider = None
    _initialized = False
    _custom_exporter = None
    _response_time_histogram = None
    _api_call_duration_histogram = None
    _tool_execution_duration_histogram = None
    _message_building_duration_histogram = None
    _api_calls_counter = None
    _tool_calls_counter = None
    _tokens_used_counter = None
    _cost_histogram = None
    _cost_counter = None
    _errors_counter = None
    _tool_failures_counter = None
    _last_recorded_metrics = {
        "input_tokens": 0,
        "output_tokens": 0,
        "cached_tokens": 0,
        "cost": 0.0,
        "duration": 0.0,
    }
    _metrics_history = []


def setup_metrics(config=None, reader=None, verbose=False):
    """Initialize OpenTelemetry metrics.

    This function should be called once at application startup.
    It's safe to call multiple times - subsequent calls are no-ops.

    Args:
        config: Optional ObservabilityConfig. If None, loads from environment.
        reader: Optional custom MetricReader. If provided, overrides config.
        verbose: If True, use simplified console output. If False, suppress console output.
    """
    global _meter_provider, _initialized, _custom_exporter
    global _response_time_histogram, _api_call_duration_histogram
    global _tool_execution_duration_histogram, _message_building_duration_histogram
    global _api_calls_counter, _tool_calls_counter, _tokens_used_counter
    global _cost_histogram, _cost_counter, _errors_counter, _tool_failures_counter

    if _initialized:
        return

    if not METRICS_AVAILABLE:
        _initialized = True
        return

    if config is None:
        config = load_config_from_env()

    # Honor metrics_enabled if explicitly set, otherwise fall back to tracing_enabled
    metrics_enabled = config.metrics_enabled if config.metrics_enabled is not None else config.tracing_enabled
    if not metrics_enabled:
        _initialized = True
        return

    # Create resource with service name
    resource = Resource(attributes={SERVICE_NAME: config.service_name})

    # Create metric reader based on exporter type
    if reader is None:
        if config.metrics_exporter_type == "console":
            # Use our custom simplified exporter instead of the default ConsoleMetricExporter
            if CUSTOM_EXPORTER_AVAILABLE:
                _custom_exporter = SimplifiedConsoleMetricExporter(verbose=verbose)
                exporter = _custom_exporter
            else:
                exporter = ConsoleMetricExporter()
            reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
        elif config.metrics_exporter_type == "otlp":
            # OTLP metric exporter (requires opentelemetry-exporter-otlp)
            try:
                from opentelemetry.exporter.otlp.proto.grpc.metric_exporter import (
                    OTLPMetricExporter,
                )

                exporter = OTLPMetricExporter(endpoint=config.otlp_endpoint)
                reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
            except ImportError:
                # Fall back to custom exporter if OTLP not installed
                if CUSTOM_EXPORTER_AVAILABLE:
                    _custom_exporter = SimplifiedConsoleMetricExporter(verbose=verbose)
                    exporter = _custom_exporter
                else:
                    exporter = ConsoleMetricExporter()
                reader = PeriodicExportingMetricReader(exporter, export_interval_millis=60000)
        elif config.metrics_exporter_type == "none":
            # No exporter - metrics are tracked internally but not exported periodically
            # CLI can still display metrics on-demand via get_and_clear_last_metrics()
            reader = None

    # Create meter provider
    if reader:
        _meter_provider = MeterProvider(resource=resource, metric_readers=[reader])
    else:
        _meter_provider = MeterProvider(resource=resource)

    metrics.set_meter_provider(_meter_provider)

    # Initialize metric instruments
    meter = _meter_provider.get_meter(__name__)

    # Performance Metrics (Histograms)
    _response_time_histogram = meter.create_histogram(
        name="bot.response_time",
        description="Total time for bot.respond() in seconds",
        unit="s",
    )

    _api_call_duration_histogram = meter.create_histogram(
        name="bot.api_call_duration",
        description="Time spent in API calls in seconds",
        unit="s",
    )

    _tool_execution_duration_histogram = meter.create_histogram(
        name="bot.tool_execution_duration",
        description="Time spent executing tools in seconds",
        unit="s",
    )

    _message_building_duration_histogram = meter.create_histogram(
        name="bot.message_building_duration",
        description="Time building messages in seconds",
        unit="s",
    )

    # Usage Metrics (Counters)
    _api_calls_counter = meter.create_counter(
        name="bot.api_calls_total",
        description="Total number of API calls",
        unit="1",
    )

    _tool_calls_counter = meter.create_counter(
        name="bot.tool_calls_total",
        description="Total number of tool executions",
        unit="1",
    )

    _tokens_used_counter = meter.create_counter(
        name="bot.tokens_used",
        description="Total tokens used",
        unit="1",
    )

    # Cost Metrics
    _cost_histogram = meter.create_histogram(
        name="bot.cost_usd",
        description="Cost per operation in USD",
        unit="USD",
    )

    _cost_counter = meter.create_counter(
        name="bot.cost_total_usd",
        description="Total cost in USD",
        unit="USD",
    )

    # Error Metrics
    _errors_counter = meter.create_counter(
        name="bot.errors_total",
        description="Total number of errors",
        unit="1",
    )

    _tool_failures_counter = meter.create_counter(
        name="bot.tool_failures_total",
        description="Total number of tool failures",
        unit="1",
    )

    _initialized = True


def get_total_tokens(since_timestamp: float) -> Dict[str, int]:
    """Get total token usage since a given timestamp.

    This function sums all token recordings that occurred after the specified timestamp.
    The metrics history resets when a new Python process/CLI instance starts.

    Args:
        since_timestamp: Unix timestamp (from time.time()). Only metrics recorded after
                        this time will be included in the totals.

    Returns:
        dict: Dictionary with keys:
            - 'input': Total input tokens (represents conversation size in context-aware APIs)
            - 'output': Total output tokens (bot responses)
            - 'cached': Total cached tokens
            - 'total': Sum of input + output + cached tokens

    Example:
        >>> import time
        >>> session_start = time.time()
        >>> # ... make API calls ...
        >>> totals = get_total_tokens(session_start)
        >>> print(f"Input tokens: {totals['input']}")
    """
    with _metrics_lock:
        input_total = 0
        output_total = 0
        cached_total = 0

        for timestamp, input_tokens, output_tokens, cached_tokens, _ in _metrics_history:
            if timestamp > since_timestamp:
                input_total += input_tokens
                output_total += output_tokens
                cached_total += cached_tokens

        return {
            "input": input_total,
            "output": output_total,
            "cached": cached_total,
            "total": input_total + output_total + cached_total,
        }


def get_total_cost(since_timestamp: float) -> float:
    """Get total cost since a given timestamp.

    This function sums all cost recordings that occurred after the specified timestamp.
    The metrics history resets when a new Python process/CLI instance starts.

    Args:
        since_timestamp: Unix timestamp (from time.time()). Only costs recorded after
                        this time will be included in the total.

    Returns:
        float: Total cost in USD since the given timestamp

    Example:
        >>> import time
        >>> session_start = time.time()
        >>> # ... make API calls ...
        >>> total_cost = get_total_cost(session_start)
        >>> print(f"Session cost: ${total_cost:.4f}")
    """
    with _metrics_lock:
        cost_total = 0.0

        for timestamp, _, _, _, cost in _metrics_history:
            if timestamp > since_timestamp:
                cost_total += cost

        return cost_total


def set_metrics_verbose(verbose: bool):
    """Set verbose mode for metrics output.

    Args:
        verbose: If True, display simplified metrics. If False, suppress output.
    """
    if _custom_exporter is not None and hasattr(_custom_exporter, "set_verbose"):
        _custom_exporter.set_verbose(verbose)


def get_meter(name: str):
    """Get a meter for the given module.

    Args:
        name: Name of the module (typically __name__)

    Returns:
        Meter instance, or None if metrics not available
    """
    if not METRICS_AVAILABLE:
        return None

    if not _initialized:
        setup_metrics()

    if _meter_provider is None:
        return None

    return _meter_provider.get_meter(name)


# Helper functions for recording metrics


def record_response_time(duration: float, provider: str, model: str, success: bool = True):
    """Record bot response time.

    Args:
        duration: Response time in seconds
        provider: Provider name (e.g., "anthropic", "openai", "google")
        model: Model name
        success: Whether the response was successful
    """
    if not _initialized or _response_time_histogram is None:
        return

    _response_time_histogram.record(
        duration,
        attributes={
            "provider": provider,
            "model": model,
            "success": str(success).lower(),
        },
    )


def record_api_call(duration: float, provider: str, model: str, status: str = "success"):
    """Record API call metrics.

    Args:
        duration: API call duration in seconds
        provider: Provider name (e.g., "anthropic", "openai", "google")
        model: Model name
        status: Call status ("success", "error", "timeout")
    """
    # Update last recorded metrics for CLI display (thread-safe)
    with _metrics_lock:
        _last_recorded_metrics["duration"] = duration

    if not _initialized:
        return

    if _api_call_duration_histogram is not None:
        _api_call_duration_histogram.record(
            duration,
            attributes={
                "provider": provider,
                "model": model,
                "status": status,
            },
        )

    if _api_calls_counter is not None:
        _api_calls_counter.add(
            1,
            attributes={
                "provider": provider,
                "model": model,
                "status": status,
            },
        )


def record_tool_execution(duration: float, tool_name: str, success: bool = True):
    """Record tool execution metrics.

    Args:
        duration: Tool execution duration in seconds
        tool_name: Name of the tool
        success: Whether the tool execution was successful
    """
    if not _initialized:
        return

    if _tool_execution_duration_histogram is not None:
        _tool_execution_duration_histogram.record(
            duration,
            attributes={
                "tool_name": tool_name,
                "success": str(success).lower(),
            },
        )

    if _tool_calls_counter is not None:
        _tool_calls_counter.add(
            1,
            attributes={
                "tool_name": tool_name,
                "success": str(success).lower(),
            },
        )


def record_message_building(duration: float, provider: str, model: str):
    """Record message building duration.

    Args:
        duration: Message building duration in seconds
        provider: Provider name
        model: Model name
    """
    if not _initialized or _message_building_duration_histogram is None:
        return

    _message_building_duration_histogram.record(
        duration,
        attributes={
            "provider": provider,
            "model": model,
        },
    )


def record_tokens(
    input_tokens: int,
    output_tokens: int,
    provider: str,
    model: str,
    cached_tokens: int = 0,
):
    """Record token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        provider: Provider name
        model: Model name
        cached_tokens: Number of cached tokens (optional, default 0)
    """
    # Update last recorded metrics for CLI display (thread-safe)
    with _metrics_lock:
        _last_recorded_metrics["input_tokens"] = input_tokens
        _last_recorded_metrics["output_tokens"] = output_tokens
        _last_recorded_metrics["cached_tokens"] = cached_tokens

        # Add to metrics history for session tracking
        _metrics_history.append(
            (time.time(), input_tokens, output_tokens, cached_tokens, 0.0)  # cost will be recorded separately
        )

    if not _initialized or _tokens_used_counter is None:
        return

    _tokens_used_counter.add(
        input_tokens,
        attributes={
            "provider": provider,
            "model": model,
            "token_type": "input",
        },
    )

    _tokens_used_counter.add(
        output_tokens,
        attributes={
            "provider": provider,
            "model": model,
            "token_type": "output",
        },
    )

    # Record cached tokens if provided
    if cached_tokens > 0:
        _tokens_used_counter.add(
            cached_tokens,
            attributes={
                "provider": provider,
                "model": model,
                "token_type": "cached",
            },
        )


def record_cost(cost: float, provider: str, model: str):
    """Record cost metrics.

    Args:
        cost: Cost in USD
        provider: Provider name
        model: Model name
    """
    # Update last recorded metrics for CLI display (thread-safe)
    with _metrics_lock:
        _last_recorded_metrics["cost"] = cost

        # Add to metrics history for session tracking
        _metrics_history.append(
            (
                time.time(),
                0,  # input_tokens (recorded separately)
                0,  # output_tokens (recorded separately)
                0,  # cached_tokens (recorded separately)
                cost,
            )
        )

    if not _initialized:
        return

    if _cost_histogram is not None:
        _cost_histogram.record(
            cost,
            attributes={
                "provider": provider,
                "model": model,
            },
        )

    if _cost_counter is not None:
        _cost_counter.add(
            cost,
            attributes={
                "provider": provider,
                "model": model,
            },
        )


def record_error(error_type: str, provider: str, operation: str):
    """Record error metrics.

    Args:
        error_type: Type of error (exception class name)
        provider: Provider name
        operation: Operation that failed (e.g., "respond", "api_call")
    """
    if not _initialized or _errors_counter is None:
        return

    _errors_counter.add(
        1,
        attributes={
            "provider": provider,
            "error_type": error_type,
            "operation": operation,
        },
    )


def record_tool_failure(tool_name: str, error_type: str):
    """Record tool failure metrics.

    Args:
        tool_name: Name of the tool that failed
        error_type: Type of error (exception class name)
    """
    if not _initialized or _tool_failures_counter is None:
        return

    _tool_failures_counter.add(
        1,
        attributes={
            "tool_name": tool_name,
            "error_type": error_type,
        },
    )


def get_and_clear_last_metrics():
    """Get the last recorded metrics and clear them.

    Returns:
        dict: Dictionary with keys: input_tokens, output_tokens, cached_tokens, cost, duration
    """
    global _last_recorded_metrics

    # Make a copy and clear atomically (thread-safe)
    with _metrics_lock:
        metrics_copy = _last_recorded_metrics.copy()
        _last_recorded_metrics = {
            "input_tokens": 0,
            "output_tokens": 0,
            "cached_tokens": 0,
            "cost": 0.0,
            "duration": 0.0,
        }

    return metrics_copy


# Auto-initialize on import (lazy initialization)
# This ensures metrics are ready when first used
# If OTEL_SDK_DISABLED=true, this becomes a no-op
def _lazy_init():
    """Lazy initialization of metrics on first use."""

    if _initialized:
        return

    with _init_lock:
        # Double-check after acquiring lock
        if _initialized:
            return

        try:
            setup_metrics()
        except Exception as e:
            # Log failure but don't crash - metrics become no-ops
            import logging

            logger = logging.getLogger(__name__)
            logger.debug(f"Metrics initialization failed: {e}")


# Call lazy init on import
_lazy_init()
