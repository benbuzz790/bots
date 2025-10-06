# OpenTelemetry Implementation Requirements Checklist

## Extracted from ROADMAP.md Item #14

### 1. Metrics to Track

#### Performance Metrics
- [ ] `bot.response_time` - Total time for bot.respond()
- [ ] `bot.api_call_duration` - Time spent in API calls
- [ ] `bot.tool_execution_duration` - Time spent executing tools
- [ ] `bot.message_building_duration` - Time building messages

#### Usage Metrics
- [ ] `bot.api_calls_total` - Count of API calls (by provider, model)
- [ ] `bot.tool_calls_total` - Count of tool executions (by tool name)
- [ ] `bot.conversations_total` - Count of conversations
- [ ] `bot.tokens_used` - Token usage (input/output, by provider)

#### Cost Metrics
- [ ] `bot.cost_usd` - Cost in USD (by provider, model)
- [ ] `bot.cost_per_conversation` - Average cost per conversation

#### Error Metrics
- [ ] `bot.errors_total` - Count of errors (by type, provider)
- [ ] `bot.tool_failures_total` - Count of tool failures (by tool)

### 2. Span Attributes to Capture

#### Bot-level Attributes
- [ ] `prompt_length` - Length of user prompt
- [ ] `provider` - LLM provider (anthropic, openai, google)
- [ ] `model` - Model name
- [ ] `bot.name` - Bot instance name
- [ ] `message_count` - Number of messages in conversation

#### API Call Attributes
- [ ] `input_tokens` - Tokens sent to API
- [ ] `output_tokens` - Tokens received from API
- [ ] `cost_usd` - Cost of this API call

#### Tool Execution Attributes
- [ ] `tool_count` - Number of tools called
- [ ] `tool_name` - Name of specific tool
- [ ] `tool_args` - Arguments passed to tool
- [ ] `tool_result_length` - Length of tool result

### 3. Span Structure (Nested Hierarchy)

```
bot.respond
├── build_messages
├── api_call
├── process_response
└── execute_tools
    ├── tool.{tool_name_1}
    └── tool.{tool_name_2}
```

### 4. Integration with Other ROADMAP Items

#### Item #11: Remove Print Statements
- [ ] Replace print statements in anthropic_bots.py
- [ ] Replace print statements in openai_bots.py
- [ ] Replace print statements in gemini_bots.py
- [ ] Use `logger.info()` with structured context
- [ ] Use `span.add_event()` for important events

#### Item #12: Enable Callbacks
- [ ] Callback interface can use `trace.get_current_span()`
- [ ] `on_step_start()` → `span.add_event("step.{name}.start")`
- [ ] `on_step_complete()` → `span.add_event("step.{name}.complete")`

### 5. Phase 1 Implementation Checklist (CURRENT FOCUS)

- [ ] Install OpenTelemetry packages: `opentelemetry-api`, `opentelemetry-sdk`
- [ ] Create `bots/observability/tracing.py` module
- [ ] Initialize TracerProvider with ConsoleSpanExporter
- [ ] Add tracing to `Bot.respond()` method
- [ ] Add tracing to `Bot._cvsn_respond()` method
- [ ] Add tracing to `ToolHandler.exec_requests()` method
- [ ] Add tracing to `AnthropicMailbox.send_message()`
- [ ] Add tracing to `OpenAIMailbox.send_message()`
- [ ] Add tracing to `GeminiMailbox.send_message()`
- [ ] Support `enable_tracing` parameter in Bot.__init__()
- [ ] Support `OTEL_SDK_DISABLED` environment variable
- [ ] Replace print statements with structured logging
- [ ] Test with console exporter

### 6. Specific Code Locations

#### base.py
- `Bot.respond()` - Main entry point
- `Bot._cvsn_respond()` - Core conversation logic
- `ToolHandler.exec_requests()` - Tool execution loop

#### Provider implementations
- `AnthropicMailbox.send_message()` - API call + token capture
- `OpenAIMailbox.send_message()` - API call + token capture
- `GeminiMailbox.send_message()` - API call + token capture
