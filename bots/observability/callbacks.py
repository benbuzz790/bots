"""
Callback system for bot operations.

Provides a flexible callback interface for monitoring and responding to bot operations.
Callbacks can be used for progress indicators, logging, monitoring, or custom behavior.

Example:
    ```python
    from bots import AnthropicBot
    from bots.observability.callbacks import ProgressCallbacks

    bot = AnthropicBot(callbacks=ProgressCallbacks(verbose=True))
    response = bot.respond("Hello!")  # Shows progress dots
    ```
"""

import sys
from abc import ABC
from typing import Any, Dict, Optional

# Try to import OpenTelemetry with graceful degradation
try:
    from opentelemetry import trace

    TRACING_AVAILABLE = True
except ImportError:
    TRACING_AVAILABLE = False
    trace = None


class BotCallbacks(ABC):
    """Abstract base class for bot operation callbacks.

    All methods are optional - subclasses only need to implement
    the callbacks they care about. Default implementations do nothing.

    Callbacks are invoked at key points during bot operations:
    - respond: Start/complete/error of bot.respond()
    - api_call: Start/complete/error of API calls
    - tool: Start/complete/error of tool execution
    - step: Start/complete/error of individual steps

    Attributes:
        None
    """

    def on_respond_start(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when bot.respond() starts.

        Args:
            prompt: The user prompt being responded to
            metadata: Optional context (bot name, model, etc.)
        """
        pass

    def on_respond_complete(self, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when bot.respond() completes successfully.

        Args:
            response: The bot's response
            metadata: Optional context (duration, token count, etc.)
        """
        pass

    def on_respond_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when bot.respond() encounters an error.

        Args:
            error: The exception that occurred
            metadata: Optional context (bot name, error type, etc.)
        """
        pass

    def on_api_call_start(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when an API call starts.

        Args:
            metadata: Optional context (provider, model, message count, etc.)
        """
        pass

    def on_api_call_complete(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when an API call completes successfully.

        Args:
            metadata: Optional context (duration, tokens, cost, etc.)
        """
        pass

    def on_api_call_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when an API call encounters an error.

        Args:
            error: The exception that occurred
            metadata: Optional context (provider, retry count, etc.)
        """
        pass

    def on_tool_start(self, tool_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a tool execution starts.

        Args:
            tool_name: Name of the tool being executed
            metadata: Optional context (tool args, etc.)
        """
        pass

    def on_tool_complete(self, tool_name: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a tool execution completes successfully.

        Args:
            tool_name: Name of the tool that was executed
            result: The tool's return value
            metadata: Optional context (duration, result length, etc.)
        """
        pass

    def on_tool_error(self, tool_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a tool execution encounters an error.

        Args:
            tool_name: Name of the tool that failed
            error: The exception that occurred
            metadata: Optional context (error type, etc.)
        """
        pass

    def on_step_start(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a processing step starts.

        Args:
            step_name: Name of the step (e.g., "build_messages", "process_response")
            metadata: Optional context
        """
        pass

    def on_step_complete(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a processing step completes.

        Args:
            step_name: Name of the step that completed
            metadata: Optional context (duration, etc.)
        """
        pass

    def on_step_error(self, step_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a processing step encounters an error.

        Args:
            step_name: Name of the step that failed
            error: The exception that occurred
            metadata: Optional context
        """
        pass


class OpenTelemetryCallbacks(BotCallbacks):
    """Callback implementation that integrates with OpenTelemetry tracing.

    Adds events and attributes to the current OpenTelemetry span for all
    bot operations. This provides detailed observability when tracing is enabled.

    If OpenTelemetry is not available or no span is active, operations
    gracefully degrade to no-ops.

    Example:
        ```python
        from bots import AnthropicBot
        from bots.observability.callbacks import OpenTelemetryCallbacks

        bot = AnthropicBot(callbacks=OpenTelemetryCallbacks())
        response = bot.respond("Hello!")  # Events logged to OTel span
        ```
    """

    def on_respond_start(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add respond.start event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"prompt.length": len(prompt)}
            if metadata:
                attributes.update(metadata)
            span.add_event("respond.start", attributes)

    def on_respond_complete(self, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add respond.complete event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"response.length": len(response)}
            if metadata:
                attributes.update(metadata)
            span.add_event("respond.complete", attributes)

    def on_respond_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record exception on current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            span.record_exception(error)
            if metadata:
                for key, value in metadata.items():
                    span.set_attribute(f"error.{key}", str(value))

    def on_api_call_start(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add api_call.start event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = metadata or {}
            span.add_event("api_call.start", attributes)

    def on_api_call_complete(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add api_call.complete event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = metadata or {}
            span.add_event("api_call.complete", attributes)

            # Set important attributes on the span itself
            if metadata:
                if "input_tokens" in metadata:
                    span.set_attribute("api.input_tokens", metadata["input_tokens"])
                if "output_tokens" in metadata:
                    span.set_attribute("api.output_tokens", metadata["output_tokens"])
                if "cost_usd" in metadata:
                    span.set_attribute("api.cost_usd", metadata["cost_usd"])

    def on_api_call_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Record API call error on current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"error.type": type(error).__name__}
            if metadata:
                attributes.update(metadata)
            span.add_event("api_call.error", attributes)

    def on_tool_start(self, tool_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add tool.start event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"tool.name": tool_name}
            if metadata:
                attributes.update(metadata)
            span.add_event("tool.start", attributes)

    def on_tool_complete(self, tool_name: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add tool.complete event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"tool.name": tool_name}
            if isinstance(result, str):
                attributes["tool.result_length"] = len(result)
            if metadata:
                attributes.update(metadata)
            span.add_event("tool.complete", attributes)

    def on_tool_error(self, tool_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add tool.error event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"tool.name": tool_name, "error.type": type(error).__name__}
            if metadata:
                attributes.update(metadata)
            span.add_event("tool.error", attributes)

    def on_step_start(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add step.start event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"step.name": step_name}
            if metadata:
                attributes.update(metadata)
            span.add_event(f"step.{step_name}.start", attributes)

    def on_step_complete(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add step.complete event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"step.name": step_name}
            if metadata:
                attributes.update(metadata)
            span.add_event(f"step.{step_name}.complete", attributes)

    def on_step_error(self, step_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Add step.error event to current span."""
        if not TRACING_AVAILABLE:
            return

        span = trace.get_current_span()
        if span and span.is_recording():
            attributes = {"step.name": step_name, "error.type": type(error).__name__}
            if metadata:
                attributes.update(metadata)
            span.add_event(f"step.{step_name}.error", attributes)


class ProgressCallbacks(BotCallbacks):
    """Callback implementation that shows progress indicators in the CLI.

    Displays dots (....) during bot operations to provide user feedback.
    Useful for CLI applications where users want to see that work is happening.

    Args:
        verbose: If True, shows step names. If False, just shows dots.
        file: Output file (default: sys.stdout)

    Example:
        ```python
        from bots import AnthropicBot
        from bots.observability.callbacks import ProgressCallbacks

        # Simple dots
        bot = AnthropicBot(callbacks=ProgressCallbacks())

        # Verbose with step names
        bot = AnthropicBot(callbacks=ProgressCallbacks(verbose=True))
        ```
    """

    def __init__(self, verbose: bool = False, file=None):
        """Initialize progress callbacks.

        Args:
            verbose: If True, shows step names. If False, just shows dots.
            file: Output file (default: sys.stdout)
        """
        self.verbose = verbose
        self.file = file or sys.stdout

    def _print(self, message: str, newline: bool = False) -> None:
        """Print a message to the output file.

        Args:
            message: Message to print
            newline: If True, add newline after message
        """
        end = "\n" if newline else ""
        print(message, end=end, file=self.file, flush=True)

    def on_respond_start(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show respond start indicator."""
        if self.verbose:
            self._print("\n[Responding", newline=False)
        else:
            self._print(".", newline=False)

    def on_respond_complete(self, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show respond complete indicator."""
        if self.verbose:
            self._print(" ✓]", newline=True)
        else:
            self._print(".", newline=False)

    def on_api_call_start(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show API call start indicator."""
        if self.verbose:
            provider = metadata.get("provider", "API") if metadata else "API"
            self._print(f" → {provider}", newline=False)
        else:
            self._print(".", newline=False)

    def on_api_call_complete(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show API call complete indicator."""
        if self.verbose:
            self._print(" ✓", newline=False)
        else:
            self._print(".", newline=False)

    def on_tool_start(self, tool_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show tool start indicator."""
        if self.verbose:
            self._print(f" → {tool_name}", newline=False)
        else:
            self._print(".", newline=False)

    def on_tool_complete(self, tool_name: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show tool complete indicator."""
        if self.verbose:
            self._print(" ✓", newline=False)
        else:
            self._print(".", newline=False)

    def on_step_start(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show step start indicator."""
        if self.verbose:
            self._print(f" [{step_name}", newline=False)

    def on_step_complete(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Show step complete indicator."""
        if self.verbose:
            self._print("]", newline=False)
