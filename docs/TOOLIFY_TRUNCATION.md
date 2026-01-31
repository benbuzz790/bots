# @toolify Decorator Auto-Truncation
## Overview
The `@toolify` decorator includes automatic truncation to prevent context overload from very long tool outputs. This feature helps maintain manageable conversation context when tools return large amounts of data (e.g., file contents, code analysis results, API responses).
## How It Works
When a tool returns output exceeding 5000 characters, the decorator automatically truncates the output from the middle while preserving the start and end content. This ensures:
1. **Context stays manageable** - Long outputs don't overwhelm the LLM's context window
2. **Important content preserved** - First and last 2000 characters are kept intact
3. **Clear indication** - A truncation message clearly shows what happened
## Default Behavior
Truncation is **always enabled** with these settings:
- **Threshold**: 5000 characters
- **Preserve**: 2000 characters from start and end
- **Message**: "(tool result truncated from middle to save you from context overload)"
### Example
```python
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
```
## Use Cases
### 1. File Reading Tools
When reading large files, truncation prevents overwhelming context:
```python
@toolify("Read file contents")
def read_file(path: str) -> str:
    with open(path, 'r') as f:
        return f.read()
```
### 2. Code Analysis Tools
Analysis results can be verbose. Truncation keeps them manageable:
```python
@toolify("Analyze Python code")
def analyze_code(code: str) -> dict:
    return {
        "functions": [...],  # Could be hundreds
        "classes": [...],    # Could be hundreds
        "issues": [...]      # Could be many
    }
```
### 3. API Response Tools
External API responses may be large. Truncation helps:
```python
@toolify("Fetch API data")
def fetch_data(endpoint: str) -> str:
    response = requests.get(endpoint)
    return response.text  # Could be megabytes
```
## Backward Compatibility
This feature is **fully backward compatible**:
- Existing `@toolify()` usage continues to work unchanged
- Normal-sized outputs (< 5000 chars) are not affected
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
### Edge Cases
- **Exact threshold**: Outputs exactly at 5000 chars are NOT truncated
- **None results**: Not affected by truncation
- **Empty strings**: Not affected by truncation
- **Error messages**: Typically short, rarely truncated
## Testing
Comprehensive tests are available in `tests/unit/test_toolify_truncation.py`:
```bash
# Run truncation tests
pytest tests/unit/test_toolify_truncation.py -xvs
```
Tests cover:
- Normal-sized outputs (no truncation)
- Outputs exceeding threshold (truncation applied)
- Edge cases (empty, None, exact threshold)
- Different output types (strings, JSON, lists)
- Integration with @toolify decorator
## Related Documentation
- [SPEC_TOOLIFY_CONTRACTS.md](../SPEC_TOOLIFY_CONTRACTS.md) - Contract-based validation
- [bots/dev/decorators.py](../bots/dev/decorators.py) - Implementation source code
- [tests/unit/test_toolify_truncation.py](../tests/unit/test_toolify_truncation.py) - Test suite
