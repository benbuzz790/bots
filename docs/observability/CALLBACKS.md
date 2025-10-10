# Bot Callbacks System

## Overview

The bots framework provides a flexible callback system for monitoring and responding to bot operations in real-time. Callbacks enable:

- **Progress indicators** for CLI applications
- **Custom logging** and monitoring
- **Integration with observability systems** (OpenTelemetry)
- **Event-driven workflows** and automation
- **User experience enhancements** with real-time feedback

Callbacks are invoked at key points during bot operations, allowing you to hook into the bot's lifecycle without modifying its core logic.

## Table of Contents

1. [Quick Start](#quick-start)
2. [Callback Interface](#callback-interface)
3. [Built-in Implementations](#built-in-implementations)
4. [Custom Callbacks](#custom-callbacks)
5. [Integration Patterns](#integration-patterns)
6. [Best Practices](#best-practices)
7. [Examples](#examples)

---

## Quick Start

### Using Progress Callbacks

```python
from bots import AnthropicBot
from bots.observability.callbacks import ProgressCallbacks

# Simple progress dots
bot = AnthropicBot(callbacks=ProgressCallbacks())
response = bot.respond("Analyze this codebase")
# Output: ........

# Verbose progress with step names
bot = AnthropicBot(callbacks=ProgressCallbacks(verbose=True))
response = bot.respond("Analyze this codebase")
# Output: [Responding → Anthropic ✓ → view_file ✓ ✓]
```

### Using OpenTelemetry Callbacks

```python
from bots import AnthropicBot
from bots.observability.callbacks import OpenTelemetryCallbacks

# Automatic integration with OpenTelemetry tracing
bot = AnthropicBot(callbacks=OpenTelemetryCallbacks())
response = bot.respond("Hello!")
# All events logged to OpenTelemetry spans
```

---

## Callback Interface

### BotCallbacks Base Class

All callback implementations inherit from `BotCallbacks`, an abstract base class that defines 12 callback methods. **All methods are optional** - you only need to implement the ones you care about.

```python
from bots.observability.callbacks import BotCallbacks
from typing import Optional, Dict, Any

class BotCallbacks(ABC):
    """Abstract base class for bot operation callbacks."""

    # Respond lifecycle
    def on_respond_start(self, prompt: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when bot.respond() starts."""
        pass

    def on_respond_complete(self, response: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when bot.respond() completes successfully."""
        pass

    def on_respond_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when bot.respond() encounters an error."""
        pass

    # API call lifecycle
    def on_api_call_start(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when an API call starts."""
        pass

    def on_api_call_complete(self, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when an API call completes successfully."""
        pass

    def on_api_call_error(self, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when an API call encounters an error."""
        pass

    # Tool execution lifecycle
    def on_tool_start(self, tool_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a tool execution starts."""
        pass

    def on_tool_complete(self, tool_name: str, result: Any, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a tool execution completes successfully."""
        pass

    def on_tool_error(self, tool_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a tool execution encounters an error."""
        pass

    # Processing step lifecycle
    def on_step_start(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a processing step starts."""
        pass

    def on_step_complete(self, step_name: str, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a processing step completes."""
        pass

    def on_step_error(self, step_name: str, error: Exception, metadata: Optional[Dict[str, Any]] = None) -> None:
        """Called when a processing step encounters an error."""
        pass
```

### Callback Lifecycle

Callbacks are invoked in the following order during a typical `bot.respond()` call:

```
1. on_respond_start(prompt)
2. on_api_call_start()
3. on_api_call_complete()  # or on_api_call_error()
4. on_tool_start(tool_name)  # for each tool
5. on_tool_complete(tool_name, result)  # or on_tool_error()
6. on_respond_complete(response)  # or on_respond_error()
```

### Metadata Dictionary

Most callbacks receive an optional `metadata` dictionary with contextual information:

**on_respond_start metadata:**
- `bot_name`: Name of the bot
- `model`: Model engine being used

**on_api_call_complete metadata:**
- `provider`: API provider (anthropic, openai, google)
- `model`: Model name
- `input_tokens`: Number of input tokens
- `output_tokens`: Number of output tokens
- `cost_usd`: Cost in USD
- `duration`: API call duration in seconds

**on_tool_complete metadata:**
- `duration`: Tool execution duration in seconds
- `result_length`: Length of result string (if applicable)

---

## Built-in Implementations

### 1. ProgressCallbacks

Displays progress indicators in the CLI for user feedback.

**Features:**
- Simple dots (`.`) or verbose step names
- Real-time feedback during long operations
- Configurable output stream
- Minimal performance overhead

**Usage:**

```python
from bots.observability.callbacks import ProgressCallbacks

# Simple mode (just dots)
callbacks = ProgressCallbacks(verbose=False)

# Verbose mode (step names)
callbacks = ProgressCallbacks(verbose=True)

# Custom output stream
import sys
callbacks = ProgressCallbacks(verbose=True, file=sys.stderr)

# Use with bot
bot = AnthropicBot(callbacks=callbacks)
```

**Output Examples:**

```
# Simple mode
........

# Verbose mode
[Responding → Anthropic ✓ → view_file ✓ → python_edit ✓ ✓]
```

### 2. OpenTelemetryCallbacks

Integrates with OpenTelemetry tracing for comprehensive observability.

**Features:**
- Adds events to current OpenTelemetry span
- Records important attributes (tokens, cost, duration)
- Graceful degradation if OpenTelemetry not available
- Automatic exception recording

**Usage:**

```python
from bots.observability.callbacks import OpenTelemetryCallbacks

# Basic usage
callbacks = OpenTelemetryCallbacks()
bot = AnthropicBot(callbacks=callbacks)

# Callbacks automatically integrate with tracing
response = bot.respond("Hello!")
# Events logged to OpenTelemetry span
```

**Events Recorded:**
- `respond.start` / `respond.complete`
- `api_call.start` / `api_call.complete`
- `tool.start` / `tool.complete`
- `step.{name}.start` / `step.{name}.complete`

**Attributes Set:**
- `api.input_tokens`
- `api.output_tokens`
- `api.cost_usd`
- `tool.name`
- `tool.result_length`

---

## Custom Callbacks

### Basic Custom Callback

Implement only the methods you need:

```python
from bots.observability.callbacks import BotCallbacks

class LoggingCallbacks(BotCallbacks):
    """Simple logging callback."""

    def on_respond_start(self, prompt, metadata=None):
        print(f"[LOG] Starting response to: {prompt[:50]}...")

    def on_respond_complete(self, response, metadata=None):
        print(f"[LOG] Response complete: {len(response)} characters")

    def on_tool_start(self, tool_name, metadata=None):
        print(f"[LOG] Executing tool: {tool_name}")

# Use it
bot = AnthropicBot(callbacks=LoggingCallbacks())
```

### Advanced Custom Callback

Track metrics and send to external system:

```python
from bots.observability.callbacks import BotCallbacks
import time
import requests

class MetricsCallbacks(BotCallbacks):
    """Send metrics to external monitoring system."""

    def __init__(self, metrics_endpoint):
        self.metrics_endpoint = metrics_endpoint
        self.start_time = None

    def on_respond_start(self, prompt, metadata=None):
        self.start_time = time.time()

    def on_respond_complete(self, response, metadata=None):
        duration = time.time() - self.start_time

        # Send metrics to external system
        requests.post(self.metrics_endpoint, json={
            'event': 'bot_respond',
            'duration': duration,
            'response_length': len(response),
            'bot_name': metadata.get('bot_name'),
            'timestamp': time.time()
        })

    def on_api_call_complete(self, metadata=None):
        # Track API costs
        if metadata and 'cost_usd' in metadata:
            requests.post(self.metrics_endpoint, json={
                'event': 'api_cost',
                'cost_usd': metadata['cost_usd'],
                'provider': metadata.get('provider'),
                'model': metadata.get('model'),
                'timestamp': time.time()
            })

# Use it
callbacks = MetricsCallbacks('https://metrics.example.com/api')
bot = AnthropicBot(callbacks=callbacks)
```

### Combining Multiple Callbacks

Use a composite pattern to combine multiple callback implementations:

```python
from bots.observability.callbacks import BotCallbacks
from typing import List

class CompositeCallbacks(BotCallbacks):
    """Combine multiple callback implementations."""

    def __init__(self, callbacks: List[BotCallbacks]):
        self.callbacks = callbacks

    def on_respond_start(self, prompt, metadata=None):
        for cb in self.callbacks:
            try:
                cb.on_respond_start(prompt, metadata)
            except Exception as e:
                print(f"Callback error: {e}")

    def on_respond_complete(self, response, metadata=None):
        for cb in self.callbacks:
            try:
                cb.on_respond_complete(response, metadata)
            except Exception as e:
                print(f"Callback error: {e}")

    # ... implement other methods similarly

# Use it
from bots.observability.callbacks import ProgressCallbacks, OpenTelemetryCallbacks

callbacks = CompositeCallbacks([
    ProgressCallbacks(verbose=True),
    OpenTelemetryCallbacks(),
    MetricsCallbacks('https://metrics.example.com/api')
])

bot = AnthropicBot(callbacks=callbacks)
```

---

## Integration Patterns

### 1. CLI Integration

Use `ProgressCallbacks` for interactive CLI applications:

```python
from bots import AnthropicBot
from bots.observability.callbacks import ProgressCallbacks
import sys

def main():
    # Verbose progress for user feedback
    callbacks = ProgressCallbacks(verbose=True, file=sys.stdout)
    bot = AnthropicBot(callbacks=callbacks)
    bot.add_tools(code_tools)

    print("Bot ready! Type 'quit' to exit.")
    while True:
        prompt = input("\nYou: ")
        if prompt.lower() == 'quit':
            break

        print("Bot: ", end="", flush=True)
        response = bot.respond(prompt)
        print(f"\n{response}")

if __name__ == "__main__":
    main()
```

### 2. Functional Prompts Integration

Callbacks work seamlessly with functional prompts:

```python
from bots import AnthropicBot
from bots.flows import functional_prompts as fp
from bots.observability.callbacks import ProgressCallbacks

# Create bot with callbacks
bot = AnthropicBot(callbacks=ProgressCallbacks(verbose=True))
bot.add_tools(code_tools)

# Use with functional prompts
responses, nodes = fp.chain(bot, [
    "Read the README.md file",
    "Summarize the key features",
    "Create a quick start guide"
])
# Progress shown for each step
```

### 3. Parallel Operations

Callbacks work in parallel branches:

```python
from bots import AnthropicBot
from bots.flows import functional_prompts as fp
from bots.observability.callbacks import ProgressCallbacks

bot = AnthropicBot(callbacks=ProgressCallbacks(verbose=True))
bot.add_tools(code_tools)

# Parallel analysis with progress tracking
analyses, nodes = fp.par_branch(bot, [
    "Security analysis",
    "Performance analysis",
    "Code quality analysis"
])
# Each branch shows its own progress
```

### 4. Production Monitoring

Combine OpenTelemetry callbacks with custom metrics:

```python
from bots import AnthropicBot
from bots.observability.callbacks import OpenTelemetryCallbacks
from bots.observability.callbacks import BotCallbacks
import logging

class ProductionCallbacks(BotCallbacks):
    """Production-ready callbacks with logging and alerting."""

    def __init__(self):
        self.logger = logging.getLogger('bot.production')
        self.error_count = 0

    def on_respond_error(self, error, metadata=None):
        self.error_count += 1
        self.logger.error(f"Bot error: {error}", extra=metadata)

        # Alert if too many errors
        if self.error_count > 10:
            self._send_alert("High error rate detected")

    def on_api_call_complete(self, metadata=None):
        # Monitor costs
        if metadata and metadata.get('cost_usd', 0) > 1.0:
            self.logger.warning(f"High cost API call: ${metadata['cost_usd']}")

    def _send_alert(self, message):
        # Send to alerting system (PagerDuty, Slack, etc.)
        pass

# Use composite callbacks for production
from bots.observability.callbacks import CompositeCallbacks

callbacks = CompositeCallbacks([
    OpenTelemetryCallbacks(),
    ProductionCallbacks()
])

bot = AnthropicBot(callbacks=callbacks)
```

---

## Best Practices

### 1. Error Handling

Always handle exceptions in callbacks to prevent disrupting bot operations:

```python
class SafeCallbacks(BotCallbacks):
    def on_respond_start(self, prompt, metadata=None):
        try:
            # Your callback logic
            self._do_something(prompt)
        except Exception as e:
            # Log but don't raise
            print(f"Callback error: {e}")
```

### 2. Performance

Keep callbacks lightweight to avoid slowing down bot operations:

```python
class FastCallbacks(BotCallbacks):
    def on_tool_complete(self, tool_name, result, metadata=None):
        # ✅ Good: Quick operation
        self.tool_count += 1

        # ❌ Bad: Slow operation
        # self._upload_to_database(result)  # Blocks bot

        # ✅ Better: Async operation
        self.queue.put((tool_name, result))  # Non-blocking
```

### 3. Graceful Degradation

Make callbacks optional and handle missing dependencies:

```python
class OptionalCallbacks(BotCallbacks):
    def __init__(self):
        try:
            import some_optional_library
            self.library = some_optional_library
            self.enabled = True
        except ImportError:
            self.enabled = False

    def on_respond_complete(self, response, metadata=None):
        if self.enabled:
            self.library.do_something(response)
```

### 4. Metadata Usage

Use metadata for context-aware behavior:

```python
class SmartCallbacks(BotCallbacks):
    def on_api_call_complete(self, metadata=None):
        if not metadata:
            return

        # Different behavior based on provider
        provider = metadata.get('provider')
        if provider == 'anthropic':
            self._handle_anthropic(metadata)
        elif provider == 'openai':
            self._handle_openai(metadata)
```

### 5. Testing

Test callbacks independently from bots:

```python
def test_logging_callbacks():
    callbacks = LoggingCallbacks()

    # Test respond lifecycle
    callbacks.on_respond_start("test prompt", {"bot_name": "test"})
    callbacks.on_respond_complete("test response", {"bot_name": "test"})

    # Verify behavior
    assert callbacks.log_count == 2
```

---

## Examples

### Example 1: Cost Tracking Callback

Track and alert on API costs:

```python
from bots.observability.callbacks import BotCallbacks

class CostTrackingCallbacks(BotCallbacks):
    """Track API costs and alert on thresholds."""

    def __init__(self, daily_budget_usd=10.0):
        self.daily_budget = daily_budget_usd
        self.daily_cost = 0.0
        self.total_cost = 0.0

    def on_api_call_complete(self, metadata=None):
        if not metadata or 'cost_usd' not in metadata:
            return

        cost = metadata['cost_usd']
        self.daily_cost += cost
        self.total_cost += cost

        # Alert if over budget
        if self.daily_cost > self.daily_budget:
            print(f"⚠️  Daily budget exceeded: ${self.daily_cost:.4f}")

        # Log high-cost calls
        if cost > 0.10:
            print(f"💰 High cost call: ${cost:.4f} ({metadata.get('model')})")

    def reset_daily(self):
        """Call this at midnight to reset daily tracking."""
        self.daily_cost = 0.0

# Use it
callbacks = CostTrackingCallbacks(daily_budget_usd=5.0)
bot = AnthropicBot(callbacks=callbacks)
```

### Example 2: Performance Monitoring Callback

Monitor response times and tool usage:

```python
from bots.observability.callbacks import BotCallbacks
import time

class PerformanceCallbacks(BotCallbacks):
    """Monitor performance metrics."""

    def __init__(self):
        self.start_times = {}
        self.metrics = {
            'respond_times': [],
            'api_times': [],
            'tool_times': {}
        }

    def on_respond_start(self, prompt, metadata=None):
        self.start_times['respond'] = time.time()

    def on_respond_complete(self, response, metadata=None):
        duration = time.time() - self.start_times['respond']
        self.metrics['respond_times'].append(duration)

        if duration > 10.0:
            print(f"⚠️  Slow response: {duration:.2f}s")

    def on_api_call_start(self, metadata=None):
        self.start_times['api'] = time.time()

    def on_api_call_complete(self, metadata=None):
        duration = time.time() - self.start_times['api']
        self.metrics['api_times'].append(duration)

    def on_tool_start(self, tool_name, metadata=None):
        self.start_times[f'tool_{tool_name}'] = time.time()

    def on_tool_complete(self, tool_name, result, metadata=None):
        key = f'tool_{tool_name}'
        duration = time.time() - self.start_times[key]

        if tool_name not in self.metrics['tool_times']:
            self.metrics['tool_times'][tool_name] = []
        self.metrics['tool_times'][tool_name].append(duration)

    def get_summary(self):
        """Get performance summary."""
        import statistics

        return {
            'avg_respond_time': statistics.mean(self.metrics['respond_times']) if self.metrics['respond_times'] else 0,
            'avg_api_time': statistics.mean(self.metrics['api_times']) if self.metrics['api_times'] else 0,
            'slowest_tool': max(
                ((name, max(times)) for name, times in self.metrics['tool_times'].items()),
                key=lambda x: x[1],
                default=('none', 0)
            )
        }

# Use it
callbacks = PerformanceCallbacks()
bot = AnthropicBot(callbacks=callbacks)

# ... use bot ...

# Get summary
summary = callbacks.get_summary()
print(f"Average response time: {summary['avg_respond_time']:.2f}s")
print(f"Slowest tool: {summary['slowest_tool'][0]} ({summary['slowest_tool'][1]:.2f}s)")
```

### Example 3: Audit Trail Callback

Create detailed audit logs for compliance:

```python
from bots.observability.callbacks import BotCallbacks
import json
import datetime

class AuditCallbacks(BotCallbacks):
    """Create detailed audit trail."""

    def __init__(self, audit_file='audit.jsonl'):
        self.audit_file = audit_file
        self.session_id = datetime.datetime.now().isoformat()

    def _write_audit(self, event_type, data):
        """Write audit entry."""
        entry = {
            'timestamp': datetime.datetime.now().isoformat(),
            'session_id': self.session_id,
            'event_type': event_type,
            'data': data
        }

        with open(self.audit_file, 'a') as f:
            f.write(json.dumps(entry) + '\n')

    def on_respond_start(self, prompt, metadata=None):
        self._write_audit('respond_start', {
            'prompt': prompt,
            'bot_name': metadata.get('bot_name') if metadata else None
        })

    def on_respond_complete(self, response, metadata=None):
        self._write_audit('respond_complete', {
            'response_length': len(response),
            'bot_name': metadata.get('bot_name') if metadata else None
        })

    def on_tool_start(self, tool_name, metadata=None):
        self._write_audit('tool_execution', {
            'tool_name': tool_name,
            'args': metadata.get('args') if metadata else None
        })

    def on_api_call_complete(self, metadata=None):
        if metadata:
            self._write_audit('api_call', {
                'provider': metadata.get('provider'),
                'model': metadata.get('model'),
                'input_tokens': metadata.get('input_tokens'),
                'output_tokens': metadata.get('output_tokens'),
                'cost_usd': metadata.get('cost_usd')
            })

# Use it
callbacks = AuditCallbacks(audit_file='bot_audit.jsonl')
bot = AnthropicBot(callbacks=callbacks)
```

---

## Summary

The callback system provides a powerful, flexible way to monitor and respond to bot operations:

- **12 callback methods** covering the complete bot lifecycle
- **All methods optional** - implement only what you need
- **Built-in implementations** for common use cases (progress, OpenTelemetry)
- **Easy to extend** with custom callbacks
- **Composable** - combine multiple callbacks
- **Production-ready** with error handling and graceful degradation

Use callbacks to enhance user experience, monitor performance, track costs, and integrate with external systems - all without modifying bot core logic.

---

## See Also

- [SETUP.md](SETUP.md) - OpenTelemetry setup and configuration
- [COST_TRACKING.md](COST_TRACKING.md) - Cost tracking and optimization
- [DASHBOARDS.md](DASHBOARDS.md) - Metrics visualization and dashboards
