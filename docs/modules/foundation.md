# Foundation Module

**Module**: `bots/foundation/`
**Version**: 3.0.0

## Overview

Core bot implementations and model registry

## Architecture

```
foundation/
├── __init__.py
├── anthropic_bots.py
├── base.py
├── gemini_bots.py
├── model_registry.py
├── openai_bots.py
```

## Key Components

### AnthropicNode

A conversation node implementation specific to Anthropic's API

### Engines

Enum class representing different AI model engines.

### GeminiNode

Conversation node implementation for Gemini's chat format.


## Usage Examples

```python
from bots.foundation import ClaudeBot

# Create a bot instance
bot = ClaudeBot(model="claude-sonnet-4-20250514")

# Send a message
response = bot("What is the capital of France?")
print(response)
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `AnthropicNode` | Class | A conversation node implementation specific to Anthropic's A |
| `AnthropicToolHandler` | Class | Tool handler implementation specific to Anthropic's API |
| `AnthropicMailbox` | Class | Handles communication with Anthropic's API. |
| `AnthropicBot` | Class | A bot implementation using the Anthropic API. |
| `CacheController` | Class | Manages cache control directives in Anthropic message histor |
| `generate_tool_schema` | Function | Generate Anthropic-compatible tool schema from a Python func |
| `generate_request_schema` | Function | Generate request schema from an Anthropic API response. |
| `tool_name_and_input` | Function | Extract tool name and input parameters from a request schema |
| `generate_response_schema` | Function | Generate response schema for tool execution results. |
| `generate_error_schema` | Function | Generate an error response schema in Anthropic's format. |
| `send_message` | Function | Send a message to the Anthropic API with retry logic. |
| `process_response` | Function | Process the API response and handle incomplete responses. |
| `find_cache_control_positions` | Function | Find positions of all cache control directives in the messag |
| `should_add_cache_control` | Function | Determine if a new cache control directive should be added. |
| `shift_cache_control_out_of_tool_block` | Function | Move cache control directives out of tool-related message bl |
| `insert_cache_control` | Function | Insert a cache control directive at the specified position. |
| `remove_cache_control_at_position` | Function | Remove cache control directive at the specified position. |
| `manage_cache_controls` | Function | Manage cache control directives across the entire message hi |
| `should_continue` | Function | Determine if response continuation is needed. |
| `load` | Function | Load a saved bot from a file. |
| `Engines` | Class | Enum class representing different AI model engines. |
| `ConversationNode` | Class | Tree-based storage for conversation history and tool interac |
| `ModuleContext` | Class | Context container for module-level tool preservation. |
| `ToolHandlerError` | Class | Base exception class for ToolHandler errors. |
| `ToolNotFoundError` | Class | Raised when a requested tool is not available. |
| `ModuleLoadError` | Class | Raised when a module cannot be loaded for tool extraction. |
| `ToolHandler` | Class | Abstract base class for managing bot tool operations. |
| `Mailbox` | Class | Abstract base class for LLM service communication. |
| `Bot` | Class | Abstract base class for LLM-powered conversational agents. |
| `get` | Function | Retrieve an Engines enum member by its string value. |
| `get_bot_class` | Function | Get the appropriate Bot subclass for a given model engine. |
| `get_conversation_node_class` | Function | Get the appropriate ConversationNode subclass by name. |
| `get_info` | Function | Get basic information about this model. |
| `tool_results` | Function | Get tool results. |
| `tool_results` | Function | Set tool results with validation. |
| `generate_tool_schema` | Function | Generate the tool schema for the bot's api. Must be implemen |
| `generate_request_schema` | Function | Extract tool requests from an LLM response. Must be implemen |
| `tool_name_and_input` | Function | Extract tool name and parameters from a request schema. Must |
| `generate_response_schema` | Function | Generate a response schema from tool execution results. Must |
| `generate_error_schema` | Function | Generate an error response schema. Must be implemented per p |
| `extract_requests` | Function | Extract and parse tool requests from an LLM response. |
| `exec_requests` | Function | Execute pending tool requests and generate results. |
| `add_tool` | Function | Add a single Python function as a tool for LLM use. |
| `register_tool` | Function | Add tool to registry without loading it into active tools. |
| `load_tool_by_name` | Function | Load a specific tool from registry into active tools. |
| `unload_tool` | Function | Remove tool from active set (but keep in registry). |
| `get_registry_info` | Function | Get info about available tools in registry. |
| `to_dict` | Function | Serialize the ToolHandler state to a dictionary. |
| `from_dict` | Function | Reconstruct a ToolHandler instance from serialized state. |
| `get_tools_json` | Function | Get a JSON string representation of all registered tools. |
| `clear` | Function | Clear all stored tool results and requests. |
| `add_request` | Function | Add a new tool request to the pending requests. |
| `add_result` | Function | Add a new tool result to the stored results. |
| `get_results` | Function | Get all stored tool execution results. |
| `get_requests` | Function | Get all stored tool requests. |
| `log_message` | Function | Logs a message with timestamp and direction to the log file. |
| `send_message` | Function | Send a message to the LLM service. |
| `process_response` | Function | Process the raw LLM response into a standardized format. |
| `respond` | Function | Send a prompt to the bot and get its response. |
| `add_tools` | Function | Add Python functions as tools available to the bot. |
| `set_system_message` | Function | Set the system-level instructions for the bot. |
| `load` | Function | Load a saved bot from a file. |
| `save` | Function | Save the bot's complete state to a file. |
| `chat` | Function | Start an interactive chat session with the bot. |
| `is_tracing_enabled` | Function | Checks if tracing functionality is currently enabled. |
| `get_default_tracing_preference` | Function | Returns the default tracing preference setting. |
| `make_hash` | Function | Create hash of result for deduplication. |
| `process_item` | Function | Process a tool item by adding it to the tool handler based o |
| `format_conversation` | Function | Format conversation node display with appropriate indentatio |
| `AnnotationVisitor` | Class | Visits function definition nodes to extract type annotation  |
| `placeholder_func` | Function | Placeholder function that displays information about a dynam |
| `visit_FunctionDef` | Function | Visit a function definition node and extract names from type |
| `visit_AsyncFunctionDef` | Function | Visit an async function definition node and extract type ann |
| `NameCollector` | Class | Visits Name nodes in an AST and collects variable names that |
| `visit_Name` | Function | Visits AST Name nodes and tracks loaded variable names. |
| `GeminiNode` | Class | Conversation node implementation for Gemini's chat format. |
| `GeminiToolHandler` | Class | Tool handler for Gemini's function calling format. |
| `GeminiMailbox` | Class | Mailbox implementation for Gemini API communication. |
| `GeminiBot` | Class | Bot implementation using the Gemini API. |
| `generate_tool_schema` | Function | Generate a JSON schema representation for a given function. |
| `generate_request_schema` | Function | Extracts function call schemas from a Gemini API response. |
| `tool_name_and_input` | Function | Extract tool name and input arguments from a request schema  |
| `generate_response_schema` | Function | Generate a response schema for tool output in Gemini format. |
| `generate_error_schema` | Function | Generate an error response schema for tool calls. |
| `send_message` | Function | Send a message to the Gemini API with metrics tracking. |
| `process_response` | Function | Processes a response from the bot, handling function calls r |
| `get_model_info` | Function | Get complete information for a model by name. |
| `get_provider_discounts` | Function | Get discount configuration for a provider. |
| `OpenAINode` | Class | A conversation node implementation specific to OpenAI's chat |
| `OpenAIToolHandler` | Class | Tool handler implementation specific to OpenAI's function ca |
| `OpenAIMailbox` | Class | Mailbox implementation for handling OpenAI API communication |
| `ChatGPT_Bot` | Class | A bot implementation using the OpenAI GPT API. |
| `generate_tool_schema` | Function | Generate OpenAI-compatible function definitions from Python |
| `generate_request_schema` | Function | Extract tool calls from OpenAI API responses. |
| `tool_name_and_input` | Function | Parse OpenAI's function call format into tool name and argum |
| `generate_response_schema` | Function | Format tool execution results for OpenAI's expected format. |
| `generate_error_schema` | Function | Generate an error response in OpenAI's expected format. |
| `send_message` | Function | Send a message to OpenAI's chat completion API. |
| `process_response` | Function | Process OpenAI's response and handle any tool calls recursiv |
