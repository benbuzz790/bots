"""
Configuration for observability features.

Handles:
- Environment variable parsing
- Default configurations
- Exporter configuration
- Metrics configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ObservabilityConfig:
    """Configuration for OpenTelemetry observability.

    Attributes:
        tracing_enabled: Whether tracing is enabled (default: True)
        exporter_type: Type of exporter to use ('console', 'otlp', 'jaeger', 'none')
        otlp_endpoint: Endpoint for OTLP exporter (if using OTLP)
        service_name: Service name for traces (default: 'bots')
        metrics_enabled: Whether metrics collection is enabled (default: follows tracing_enabled)
        metrics_exporter_type: Type of metrics exporter ('console', 'otlp', 'prometheus', 'none')
        jaeger_endpoint: Endpoint for Jaeger exporter (if using Jaeger)
    """

    tracing_enabled: bool = True
    exporter_type: str = "console"
    otlp_endpoint: Optional[str] = None
    service_name: str = "bots"
    metrics_enabled: Optional[bool] = None  # None means follow tracing_enabled
    metrics_exporter_type: str = "console"
    jaeger_endpoint: Optional[str] = None


def load_config_from_env() -> ObservabilityConfig:
    """Load observability configuration from environment variables.

    Environment variables:
        OTEL_SDK_DISABLED: If 'true', disables all OpenTelemetry (standard OTel var)
        BOTS_OTEL_EXPORTER: Exporter type ('console', 'otlp', 'jaeger', 'none')
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (standard OTel var)
        OTEL_SERVICE_NAME: Service name (standard OTel var)
        BOTS_OTEL_METRICS_ENABLED: If set, explicitly enable/disable metrics (overrides default)
        BOTS_OTEL_METRICS_EXPORTER: Metrics exporter type ('console', 'otlp', 'prometheus', 'none')
        OTEL_EXPORTER_JAEGER_ENDPOINT: Jaeger endpoint (if using Jaeger)

    Returns:
        ObservabilityConfig: Configuration object
    """
    # Check if OpenTelemetry SDK is disabled (standard OTel env var)
    # Handle case-insensitive values and empty strings
    otel_disabled_raw = os.getenv("OTEL_SDK_DISABLED", "false").strip()
    otel_disabled = otel_disabled_raw.lower() == "true" if otel_disabled_raw else False

    # Get exporter type, handle empty strings
    exporter_type_raw = os.getenv("BOTS_OTEL_EXPORTER", "console").strip()
    exporter_type = exporter_type_raw.lower() if exporter_type_raw else "console"

    # Get service name, handle empty strings
    service_name_raw = os.getenv("OTEL_SERVICE_NAME", "bots").strip()
    service_name = service_name_raw if service_name_raw else "bots"

    # Get metrics configuration
    # If BOTS_OTEL_METRICS_ENABLED is set, use it; otherwise follow tracing_enabled
    metrics_enabled_raw = os.getenv("BOTS_OTEL_METRICS_ENABLED", "").strip()
    if metrics_enabled_raw:
        metrics_enabled = metrics_enabled_raw.lower() == "true"
    else:
        metrics_enabled = None  # Will follow tracing_enabled

    # Get metrics exporter type
    metrics_exporter_raw = os.getenv("BOTS_OTEL_METRICS_EXPORTER", "console").strip()
    metrics_exporter_type = metrics_exporter_raw.lower() if metrics_exporter_raw else "console"

    config = ObservabilityConfig(
        tracing_enabled=not otel_disabled,
        exporter_type=exporter_type,
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        service_name=service_name,
        metrics_enabled=metrics_enabled,
        metrics_exporter_type=metrics_exporter_type,
        jaeger_endpoint=os.getenv("OTEL_EXPORTER_JAEGER_ENDPOINT"),
    )

    return config


# Global configuration instance
DEFAULT_CONFIG = load_config_from_env()
