
## OpenAI Bots Instrumentation Summary

### File: bots/foundation/openai_bots.py

#### Changes Made:

1. **Added Tracing Import** (lines 29-38)
   - Imported `get_tracer` from `bots.observability.tracing`
   - Imported `trace` from `opentelemetry` for status handling
   - Added `TRACING_AVAILABLE` flag for graceful degradation
   - Wrapped in try/except for optional dependency

2. **Instrumented send_message() Method** (lines 321-330)
   - Added check for `bot._tracing_enabled` attribute
   - Created span "mailbox.send_message" when tracing is enabled
   - Set attributes:
     - `provider`: "openai"
     - `model`: The model engine value
   - Delegates to `_send_message_impl()` with optional span

3. **Created _send_message_impl() Method** (lines 332-384)
   - Extracted original implementation to separate method
   - Accepts optional `span` parameter
   - Sets `message_count` attribute on span (line 338)
   - Captures token usage after API call (lines 374-377):
     - `input_tokens`: prompt_tokens
     - `output_tokens`: completion_tokens
     - `total_tokens`: total_tokens
   - Records exceptions on span (lines 381-383)
   - Sets error status on span when exceptions occur

4. **Print Statements**
   - ✓ No print() statements found in openai_bots.py
   - No changes needed

#### Span Attributes Captured:
- `provider`: "openai"
- `model`: Model name (e.g., "gpt-4")
- `message_count`: Number of messages in conversation
- `input_tokens`: Tokens sent to API
- `output_tokens`: Tokens received from API
- `total_tokens`: Total tokens used

#### Error Handling:
- Exceptions are recorded on the span
- Span status is set to ERROR with exception message
- Original exception is re-raised (no behavior change)

#### Backward Compatibility:
- ✓ Tracing is optional (graceful degradation if not available)
- ✓ Only traces if `bot._tracing_enabled` is True
- ✓ No changes to method signatures
- ✓ No changes to return values or behavior
