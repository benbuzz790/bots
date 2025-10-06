"""
Configuration for observability features.

Handles:
- Environment variable parsing
- Default configurations
- Exporter configuration
"""

import os
from dataclasses import dataclass
from typing import Optional


@dataclass
class ObservabilityConfig:
    """Configuration for OpenTelemetry observability.

    Attributes:
        tracing_enabled: Whether tracing is enabled (default: True)
        exporter_type: Type of exporter to use ('console', 'otlp', 'none')
        otlp_endpoint: Endpoint for OTLP exporter (if using OTLP)
        service_name: Service name for traces (default: 'bots')
    """

    tracing_enabled: bool = True
    exporter_type: str = "console"
    otlp_endpoint: Optional[str] = None
    service_name: str = "bots"


def load_config_from_env() -> ObservabilityConfig:
    """Load observability configuration from environment variables.

    Environment variables:
        OTEL_SDK_DISABLED: If 'true', disables all OpenTelemetry (standard OTel var)
        BOTS_OTEL_EXPORTER: Exporter type ('console', 'otlp', 'none')
        OTEL_EXPORTER_OTLP_ENDPOINT: OTLP endpoint (standard OTel var)
        OTEL_SERVICE_NAME: Service name (standard OTel var)

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

    config = ObservabilityConfig(
        tracing_enabled=not otel_disabled,
        exporter_type=exporter_type,
        otlp_endpoint=os.getenv("OTEL_EXPORTER_OTLP_ENDPOINT"),
        service_name=service_name,
    )

    return config


# Global configuration instance
DEFAULT_CONFIG = load_config_from_env()
