# Namshubs

**Namshubs** are specialized workflow modules that can be invoked on bots to execute specific tasks. The name comes from Neal Stephenson's *Snow Crash*, where namshubs are powerful "word programs" that directly affect behavior.

## What is a Namshub?

A namshub is a self-contained Python module that:

1. **Temporarily transforms a bot** - modifies system prompts and toolkit
2. **Executes a structured workflow** - uses functional prompts to guide the bot through steps
3. **Restores original state** - returns the bot to its original configuration after completion

## Structure

Each namshub follows this pattern:

```python
"""Namshub description - what it does and when to use it."""
from typing import Tuple
from bots.flows import functional_prompts as fp
from bots.foundation.base import Bot, ConversationNode
def _create_toolkit(bot: Bot) -> None:
    """Replace bot's toolkit with specialized tools."""
    # Create fresh bot with only needed tools
    temp_bot = bot.__class__(autosave=False)
    temp_bot.add_tools(tool1, tool2, tool3)
    bot.tool_handler = temp_bot.tool_handler
def _set_system_message(bot: Bot, **params) -> None:
    """Set specialized system message for this workflow."""
    system_message = """Your specialized instructions here..."""
    bot.set_system_message(system_message.strip())
def invoke(bot: Bot, param1: str = None, param2: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the namshub workflow.
    Parameters:
        bot (Bot): The bot to execute the workflow on
        param1 (str, optional): Description of parameter
        param2 (str, optional): Description of parameter
        **kwargs: Additional parameters for compatibility
    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # Validate parameters
    if not param1:
        return ("Error: param1 required", bot.conversation)
    # Configure the bot
    _create_toolkit(bot)
    _set_system_message(bot, param1=param1)
    # Define workflow prompts
    workflow_prompts = [
        "INSTRUCTION: Do something...",
        "INSTRUCTION: Do something else...",
        "INSTRUCTION: Finish up..."
    ]
    # Execute workflow using functional prompts
    responses, nodes = fp.chain_while(
        bot,
        workflow_prompts,
        stop_condition=fp.conditions.tool_not_used,
        continue_prompt="Focus on the previous INSTRUCTION. Only move on when explicitly instructed."
    )
    # Return final result
    return responses[-1], nodes[-1]
```

## Key Components

### 1. Module Docstring

Clear description of what the namshub does and when to use it.

### 2. Helper Functions

- `_create_toolkit(bot)`: Replaces bot's tools with specialized subset
- `_set_system_message(bot, **params)`: Configures bot's system prompt

### 3. Invoke Function

- **Signature**: `invoke(bot: Bot, **kwargs) -> Tuple[str, ConversationNode]`
- **Parameters**: Accept kwargs for flexibility
- **Returns**: Final response and conversation node
- **Workflow**: Uses functional prompts (chain, chain_while, prompt_while, etc.)

## Usage

Bots can invoke namshubs using the `invoke_namshub` tool:

```python
# From within a bot's conversation
invoke_namshub("namshub_of_code_review", target_file="main.py")
invoke_namshub("namshub_of_pull_requests", pr_number="123")
invoke_namshub("namshub_of_test_generation", target_file="utils.py")
```

## Available Namshubs

### namshub_of_code_review

Performs thorough code review on a Python file.

- **Parameters**: `target_file` (required)
- **Workflow**: Read ? Analyze ? Review ? Summarize
- **Tools**: view, view_dir, python_view (read-only)

### namshub_of_pull_requests

Handles GitHub PR CI/CD workflow.

- **Parameters**: `pr_number` (required)
- **Workflow**: Check status ? Analyze failures ? Fix issues ? Post update
- **Tools**: execute_powershell, view, python_view, python_edit

### namshub_of_test_generation

Generates comprehensive pytest tests for Python code.

- **Parameters**: `target_file` (required), `test_file` (optional)
- **Workflow**: Analyze ? Identify tests ? Create structure ? Generate tests ? Verify
- **Tools**: execute_powershell, execute_python, view, python_view, python_edit### namshub_of_documentation
Generates or improves documentation for Python code.
- **Parameters**: `target_file` (required)
- **Workflow**: Analyze ? Module docs ? Class docs ? Function docs ? Review ? Verify
- **Tools**: view, view_dir, python_view, python_edit

## Creating New Namshubs

1. **Name**: Use pattern `namshub_of_<purpose>.py`
2. **Location**: Place in `bots/namshubs/`
3. **Structure**: Follow the pattern above
4. **Documentation**: Clear docstrings explaining purpose and usage
5. **Parameters**: Accept kwargs for flexibility
6. **Workflow**: Use functional prompts from `bots.flows.functional_prompts`
7. **Tools**: Only include necessary tools for the task

## Best Practices

### INSTRUCTION Pattern

For `chain_while` workflows, use the INSTRUCTION pattern:

```python
workflow_prompts = [
    "INSTRUCTION: First step here...",
    "INSTRUCTION: Second step here...",
    "INSTRUCTION: Final step here..."
]
responses, nodes = fp.chain_while(
    bot,
    workflow_prompts,
    stop_condition=fp.conditions.tool_not_used,
    continue_prompt="Focus on the previous INSTRUCTION. Only move on when explicitly instructed."
)
```

The all-caps "INSTRUCTION:" prefix draws attention and the continue prompt keeps the bot focused on completing each step fully before moving on.

## Design Principles

1. **Single Purpose**: Each namshub does one thing well
2. **Minimal Toolkit**: Only include tools needed for the task
3. **Clear Workflow**: Use functional prompts to structure the process
4. **Parameterized**: Accept kwargs for flexibility
5. **Restorable**: Original bot state is automatically restored
6. **Self-Contained**: All logic within the namshub module
7. **Documented**: Clear docstrings and comments

## Technical Details

### Tool Swapping

```python
# Save original
original_tool_handler = bot.tool_handler
# Create new toolkit
temp_bot = bot.__class__(autosave=False)
temp_bot.add_tools(specific_tools)
bot.tool_handler = temp_bot.tool_handler
# Restore (done automatically by invoke_namshub)
bot.tool_handler = original_tool_handler
```

### Functional Prompts

Namshubs use functional prompts to structure workflows:

- `chain()`: Sequential prompts
- `chain_while()`: Sequential with iteration per step
- `prompt_while()`: Single prompt with iteration
- `branch()`: Parallel exploration
- `tree_of_thought()`: Branch ? explore ? synthesize

### State Management

The `invoke_namshub` tool automatically:

1. Saves original tool_handler and system_message
2. Executes the namshub
3. Restores original state (even on error)

## Examples

See the existing namshubs in this directory for complete examples:

- `namshub_of_code_review.py`
- `namshub_of_pull_requests.py`
- `namshub_of_test_generation.py`
