# Handler Return Format Specification
## Overview
All CLI handler methods follow a consistent pattern: they return data instead of calling display functions directly. This enables the frontend abstraction layer to handle presentation while keeping handlers focused on business logic.
## Return Types
Handlers can return three types of values:
### 1. String (Simple Messages)
The most common return type for status messages and simple results.
```python
def save(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
    filename = args[0] if args else \"quicksave.bot\"
    bot.save(filename)
    return f\"Bot saved to {filename}\"
```
**Frontend handling:**
- Displayed using `frontend.display_system()`
- Appropriate for success messages, status updates, simple results
### 2. Dict (Structured Data)
Used when additional metadata or type information is needed.
```python
def some_handler(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
    return {
        \"type\": \"error\",
        \"content\": \"File not found: missing.bot\"
    }
```
**Supported types:**
- `\"system\"` - System messages (displayed via `display_system()`)
- `\"error\"` - Error messages (displayed via `display_error()`)
- `\"message\"` - Conversation messages (displayed via `display_message()`)
- `\"metrics\"` - API metrics (displayed via `display_metrics()`)
**Frontend handling:**
- Routed to appropriate display method based on `type` field
- `content` field contains the actual message/data
### 3. Tuple (Multiple Values)
Used when returning multiple pieces of information.
```python
def load_prompt(self, bot: Bot, context: CLIContext, args: List[str]) -> tuple[str, Optional[str]]:
    prompt_content = self.manager.load_prompt(name)
    return (f\"Loaded prompt: {name}\", prompt_content)
```
**Frontend handling:**
- First element is typically a status message
- Subsequent elements are data values
- CLI unpacks and handles appropriately
## Handler Classes
### ConversationHandler
**Methods:** `up`, `down`, `left`, `right`, `root`, `label`, `leaf`, `combine_leaves`
**Return format:** Dict with `type` and `content`
```python
# Navigation success
{\"type\": \"message\", \"content\": \"Moved up to previous node\"}
# Navigation with selection
{\"type\": \"system\", \"content\": \"Multiple replies available:\\n  0: ...\\n  1: ...\"}
# Error
{\"type\": \"error\", \"content\": \"Cannot move up from root\"}
```
### StateHandler
**Methods:** `save`, `load`
**Return format:** String
```python
# Success
\"Bot saved to mybot.bot\"
\"Bot loaded from mybot.bot\"
# Error (as string)
\"Error: File not found\"
```
### SystemHandler
**Methods:** `help`, `verbose`, `quiet`, `config`, `auto_stash`, `load_stash`, `add_tool`
**Return format:** String
```python
# Status messages
\"Verbose mode enabled\"
\"Auto-stash created: WIP: updated README\"
# Help text
\"Available commands:\\n/help - Show this help...\"
```
### PromptHandler
**Methods:** `save_prompt`, `delete_prompt`, `load_prompt`, `recent_prompts`
**Return format:** String or Tuple
```python
# save_prompt, delete_prompt
\"Prompt saved as: analyze_code\"
\"Prompt deleted: old_prompt\"
# load_prompt, recent_prompts (tuple)
(\"Loaded prompt: analyze_code\", \"Analyze this code for bugs...\")
(\"Recent prompts:\", None)  # None when just displaying list
```
### DynamicFunctionalPromptHandler
**Methods:** `execute`, `broadcast_fp`
**Return format:** String
```python
# Execution status
\"Executing functional prompt: chain\"
\"Broadcast complete: applied to 5 leaves\"
```
**Note:** These methods use interactive wizards (`print()`/`input()`) for parameter collection. This is acceptable for complex flows.
## Display Routing in CLI
The CLI routes handler returns to appropriate frontend methods:
```python
def _handle_command(self, bot: Bot, user_input: str):
    # ... handler execution ...
    # Route based on return type
    if isinstance(result, dict):
        if result[\"type\"] == \"error\":
            self.context.frontend.display_error(result[\"content\"])
        elif result[\"type\"] == \"system\":
            self.context.frontend.display_system(result[\"content\"])
        elif result[\"type\"] == \"message\":
            self.context.frontend.display_message(\"assistant\", result[\"content\"])
    elif isinstance(result, str):
        self.context.frontend.display_system(result)
    elif isinstance(result, tuple):
        message, data = result
        self.context.frontend.display_system(message)
        # Handle data appropriately
```
## Guidelines for New Handlers
When creating new handler methods:
### 1. Return Data, Don't Display
**Bad:**
```python
def my_handler(self, bot, context, args):
    result = do_something()
    context.frontend.display_system(f\"Result: {result}\")
    return None
```
**Good:**
```python
def my_handler(self, bot, context, args):
    result = do_something()
    return f\"Result: {result}\"
```
### 2. Use Appropriate Return Type
- **String** for simple messages
- **Dict** when you need to specify message type (error vs system)
- **Tuple** when returning multiple values
### 3. Handle Errors Consistently
**Option A: Return error dict**
```python
if not file_exists:
    return {\"type\": \"error\", \"content\": \"File not found\"}
```
**Option B: Return error string**
```python
if not file_exists:
    return \"Error: File not found\"
```
Both work, but dicts allow frontend to style errors differently.
### 4. Avoid Direct Input/Output
**Exception:** Interactive wizards for complex parameter collection are acceptable (see DynamicFunctionalPromptHandler).
For simple input, use `args` parameter:
```python
def my_handler(self, bot, context, args):
    value = args[0] if args else \"default\"
    # Don't call input() directly
```
### 5. Test Return Format
Always test that your handler returns the expected format:
```python
def test_my_handler_returns_string():
    handler = MyHandler()
    result = handler.my_method(bot, context, [\"arg\"])
    assert isinstance(result, str)
    assert \"expected text\" in result
def test_my_handler_returns_error_dict():
    handler = MyHandler()
    result = handler.my_method(bot, context, [])
    assert isinstance(result, dict)
    assert result[\"type\"] == \"error\"
```
## Migration from Legacy Code
If you find handlers that call display functions directly:
### Before (Legacy)
```python
def old_handler(self, bot, context, args):
    result = do_work()
    pretty(result, \"system\")
    return None
```
### After (Refactored)
```python
def new_handler(self, bot, context, args):
    result = do_work()
    return result
```
The CLI will automatically route the return value to the frontend.
## Interactive Flows
Some handlers need complex user interaction (wizards, multi-step selection). Two approaches:
### Approach 1: Return Data for Frontend to Handle (Preferred)
```python
def select_option(self, bot, context, args):
    options = get_options()
    return {
        \"type\": \"selection\",
        \"options\": options,
        \"prompt\": \"Choose an option:\"
    }
```
Frontend implements selection UI.
### Approach 2: Direct Interaction (Acceptable for Complex Wizards)
```python
def complex_wizard(self, bot, context, args):
    # Multi-step parameter collection
    print(\"Step 1: Choose pattern\")
    pattern = input(\"Pattern: \")
    print(\"Step 2: Configure options\")
    # ... more steps ...
    return \"Wizard complete\"
```
Use this sparingly, only when the interaction is too complex for simple frontend methods.
## Summary
**Key principles:**
1. Handlers return data, frontends display it
2. Use strings for simple messages, dicts for structured data
3. Test return formats
4. Avoid direct I/O except for complex wizards
5. Keep handlers focused on business logic
This separation enables multiple frontend implementations while maintaining consistent handler behavior.
