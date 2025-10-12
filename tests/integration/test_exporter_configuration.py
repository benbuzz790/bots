"""
Integration tests for OpenTelemetry exporter configuration.

Tests the configuration system for different exporters including:
- Console exporter (development)
- OTLP exporter (production)
- Jaeger exporter (optional)
- Environment variable handling
- Runtime exporter switching

Test Coverage:
    - Console exporter setup and operation
    - OTLP exporter configuration
    - Jaeger exporter configuration
    - Environment variable parsing
    - Exporter switching at runtime
    - Configuration validation
    - Graceful degradation when exporters unavailable
"""

import os
import unittest
from unittest.mock import patch

from bots.observability import metrics, tracing
from bots.observability.config import ObservabilityConfig, load_config_from_env


class TestExporterConfiguration(unittest.TestCase):
    """Integration tests for exporter configuration."""

    def setUp(self):
        """Set up test environment."""
        # Save original environment
        self.original_env = os.environ.copy()

        # Reset tracing and metrics state
        tracing._initialized = False
        tracing._tracer_provider = None
        metrics.reset_metrics()

    def tearDown(self):
        """Clean up test environment."""
        # Restore original environment
        os.environ.clear()
        os.environ.update(self.original_env)

        # Reset state
        tracing._initialized = False
        tracing._tracer_provider = None
        metrics.reset_metrics()

    def test_console_exporter_configuration(self):
        """Test console exporter configuration from environment."""
        os.environ["BOTS_OTEL_EXPORTER"] = "console"
        os.environ["OTEL_SERVICE_NAME"] = "test-service"

        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)
        self.assertEqual(config.exporter_type, "console")
        self.assertEqual(config.service_name, "test-service")

    def test_otlp_exporter_configuration(self):
        """Test OTLP exporter configuration from environment."""
        os.environ["BOTS_OTEL_EXPORTER"] = "otlp"
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = "http://localhost:4317"
        os.environ["OTEL_SERVICE_NAME"] = "bots-prod"

        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)
        self.assertEqual(config.exporter_type, "otlp")
        self.assertEqual(config.otlp_endpoint, "http://localhost:4317")
        self.assertEqual(config.service_name, "bots-prod")

    def test_jaeger_exporter_configuration(self):
        """Test Jaeger exporter configuration from environment."""
        os.environ["BOTS_OTEL_EXPORTER"] = "jaeger"
        os.environ["OTEL_EXPORTER_JAEGER_ENDPOINT"] = "http://localhost:14268/api/traces"

        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)
        self.assertEqual(config.exporter_type, "jaeger")
        self.assertEqual(config.jaeger_endpoint, "http://localhost:14268/api/traces")

    def test_none_exporter_configuration(self):
        """Test 'none' exporter configuration (tracing enabled but not exported)."""
        os.environ["BOTS_OTEL_EXPORTER"] = "none"

        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)
        self.assertEqual(config.exporter_type, "none")

    def test_disabled_tracing_configuration(self):
        """Test disabling tracing via OTEL_SDK_DISABLED."""
        os.environ["OTEL_SDK_DISABLED"] = "true"

        config = load_config_from_env()

        self.assertFalse(config.tracing_enabled)

    def test_metrics_exporter_configuration(self):
        """Test metrics exporter configuration."""
        os.environ["BOTS_OTEL_METRICS_EXPORTER"] = "otlp"
        os.environ["BOTS_OTEL_METRICS_ENABLED"] = "true"

        config = load_config_from_env()

        self.assertTrue(config.metrics_enabled)
        self.assertEqual(config.metrics_exporter_type, "otlp")

    def test_metrics_follows_tracing_by_default(self):
        """Test that metrics_enabled follows tracing_enabled when not explicitly set."""
        os.environ["OTEL_SDK_DISABLED"] = "false"
        # Don't set BOTS_OTEL_METRICS_ENABLED

        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)
        self.assertIsNone(config.metrics_enabled)  # None means follow tracing

    def test_metrics_can_be_disabled_independently(self):
        """Test that metrics can be disabled while tracing is enabled."""
        os.environ["OTEL_SDK_DISABLED"] = "false"
        os.environ["BOTS_OTEL_METRICS_ENABLED"] = "false"

        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)
        self.assertFalse(config.metrics_enabled)

    def test_environment_variable_case_insensitivity(self):
        """Test that boolean environment variables are case-insensitive."""
        os.environ["OTEL_SDK_DISABLED"] = "TRUE"

        config = load_config_from_env()

        self.assertFalse(config.tracing_enabled)

        os.environ["OTEL_SDK_DISABLED"] = "False"
        config = load_config_from_env()

        self.assertTrue(config.tracing_enabled)

    def test_empty_string_environment_variables(self):
        """Test handling of empty string environment variables."""
        os.environ["BOTS_OTEL_EXPORTER"] = ""
        os.environ["OTEL_SERVICE_NAME"] = ""

        config = load_config_from_env()

        # Empty strings should use defaults
        self.assertEqual(config.exporter_type, "none")  # Changed from "console" to "none"
        self.assertEqual(config.service_name, "bots")

    def test_whitespace_environment_variables(self):
        """Test handling of whitespace-only environment variables."""
        os.environ["BOTS_OTEL_EXPORTER"] = "  "
        os.environ["OTEL_SERVICE_NAME"] = "  "

        config = load_config_from_env()

        # Whitespace should be stripped and defaults used
        self.assertEqual(config.exporter_type, "none")  # Changed from "console" to "none"
        self.assertEqual(config.service_name, "bots")

    def test_console_exporter_setup(self):
        """Test that console exporter can be set up successfully."""
        config = ObservabilityConfig(tracing_enabled=True, exporter_type="console", service_name="test-console")

        # Should not raise any errors
        tracing.setup_tracing(config)

        self.assertTrue(tracing._initialized)

    def test_otlp_exporter_fallback_to_console(self):
        """Test that OTLP exporter falls back to console when package not available."""
        config = ObservabilityConfig(
            tracing_enabled=True, exporter_type="otlp", otlp_endpoint="http://localhost:4317", service_name="test-otlp"
        )

        # Mock the OTLP import to fail
        with patch.dict("sys.modules", {"opentelemetry.exporter.otlp.proto.grpc.trace_exporter": None}):
            # Should fall back to console exporter without errors
            tracing.setup_tracing(config)

            self.assertTrue(tracing._initialized)

    def test_none_exporter_setup(self):
        """Test that 'none' exporter sets up tracing without exporting."""
        config = ObservabilityConfig(tracing_enabled=True, exporter_type="none", service_name="test-none")

        tracing.setup_tracing(config)

        self.assertTrue(tracing._initialized)
        self.assertIsNotNone(tracing._tracer_provider)

    def test_disabled_tracing_setup(self):
        """Test that disabled tracing doesn't initialize provider."""
        config = ObservabilityConfig(tracing_enabled=False, exporter_type="console", service_name="test-disabled")

        tracing.setup_tracing(config)

        self.assertTrue(tracing._initialized)
        self.assertIsNone(tracing._tracer_provider)

    def test_metrics_console_exporter_setup(self):
        """Test that metrics console exporter can be set up successfully."""
        config = ObservabilityConfig(
            tracing_enabled=True,
            exporter_type="console",
            metrics_enabled=True,
            metrics_exporter_type="console",
            service_name="test-metrics-console",
        )

        # Should not raise any errors
        metrics.setup_metrics(config)

        self.assertTrue(metrics._initialized)

    def test_metrics_otlp_exporter_fallback(self):
        """Test that metrics OTLP exporter falls back to console when unavailable."""
        config = ObservabilityConfig(
            tracing_enabled=True,
            exporter_type="console",
            metrics_enabled=True,
            metrics_exporter_type="otlp",
            otlp_endpoint="http://localhost:4317",
            service_name="test-metrics-otlp",
        )

        # Mock the OTLP import to fail
        with patch.dict("sys.modules", {"opentelemetry.exporter.otlp.proto.grpc.metric_exporter": None}):
            # Should fall back to console exporter without errors
            metrics.setup_metrics(config)

            self.assertTrue(metrics._initialized)

    def test_metrics_none_exporter_setup(self):
        """Test that 'none' metrics exporter sets up metrics without exporting."""
        config = ObservabilityConfig(
            tracing_enabled=True,
            exporter_type="console",
            metrics_enabled=True,
            metrics_exporter_type="none",
            service_name="test-metrics-none",
        )

        metrics.setup_metrics(config)

        self.assertTrue(metrics._initialized)
        self.assertIsNotNone(metrics._meter_provider)

    def test_runtime_exporter_switching(self):
        """Test switching exporters at runtime using configure_exporter."""
        # Start with console
        config1 = ObservabilityConfig(tracing_enabled=True, exporter_type="console", service_name="test-switch")
        tracing.setup_tracing(config1)
        self.assertTrue(tracing._initialized)

        # Switch to 'none' exporter
        tracing.configure_exporter(exporter_type="none")

        # Should be re-initialized
        self.assertTrue(tracing._initialized)

    def test_custom_exporter_configuration(self):
        """Test configuring with a custom exporter instance."""
        from opentelemetry.sdk.trace.export import ConsoleSpanExporter

        custom_exporter = ConsoleSpanExporter()

        # Should accept custom exporter
        tracing.setup_tracing(exporter=custom_exporter)

        self.assertTrue(tracing._initialized)

    def test_multiple_setup_calls_are_noop(self):
        """Test that multiple setup_tracing calls are no-ops."""
        config = ObservabilityConfig(tracing_enabled=True, exporter_type="console", service_name="test-multiple")

        tracing.setup_tracing(config)
        first_provider = tracing._tracer_provider

        # Second call should be no-op
        tracing.setup_tracing(config)
        second_provider = tracing._tracer_provider

        self.assertIs(first_provider, second_provider)

    def test_exporter_type_normalization(self):
        """Test that exporter types are normalized to lowercase."""
        os.environ["BOTS_OTEL_EXPORTER"] = "CONSOLE"

        config = load_config_from_env()

        self.assertEqual(config.exporter_type, "console")

    def test_service_name_preservation(self):
        """Test that service names preserve case and special characters."""
        os.environ["OTEL_SERVICE_NAME"] = "My-Service_123"

        config = load_config_from_env()

        self.assertEqual(config.service_name, "My-Service_123")

    def test_endpoint_url_preservation(self):
        """Test that endpoint URLs are preserved exactly."""
        endpoint = "https://api.example.com:4317/v1/traces"
        os.environ["OTEL_EXPORTER_OTLP_ENDPOINT"] = endpoint

        config = load_config_from_env()

        self.assertEqual(config.otlp_endpoint, endpoint)

    def test_config_dataclass_defaults(self):
        """Test ObservabilityConfig dataclass default values."""
        config = ObservabilityConfig()

        self.assertTrue(config.tracing_enabled)
        self.assertEqual(config.exporter_type, "none")
        self.assertIsNone(config.otlp_endpoint)
        self.assertEqual(config.service_name, "bots")
        self.assertIsNone(config.metrics_enabled)
        self.assertEqual(config.metrics_exporter_type, "none")


if __name__ == "__main__":
    unittest.main()
