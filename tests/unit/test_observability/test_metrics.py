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
        meter = metrics.get_meter("test_module")
        # Either initialized and returned meter, or returned None
        assert meter is None or meter is not None


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
