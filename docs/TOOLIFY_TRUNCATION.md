# @toolify Decorator Auto-Truncation
## Overview
The `@toolify` decorator includes automatic truncation as an emergency measure to prevent context overload from pathological cases where tools return extremely large outputs.
## How It Works
When a tool returns output exceeding 500,000 characters, the decorator automatically truncates the output from the middle while preserving the start and end content. This is an emergency safeguard for extreme cases.
## Default Behavior
Truncation is **always enabled** with these settings:
- **Threshold**: 500,000 characters (~5,000 lines at 100 chars/line)
- **Preserve**: 100,000 characters from start and end
- **Message**: "(tool result truncated from middle to save you from context overload)"
This is intentionally set very high - it's an emergency measure, not an efficiency technique.
### Example
```python
from bots.dev.decorators import toolify
@toolify()
def read_massive_file(filename: str) -> str:
    """Read and return file contents."""
    with open(filename, 'r') as f:
        return f.read()
# Only if file is > 500,000 chars will output be truncated:
# [First 100,000 chars]
#
# ... (tool result truncated from middle to save you from context overload) ...
#
# [Last 100,000 chars]
```
## Use Cases
This is primarily for pathological cases:
- Accidentally reading a multi-megabyte file
- API responses that return unexpectedly large datasets
- Runaway output generation
For normal use, outputs should be well under the 500k threshold.
## Backward Compatibility
This feature is **fully backward compatible**:
- Existing `@toolify()` usage continues to work unchanged
- Normal-sized outputs (< 500k chars) are not affected
- No changes to tool function signatures required
## Technical Details
### Implementation
Truncation occurs in the `_convert_tool_output()` function after:
1. Tool execution completes
2. Result is converted to string
3. Before returning to the LLM
### Performance
- **Minimal overhead** - Only checks length and slices strings
- **No parsing** - Works on final string output
- **No buffering** - Processes output after tool completes
## Testing
Tests are available in `tests/unit/test_toolify_truncation.py`:
```bash
# Run truncation tests
pytest tests/unit/test_toolify_truncation.py -xvs
```
## Related Documentation
- [SPEC_TOOLIFY_CONTRACTS.md](../SPEC_TOOLIFY_CONTRACTS.md) - Contract-based validation
- [bots/dev/decorators.py](../bots/dev/decorators.py) - Implementation source code
- [tests/unit/test_toolify_truncation.py](../tests/unit/test_toolify_truncation.py) - Test suite