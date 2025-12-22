# CLI Frontend Development Guide
## Overview
The Bots CLI uses a frontend abstraction layer to separate presentation logic from business logic. This enables multiple frontend implementations (terminal, GUI, web, plugins) to share the same command handlers.
## Architecture
### Core Components
**CLIFrontend (Abstract Base Class)**
- Defines the interface all frontends must implement
- Located in `bots/dev/cli_frontend.py`
- Provides methods for display and user input
**TerminalFrontend (Default Implementation)**
- Terminal-based implementation using ANSI colors
- Uses the current `pretty()` display behavior
- Default frontend for the CLI
**Handler Classes**
- Return structured data instead of calling display functions
- Business logic separated from presentation
- Easy to test with mock frontends
### Data Flow
```
User Input → CLI → Handler → Data Dict → Frontend → Display
                     ↓
                  Business Logic
                  (no display calls)
```
## Creating a Custom Frontend
### Step 1: Implement CLIFrontend
```python
from bots.dev.cli_frontend import CLIFrontend
class MyCustomFrontend(CLIFrontend):
    \"\"\"Custom frontend implementation.\"\"\"
    def display_message(self, role: str, content: str) -> None:
        \"\"\"Display a conversation message.\"\"\"
        # Your implementation here
        pass
    def display_system(self, message: str) -> None:
        \"\"\"Display a system message.\"\"\"
        # Your implementation here
        pass
    def display_error(self, message: str) -> None:
        \"\"\"Display an error message.\"\"\"
        # Your implementation here
        pass
    def display_metrics(self, metrics: dict) -> None:
        \"\"\"Display API usage metrics.\"\"\"
        # Your implementation here
        pass
    def display_tool_call(self, name: str, args: dict) -> None:
        \"\"\"Display a tool being called.\"\"\"
        # Your implementation here
        pass
    def display_tool_result(self, name: str, result: str) -> None:
        \"\"\"Display a tool result.\"\"\"
        # Your implementation here
        pass
    def get_user_input(self, prompt: str = \">>> \") -> str:
        \"\"\"Get single-line input from user.\"\"\"
        # Your implementation here
        pass
    def get_multiline_input(self, prompt: str) -> str:
        \"\"\"Get multi-line input from user.\"\"\"
        # Your implementation here
        pass
    def confirm(self, question: str) -> bool:
        \"\"\"Ask user for yes/no confirmation.\"\"\"
        # Your implementation here
        pass
```
### Step 2: Use Your Frontend
```python
from bots.dev.cli import CLI
from my_frontend import MyCustomFrontend
# Create CLI with custom frontend
cli = CLI()
cli.context.frontend = MyCustomFrontend(cli.context)
cli.run()
```
## Handler Return Format
Handlers return structured data that frontends can display appropriately.
### Return Types
**String (Simple Messages)**
```python
def some_handler(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
    return \"Operation completed successfully\"
```
**Dict (Structured Data)**
```python
def some_handler(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
    return {
        \"type\": \"system\",  # or \"error\", \"message\", \"metrics\"
        \"content\": \"Detailed message here\"
    }
```
**Tuple (Multiple Values)**
```python
def load_prompt(self, bot: Bot, context: CLIContext, args: List[str]) -> tuple:
    return (\"Prompt loaded\", prompt_content)
```
### Display Type Mapping
| Return Type | Frontend Method |
|------------|----------------|
| `{\"type\": \"system\", ...}` | `display_system()` |
| `{\"type\": \"error\", ...}` | `display_error()` |
| `{\"type\": \"message\", ...}` | `display_message()` |
| `{\"type\": \"metrics\", ...}` | `display_metrics()` |
| Plain string | `display_system()` |
## Testing Your Frontend
### Unit Tests
```python
import pytest
from my_frontend import MyCustomFrontend
from bots.dev.cli import CLIContext
def test_display_message():
    context = CLIContext()
    frontend = MyCustomFrontend(context)
    # Test message display
    frontend.display_message(\"user\", \"Hello\")
    # Assert your expected behavior
def test_display_error():
    context = CLIContext()
    frontend = MyCustomFrontend(context)
    # Test error display
    frontend.display_error(\"Something went wrong\")
    # Assert your expected behavior
```
### Integration Tests
```python
def test_handler_with_frontend():
    \"\"\"Test that handlers work with custom frontend.\"\"\"
    from bots.dev.cli import CLI, CLIContext
    from bots.foundation.anthropic_bots import AnthropicBot
    bot = AnthropicBot()
    context = CLIContext()
    context.frontend = MyCustomFrontend(context)
    # Test a handler
    from bots.dev.cli import StateHandler
    handler = StateHandler()
    result = handler.save(bot, context, [\"test.bot\"])
    # Verify result format
    assert isinstance(result, dict)
    assert "type" in result and "message" in result
```
## Examples
### GUI Frontend (Conceptual)
```python
import tkinter as tk
from bots.dev.cli_frontend import CLIFrontend
class GUIFrontend(CLIFrontend):
    def __init__(self, context, root):
        super().__init__(context)
        self.root = root
        self.text_widget = tk.Text(root)
        self.text_widget.pack()
    def display_message(self, role: str, content: str) -> None:
        color = \"blue\" if role == \"user\" else \"green\"
        self.text_widget.insert(tk.END, f\"{role}: {content}\\n\", color)
    def display_system(self, message: str) -> None:
        self.text_widget.insert(tk.END, f\"System: {message}\\n\", \"gray\")
    # ... implement other methods
```
### Web Frontend (Conceptual)
```python
from flask import Flask, render_template, request
from bots.dev.cli_frontend import CLIFrontend
class WebFrontend(CLIFrontend):
    def __init__(self, context):
        super().__init__(context)
        self.messages = []
    def display_message(self, role: str, content: str) -> None:
        self.messages.append({
            \"role\": role,
            \"content\": content,
            \"type\": \"message\"
        })
    def display_system(self, message: str) -> None:
        self.messages.append({
            \"content\": message,
            \"type\": \"system\"
        })
    # ... implement other methods
```
## Best Practices
1. **Keep frontends stateless** - Store state in CLIContext, not frontend
2. **Handle all abstract methods** - Implement every method from CLIFrontend
3. **Test thoroughly** - Use mock frontends for handler tests
4. **Follow conventions** - Match TerminalFrontend behavior for consistency
5. **Document differences** - If your frontend behaves differently, document why
## Troubleshooting
### Handler still calling display functions directly
Some handlers may have legacy display calls. These should be refactored to return data instead.
**Before:**
```python
def my_handler(self, bot, context, args):
    pretty(\"Result\", \"system\")
    return None
```
**After:**
```python
def my_handler(self, bot, context, args):
    return \"Result\"
```
### Frontend not receiving data
Check that CLI._handle_command() is routing handler results to the frontend:
```python
result = handler_method(bot, context, args)
if isinstance(result, dict):
    context.frontend.display_system(result[\"content\"])
elif isinstance(result, str):
    context.frontend.display_system(result)
```
## Future Enhancements
Potential improvements to the frontend system:
- **Rich terminal UI** - Using textual or prompt_toolkit
- **Progress indicators** - For long-running operations
- **Interactive tree visualization** - Visual conversation tree navigation
- **Syntax highlighting** - For code in messages
- **Mouse support** - Click to navigate tree
- **Themes** - Customizable color schemes
## Contributing
When adding new handler methods:
1. Return data (string or dict), don't call display functions
2. Add tests for the handler
3. Update this guide if new return formats are introduced
4. Ensure backward compatibility with existing frontends
