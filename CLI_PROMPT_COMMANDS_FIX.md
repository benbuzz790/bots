# CLI Prompt Commands Fix Summary
## Issue
The /s (save prompt) and /p (load prompt) commands in `bots/dev/cli.py` were broken, causing an `AttributeError: 'CLI' object has no attribute 'prompts'`.
### Error Message
```
You: /s
Error: Command error: 'CLI' object has no attribute 'prompts'
```
## Root Cause
In commit `acbf852` (Fix WO013: Save/Load & CLI Maintenance), the `PromptHandler` class existed and was instantiated in the CLI's `__init__` method as `self.prompts = PromptHandler()`. However, in a subsequent refactoring, the `PromptHandler` class was removed from the codebase, but the CLI still referenced `self.prompts` in:
- `_handle_load_prompt()` method
- `_handle_save_prompt()` method
This caused the AttributeError when users tried to use `/s` or `/p` commands.
## Solution
### 1. Restored `PromptHandler` Class
Added back the `PromptHandler` class to `bots/dev/cli.py` with the following methods:
- `__init__()` - Initializes with a `PromptManager` instance
- `_get_input_with_prefill()` - Helper for readline prefill support
- `load_prompt()` - Handles `/p` command logic (search, selection, loading)
- `save_prompt()` - Handles `/s` command logic (save with args or last message)
### 2. Updated CLI Initialization
Modified `CLI.__init__()` to instantiate the `PromptHandler`:
```python
self.prompts = PromptHandler()
```
### 3. Enhanced `_handle_chat()` Method
Added tracking of the last user message to support `/s` command without arguments:
```python
def _handle_chat(self, bot: Bot, user_input: str):
    # Track last user message for /s command
    self.last_user_message = user_input
    # ... rest of method
```
## Features
### `/s` Command (Save Prompt)
- **With arguments**: `/s This is my prompt` - Saves the provided text
- **Without arguments**: `/s` - Saves the last user message sent to the bot
- Auto-generates descriptive names using Claude Haiku
- Handles duplicate names by appending counters (`prompt_1`, `prompt_2`, etc.)
### `/p` Command (Load Prompt)
- **With search query**: `/p coding` - Searches for prompts matching "coding"
- **Without query**: `/p` - Shows recent prompts
- **Single match**: Loads directly and prefills input
- **Multiple matches**: Shows numbered list for selection
- Updates recency tracking (keeps last 5 used prompts)
## Tests
Created comprehensive test suite in `tests/test_cli/test_prompt_commands.py`:
### Test Coverage (27 tests, all passing)
1. **PromptManager Tests** (11 tests)
   - Save with/without name
   - Duplicate name handling
   - Load existing/nonexistent prompts
   - Search by name and content
   - Recency tracking and limits
2. **PromptHandler Tests** (9 tests)
   - Save with args vs last message
   - Empty/invalid input handling
   - Single/multiple match loading
   - Selection validation and cancellation
3. **CLI Integration Tests** (5 tests)
   - Command registration
   - Save/load through CLI commands
   - Last message tracking in chat
4. **End-to-End Tests** (3 tests)
   - Complete save → load workflow
   - Save after chat → load workflow
   - Multiple saves with search
### Test Results
```
============================= 27 passed in 3.54s ==============================
```
## Files Modified
1. `bots/dev/cli.py`
   - Added `PromptHandler` class (96 lines)
   - Updated `CLI.__init__()` to instantiate `self.prompts`
   - Updated `_handle_chat()` to track `last_user_message`
2. `tests/test_cli/test_prompt_commands.py` (NEW)
   - Comprehensive test suite for `/s` and `/p` commands
   - 27 tests covering all functionality
## Verification
Manual testing confirms:
- ✅ `/s` command saves prompts without AttributeError
- ✅ `/s` with arguments saves the provided text
- ✅ `/s` without arguments saves the last user message
- ✅ `/p` command loads prompts and prefills input
- ✅ `/p` with search finds matching prompts
- ✅ All 27 automated tests pass
## Usage Examples
### Save a prompt with text
```
You: /s Write a function to sort a list
system: Saved prompt as: sort_list_function
```
### Save the last message
```
You: Please review this code for bugs
Bot: [response]
You: /s
system: Saved prompt as: code_review_request
```
### Load a prompt
```
You: /p review
Found 2 matches:
  1. code_review_request: Please review this code for bugs
  2. review_documentation: Review the API documentation
Select prompt (1-2): 1
system: Loaded prompt: code_review_request
You: Please review this code for bugs█  # Prefilled and ready to edit
```
## Related Issues
- Fixes the bug reported in the user's message
- Restores functionality from commit `acbf852`
- Maintains backward compatibility with existing prompts.json files
