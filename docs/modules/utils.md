# Utils Module

**Module**: `bots/utils/`
**Version**: 3.0.0

## Overview

Utility functions and helpers

## Architecture

```
utils/
├── __init__.py
├── compile_bot_errors.py
├── helpers.py
├── logging.py
├── unicode_utils.py
```

## Key Components

### LogLevel

Log levels for the bots framework.


## Usage Examples

```python
from bots.utils import *

# Usage examples coming soon
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `find_tool_results` | Function | Find all tool result JSON-like structures in the content. |
| `has_error_content` | Function | Check if a tool result contains error-related content. |
| `process_bot_file` | Function | Process a single .bot file and extract error messages from t |
| `main` | Function | Process all .bot files in the current directory and generate |
| `remove_code_blocks` | Function | Extract code blocks and language labels from markdown-format |
| `formatted_datetime` | Function | Get current datetime formatted as a string suitable for file |
| `LogLevel` | Class | Log levels for the bots framework. |
| `LogCategory` | Class | Log categories for different framework components. |
| `BotsLogger` | Class | Centralized logger for the bots framework. |
| `get_logger` | Function | Get or create the global logger instance. |
| `configure_logging` | Function | Configure the global logging system. |
| `debug` | Function | Log a debug message using the global logger. |
| `info` | Function | Log an info message using the global logger. |
| `warning` | Function | Log a warning message using the global logger. |
| `error` | Function | Log an error message using the global logger. |
| `critical` | Function | Log a critical message using the global logger. |
| `log_context` | Function | Add context to all log messages within this block using the  |
| `log_performance` | Function | Context manager for logging operation performance. |
| `context` | Function | Add context to all log messages within this block. |
| `debug` | Function | Log a debug message. |
| `info` | Function | Log an info message. |
| `warning` | Function | Log a warning message. |
| `error` | Function | Log an error message. |
| `critical` | Function | Log a critical message. |
| `bot_info` | Function | Log bot-related info. |
| `bot_error` | Function | Log bot-related error. |
| `conversation_info` | Function | Log conversation-related info. |
| `tool_info` | Function | Log tool-related info. |
| `tool_error` | Function | Log tool-related error. |
| `api_info` | Function | Log API-related info. |
| `api_error` | Function | Log API-related error. |
| `fp_info` | Function | Log functional prompt-related info. |
| `fp_error` | Function | Log functional prompt-related error. |
| `performance_log` | Function | Log performance metrics. |
| `ensure_utf8_encoding` | Function | Ensure proper UTF-8 encoding for the current environment. |
| `clean_unicode_string` | Function | Clean a string of problematic Unicode characters. |
| `clean_dict_strings` | Function | Recursively clean all strings in a dictionary or list. |
