# @toolify Decorator Auto-Truncation
## Overview
The `@toolify` decorator now includes automatic truncation to prevent context overload from very long tool outputs. This feature helps maintain manageable conversation context when tools return large amounts of data (e.g., file contents, code analysis results, API responses).
## How It Works
When a tool returns output exceeding a configurable threshold, the decorator automatically truncates the output from the middle while preserving the start and end content. This ensures:
1. **Context stays manageable** - Long outputs don't overwhelm the LLM's context window
2. **Important content preserved** - Start and end of outputs are kept intact
3. **Clear indication** - A truncation message clearly shows what happened
4. **Configurable behavior** - Thresholds can be adjusted per use case
## Default Behavior
By default, truncation is **enabled** with these settings:
- **Threshold**: 5000 characters
- **Preserve**: 2000 characters from start and end
- **Message**: "(tool result truncated from middle to save you from context overload)"
### Example
``python
from bots.dev.decorators import toolify
@toolify()
def read_large_file(filename: str) -> str:
    """Read and return file contents."""
    with open(filename, 'r') as f:
        return f.read()
# If file is > 5000 chars, output will be truncated:
# [First 2000 chars]
#
# ... (tool result truncated from middle to save you from context overload) ...
#
# [Last 2000 chars]
``
## Configuration
Truncation behavior is controlled via environment variables:
### TOOLIFY_TRUNCATE_ENABLED
Enable or disable truncation globally.
- **Values**: `"true"` or `"false"`
- **Default**: `"true"`
``bash
# Disable truncation
export TOOLIFY_TRUNCATE_ENABLED="false"
``
### TOOLIFY_TRUNCATE_THRESHOLD
Maximum characters before truncation is applied.
- **Type**: Integer (as string)
- **Default**: `"5000"`
``bash
# Increase threshold to 10000 characters
export TOOLIFY_TRUNCATE_THRESHOLD="10000"
``
### TOOLIFY_TRUNCATE_PRESERVE
Number of characters to preserve from start and end.
- **Type**: Integer (as string)
- **Default**: `"2000"`
``bash
# Preserve more content (3000 chars from each end)
export TOOLIFY_TRUNCATE_PRESERVE="3000"
``
## Use Cases
### 1. File Reading Tools
When reading large files, truncation prevents overwhelming context:
``python
@toolify("Read file contents")
def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()
``
### 2. Code Analysis Tools
Analysis results can be verbose. Truncation keeps them manageable:
``python
@toolify("Analyze Python code")
def analyze_code(code: str) -> dict:
    return {
        "functions": [...],  # Could be hundreds
        "classes": [...],    # Could be hundreds
        "issues": [...]      # Could be many
    }
``
### 3. API Response Tools
External API responses may be large. Truncation helps:
``python
@toolify("Fetch API data")
def fetch_data(endpoint: str) -> str:
    response = requests.get(endpoint)
    return response.text  # Could be megabytes
``
## Configuration Examples
### Development Environment (More Verbose)
``bash
# See more output during development
export TOOLIFY_TRUNCATE_THRESHOLD="10000"
export TOOLIFY_TRUNCATE_PRESERVE="4000"
``
### Production Environment (More Aggressive)
``bash
# Tighter limits for production
export TOOLIFY_TRUNCATE_THRESHOLD="3000"
export TOOLIFY_TRUNCATE_PRESERVE="1000"
``
### Debugging (Disable Truncation)
``bash
# See full outputs when debugging
export TOOLIFY_TRUNCATE_ENABLED="false"
``
## Best Practices
1. **Keep defaults for most cases** - The default settings (5000/2000) work well for typical use
2. **Adjust per environment** - Use different settings for dev vs production
3. **Consider tool purpose** - Tools that return structured data may need higher thresholds
4. **Monitor context usage** - If you hit context limits, lower thresholds
5. **Test with real data** - Verify truncation works well with your actual tool outputs
## Backward Compatibility
This feature is **fully backward compatible**:
- Existing `@toolify()` usage continues to work unchanged
- Normal-sized outputs (< threshold) are not affected
- No changes to tool function signatures required
- Can be disabled entirely if needed
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
### Edge Cases
- **Exact threshold**: Outputs exactly at threshold are NOT truncated
- **Invalid config**: Falls back to defaults if env vars are invalid
- **None results**: Not affected by truncation
- **Empty strings**: Not affected by truncation
- **Error messages**: Typically short, rarely truncated
## Testing
Comprehensive tests are available in `tests/unit/test_toolify_truncation.py`:
``bash
# Run truncation tests
pytest tests/unit/test_toolify_truncation.py -xvs
``
Tests cover:
- Normal-sized outputs (no truncation)
- Outputs exceeding threshold (truncation applied)
- Configuration via environment variables
- Edge cases (empty, None, exact threshold)
- Different output types (strings, JSON, lists)
- Integration with @toolify decorator
## Troubleshooting
### Outputs still too long?
Lower the threshold:
``bash
export TOOLIFY_TRUNCATE_THRESHOLD="2000"
``
### Need to see full output?
Disable truncation temporarily:
``bash
export TOOLIFY_TRUNCATE_ENABLED="false"
``
### Truncation too aggressive?
Increase preserve amount:
``bash
export TOOLIFY_TRUNCATE_PRESERVE="3000"
``
### Want different settings per tool?
Currently, settings are global. For per-tool control, you can:
1. Wrap your tool function with custom truncation logic
2. Use environment variables in different processes
3. Request per-tool configuration as a feature enhancement
## Future Enhancements
Potential improvements (not currently implemented):
- Per-tool truncation settings via decorator parameters
- Smart truncation based on content type (JSON, code, text)
- Configurable truncation message
- Metrics on truncation frequency
- Adaptive thresholds based on context usage
## Related Documentation
- [SPEC_TOOLIFY_CONTRACTS.md](../SPEC_TOOLIFY_CONTRACTS.md) - Contract-based validation
- [bots/dev/decorators.py](../bots/dev/decorators.py) - Implementation source code
- [tests/unit/test_toolify_truncation.py](../tests/unit/test_toolify_truncation.py) - Test suite
