# OpenTelemetry Instrumentation Points in base.py

## Bot Class Methods

### 1. `Bot.respond(self, prompt: str, role: str = "user") -> str`
**What it does**: Primary interface for bot interaction. Adds prompt to conversation, calls _cvsn_respond(), returns response.

**Span attributes to capture**:
- `bot.name` - Bot instance name
- `bot.model` - Model engine being used (e.g., "claude-3-5-sonnet")
- `prompt.length` - Length of user prompt
- `prompt.role` - Role of the message sender
- `conversation.depth` - Current depth in conversation tree
- `autosave.enabled` - Whether autosave is on

**Span name**: `bot.respond`

---

### 2. `Bot._cvsn_respond(self) -> Tuple[str, ConversationNode]`
**What it does**: Core conversation logic. Clears tool handler, sends message via mailbox, extracts tool requests, processes response, executes tools, adds results to conversation.

**Span attributes to capture**:
- `tool_handler.cleared` - Tool handler was cleared
- `tools.requested_count` - Number of tool requests extracted
- `tools.executed_count` - Number of tools executed
- `response.text_length` - Length of response text
- `conversation.node_id` - ID of new conversation node

**Span name**: `bot._cvsn_respond`

**Child spans**:
- Calls `mailbox.send_message()` - should have its own span
- Calls `tool_handler.exec_requests()` - should have its own span

---

## ToolHandler Class Methods

### 3. `ToolHandler.exec_requests(self) -> List[Dict[str, Any]]`
**What it does**: Executes all pending tool requests. Iterates through requests, looks up functions, executes them, handles errors, generates response schemas.

**Span attributes to capture**:
- `tools.request_count` - Number of tool requests to execute
- `tools.success_count` - Number of successful executions
- `tools.error_count` - Number of failed executions

**Span name**: `tools.execute_all`

**Child spans** (one per tool):
- `tool.{tool_name}` for each individual tool execution
  - `tool.name` - Name of the tool
  - `tool.input_size` - Size of input arguments (JSON length)
  - `tool.output_size` - Size of output (string length)
  - `tool.execution_time` - Duration (automatic from span)
  - `tool.status` - "success" or "error"
  - `tool.error_type` - Type of error if failed (ToolNotFoundError, TypeError, etc.)

---

### 4. `ToolHandler.extract_requests(self, response: Any) -> List[Dict[str, Any]]`
**What it does**: Extracts tool requests from LLM response using generate_request_schema.

**Span attributes to capture**:
- `requests.extracted_count` - Number of tool requests found
- `response.type` - Type of response object

**Span name**: `tools.extract_requests`

---

## Mailbox Class Methods

### 5. `Mailbox.send_message(self, bot: Bot) -> Dict[str, Any]`
**What it does**: Abstract method - sends message to LLM service. Implemented in provider-specific subclasses.

**Span attributes to capture** (in subclass implementations):
- `provider` - Provider name (e.g., "anthropic", "openai", "gemini")
- `model` - Model name
- `messages.count` - Number of messages in conversation
- `messages.total_length` - Total character count of all messages
- `tools.available_count` - Number of tools available
- `api.timeout` - Timeout setting
- `api.retry_count` - Number of retries attempted (if any)
- `api.cache_used` - Whether cache was used (Anthropic-specific)

**Span name**: `mailbox.send_message`

**Child span** (for actual API call):
- `api.call.{provider}` 
  - `api.request_id` - Request ID from provider
  - `api.latency_ms` - API call latency
  - `usage.input_tokens` - Input tokens consumed
  - `usage.output_tokens` - Output tokens generated
  - `usage.cache_read_tokens` - Cache read tokens (if applicable)
  - `usage.cache_creation_tokens` - Cache creation tokens (if applicable)
  - `cost.input_usd` - Estimated input cost
  - `cost.output_usd` - Estimated output cost
  - `cost.total_usd` - Total estimated cost

---

### 6. `Mailbox.process_response(self, response: Dict[str, Any], bot: Optional[Bot] = None) -> Tuple[str, str, Dict[str, Any]]`
**What it does**: Processes raw LLM response into standardized format.

**Span attributes to capture**:
- `response.role` - Role from response
- `response.text_length` - Length of response text
- `response.has_metadata` - Whether metadata was included
- `response.stop_reason` - Why the model stopped (if available)

**Span name**: `mailbox.process_response`

---

## Summary of Instrumentation Points

**Total methods to instrument**: 6 core methods

**Hierarchy**:
```
bot.respond
└── bot._cvsn_respond
    ├── mailbox.send_message
    │   └── api.call.{provider}
    ├── mailbox.process_response
    └── tools.execute_all
        ├── tool.{tool_name_1}
        ├── tool.{tool_name_2}
        └── tool.{tool_name_n}
```

**Key metrics to derive**:
- Total API calls per session
- Total tokens consumed (input + output)
- Total cost per session
- Tool usage frequency
- Average response time
- Error rates by tool
- Cache hit rates (Anthropic)
