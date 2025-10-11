"""
Custom metric exporters for the bots framework.

Provides simplified, human-readable metric output for CLI usage.
"""

from typing import Optional

try:
    from opentelemetry.sdk.metrics.export import MetricExporter, MetricExportResult
    METRICS_AVAILABLE = True
except ImportError:
    METRICS_AVAILABLE = False
    MetricExporter = object
    MetricExportResult = None


class SimplifiedConsoleMetricExporter(MetricExporter):
    """A simplified metric exporter that prints only key metrics in a readable format.

    Only displays:
    - Total tokens (input + output)
    - Total cost in USD
    - API call duration

    This is designed for CLI usage where the full OpenTelemetry JSON output is too verbose.
    """

    def __init__(self, verbose: bool = False):
        """Initialize the exporter.

        Args:
            verbose: If True, print metrics. If False, suppress output.
        """
        self.verbose = verbose
        super().__init__()

    def export(self, metrics_data, timeout_millis: float = 10_000, **kwargs) -> "MetricExportResult":
        """Export metrics in a simplified format.

        Args:
            metrics_data: The metrics data to export
            timeout_millis: Timeout in milliseconds (unused)
            **kwargs: Additional arguments

        Returns:
            MetricExportResult.SUCCESS
        """
        if not self.verbose:
            return MetricExportResult.SUCCESS

        # Extract key metrics
        tokens_input = 0
        tokens_output = 0
        tokens_cached = 0
        total_cost = 0.0
        api_duration = 0.0

        try:
            for resource_metric in metrics_data.resource_metrics:
                for scope_metric in resource_metric.scope_metrics:
                    for metric in scope_metric.metrics:
                        if metric.name == "bot.tokens_used":
                            for point in metric.data.data_points:
                                token_type = point.attributes.get("token_type", "")
                                if token_type == "input":
                                    tokens_input += point.value
                                elif token_type == "output":
                                    tokens_output += point.value
                                elif token_type == "cached":
                                    tokens_cached += point.value

                        elif metric.name == "bot.cost_total_usd":
                            for point in metric.data.data_points:
                                total_cost += point.value

                        elif metric.name == "bot.api_call_duration":
                            for point in metric.data.data_points:
                                api_duration += point.sum

            # Print simplified output
            if tokens_input > 0 or tokens_output > 0 or total_cost > 0:
                print("\n" + "="*60)
                print("📊 API Metrics Summary")
                print("="*60)

                if tokens_input > 0 or tokens_output > 0:
                    total_tokens = tokens_input + tokens_output
                    print(f"🔢 Tokens:        {total_tokens:,} ({tokens_input:,} in, {tokens_output:,} out)", end="")
                    if tokens_cached > 0:
                        print(f", {tokens_cached:,} cached", end="")
                    print()

                if total_cost > 0:
                    print(f"💰 Cost:          ${total_cost:.4f}")

                if api_duration > 0:
                    print(f"⏱️  Response Time: {api_duration:.2f}s")

                print("="*60 + "\n")

        except Exception as e:
            # Silently fail if there's an error parsing metrics
            pass

        return MetricExportResult.SUCCESS

    def shutdown(self, timeout_millis: float = 30_000, **kwargs) -> None:
        """Shutdown the exporter."""
        pass

    def force_flush(self, timeout_millis: float = 10_000) -> bool:
        """Force flush any buffered metrics."""
        return True

    def set_verbose(self, verbose: bool):
        """Update the verbose setting.

        Args:
            verbose: If True, print metrics. If False, suppress output.
        """
        self.verbose = verbose