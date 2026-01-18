# Observability Module

**Module**: `bots/observability/`
**Version**: 3.0.0

## Overview

Tracing, metrics, and cost tracking

## Architecture

```
observability/
├── __init__.py
├── callbacks.py
├── config.py
├── cost_calculator.py
├── custom_exporters.py
├── metrics.py
├── tracing.py
```

## Key Components

### BotCallbacks

Abstract base class for bot operation callbacks.

### ObservabilityConfig

Configuration for OpenTelemetry observability.

### SimplifiedConsoleMetricExporter

A simplified metric exporter that prints only key metrics in a readable format.


## Usage Examples

```python
from bots.observability import *

# Usage examples coming soon
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `BotCallbacks` | Class | Abstract base class for bot operation callbacks. |
| `OpenTelemetryCallbacks` | Class | Callback implementation that integrates with OpenTelemetry t |
| `ProgressCallbacks` | Class | Callback implementation that shows progress indicators in th |
| `on_respond_start` | Function | Called when bot.respond() starts. |
| `on_respond_complete` | Function | Called when bot.respond() completes successfully. |
| `on_respond_error` | Function | Called when bot.respond() encounters an error. |
| `on_api_call_start` | Function | Called when an API call starts. |
| `on_api_call_complete` | Function | Called when an API call completes successfully. |
| `on_api_call_error` | Function | Called when an API call encounters an error. |
| `on_tool_start` | Function | Called when a tool execution starts. |
| `on_tool_complete` | Function | Called when a tool execution completes successfully. |
| `on_tool_error` | Function | Called when a tool execution encounters an error. |
| `on_step_start` | Function | Called when a processing step starts. |
| `on_step_complete` | Function | Called when a processing step completes. |
| `on_step_error` | Function | Called when a processing step encounters an error. |
| `on_respond_start` | Function | Add respond.start event to current span. |
| `on_respond_complete` | Function | Add respond.complete event to current span. |
| `on_respond_error` | Function | Record exception on current span. |
| `on_api_call_start` | Function | Add api_call.start event to current span. |
| `on_api_call_complete` | Function | Add api_call.complete event to current span. |
| `on_api_call_error` | Function | Record API call error on current span. |
| `on_tool_start` | Function | Add tool.start event to current span. |
| `on_tool_complete` | Function | Add tool.complete event to current span. |
| `on_tool_error` | Function | Add tool.error event to current span. |
| `on_step_start` | Function | Add step.start event to current span. |
| `on_step_complete` | Function | Add step.complete event to current span. |
| `on_step_error` | Function | Add step.error event to current span. |
| `on_respond_start` | Function | Show respond start indicator. |
| `on_respond_complete` | Function | Show respond complete indicator. |
| `on_api_call_start` | Function | Show API call start indicator. |
| `on_api_call_complete` | Function | Show API call complete indicator. |
| `on_tool_start` | Function | Show tool start indicator. |
| `on_tool_complete` | Function | Show tool complete indicator. |
| `on_step_start` | Function | Show step start indicator. |
| `on_step_complete` | Function | Show step complete indicator. |
| `ObservabilityConfig` | Class | Configuration for OpenTelemetry observability. |
| `load_config_from_env` | Function | Load observability configuration from environment variables. |
| `normalize_provider` | Function | Normalize provider name to canonical form. |
| `normalize_model` | Function | Normalize model name to match registry keys. |
| `get_model_pricing` | Function | Get pricing information for a specific model. |
| `calculate_cost` | Function | Calculate the cost of an LLM API call in USD. |
| `get_pricing_info` | Function | Get pricing information for providers and models. |
| `estimate_cost_from_text` | Function | Estimate cost from text strings (rough approximation). |
| `SimplifiedConsoleMetricExporter` | Class | A simplified metric exporter that prints only key metrics in |
| `export` | Function | Export metrics in a simplified format. |
| `shutdown` | Function | Shutdown the exporter. |
| `force_flush` | Function | Force flush any buffered metrics. |
| `set_verbose` | Function | Update the verbose setting. |
| `is_metrics_enabled` | Function | Check if OpenTelemetry metrics are enabled. |
| `reset_metrics` | Function | Reset metrics state for testing purposes. |
| `setup_metrics` | Function | Initialize OpenTelemetry metrics. |
| `get_total_tokens` | Function | Get total token usage since a given timestamp. |
| `get_total_cost` | Function | Get total cost since a given timestamp. |
| `set_metrics_verbose` | Function | Set verbose mode for metrics output. |
| `get_meter` | Function | Get a meter for the given module. |
| `record_response_time` | Function | Record bot response time. |
| `record_api_call` | Function | Record API call metrics. |
| `record_tool_execution` | Function | Record tool execution metrics. |
| `record_message_building` | Function | Record message building duration. |
| `record_tokens` | Function | Record token usage. |
| `record_cost` | Function | Record cost metrics. |
| `record_error` | Function | Record error metrics. |
| `record_tool_failure` | Function | Record tool failure metrics. |
| `get_and_clear_last_metrics` | Function | Get the last recorded metrics and clear them. |
| `is_tracing_enabled` | Function | Check if OpenTelemetry tracing is enabled. |
| `get_default_tracing_preference` | Function | Get the default tracing preference from environment. |
| `setup_tracing` | Function | Initialize OpenTelemetry tracing. |
| `get_tracer` | Function | Get a tracer for the given module. |
| `configure_exporter` | Function | Configure the trace exporter. |
