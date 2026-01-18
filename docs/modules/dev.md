# Dev Module

**Module**: `bots/dev/`
**Version**: 3.0.0

## Overview

Development tools, CLI, and bot session management

## Architecture

```
dev/
├── __init__.py
├── __main__.py
├── bot_session.py
├── cli.py
├── cli_frontend.py
    ├── __init__.py
    ├── __main__.py
        ├── __init__.py
├── decorators.py
├── pr_comment_parser.py
    └── ... (3 more files)
```

## Key Components

### BotSession

Simple session interface for bot interactions.

### EscapeException

Exception raised when user presses ESC to cancel input.

### CLIFrontend

Abstract base class for CLI frontends.


## Usage Examples

```python
from bots.dev import *

# Usage examples coming soon
```

## API Reference

### Classes and Functions

| Name | Type | Description |
|------|------|-------------|
| `BotSession` | Class | Simple session interface for bot interactions. |
| `input` | Function | Process user input and return response. |
| `bot` | Function | Get the current bot instance. |
| `get_config` | Function | Get the current configuration. |
| `set_config` | Function | Update configuration settings. |
| `EscapeException` | Class | Exception raised when user presses ESC to cancel input. |
| `input_with_esc` | Function | Get user input with ESC key support to cancel/interrupt. |
| `create_auto_stash` | Function | Create an automatic git stash with AI-generated message base |
| `DynamicParameterCollector` | Class | Dynamically collect parameters for functional prompts based  |
| `CLIConfig` | Class | Configuration management for CLI settings. |
| `RealTimeDisplayCallbacks` | Class | Callback that displays bot response and tools in real-time a |
| `CLICallbacks` | Class | Centralized callback management for CLI operations. |
| `CLIContext` | Class | Shared context for CLI operations. |
| `PromptManager` | Class | Manager for saving, loading, and editing prompts with recenc |
| `ConversationHandler` | Class | Handler for conversation navigation commands. |
| `StateHandler` | Class | Handler for bot state management commands. |
| `SystemHandler` | Class | Handler for system and configuration commands. |
| `DynamicFunctionalPromptHandler` | Class | Handler for functional prompt commands using dynamic paramet |
| `BackupHandler` | Class | Handler for backup management commands. |
| `format_tool_data` | Function | Format tool arguments or results in a clean, minimal way. |
| `check_for_interrupt` | Function | Check if user pressed Escape without blocking execution. |
| `setup_raw_mode` | Function | Set up terminal for raw input mode on Unix systems. |
| `restore_terminal` | Function | Restore terminal settings on Unix systems. |
| `clean_dict` | Function | Clean a dict containing recursive json dumped strings for pr |
| `display_metrics` | Function | Display API metrics if verbose mode is on. |
| `pretty` | Function | Print a string nicely formatted with explicit color. |
| `CLI` | Class | Main CLI class that orchestrates all handlers. |
| `PromptHandler` | Class | Handler for prompt management commands. |
| `parse_args` | Function | Parse command line arguments. |
| `main` | Function | Entry point for the CLI. |
| `dfs` | Function | Performs depth-first search traversal to find all leaf nodes |
| `collect_parameters` | Function | Dynamically collect parameters based on function signature. |
| `load_config` | Function | Load configuration from file if it exists. |
| `save_config` | Function | Save current configuration to file. |
| `on_api_call_complete` | Function | Display bot response immediately after API call completes, b |
| `on_tool_start` | Function | Display tool request when it starts - show only the tool nam |
| `on_tool_complete` | Function | Display tool result when it completes - show just the result |
| `create_message_only_callback` | Function | Create a callback that only prints bot messages, no tool inf |
| `create_verbose_callback` | Function | Create a callback that shows only metrics. |
| `create_quiet_callback` | Function | Create a callback that shows only user and bot messages (no  |
| `get_standard_callback` | Function | Get the standard callback based on current config settings. |
| `create_backup` | Function | Create a complete backup of the current bot. |
| `restore_backup` | Function | Restore bot from backup. |
| `has_backup` | Function | Check if a backup is available. |
| `get_backup_info` | Function | Get information about the current backup. |
| `search_prompts` | Function | Search prompts by name and content. Returns list of (name, c |
| `save_prompt` | Function | Save a prompt with optional name. If no name, generate one. |
| `load_prompt` | Function | Load a prompt by name and update recency. |
| `get_prompt_names` | Function | Get all prompt names. |
| `delete_prompt` | Function | Delete a prompt by name. Returns True if deleted, False if n |
| `get_recents` | Function | Get recent prompts as list of (name, content) tuples. |
| `up` | Function | Move up in conversation tree. |
| `down` | Function | Move down in conversation tree. |
| `left` | Function | Move left to sibling in conversation tree. |
| `right` | Function | Move right to sibling in conversation tree. |
| `root` | Function | Move to root of conversation tree. |
| `lastfork` | Function | Move to the previous node (going up the tree) that has multi |
| `nextfork` | Function | Move to the next node (going down the tree) that has multipl |
| `label` | Function | Show all labels and create new label or jump to existing one |
| `leaf` | Function | Show all leaf nodes and optionally jump to one by number. |
| `combine_leaves` | Function | Combine all leaves below current node using a recombinator f |
| `save` | Function | Save bot state. |
| `load` | Function | Load bot state. |
| `help` | Function | Display help information about available commands. |
| `verbose` | Function | Enable verbose mode. |
| `quiet` | Function | Disable verbose mode. |
| `config` | Function | Show or modify configuration. |
| `auto` | Function | Run bot autonomously until it stops using tools. |
| `auto_stash` | Function | Toggle auto git stash functionality. |
| `load_stash` | Function | Load a git stash by name or index. |
| `add_tool` | Function | Add a tool to the bot from a Python file or module. |
| `models` | Function | Display available models with metadata. |
| `switch` | Function | Switch to a different model within the same provider. |
| `clear` | Function | Clear the terminal screen. |
| `execute` | Function | Execute functional prompt wizard with dynamic parameter coll |
| `broadcast_fp` | Function | Execute broadcast_fp functional prompt with leaf selection b |
| `backup` | Function | Manually create a backup of current bot state. |
| `restore` | Function | Restore bot from backup. |
| `backup_info` | Function | Show information about current backup. |
| `undo` | Function | Quick restore from backup (alias for /restore). |
| `last_user_message` | Function | Get last user message from session. |
| `last_user_message` | Function | Set last user message in session. |
| `pending_prefill` | Function | Get pending prefill from session. |
| `pending_prefill` | Function | Set pending prefill in session. |
| `run` | Function | Main CLI loop with terminal I/O. |
| `load_prompt` | Function | Load a saved prompt by name or search query. |
| `save_prompt` | Function | Save a prompt. If args provided, save the args. Otherwise sa |
| `delete_prompt` | Function | Delete a saved prompt. |
| `recent_prompts` | Function | Show recently used prompts with search capability. |
| `message_only_callback` | Function | Callback function that displays only the last bot response m |
| `verbose_callback` | Function | Callback function that displays bot metrics after processing |
| `quiet_callback` | Function | Callback function for quiet mode operation that suppresses t |
| `find_path_length` | Function | Find the depth of a target node in a tree structure using de |
| `startup_hook` | Function | Startup hook function that inserts prefilled text into the r |
| `stop_on_no_tools` | Function | Determines whether the bot should stop based on the absence  |
| `auto_callback` | Function | Updates cooldown settings based on input token metrics from  |
| `combined_callback` | Function | Executes both auto callback and display callback functions i |
| `single_callback` | Function | Formats and displays a single response from a bot node using |
| `CLIFrontend` | Class | Abstract base class for CLI frontends. |
| `TerminalFrontend` | Class | Terminal-based frontend implementation. |
| `display_message` | Function | Display a conversation message. |
| `display_system` | Function | Display a system message. |
| `display_error` | Function | Display an error message. |
| `display_metrics` | Function | Display API usage metrics. |
| `display_tool_call` | Function | Display a tool being called. |
| `display_tool_result` | Function | Display a tool execution result. |
| `get_user_input` | Function | Get single-line input from user. |
| `get_multiline_input` | Function | Get multi-line input from user. |
| `confirm` | Function | Ask user for yes/no confirmation. |
| `display_message` | Function | Display a conversation message with role-appropriate formatt |
| `display_system` | Function | Display a system message. |
| `display_error` | Function | Display an error message. |
| `display_metrics` | Function | Display API usage metrics if verbose mode is on. |
| `display_tool_call` | Function | Display a tool being called. |
| `display_tool_result` | Function | Display a tool execution result. |
| `get_user_input` | Function | Get single-line input from user. |
| `get_multiline_input` | Function | Get multi-line input from user (until empty line). |
| `confirm` | Function | Ask user for yes/no confirmation. |
| `ToolExecutionError` | Class | Custom exception for tool execution failures that should not |
| `NoHTTPFilter` | Class | Filters out logging records containing 'response' in the log |
| `lazy_fn` | Function | Decorator that lazily implements a function using an LLM at  |
| `lazy_class` | Function | Decorator that lazily implements a class using an LLM at run |
| `lazy` | Function | Smart decorator that implements a function or class using an |
| `debug_on_error` | Function | Decorator that launches post-mortem debugging on exception. |
| `log_errors` | Function | Decorator that logs errors to a file when a function raises  |
| `toolify` | Function | Convert any function into a bot tool with string-in, string- |
| `filter` | Function | Check if the log record should be filtered. |
| `decorator` | Function | Inner decorator function that sets up the lazy implementatio |
| `decorator` | Function | Inner decorator function that sets up the lazy class impleme |
| `get_docstring` | Function | Extract docstring from an AST node. |
| `format_function` | Function | Format a function definition with its signature and docstrin |
| `format_class` | Function | Format a class definition with its signature, docstring, and |
| `decorator` | Function | Inner decorator that dispatches to either lazy or lazy_class |
| `wrapper` | Function | No description |
| `wrapper` | Function | No description |
| `decorator` | Function | No description |
| `wrapper` | Function | Wrapper function that handles lazy function implementation. |
| `new_new` | Function | Replacement for __new__ that handles lazy class implementati |
| `wrapper` | Function | No description |
| `FunctionReplacer` | Class | AST transformer that replaces a function definition with new |
| `ClassReplacer` | Class | AST transformer that replaces a class definition with new co |
| `visit_FunctionDef` | Function | No description |
| `visit_ClassDef` | Function | No description |
| `validate_repo` | Function | Validate and sanitize repository string. |
| `get_pr_comments` | Function | Fetch all comments from a GitHub PR using gh CLI. |
| `get_pr_review_comments` | Function | Fetch all review comments (inline comments) from a GitHub PR |
| `extract_coderabbit_prompts` | Function | Extract CodeRabbit AI prompt from a comment. |
| `is_outdated` | Function | Check if a comment is marked as outdated. |
| `parse_pr_comments` | Function | Parse PR comments and optionally save to file. |
| `save_coderabbit_prompts` | Function | Extract and save all CodeRabbit AI prompts from a PR. |
