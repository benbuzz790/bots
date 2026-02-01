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

Per-Bot Tracking:
- Bot-specific metrics isolation for concurrent bot executions
- Use get_bot_cost(bot_id, timestamp) and get_bot_tokens(bot_id, timestamp) for per-bot queries
- Recording functions accept optional bot_id parameter for attribution
- Prevents cost/token stealing between concurrent bots

Example:
    ```python
    from bots.observability import metrics
    import time

    # Record API call with bot_id
    metrics.record_api_call(
        duration=2.5,
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        status="success",
        bot_id="bot_1_abc123"
    )

    # Record cost with bot_id
    metrics.record_cost(
        cost=0.015,
        provider="anthropic",
        model="claude-3-5-sonnet-latest",
        bot_id="bot_1_abc123"
    )

    # Track session totals (global)
    session_start = time.time()
    # ... make API calls ...
    totals = metrics.get_total_tokens(session_start)
    cost = metrics.get_total_cost(session_start)

    # Track per-bot totals
    bot_totals = metrics.get_bot_tokens("bot_1_abc123", session_start)
    bot_cost = metrics.get_bot_cost("bot_1_abc123", session_start)
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

# Track last recorded metrics for CLI display (backward compatibility - global)
_last_recorded_metrics = {"input_tokens": 0, "output_tokens": 0, "cached_tokens": 0, "cost": 0.0, "duration": 0.0}
_metrics_lock = threading.Lock()  # Lock for thread-safe metrics updates

# Metrics history for session tracking (global)
# Each entry is a tuple: (timestamp, input_tokens, output_tokens, cached_tokens, cost)
# This list resets when a new Python process/CLI instance starts
# Used by get_total_tokens() and get_total_cost() to calculate cumulative totals since a given timestamp
_metrics_history: List[Tuple[float, int, int, int, float]] = []

# Per-bot metrics tracking
# Key: bot_id, Value: dict with 'last_metrics' and 'history'
_bot_metrics: Dict[str, Dict] = {}

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
    global _last_recorded_metrics, _metrics_history, _bot_metrics
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
    _bot_metrics = {}


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


def get_bot_tokens(bot_id: str, since_timestamp: float = 0.0) -> Dict[str, int]:
    """Get token usage for a specific bot since a given timestamp.

    This function provides per-bot token isolation for concurrent bot executions.
    Prevents token attribution errors when multiple bots run simultaneously.

    Args:
        bot_id: Unique identifier for the bot
        since_timestamp: Unix timestamp (from time.time()). Only metrics recorded after
                        this time will be included. Defaults to 0.0 (all history).

    Returns:
        dict: Dictionary with keys:
            - 'input': Total input tokens for this bot
            - 'output': Total output tokens for this bot
            - 'cached': Total cached tokens for this bot
            - 'total': Sum of input + output + cached tokens

    Example:
        >>> import time
        >>> session_start = time.time()
        >>> # ... bot makes API calls with bot_id="bot_1" ...
        >>> totals = get_bot_tokens("bot_1", session_start)
        >>> print(f"Bot 1 used {totals['total']} tokens")
    """
    with _metrics_lock:
        if bot_id not in _bot_metrics:
            return {"input": 0, "output": 0, "cached": 0, "total": 0}

        input_total = 0
        output_total = 0
        cached_total = 0

        for timestamp, input_tokens, output_tokens, cached_tokens, _ in _bot_metrics[bot_id]["history"]:
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


def get_bot_cost(bot_id: str, since_timestamp: float = 0.0) -> float:
    """Get total cost for a specific bot since a given timestamp.

    This function provides per-bot cost isolation for concurrent bot executions.
    Prevents cost attribution errors when multiple bots run simultaneously.

    Args:
        bot_id: Unique identifier for the bot
        since_timestamp: Unix timestamp (from time.time()). Only costs recorded after
                        this time will be included. Defaults to 0.0 (all history).

    Returns:
        float: Total cost in USD for this bot since the given timestamp

    Example:
        >>> import time
        >>> session_start = time.time()
        >>> # ... bot makes API calls with bot_id="bot_1" ...
        >>> cost = get_bot_cost("bot_1", session_start)
        >>> print(f"Bot 1 cost: ${cost:.4f}")
    """
    with _metrics_lock:
        if bot_id not in _bot_metrics:
            return 0.0

        cost_total = 0.0

        for timestamp, _, _, _, cost in _bot_metrics[bot_id]["history"]:
            if timestamp > since_timestamp:
                cost_total += cost

        return cost_total


def clear_bot_metrics(bot_id: str):
    """Clear all metrics for a specific bot.

    Use this to reset a bot's metrics tracking, useful when reusing bot IDs
    or cleaning up after bot execution completes.

    Args:
        bot_id: Unique identifier for the bot

    Example:
        >>> clear_bot_metrics("bot_1")
    """
    with _metrics_lock:
        if bot_id in _bot_metrics:
            del _bot_metrics[bot_id]


def get_all_bot_ids() -> List[str]:
    """Get list of all bot IDs that have recorded metrics.

    Returns:
        list: List of bot IDs (strings)

    Example:
        >>> bot_ids = get_all_bot_ids()
        >>> for bot_id in bot_ids:
        ...     cost = get_bot_cost(bot_id)
        ...     print(f"{bot_id}: ${cost:.4f}")
    """
    with _metrics_lock:
        return list(_bot_metrics.keys())


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


def _ensure_bot_metrics(bot_id: str):
    """Internal helper to ensure bot metrics structure exists.

    Must be called with _metrics_lock held.

    Args:
        bot_id: Unique identifier for the bot
    """
    if bot_id not in _bot_metrics:
        _bot_metrics[bot_id] = {
            "last_metrics": {
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "cost": 0.0,
                "duration": 0.0,
            },
            "history": [],
        }


def record_response_time(duration: float, provider: str, model: str, success: bool = True, bot_id: Optional[str] = None):
    """Record bot response time.

    Args:
        duration: Response time in seconds
        provider: Provider name (e.g., "anthropic", "openai", "google")
        model: Model name
        success: Whether the response was successful
        bot_id: Optional bot identifier for per-bot tracking
    """
    if not _initialized or _response_time_histogram is None:
        return

    attributes = {
        "provider": provider,
        "model": model,
        "success": str(success).lower(),
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    _response_time_histogram.record(duration, attributes=attributes)


def record_api_call(duration: float, provider: str, model: str, status: str = "success", bot_id: Optional[str] = None):
    """Record API call metrics.

    Args:
        duration: API call duration in seconds
        provider: Provider name (e.g., "anthropic", "openai", "google")
        model: Model name
        status: Call status ("success", "error", "timeout")
        bot_id: Optional bot identifier for per-bot tracking
    """
    # Update last recorded metrics for CLI display (thread-safe)
    with _metrics_lock:
        _last_recorded_metrics["duration"] = duration

        # Update per-bot metrics if bot_id provided
        if bot_id:
            _ensure_bot_metrics(bot_id)
            _bot_metrics[bot_id]["last_metrics"]["duration"] = duration

    if not _initialized:
        return

    attributes = {
        "provider": provider,
        "model": model,
        "status": status,
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    if _api_call_duration_histogram is not None:
        _api_call_duration_histogram.record(duration, attributes=attributes)

    if _api_calls_counter is not None:
        _api_calls_counter.add(1, attributes=attributes)


def record_tool_execution(duration: float, tool_name: str, success: bool = True, bot_id: Optional[str] = None):
    """Record tool execution metrics.

    Args:
        duration: Tool execution duration in seconds
        tool_name: Name of the tool
        success: Whether the tool execution was successful
        bot_id: Optional bot identifier for per-bot tracking
    """
    if not _initialized:
        return

    attributes = {
        "tool_name": tool_name,
        "success": str(success).lower(),
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    if _tool_execution_duration_histogram is not None:
        _tool_execution_duration_histogram.record(duration, attributes=attributes)

    if _tool_calls_counter is not None:
        _tool_calls_counter.add(1, attributes=attributes)


def record_message_building(duration: float, provider: str, model: str, bot_id: Optional[str] = None):
    """Record message building duration.

    Args:
        duration: Message building duration in seconds
        provider: Provider name
        model: Model name
        bot_id: Optional bot identifier for per-bot tracking
    """
    if not _initialized or _message_building_duration_histogram is None:
        return

    attributes = {
        "provider": provider,
        "model": model,
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    _message_building_duration_histogram.record(duration, attributes=attributes)


def record_tokens(
    input_tokens: int,
    output_tokens: int,
    provider: str,
    model: str,
    cached_tokens: int = 0,
    bot_id: Optional[str] = None,
):
    """Record token usage.

    Args:
        input_tokens: Number of input tokens
        output_tokens: Number of output tokens
        provider: Provider name
        model: Model name
        cached_tokens: Number of cached tokens (optional, default 0)
        bot_id: Optional bot identifier for per-bot tracking
    """
    # Update last recorded metrics for CLI display (thread-safe)
    with _metrics_lock:
        _last_recorded_metrics["input_tokens"] = input_tokens
        _last_recorded_metrics["output_tokens"] = output_tokens
        _last_recorded_metrics["cached_tokens"] = cached_tokens

        # Add to global metrics history for session tracking
        _metrics_history.append(
            (time.time(), input_tokens, output_tokens, cached_tokens, 0.0)  # cost will be recorded separately
        )

        # Update per-bot metrics if bot_id provided
        if bot_id:
            _ensure_bot_metrics(bot_id)
            _bot_metrics[bot_id]["last_metrics"]["input_tokens"] = input_tokens
            _bot_metrics[bot_id]["last_metrics"]["output_tokens"] = output_tokens
            _bot_metrics[bot_id]["last_metrics"]["cached_tokens"] = cached_tokens
            _bot_metrics[bot_id]["history"].append((time.time(), input_tokens, output_tokens, cached_tokens, 0.0))

    if not _initialized or _tokens_used_counter is None:
        return

    attributes_base = {
        "provider": provider,
        "model": model,
    }

    if bot_id:
        attributes_base["bot_id"] = bot_id

    # Record input tokens
    attributes_input = {**attributes_base, "token_type": "input"}
    _tokens_used_counter.add(input_tokens, attributes=attributes_input)

    # Record output tokens
    attributes_output = {**attributes_base, "token_type": "output"}
    _tokens_used_counter.add(output_tokens, attributes=attributes_output)

    # Record cached tokens if provided
    if cached_tokens > 0:
        attributes_cached = {**attributes_base, "token_type": "cached"}
        _tokens_used_counter.add(cached_tokens, attributes=attributes_cached)


def record_cost(cost: float, provider: str, model: str, bot_id: Optional[str] = None):
    """Record cost metrics.

    Args:
        cost: Cost in USD
        provider: Provider name
        model: Model name
        bot_id: Optional bot identifier for per-bot tracking
    """
    # Update last recorded metrics for CLI display (thread-safe)
    with _metrics_lock:
        _last_recorded_metrics["cost"] = cost

        # Add to global metrics history for session tracking
        _metrics_history.append(
            (
                time.time(),
                0,  # input_tokens (recorded separately)
                0,  # output_tokens (recorded separately)
                0,  # cached_tokens (recorded separately)
                cost,
            )
        )

        # Update per-bot metrics if bot_id provided
        if bot_id:
            _ensure_bot_metrics(bot_id)
            _bot_metrics[bot_id]["last_metrics"]["cost"] = cost
            _bot_metrics[bot_id]["history"].append((time.time(), 0, 0, 0, cost))

    if not _initialized:
        return

    attributes = {
        "provider": provider,
        "model": model,
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    if _cost_histogram is not None:
        _cost_histogram.record(cost, attributes=attributes)

    if _cost_counter is not None:
        _cost_counter.add(cost, attributes=attributes)


def record_error(error_type: str, provider: str, operation: str, bot_id: Optional[str] = None):
    """Record error metrics.

    Args:
        error_type: Type of error (exception class name)
        provider: Provider name
        operation: Operation that failed (e.g., "respond", "api_call")
        bot_id: Optional bot identifier for per-bot tracking
    """
    if not _initialized or _errors_counter is None:
        return

    attributes = {
        "provider": provider,
        "error_type": error_type,
        "operation": operation,
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    _errors_counter.add(1, attributes=attributes)


def record_tool_failure(tool_name: str, error_type: str, bot_id: Optional[str] = None):
    """Record tool failure metrics.

    Args:
        tool_name: Name of the tool that failed
        error_type: Type of error (exception class name)
        bot_id: Optional bot identifier for per-bot tracking
    """
    if not _initialized or _tool_failures_counter is None:
        return

    attributes = {
        "tool_name": tool_name,
        "error_type": error_type,
    }

    if bot_id:
        attributes["bot_id"] = bot_id

    _tool_failures_counter.add(1, attributes=attributes)


def get_and_clear_last_metrics(bot_id: Optional[str] = None):
    """Get the last recorded metrics and clear them.

    Args:
        bot_id: Optional bot identifier. If provided, returns and clears bot-specific metrics.
                If None, returns and clears global metrics (backward compatibility).

    Returns:
        dict: Dictionary with keys: input_tokens, output_tokens, cached_tokens, cost, duration
    """
    global _last_recorded_metrics

    # Make a copy and clear atomically (thread-safe)
    with _metrics_lock:
        if bot_id:
            # Per-bot metrics
            if bot_id not in _bot_metrics:
                return {
                    "input_tokens": 0,
                    "output_tokens": 0,
                    "cached_tokens": 0,
                    "cost": 0.0,
                    "duration": 0.0,
                }

            metrics_copy = _bot_metrics[bot_id]["last_metrics"].copy()
            _bot_metrics[bot_id]["last_metrics"] = {
                "input_tokens": 0,
                "output_tokens": 0,
                "cached_tokens": 0,
                "cost": 0.0,
                "duration": 0.0,
            }
        else:
            # Global metrics (backward compatibility)
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
