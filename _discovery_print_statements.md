
# Print Statement Analysis - Discovery Results

## Executive Summary

**Total print statements found: 14** (all in anthropic_bots.py)

- anthropic_bots.py: 14 statements
- openai_bots.py: 0 statements  
- gemini_bots.py: 0 statements

## Key Findings

1. **Only Anthropic implementation has print statements** - OpenAI and Gemini implementations are already clean
2. **All statements are in two methods**: `send_message()` and `process_response()`
3. **Primary purposes**: Debug flow tracking (50%), retry warnings (21%), error reporting (29%)

## Breakdown by Log Level

- **DEBUG (7)**: Flow tracking that can be replaced by OTel spans
- **WARNING (3)**: Retry attempts and recoverable errors - should be preserved as structured logs
- **ERROR (4)**: Fatal errors and max retries - should be enhanced with full context

## Action Items

### High Priority (Replace with OTel)
- Lines 269, 313, 360, 402: Simple flow tracking → Replace with span events
- Lines 331-333: Debug dump → Replace with span attributes

### Medium Priority (Convert to structured logging)
- Lines 319, 336: Retry warnings → Keep as WARNING logs with context
- Lines 275, 323, 338, 400: Error messages → Keep as ERROR logs with enhanced context
- Line 398: 400 error → Keep as WARNING log

## Implementation Strategy

1. **Phase 1**: Add OpenTelemetry spans to `send_message()` and `process_response()`
2. **Phase 2**: Remove redundant debug prints (lines 269, 313, 360, 402)
3. **Phase 3**: Convert retry/error prints to structured logging (lines 319, 323, 336, 338, 275, 398, 400)
4. **Phase 4**: Replace debug dump with span attributes (lines 331-333)

## OpenTelemetry Mapping

```python
# Before: print("mailbox send called")
# After: Span automatically records entry

# Before: print(f"Timeout on attempt {attempt + 1}. Retrying...")
# After: span.add_event("retry", {"attempt": attempt + 1, "reason": "timeout"})

# Before: print(create_dict)
# After: span.set_attribute("request.params", sanitize(create_dict))
```

## Conclusion

The migration is straightforward:
- ✅ Only one file needs modification (anthropic_bots.py)
- ✅ Clear mapping from prints to OTel concepts
- ✅ No breaking changes required
- ✅ Improved observability with structured data
