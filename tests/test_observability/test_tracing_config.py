"""Tests for observability configuration module.

This module tests the configuration system for OpenTelemetry tracing,
including environment variable handling, default values, and precedence rules.
"""

from bots.observability.config import ObservabilityConfig, load_config_from_env


class TestObservabilityConfig:
    """Test the ObservabilityConfig dataclass."""

    def test_default_config(self):
        """Test that ObservabilityConfig has correct default values.

        Verifies:
        - tracing_enabled defaults to True
        - exporter_type defaults to "console"
        - service_name defaults to "bots"
        - otlp_endpoint is None by default
        """
        config = ObservabilityConfig()

        assert config.tracing_enabled is True
        assert config.exporter_type == "console"
        assert config.service_name == "bots"
        assert config.otlp_endpoint is None

    def test_custom_config_values(self):
        """Test creating ObservabilityConfig with custom values.

        Verifies that all fields can be set to custom values.
        """
        config = ObservabilityConfig(
            tracing_enabled=False, exporter_type="otlp", service_name="my-service", otlp_endpoint="http://localhost:4317"
        )

        assert config.tracing_enabled is False
        assert config.exporter_type == "otlp"
        assert config.service_name == "my-service"
        assert config.otlp_endpoint == "http://localhost:4317"


class TestLoadConfigFromEnv:
    """Test loading configuration from environment variables."""

    def test_load_config_from_env_defaults(self, clean_otel_env):
        """Test load_config_from_env with no environment variables set.

        Verifies that when no env vars are set, the function returns
        default configuration values.
        """
        config = load_config_from_env()

        assert config.tracing_enabled is True
        assert config.exporter_type == "console"
        assert config.service_name == "bots"
        assert config.otlp_endpoint is None

    def test_otel_sdk_disabled_true(self, clean_otel_env, monkeypatch):
        """Test that OTEL_SDK_DISABLED=true disables tracing.

        Verifies that setting OTEL_SDK_DISABLED to "true" (case-insensitive)
        results in tracing_enabled=False.
        """
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
        config = load_config_from_env()

        assert config.tracing_enabled is False

    def test_otel_sdk_disabled_case_insensitive(self, clean_otel_env, monkeypatch):
        """Test that OTEL_SDK_DISABLED is case-insensitive.

        Verifies that "True", "TRUE", "true" all disable tracing.
        """
        for value in ["True", "TRUE", "true", "TrUe"]:
            monkeypatch.setenv("OTEL_SDK_DISABLED", value)
            config = load_config_from_env()
            assert config.tracing_enabled is False, f"Failed for value: {value}"

    def test_otel_sdk_disabled_false(self, clean_otel_env, monkeypatch):
        """Test that OTEL_SDK_DISABLED=false enables tracing.

        Verifies that setting OTEL_SDK_DISABLED to "false" or any
        non-"true" value results in tracing_enabled=True.
        """
        monkeypatch.setenv("OTEL_SDK_DISABLED", "false")
        config = load_config_from_env()

        assert config.tracing_enabled is True

    def test_custom_exporter_type_console(self, clean_otel_env, monkeypatch):
        """Test BOTS_OTEL_EXPORTER=console.

        Verifies that the exporter type can be set via environment variable.
        """
        monkeypatch.setenv("BOTS_OTEL_EXPORTER", "console")
        config = load_config_from_env()

        assert config.exporter_type == "console"

    def test_custom_exporter_type_otlp(self, clean_otel_env, monkeypatch):
        """Test BOTS_OTEL_EXPORTER=otlp.

        Verifies that the OTLP exporter can be selected.
        """
        monkeypatch.setenv("BOTS_OTEL_EXPORTER", "otlp")
        config = load_config_from_env()

        assert config.exporter_type == "otlp"

    def test_custom_exporter_type_none(self, clean_otel_env, monkeypatch):
        """Test BOTS_OTEL_EXPORTER=none.

        Verifies that exporter can be disabled with "none".
        """
        monkeypatch.setenv("BOTS_OTEL_EXPORTER", "none")
        config = load_config_from_env()

        assert config.exporter_type == "none"

    def test_otlp_endpoint(self, clean_otel_env, monkeypatch):
        """Test OTEL_EXPORTER_OTLP_ENDPOINT environment variable.

        Verifies that the OTLP endpoint can be configured via standard
        OpenTelemetry environment variable.
        """
        endpoint = "http://localhost:4317"
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", endpoint)
        config = load_config_from_env()

        assert config.otlp_endpoint == endpoint

    def test_service_name(self, clean_otel_env, monkeypatch):
        """Test OTEL_SERVICE_NAME environment variable.

        Verifies that the service name can be configured via standard
        OpenTelemetry environment variable.
        """
        service_name = "my-custom-bot-service"
        monkeypatch.setenv("OTEL_SERVICE_NAME", service_name)
        config = load_config_from_env()

        assert config.service_name == service_name

    def test_otel_sdk_disabled_overrides_all(self, clean_otel_env, monkeypatch):
        """Test that OTEL_SDK_DISABLED=true takes precedence over all other settings.

        Verifies that even when other configuration is set, OTEL_SDK_DISABLED=true
        will disable tracing. This is the emergency kill-switch behavior.
        """
        # Set up a fully configured environment
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")
        monkeypatch.setenv("BOTS_OTEL_EXPORTER", "otlp")
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")
        monkeypatch.setenv("OTEL_SERVICE_NAME", "my-service")

        config = load_config_from_env()

        # Tracing should be disabled despite other settings
        assert config.tracing_enabled is False

        # Other settings should still be loaded (for when tracing is re-enabled)
        assert config.exporter_type == "otlp"
        assert config.otlp_endpoint == "http://localhost:4317"
        assert config.service_name == "my-service"

    def test_multiple_env_vars_together(self, clean_otel_env, monkeypatch):
        """Test loading multiple environment variables together.

        Verifies that all configuration options work together correctly.
        """
        monkeypatch.setenv("BOTS_OTEL_EXPORTER", "otlp")
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://collector:4317")
        monkeypatch.setenv("OTEL_SERVICE_NAME", "test-bot")

        config = load_config_from_env()

        assert config.tracing_enabled is True
        assert config.exporter_type == "otlp"
        assert config.otlp_endpoint == "http://collector:4317"
        assert config.service_name == "test-bot"

    def test_empty_string_env_vars(self, clean_otel_env, monkeypatch):
        """Test behavior with empty string environment variables.

        Verifies that empty strings are handled gracefully and defaults are used.
        """
        monkeypatch.setenv("BOTS_OTEL_EXPORTER", "")
        monkeypatch.setenv("OTEL_SERVICE_NAME", "")

        config = load_config_from_env()

        # Empty strings should result in defaults
        assert config.exporter_type == "console"
        assert config.service_name == "bots"


class TestConfigPrecedence:
    """Test configuration precedence rules."""

    def test_otel_sdk_disabled_is_highest_priority(self, clean_otel_env, monkeypatch):
        """Test that OTEL_SDK_DISABLED has highest priority.

        This is the emergency kill-switch and should override everything.
        """
        monkeypatch.setenv("OTEL_SDK_DISABLED", "true")

        config = load_config_from_env()
        assert config.tracing_enabled is False

    def test_standard_otel_env_vars_respected(self, clean_otel_env, monkeypatch):
        """Test that standard OpenTelemetry env vars are respected.

        Verifies that we follow OpenTelemetry conventions for standard
        environment variables like OTEL_SERVICE_NAME and OTEL_EXPORTER_OTLP_ENDPOINT.
        """
        monkeypatch.setenv("OTEL_SERVICE_NAME", "standard-service")
        monkeypatch.setenv("OTEL_EXPORTER_OTLP_ENDPOINT", "http://standard:4317")

        config = load_config_from_env()

        assert config.service_name == "standard-service"
        assert config.otlp_endpoint == "http://standard:4317"
