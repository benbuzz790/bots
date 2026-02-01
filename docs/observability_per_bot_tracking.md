# Per-Bot Observability Tracking

## Overview

The bots framework provides per-bot observability functions to enable accurate cost and token tracking for concurrent bot executions. This prevents cost attribution errors when multiple bots run simultaneously.

## Problem Statement

When multiple bots run concurrently (e.g., in portfolio_manager_bot scenarios), the global metrics system can cause cost attribution errors. Bots "steal" each other's metrics because `get_and_clear_last_metrics()` clears metrics for ALL bots.

**Before (Global Only):**
```python
# Bot A records: 100 tokens, $0.015
# Bot B records: 200 tokens, $0.025
# Bot A calls get_and_clear_last_metrics() -> Gets Bot B's metrics!
# Result: Incorrect cost attribution
```

## Solution

Per-bot metrics isolation using bot_id parameter:

**After (Per-Bot Tracking):**
```python
# Bot A records with bot_id="bot_a"
metrics.record_tokens(..., bot_id="bot_a")
metrics.record_cost(..., bot_id="bot_a")

# Bot B records with bot_id="bot_b"
metrics.record_tokens(..., bot_id="bot_b")
metrics.record_cost(..., bot_id="bot_b")

# Each bot gets only its own metrics
bot_a_cost = metrics.get_bot_cost("bot_a")  # $0.015
bot_b_cost = metrics.get_bot_cost("bot_b")  # $0.025
```

## API Reference

### Recording Functions (Updated)

All recording functions now accept an optional `bot_id` parameter:

```python
def record_tokens(
    input_tokens: int,
    output_tokens: int,
    provider: str,
    model: str,
    cached_tokens: int = 0,
    bot_id: Optional[str] = None,  # NEW
)

def record_cost(
    cost: float,
    provider: str,
    model: str,
    bot_id: Optional[str] = None,  # NEW
)

def record_api_call(
    duration: float,
    provider: str,
    model: str,
    status: str = "success",
    bot_id: Optional[str] = None,  # NEW
)

def record_tool_execution(
    duration: float,
    tool_name: str,
    success: bool = True,
    bot_id: Optional[str] = None,  # NEW
)

def record_message_building(
    duration: float,
    provider: str,
    model: str,
    bot_id: Optional[str] = None,  # NEW
)

def record_response_time(
    duration: float,
    provider: str,
    model: str,
    success: bool = True,
    bot_id: Optional[str] = None,  # NEW
)

def record_error(
    error_type: str,
    provider: str,
    operation: str,
    bot_id: Optional[str] = None,  # NEW
)

def record_tool_failure(
    tool_name: str,
    error_type: str,
    bot_id: Optional[str] = None,  # NEW
)
```

### Query Functions (New)

```python
def get_bot_tokens(bot_id: str, since_timestamp: float = 0.0) -> Dict[str, int]:
    """Get token usage for a specific bot since a given timestamp.

    Args:
        bot_id: Unique identifier for the bot
        since_timestamp: Unix timestamp (from time.time()). Only metrics recorded after
                        this time will be included. Defaults to 0.0 (all history).

    Returns:
        dict: Dictionary with keys:
            - 'input': Total input tokens for this bot
            - 'output': Total output tokens for this bot
            - 'cached': Total cached tokens for this bot
            - 'total': Sum of input + output + cached tokens
    """

def get_bot_cost(bot_id: str, since_timestamp: float = 0.0) -> float:
    """Get total cost for a specific bot since a given timestamp.

    Args:
        bot_id: Unique identifier for the bot
        since_timestamp: Unix timestamp (from time.time()). Only costs recorded after
                        this time will be included. Defaults to 0.0 (all history).

    Returns:
        float: Total cost in USD for this bot since the given timestamp
    """

def clear_bot_metrics(bot_id: str):
    """Clear all metrics for a specific bot.

    Use this to reset a bot's metrics tracking, useful when reusing bot IDs
    or cleaning up after bot execution completes.

    Args:
        bot_id: Unique identifier for the bot
    """

def get_all_bot_ids() -> List[str]:
    """Get list of all bot IDs that have recorded metrics.

    Returns:
        list: List of bot IDs (strings)
    """

def get_and_clear_last_metrics(bot_id: Optional[str] = None):
    """Get the last recorded metrics and clear them.

    Args:
        bot_id: Optional bot identifier. If provided, returns and clears bot-specific metrics.
                If None, returns and clears global metrics (backward compatibility).

    Returns:
        dict: Dictionary with keys: input_tokens, output_tokens, cached_tokens, cost, duration
    """
```

## Usage Examples

### Basic Per-Bot Tracking

```python
from bots.observability import metrics
import time

# Start tracking for bot_1
session_start = time.time()

# Record metrics with bot_id
metrics.record_tokens(
    input_tokens=1000,
    output_tokens=500,
    provider="anthropic",
    model="claude-3-5-sonnet-latest",
    bot_id="bot_1"
)

metrics.record_cost(
    cost=0.015,
    provider="anthropic",
    model="claude-3-5-sonnet-latest",
    bot_id="bot_1"
)

# Query bot-specific metrics
bot_1_tokens = metrics.get_bot_tokens("bot_1", session_start)
print(f"Bot 1 tokens: {bot_1_tokens['total']}")

bot_1_cost = metrics.get_bot_cost("bot_1", session_start)
print(f"Bot 1 cost: ${bot_1_cost:.4f}")
```

### Concurrent Bot Execution

```python
import threading
from bots.observability import metrics

def bot_worker(bot_id: str, num_calls: int):
    """Simulate a bot making multiple API calls."""
    for i in range(num_calls):
        # Each bot records with its own bot_id
        metrics.record_tokens(
            input_tokens=100 + i,
            output_tokens=50 + i,
            provider="anthropic",
            model="claude-3-5-sonnet-latest",
            bot_id=bot_id
        )

        metrics.record_cost(
            cost=0.001 * (i + 1),
            provider="anthropic",
            model="claude-3-5-sonnet-latest",
            bot_id=bot_id
        )

# Create threads for concurrent bots
threads = []
for i in range(5):
    bot_id = f"bot_{i}"
    thread = threading.Thread(target=bot_worker, args=(bot_id, 10))
    threads.append(thread)
    thread.start()

# Wait for completion
for thread in threads:
    thread.join()

# Query each bot's metrics independently
for i in range(5):
    bot_id = f"bot_{i}"
    cost = metrics.get_bot_cost(bot_id)
    tokens = metrics.get_bot_tokens(bot_id)
    print(f"{bot_id}: ${cost:.4f}, {tokens['total']} tokens")
```

### Portfolio Manager Scenario

```python
from bots.observability import metrics
import time

class WorkOrderBot:
    def __init__(self, work_order_id: str):
        self.bot_id = f"wo_{work_order_id}"
        self.start_time = time.time()

    def execute(self):
        # Record metrics with bot_id
        metrics.record_tokens(
            input_tokens=5000,
            output_tokens=2000,
            provider="anthropic",
            model="claude-3-5-sonnet-latest",
            bot_id=self.bot_id
        )

        metrics.record_cost(
            cost=0.035,
            provider="anthropic",
            model="claude-3-5-sonnet-latest",
            bot_id=self.bot_id
        )

    def get_metrics(self):
        return {
            "tokens": metrics.get_bot_tokens(self.bot_id, self.start_time),
            "cost": metrics.get_bot_cost(self.bot_id, self.start_time)
        }

# Execute multiple work orders concurrently
bots = [WorkOrderBot(f"WO{i:03d}") for i in range(10)]

for bot in bots:
    bot.execute()

# Get accurate per-bot metrics
for bot in bots:
    metrics_data = bot.get_metrics()
    print(f"{bot.bot_id}: ${metrics_data['cost']:.4f}")
```

### Cleanup After Bot Execution

```python
from bots.observability import metrics

# Execute bot
bot_id = "temporary_bot"
metrics.record_cost(0.015, "anthropic", "claude-3-5-sonnet-latest", bot_id=bot_id)

# Get final metrics
final_cost = metrics.get_bot_cost(bot_id)
print(f"Final cost: ${final_cost:.4f}")

# Clean up
metrics.clear_bot_metrics(bot_id)

# Verify cleanup
assert metrics.get_bot_cost(bot_id) == 0.0
```

### Monitoring All Active Bots

```python
from bots.observability import metrics

# Get all bot IDs that have recorded metrics
bot_ids = metrics.get_all_bot_ids()

# Generate report for all bots
for bot_id in bot_ids:
    cost = metrics.get_bot_cost(bot_id)
    tokens = metrics.get_bot_tokens(bot_id)
    print(f"{bot_id}:")
    print(f"  Cost: ${cost:.4f}")
    print(f"  Tokens: {tokens['total']}")
    print(f"  Input: {tokens['input']}, Output: {tokens['output']}")
```

## Backward Compatibility

All existing code continues to work without modification:

```python
# Old code (still works)
metrics.record_tokens(100, 50, "anthropic", "claude-3-5-sonnet-latest")
metrics.record_cost(0.015, "anthropic", "claude-3-5-sonnet-latest")

# Global metrics still available
global_tokens = metrics.get_total_tokens(session_start)
global_cost = metrics.get_total_cost(session_start)
last_metrics = metrics.get_and_clear_last_metrics()
```

## Thread Safety

All per-bot metrics functions are thread-safe:

- Uses existing `_metrics_lock` for synchronization
- Safe for concurrent reads and writes
- No race conditions between bots
- Atomic operations for get-and-clear

## Implementation Details

### Data Structure

```python
# Per-bot metrics storage
_bot_metrics: Dict[str, Dict] = {
    "bot_1": {
        "last_metrics": {
            "input_tokens": 100,
            "output_tokens": 50,
            "cached_tokens": 0,
            "cost": 0.015,
            "duration": 2.5
        },
        "history": [
            (timestamp, input_tokens, output_tokens, cached_tokens, cost),
            ...
        ]
    },
    "bot_2": { ... }
}
```

### Timestamp Filtering

- Uses `>` (strictly greater than) for timestamp comparison
- To include recordings at exactly `start_time`, use `start_time - 0.001`
- Consistent with global metrics behavior

### Memory Management

- Metrics accumulate in memory during process lifetime
- Use `clear_bot_metrics(bot_id)` to free memory for completed bots
- Global `reset_metrics()` clears all metrics (test use only)

## Best Practices

1. **Use Unique Bot IDs**: Ensure each concurrent bot has a unique identifier
   ```python
   bot_id = f"bot_{uuid.uuid4()}"  # Guaranteed unique
   ```

2. **Clean Up After Completion**: Clear metrics for long-running processes
   ```python
   try:
       # Execute bot
       execute_bot(bot_id)
   finally:
       # Clean up
       metrics.clear_bot_metrics(bot_id)
   ```

3. **Timestamp Management**: Capture start time before any recordings
   ```python
   start_time = time.time()
   # ... record metrics ...
   cost = metrics.get_bot_cost(bot_id, start_time)
   ```

4. **Error Handling**: Record errors with bot_id for debugging
   ```python
   try:
       # Bot execution
       pass
   except Exception as e:
       metrics.record_error(
           error_type=type(e).__name__,
           provider="anthropic",
           operation="respond",
           bot_id=bot_id
       )
   ```

## Testing

See `tests/integration/test_concurrent_observability.py` for comprehensive test coverage:

- Per-bot token tracking
- Per-bot cost tracking
- Timestamp filtering
- Concurrent bot execution
- Thread safety stress tests
- Backward compatibility
- Mixed global and per-bot metrics

Run tests:
```bash
pytest tests/integration/test_concurrent_observability.py -v
```

## Migration Guide

### From Global to Per-Bot Tracking

**Before:**
```python
# Global tracking only
metrics.record_cost(0.015, "anthropic", "claude-3-5-sonnet-latest")
cost = metrics.get_total_cost(session_start)
```

**After:**
```python
# Per-bot tracking
bot_id = "my_bot_instance"
metrics.record_cost(0.015, "anthropic", "claude-3-5-sonnet-latest", bot_id=bot_id)
cost = metrics.get_bot_cost(bot_id, session_start)
```

### Gradual Migration

You can mix global and per-bot tracking:

```python
# Some bots use bot_id
metrics.record_cost(0.015, "anthropic", "claude", bot_id="bot_1")

# Some don't (backward compatible)
metrics.record_cost(0.025, "anthropic", "claude")

# Query separately
bot_1_cost = metrics.get_bot_cost("bot_1")  # Only bot_1's costs
global_cost = metrics.get_total_cost(0.0)   # All costs (including bot_1)
```

## Performance Considerations

- **Memory**: O(n) where n = number of metric recordings per bot
- **Lookup**: O(1) for bot_id lookup (dictionary-based)
- **Thread Safety**: Minimal lock contention (single lock for all operations)
- **Overhead**: Negligible (<1μs per recording)

## Troubleshooting

### Issue: Bot metrics showing zero

**Cause**: Bot ID not provided during recording

**Solution**: Ensure `bot_id` parameter is passed:
```python
metrics.record_cost(0.015, "anthropic", "claude", bot_id="my_bot")
```

### Issue: Metrics from multiple bots mixed together

**Cause**: Using same bot_id for different bots

**Solution**: Use unique bot IDs:
```python
import uuid
bot_id = f"bot_{uuid.uuid4()}"
```

### Issue: Timestamp filtering not working

**Cause**: Using `>=` semantics with `>` comparison

**Solution**: Get timestamp slightly before recording:
```python
start_time = time.time() - 0.001  # Ensure > comparison works
```

## Related Documentation

- [Observability Overview](observability.md)
- [Cost Calculator](cost_calculator.md)
- [Metrics API](metrics_api.md)
- [OpenTelemetry Integration](opentelemetry.md)
