# Namshub Quick Start Guide

## Creating Your First Namshub

### 1. Choose a Name

Use the pattern: `namshub_of_<purpose>.py`
Examples:

- `namshub_of_code_review.py`
- `namshub_of_refactoring.py`
- `namshub_of_security_audit.py`

### 2. Basic Template

```python
"""Brief description of what this namshub does.
Detailed explanation of:
- What it transforms the bot into
- What steps it takes
- What the output is
"""
from typing import Tuple
from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import (
    create_toolkit,
    chain_workflow,
    validate_required_params,
)
# Import the tools you need
from bots.tools.code_tools import view, view_dir
from bots.tools.python_edit import python_view, python_edit
def _set_system_message(bot: Bot, param1: str) -> None:
    """Set specialized system message."""
    system_message = f"""You are a specialist in [domain].
Your task: [description using {param1}]
Guidelines:
1. [Guideline 1]
2. [Guideline 2]
3. [Guideline 3]
"""
    bot.set_system_message(system_message.strip())
def invoke(bot: Bot, param1: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the namshub workflow.
    Parameters:
        bot (Bot): The bot to execute the workflow on
        param1 (str, optional): Description of parameter
        **kwargs: Additional parameters
    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # Validate parameters
    valid, error = validate_required_params(param1=param1)
    if not valid:
        return (
            error + "\nUsage: invoke_namshub('namshub_of_example', param1='value')",
            bot.conversation
        )
    # Configure the bot
    create_toolkit(bot, view, view_dir, python_view, python_edit)
    _set_system_message(bot, param1)
    # Define workflow
    workflow_prompts = [
        "Step 1 description",
        "Step 2 description",
        "Step 3 description"
    ]
    # Execute workflow
    responses, nodes = chain_workflow(bot, workflow_prompts)
    # Return result
    return responses[-1], nodes[-1]
```

### 3. Helper Functions Reference

#### create_toolkit(bot, *tools)

Replace bot's toolkit with specific tools.

```python
from bots.tools.code_tools import view, view_dir
from bots.tools.python_edit import python_view, python_edit
create_toolkit(bot, view, view_dir, python_view, python_edit)
```

#### validate_required_params(**params)

Check that required parameters are provided.

```python
valid, error = validate_required_params(
    target_file=target_file,
    pr_number=pr_number
)
if not valid:
    return (error, bot.conversation)
```

#### chain_workflow(bot, prompts, ...)

Execute a chain_while workflow with INSTRUCTION pattern.

```python
responses, nodes = chain_workflow(bot, [
    "Read the file",
    "Analyze it",
    "Write summary"
])
```

### 4. Best Practices

1. **Single Purpose**: Each namshub should do one thing well
2. **Clear Documentation**: Explain what it does and when to use it
3. **Minimal Tools**: Only include tools needed for the task
4. **Parameter Validation**: Always validate required parameters
5. **INSTRUCTION Pattern**: Use for multi-step workflows that need iteration
6. **Error Messages**: Provide clear usage examples in error messages
7. **Final Summary**: Return a clear summary of what was accomplished

### 5. Example: Complete Namshub

See the existing namshubs for complete examples:

- `namshub_of_code_review.py` - Simple sequential workflow
- `namshub_of_pull_requests.py` - Complex workflow with INSTRUCTION pattern
- `namshub_of_test_generation.py` - File generation workflow
- `namshub_of_documentation.py` - Code modification workflow
