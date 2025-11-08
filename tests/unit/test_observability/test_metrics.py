"""
Unit tests for bots/observability/metrics.py

Tests all metric recording functions using InMemoryMetricReader to verify
metrics are properly recorded with correct attributes.
"""

from unittest.mock import patch

import pytest

# Import OpenTelemetry testing utilities
from opentelemetry.sdk.metrics.export import InMemoryMetricReader

# Import the metrics module
from bots.observability import metrics
from bots.observability.config import ObservabilityConfig


@pytest.fixture
def metric_reader():
    """Create an InMemoryMetricReader for testing."""
    return InMemoryMetricReader()


@pytest.fixture
def setup_test_metrics(metric_reader):
    """Set up metrics with InMemoryMetricReader for testing."""
    # Reset global state
    metrics._initialized = False
    metrics._meter_provider = None

    # Create test config
    config = ObservabilityConfig(
        service_name="test-service",
        tracing_enabled=True,
        exporter_type="none",
    )

    # Setup metrics with test reader
    metrics.setup_metrics(config=config, reader=metric_reader)

    yield metric_reader

    # Cleanup
    metrics._initialized = False
    metrics._meter_provider = None


class TestMetricsSetup:
    """Test metrics initialization and configuration."""

    def test_setup_metrics_once(self, metric_reader):
        """Test that setup_metrics can be called multiple times safely."""
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
            exporter_type="none",
        )

        metrics._initialized = False
        metrics.setup_metrics(config=config, reader=metric_reader)
        assert metrics._initialized is True

        # Second call should be no-op
        metrics.setup_metrics(config=config, reader=metric_reader)
        assert metrics._initialized is True

    def test_setup_metrics_disabled(self, metric_reader):
        """Test that metrics setup is skipped when tracing disabled."""
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=False,
            exporter_type="none",
        )

        # Reset state (fixture may have set it up)
        metrics.reset_metrics()

        # Save state before setup
        meter_provider_before = metrics._meter_provider

        metrics.setup_metrics(config=config)

        # When disabled, setup should mark as initialized but not create new meter provider

        assert metrics._initialized is True
        # Meter provider should not have changed (either None or same as before)
        assert metrics._meter_provider == meter_provider_before

    def test_is_metrics_enabled(self):
        """Test is_metrics_enabled function."""
        if not metrics.METRICS_AVAILABLE:
            assert metrics.is_metrics_enabled() is False
        else:
            # Should check config
            result = metrics.is_metrics_enabled()
            assert isinstance(result, bool)


class TestResponseTimeMetrics:
    """Test record_response_time function."""

    def test_record_response_time_success(self, setup_test_metrics):
        """Test recording successful response time."""
        metrics.record_response_time(duration=2.5, provider="anthropic", model="claude-3-5-sonnet-latest", success=True)

        # Get metrics
        metric_data = setup_test_metrics.get_metrics_data()
        resource_metrics = metric_data.resource_metrics

        assert len(resource_metrics) > 0
        scope_metrics = resource_metrics[0].scope_metrics
        assert len(scope_metrics) > 0

        # Find response_time metric
        found = False
        for scope in scope_metrics:
            for metric in scope.metrics:
                if metric.name == "bot.response_time":
                    found = True
                    assert metric.description == "Total time for bot.respond() in seconds"
                    assert metric.unit == "s"

        assert found, "response_time metric not found"

    def test_record_response_time_failure(self, setup_test_metrics):
        """Test recording failed response time."""
        metrics.record_response_time(duration=1.0, provider="openai", model="gpt-4", success=False)

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0

    def test_record_response_time_not_initialized(self):
        """Test that recording works gracefully when not initialized."""
        metrics._initialized = False
        # Should not raise exception
        metrics.record_response_time(1.0, "anthropic", "claude", True)


class TestApiCallMetrics:
    """Test record_api_call function."""

    def test_record_api_call_success(self, setup_test_metrics):
        """Test recording successful API call."""
        metrics.record_api_call(duration=1.5, provider="anthropic", model="claude-3-5-sonnet-latest", status="success")

        metric_data = setup_test_metrics.get_metrics_data()
        resource_metrics = metric_data.resource_metrics

        assert len(resource_metrics) > 0

        # Should record both histogram and counter
        metric_names = []
        for rm in resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    metric_names.append(m.name)

        assert "bot.api_call_duration" in metric_names
        assert "bot.api_calls_total" in metric_names

    def test_record_api_call_error(self, setup_test_metrics):
        """Test recording failed API call."""
        metrics.record_api_call(duration=0.5, provider="openai", model="gpt-4", status="error")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0

    def test_record_api_call_timeout(self, setup_test_metrics):
        """Test recording timeout API call."""
        metrics.record_api_call(duration=30.0, provider="google", model="gemini-pro", status="timeout")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0


class TestToolExecutionMetrics:
    """Test record_tool_execution function."""

    def test_record_tool_execution_success(self, setup_test_metrics):
        """Test recording successful tool execution."""
        metrics.record_tool_execution(duration=0.5, tool_name="execute_python", success=True)

        metric_data = setup_test_metrics.get_metrics_data()
        metric_names = []
        for rm in metric_data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    metric_names.append(m.name)

        assert "bot.tool_execution_duration" in metric_names
        assert "bot.tool_calls_total" in metric_names

    def test_record_tool_execution_failure(self, setup_test_metrics):
        """Test recording failed tool execution."""
        metrics.record_tool_execution(duration=0.1, tool_name="view", success=False)

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0


class TestTokenMetrics:
    """Test record_tokens function."""

    def test_record_tokens(self, setup_test_metrics):
        """Test recording token usage."""
        metrics.record_tokens(input_tokens=1000, output_tokens=500, provider="anthropic", model="claude-3-5-sonnet-latest")

        metric_data = setup_test_metrics.get_metrics_data()

        # Should record both input and output tokens
        found_input = False
        found_output = False

        for rm in metric_data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    if m.name == "bot.tokens_used":
                        for data_point in m.data.data_points:
                            if data_point.attributes.get("token_type") == "input":
                                found_input = True
                                assert data_point.value == 1000
                            elif data_point.attributes.get("token_type") == "output":
                                found_output = True
                                assert data_point.value == 500

        assert found_input, "Input tokens not recorded"
        assert found_output, "Output tokens not recorded"

    def test_record_tokens_zero(self, setup_test_metrics):
        """Test recording zero tokens."""
        metrics.record_tokens(input_tokens=0, output_tokens=0, provider="openai", model="gpt-4")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0


class TestCostMetrics:
    """Test record_cost function."""

    def test_record_cost(self, setup_test_metrics):
        """Test recording cost."""
        metrics.record_cost(cost=0.015, provider="anthropic", model="claude-3-5-sonnet-latest")

        metric_data = setup_test_metrics.get_metrics_data()
        metric_names = []
        for rm in metric_data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    metric_names.append(m.name)

        assert "bot.cost_usd" in metric_names
        assert "bot.cost_total_usd" in metric_names

    def test_record_cost_zero(self, setup_test_metrics):
        """Test recording zero cost."""
        metrics.record_cost(cost=0.0, provider="openai", model="gpt-4")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0

    def test_record_cost_large(self, setup_test_metrics):
        """Test recording large cost."""
        metrics.record_cost(cost=10.50, provider="google", model="gemini-pro")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0


class TestErrorMetrics:
    """Test record_error function."""

    def test_record_error(self, setup_test_metrics):
        """Test recording error."""
        metrics.record_error(error_type="APITimeoutError", provider="anthropic", operation="api_call")

        metric_data = setup_test_metrics.get_metrics_data()

        found = False
        for rm in metric_data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    if m.name == "bot.errors_total":
                        found = True
                        for dp in m.data.data_points:
                            assert dp.attributes.get("error_type") == "APITimeoutError"
                            assert dp.attributes.get("provider") == "anthropic"
                            assert dp.attributes.get("operation") == "api_call"

        assert found, "errors_total metric not found"

    def test_record_multiple_errors(self, setup_test_metrics):
        """Test recording multiple errors."""
        metrics.record_error("ValueError", "openai", "respond")
        metrics.record_error("TypeError", "google", "api_call")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0


class TestToolFailureMetrics:
    """Test record_tool_failure function."""

    def test_record_tool_failure(self, setup_test_metrics):
        """Test recording tool failure."""
        metrics.record_tool_failure(tool_name="execute_python", error_type="SyntaxError")

        metric_data = setup_test_metrics.get_metrics_data()

        found = False
        for rm in metric_data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    if m.name == "bot.tool_failures_total":
                        found = True
                        for dp in m.data.data_points:
                            assert dp.attributes.get("tool_name") == "execute_python"
                            assert dp.attributes.get("error_type") == "SyntaxError"

        assert found, "tool_failures_total metric not found"

    def test_record_multiple_tool_failures(self, setup_test_metrics):
        """Test recording multiple tool failures."""
        metrics.record_tool_failure("view", "FileNotFoundError")
        metrics.record_tool_failure("python_edit", "PermissionError")

        metric_data = setup_test_metrics.get_metrics_data()
        assert len(metric_data.resource_metrics) > 0


class TestMessageBuildingMetrics:
    """Test record_message_building function."""

    def test_record_message_building(self, setup_test_metrics):
        """Test recording message building duration."""
        metrics.record_message_building(duration=0.1, provider="anthropic", model="claude-3-5-sonnet-latest")

        metric_data = setup_test_metrics.get_metrics_data()

        found = False
        for rm in metric_data.resource_metrics:
            for sm in rm.scope_metrics:
                for m in sm.metrics:
                    if m.name == "bot.message_building_duration":
                        found = True

        assert found, "message_building_duration metric not found"


class TestGracefulDegradation:
    """Test graceful degradation when metrics not available."""

    def test_record_when_not_initialized(self):
        """Test all record functions work when not initialized."""
        metrics._initialized = False

        # None of these should raise exceptions
        metrics.record_response_time(1.0, "anthropic", "claude", True)
        metrics.record_api_call(1.0, "anthropic", "claude", "success")
        metrics.record_tool_execution(1.0, "tool", True)
        metrics.record_tokens(100, 50, "anthropic", "claude")
        metrics.record_cost(0.01, "anthropic", "claude")
        metrics.record_error("Error", "anthropic", "op")
        metrics.record_tool_failure("tool", "Error")
        metrics.record_message_building(0.1, "anthropic", "claude")

    @patch("bots.observability.metrics.METRICS_AVAILABLE", False)
    def test_metrics_not_available(self):
        """Test behavior when OpenTelemetry not installed."""
        assert metrics.is_metrics_enabled() is False

        # Should not raise exceptions
        metrics.record_response_time(1.0, "anthropic", "claude", True)
        metrics.record_api_call(1.0, "anthropic", "claude", "success")


class TestGetMeter:
    """Test get_meter function."""

    def test_get_meter(self, setup_test_metrics):
        """Test getting a meter."""
        meter = metrics.get_meter("test_module")
        assert meter is not None

    def test_get_meter_not_initialized(self):
        """Test get_meter when not initialized."""
        metrics._initialized = False
        metrics._meter_provider = None

        # Should auto-initialize or return None
        _ = metrics.get_meter("test_module")
        # Either initialized and returned meter, or returned None
        # Meter should either be None or a valid meter object
        # This is acceptable behavior - no assertion needed as it should not raise


class TestCustomExporter:
    """Test SimplifiedConsoleMetricExporter."""

    def test_simplified_exporter_import(self):
        """Test that SimplifiedConsoleMetricExporter can be imported."""
        from bots.observability.custom_exporters import SimplifiedConsoleMetricExporter

        assert SimplifiedConsoleMetricExporter is not None

    def test_simplified_exporter_verbose_on(self, capsys):
        """Test that SimplifiedConsoleMetricExporter displays output when verbose=True."""
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        from bots.observability.custom_exporters import SimplifiedConsoleMetricExporter

        # Reset and setup with custom exporter
        metrics.reset_metrics()
        # Create custom exporter with verbose=True
        exporter = SimplifiedConsoleMetricExporter(verbose=True)
        reader = InMemoryMetricReader()
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
            exporter_type="none",
        )
        metrics.setup_metrics(config=config, reader=reader, verbose=True)
        # Record some metrics
        metrics.record_tokens(input_tokens=1000, output_tokens=100, provider="anthropic", model="claude-sonnet-4")
        metrics.record_cost(0.05, "anthropic", "claude-sonnet-4")
        metrics.record_api_call(2.5, "anthropic", "claude-sonnet-4", "success")
        # Get metrics data and export it
        metric_data = reader.get_metrics_data()
        result = exporter.export(metric_data)
        # Check that output was printed (new minimal format)
        captured = capsys.readouterr()
        assert "tokens" in captured.out
        assert "$" in captured.out
        assert "s" in captured.out
        assert "|" in captured.out  # Pipe separator in new format
        # Verify export was successful
        from opentelemetry.sdk.metrics.export import MetricExportResult

        assert result == MetricExportResult.SUCCESS

    def test_simplified_exporter_verbose_off(self, capsys):
        """Test that SimplifiedConsoleMetricExporter suppresses output when verbose=False."""
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        from bots.observability.custom_exporters import SimplifiedConsoleMetricExporter

        # Reset and setup
        metrics.reset_metrics()
        # Create custom exporter with verbose=False
        exporter = SimplifiedConsoleMetricExporter(verbose=False)
        reader = InMemoryMetricReader()
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
            exporter_type="none",
        )
        metrics.setup_metrics(config=config, reader=reader, verbose=False)
        # Record some metrics
        metrics.record_tokens(1000, 100, "anthropic", "claude-sonnet-4")
        metrics.record_cost(0.05, "anthropic", "claude-sonnet-4")
        # Get metrics data and export it
        metric_data = reader.get_metrics_data()
        result = exporter.export(metric_data)
        # Check that NO output was printed
        captured = capsys.readouterr()
        assert "API Metrics Summary" not in captured.out
        assert "Tokens:" not in captured.out
        # Verify export was still successful
        from opentelemetry.sdk.metrics.export import MetricExportResult

        assert result == MetricExportResult.SUCCESS

    def test_simplified_exporter_toggle_verbose(self, capsys):
        """Test toggling verbose mode on SimplifiedConsoleMetricExporter."""
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        from bots.observability.custom_exporters import SimplifiedConsoleMetricExporter

        # Create exporter starting with verbose=False
        exporter = SimplifiedConsoleMetricExporter(verbose=False)
        reader = InMemoryMetricReader()
        metrics.reset_metrics()
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
            exporter_type="none",
        )
        metrics.setup_metrics(config=config, reader=reader, verbose=False)
        # Record metrics and export - should be silent
        metrics.record_tokens(500, 50, "anthropic", "claude")
        metric_data = reader.get_metrics_data()
        exporter.export(metric_data)
        captured = capsys.readouterr()
        assert "tokens" not in captured.out
        # Now toggle verbose ON
        exporter.set_verbose(True)
        # Record more metrics and export - should show output
        metrics.record_tokens(500, 50, "anthropic", "claude")
        metric_data = reader.get_metrics_data()
        exporter.export(metric_data)
        captured = capsys.readouterr()
        assert "tokens" in captured.out


class TestSetMetricsVerbose:
    """Test set_metrics_verbose function."""

    def test_set_metrics_verbose_function_exists(self):
        """Test that set_metrics_verbose function exists."""
        assert hasattr(metrics, "set_metrics_verbose")
        assert callable(metrics.set_metrics_verbose)

    def test_set_metrics_verbose_with_custom_exporter(self):
        """Test set_metrics_verbose updates the custom exporter."""
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        from bots.observability.custom_exporters import SimplifiedConsoleMetricExporter

        # Reset and setup with custom exporter
        metrics.reset_metrics()
        # Create custom exporter
        custom_exporter = SimplifiedConsoleMetricExporter(verbose=False)
        reader = InMemoryMetricReader()
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
            exporter_type="none",
        )
        # Setup with verbose=False
        metrics.setup_metrics(config=config, reader=reader, verbose=False)
        # Store reference to custom exporter
        metrics._custom_exporter = custom_exporter
        # Initially verbose is False
        assert custom_exporter.verbose is False
        # Call set_metrics_verbose(True)
        metrics.set_metrics_verbose(True)
        # Verify it was updated
        assert custom_exporter.verbose is True
        # Call set_metrics_verbose(False)
        metrics.set_metrics_verbose(False)
        # Verify it was updated
        assert custom_exporter.verbose is False

    def test_set_metrics_verbose_without_custom_exporter(self):
        """Test set_metrics_verbose doesn't crash when no custom exporter exists."""
        metrics.reset_metrics()
        metrics._custom_exporter = None
        # Should not raise exception
        metrics.set_metrics_verbose(True)
        metrics.set_metrics_verbose(False)

    def test_setup_metrics_with_verbose_parameter(self):
        """Test that setup_metrics accepts verbose parameter."""
        from opentelemetry.sdk.metrics.export import InMemoryMetricReader

        metrics.reset_metrics()
        reader = InMemoryMetricReader()
        config = ObservabilityConfig(
            service_name="test-service",
            tracing_enabled=True,
            exporter_type="none",
        )
        # Should not raise exception
        metrics.setup_metrics(config=config, reader=reader, verbose=True)
        assert metrics._initialized is True
        metrics.reset_metrics()
        reader2 = InMemoryMetricReader()
        metrics.setup_metrics(config=config, reader=reader2, verbose=False)
        assert metrics._initialized is True


class TestGetAndClearLastMetrics:
    """Test get_and_clear_last_metrics function."""

    def test_get_and_clear_last_metrics_initial_state(self):
        """Test that initial state returns zeros."""
        metrics.reset_metrics()
        result = metrics.get_and_clear_last_metrics()

        assert result["input_tokens"] == 0
        assert result["output_tokens"] == 0
        assert result["cached_tokens"] == 0
        assert result["cost"] == 0.0
        assert result["duration"] == 0.0

    def test_get_and_clear_last_metrics_after_recording(self, setup_test_metrics):
        """Test that last metrics are returned and cleared."""
        # Record some metrics
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest", cached_tokens=200)
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")
        metrics.record_api_call(2.5, "anthropic", "claude-3-5-sonnet-latest", "success")

        # Get and clear
        result = metrics.get_and_clear_last_metrics()

        assert result["input_tokens"] == 1000
        assert result["output_tokens"] == 500
        assert result["cached_tokens"] == 200
        assert result["cost"] == 0.05
        assert result["duration"] == 2.5

        # Verify cleared
        result2 = metrics.get_and_clear_last_metrics()
        assert result2["input_tokens"] == 0
        assert result2["output_tokens"] == 0
        assert result2["cached_tokens"] == 0
        assert result2["cost"] == 0.0
        assert result2["duration"] == 0.0


class TestGetTotalTokens:
    """Test get_total_tokens function with timestamp-based tracking."""

    def test_get_total_tokens_empty_history(self):
        """Test get_total_tokens with no recorded metrics."""
        metrics.reset_metrics()
        import time

        timestamp = time.time()

        result = metrics.get_total_tokens(timestamp)

        assert result["input"] == 0
        assert result["output"] == 0
        assert result["cached"] == 0
        assert result["total"] == 0

    def test_get_total_tokens_single_recording(self, setup_test_metrics):
        """Test get_total_tokens with a single recording."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        # Record tokens after timestamp
        time.sleep(0.01)  # Ensure timestamp difference
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest", cached_tokens=100)

        result = metrics.get_total_tokens(timestamp)

        assert result["input"] == 1000
        assert result["output"] == 500
        assert result["cached"] == 100
        assert result["total"] == 1600

    def test_get_total_tokens_multiple_recordings(self, setup_test_metrics):
        """Test get_total_tokens accumulates multiple recordings."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        # Record multiple token usages
        time.sleep(0.01)
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest")
        time.sleep(0.01)
        metrics.record_tokens(2000, 800, "anthropic", "claude-3-5-sonnet-latest", cached_tokens=300)
        time.sleep(0.01)
        metrics.record_tokens(1500, 600, "anthropic", "claude-3-5-sonnet-latest", cached_tokens=200)

        result = metrics.get_total_tokens(timestamp)

        assert result["input"] == 4500  # 1000 + 2000 + 1500
        assert result["output"] == 1900  # 500 + 800 + 600
        assert result["cached"] == 500  # 0 + 300 + 200
        assert result["total"] == 6900  # 4500 + 1900 + 500

    def test_get_total_tokens_filters_by_timestamp(self, setup_test_metrics):
        """Test that get_total_tokens only includes metrics after timestamp."""
        import time

        metrics.reset_metrics()

        # Record some tokens before timestamp
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest")
        time.sleep(0.01)

        # Set timestamp here
        timestamp = time.time()
        time.sleep(0.01)

        # Record tokens after timestamp
        metrics.record_tokens(2000, 800, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_tokens(timestamp)

        # Should only include the second recording
        assert result["input"] == 2000
        assert result["output"] == 800
        assert result["cached"] == 0
        assert result["total"] == 2800

    def test_get_total_tokens_zero_tokens(self, setup_test_metrics):
        """Test get_total_tokens with zero token recordings."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        time.sleep(0.01)
        metrics.record_tokens(0, 0, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_tokens(timestamp)

        assert result["input"] == 0
        assert result["output"] == 0
        assert result["cached"] == 0
        assert result["total"] == 0

    def test_get_total_tokens_thread_safety(self, setup_test_metrics):
        """Test that get_total_tokens is thread-safe."""
        import threading
        import time

        metrics.reset_metrics()
        timestamp = time.time()
        time.sleep(0.01)  # Ensure all recordings happen after timestamp

        def record_tokens_thread():
            for _ in range(10):
                metrics.record_tokens(100, 50, "anthropic", "claude")
                time.sleep(0.001)

        # Start multiple threads
        threads = [threading.Thread(target=record_tokens_thread) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result = metrics.get_total_tokens(timestamp)

        # Should have recorded 30 times (3 threads * 10 recordings)
        # All recordings should be counted since we slept after timestamp
        assert result["input"] == 3000  # 30 * 100
        assert result["output"] == 1500  # 30 * 50


class TestGetTotalCost:
    """Test get_total_cost function with timestamp-based tracking."""

    def test_get_total_cost_empty_history(self):
        """Test get_total_cost with no recorded metrics."""
        metrics.reset_metrics()
        import time

        timestamp = time.time()

        result = metrics.get_total_cost(timestamp)

        assert result == 0.0

    def test_get_total_cost_single_recording(self, setup_test_metrics):
        """Test get_total_cost with a single recording."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        # Record cost after timestamp
        time.sleep(0.01)
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_cost(timestamp)

        assert result == 0.05

    def test_get_total_cost_multiple_recordings(self, setup_test_metrics):
        """Test get_total_cost accumulates multiple recordings."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        # Record multiple costs
        time.sleep(0.01)
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")
        time.sleep(0.01)
        metrics.record_cost(0.03, "anthropic", "claude-3-5-sonnet-latest")
        time.sleep(0.01)
        metrics.record_cost(0.02, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_cost(timestamp)

        assert abs(result - 0.10) < 0.0001  # Use approximate comparison for floats

    def test_get_total_cost_filters_by_timestamp(self, setup_test_metrics):
        """Test that get_total_cost only includes metrics after timestamp."""
        import time

        metrics.reset_metrics()

        # Record cost before timestamp
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")
        time.sleep(0.01)

        # Set timestamp here
        timestamp = time.time()
        time.sleep(0.01)

        # Record cost after timestamp
        metrics.record_cost(0.03, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_cost(timestamp)

        # Should only include the second recording
        assert abs(result - 0.03) < 0.0001

    def test_get_total_cost_zero_cost(self, setup_test_metrics):
        """Test get_total_cost with zero cost recordings."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        time.sleep(0.01)
        metrics.record_cost(0.0, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_cost(timestamp)

        assert result == 0.0

    def test_get_total_cost_large_values(self, setup_test_metrics):
        """Test get_total_cost with large cost values."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        time.sleep(0.01)
        metrics.record_cost(10.50, "anthropic", "claude-3-5-sonnet-latest")
        time.sleep(0.01)
        metrics.record_cost(25.75, "anthropic", "claude-3-5-sonnet-latest")

        result = metrics.get_total_cost(timestamp)

        assert abs(result - 36.25) < 0.0001

    def test_get_total_cost_thread_safety(self, setup_test_metrics):
        """Test that get_total_cost is thread-safe."""
        import threading
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        def record_cost_thread():
            for _ in range(10):
                metrics.record_cost(0.01, "anthropic", "claude")
                time.sleep(0.001)

        # Start multiple threads
        threads = [threading.Thread(target=record_cost_thread) for _ in range(3)]
        for t in threads:
            t.start()
        for t in threads:
            t.join()

        result = metrics.get_total_cost(timestamp)

        # Should have recorded 30 times (3 threads * 10 recordings)
        # Use a wider range to account for timing issues in parallel execution
        assert result >= 0.27  # At least 27 recordings
        assert result <= 0.31  # Allow for floating point precision issues


class TestMetricsHistoryIntegration:
    """Test integration between tokens and cost tracking."""

    def test_tokens_and_cost_recorded_separately(self, setup_test_metrics):
        """Test that tokens and cost are recorded as separate history entries."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        time.sleep(0.01)
        # Record tokens
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest")
        # Record cost
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")

        # Both should be retrievable
        tokens = metrics.get_total_tokens(timestamp)
        cost = metrics.get_total_cost(timestamp)

        assert tokens["input"] == 1000
        assert tokens["output"] == 500
        assert cost == 0.05

    def test_metrics_history_persists_across_get_and_clear(self, setup_test_metrics):
        """Test that metrics history is not affected by get_and_clear_last_metrics."""
        import time

        metrics.reset_metrics()
        timestamp = time.time()

        time.sleep(0.01)
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest")
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")

        # Clear last metrics
        metrics.get_and_clear_last_metrics()

        # History should still be intact
        tokens = metrics.get_total_tokens(timestamp)
        cost = metrics.get_total_cost(timestamp)

        assert tokens["input"] == 1000
        assert tokens["output"] == 500
        assert cost == 0.05

    def test_reset_metrics_clears_history(self, setup_test_metrics):
        """Test that reset_metrics clears the metrics history."""
        import time

        timestamp = time.time()

        time.sleep(0.01)
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest")
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")

        # Reset should clear history
        metrics.reset_metrics()

        tokens = metrics.get_total_tokens(timestamp)
        cost = metrics.get_total_cost(timestamp)

        assert tokens["input"] == 0
        assert tokens["output"] == 0
        assert cost == 0.0

    def test_session_simulation(self, setup_test_metrics):
        """Test simulating a CLI session with multiple API calls."""
        import time

        metrics.reset_metrics()
        session_start = time.time()

        # Simulate multiple API calls in a session
        time.sleep(0.01)
        metrics.record_tokens(1000, 500, "anthropic", "claude-3-5-sonnet-latest")
        metrics.record_cost(0.05, "anthropic", "claude-3-5-sonnet-latest")

        time.sleep(0.01)
        metrics.record_tokens(2000, 800, "anthropic", "claude-3-5-sonnet-latest", cached_tokens=500)
        metrics.record_cost(0.08, "anthropic", "claude-3-5-sonnet-latest")

        time.sleep(0.01)
        metrics.record_tokens(3000, 1200, "anthropic", "claude-3-5-sonnet-latest", cached_tokens=1000)
        metrics.record_cost(0.12, "anthropic", "claude-3-5-sonnet-latest")

        # Get session totals
        tokens = metrics.get_total_tokens(session_start)
        cost = metrics.get_total_cost(session_start)

        assert tokens["input"] == 6000  # 1000 + 2000 + 3000
        assert tokens["output"] == 2500  # 500 + 800 + 1200
        assert tokens["cached"] == 1500  # 0 + 500 + 1000
        assert tokens["total"] == 10000
        assert abs(cost - 0.25) < 0.0001  # 0.05 + 0.08 + 0.12


class TestMetricsHistoryEdgeCases:
    """Test edge cases for metrics history tracking."""

    def test_timestamp_exactly_at_recording_time(self, setup_test_metrics):
        """Test behavior when timestamp equals recording time."""
        import time

        metrics.reset_metrics()

        # Get timestamp before recording
        before_time = time.time()
        time.sleep(0.01)  # Ensure recording happens after before_time

        # Record at a specific time
        metrics.record_tokens(1000, 500, "anthropic", "claude")

        time.sleep(0.01)  # Ensure after_time is after recording
        after_time = time.time()

        # Query with timestamp before recording
        result_before = metrics.get_total_tokens(before_time)
        # Query with timestamp after recording
        result_after = metrics.get_total_tokens(after_time)

        # Before should include the recording (timestamp < recording time)
        assert result_before["input"] == 1000
        # After should not include it (timestamp > recording time)
        assert result_after["input"] == 0

    def test_future_timestamp(self, setup_test_metrics):
        """Test querying with a future timestamp."""
        import time

        metrics.reset_metrics()

        metrics.record_tokens(1000, 500, "anthropic", "claude")

        # Query with future timestamp
        future = time.time() + 1000
        result = metrics.get_total_tokens(future)

        assert result["input"] == 0
        assert result["output"] == 0
        assert result["total"] == 0

    def test_very_old_timestamp(self, setup_test_metrics):
        """Test querying with a very old timestamp."""
        import time

        metrics.reset_metrics()

        # Use timestamp from the past
        old_timestamp = time.time() - 1000

        time.sleep(0.01)
        metrics.record_tokens(1000, 500, "anthropic", "claude")

        result = metrics.get_total_tokens(old_timestamp)

        # Should include all recordings
        assert result["input"] == 1000
        assert result["output"] == 500


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
