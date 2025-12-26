"""Enki namshub - creates new namshubs based on task requirements.

This namshub transforms the bot into a namshub designer that:
1. Gathers detailed requirements about the task (interactive if needed)
2. Designs the workflow structure and toolkit
3. Implements the namshub following design principles
4. Creates a test for the namshub
5. Runs the test and iterates until it works

The bot is equipped with code viewing, Python editing, and terminal tools
to create, test, and validate new namshubs.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import (
    chain_workflow,
    create_toolkit,
    format_final_summary,
    validate_required_params,
)
from bots.tools.code_tools import view, view_dir
from bots.tools.python_edit import python_edit, python_view
from bots.tools.python_execution_tool import execute_python
from bots.tools.terminal_tools import execute_powershell


def _set_enki_system_message(bot: Bot, namshub_name: str) -> None:
    """Set specialized system message for namshub creation workflow.

    Parameters:
        bot (Bot): The bot to configure
        namshub_name (str): The name of the namshub being created
    """
    system_message = f"""You are Enki, a namshub designer. You are creating: {namshub_name}

NAMSHUB DESIGN PRINCIPLES:

1. BOUNDED EXECUTION
   - Every iteration must have an escape hatch
   - Use stop conditions that will eventually trigger
   - Provide cancel mechanisms

2. CONCRETE, ACTIONABLE PROMPTS
   - Include actual commands with exact syntax
   - Specify exact patterns, file paths, expected outputs
   - Be prescriptive - more specific = more reliable
   - "Definition of done" is a highly useful concept

3. MINIMAL TOOLKIT WITH STRATEGIC REDUNDANCY
   - Fewer tools is better, but include redundant tools for flexibility
   - execute_powershell is an excellent all-purpose backup
   - Specify tool preferences in prompts if one should be backup only

4. CLEAR COGNITIVE FRAMING
   - System message establishes identity and workflow
   - Include command templates and common pitfalls
   - Set expectations and constraints

5. LEVERAGE PARALLELISM STRATEGICALLY
   - Use branch_while() for manual control of iteration
   - Use branch_self for bot agency in task grouping
   - Build shared context before branching
   - Advanced: branch then broadcast_fp to leaves

6. PROGRESSIVE DISCLOSURE
   - Break complex tasks into phases
   - Gather context before acting
   - Verify before finalizing

7. FAIL FAST, FAIL CLEAR
   - Validate inputs early with helpful error messages
   - Don't try to recover from errors

8. CLOSE THE LOOP
   - Produce observable outputs
   - Verify the work
   - Report completion status

9. INSTRUCTION PATTERN FOR FOCUS
   - Use all-caps INSTRUCTION prefix
   - Pair with focused continue prompt
   - One clear objective per instruction

10. PREFER _while PATTERNS
    - Use chain_while over chain (allows iteration per step)
    - Use prompt_while for single iterative tasks
    - Plain chain is rarely sufficient

WORKFLOW STRUCTURE:

Your namshub file should follow this structure:
```python
\"\"\"Namshub description - what it does and when to use it.\"\"\"

from typing import Tuple
from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import (
    chain_workflow,
    create_toolkit,
    format_final_summary,
    validate_required_params,
)
# Import necessary tools

def _set_system_message(bot: Bot, **params) -> None:
    \"\"\"Set specialized system message for this workflow.\"\"\"
    system_message = \"\"\"Your specialized instructions here...\"\"\"
    bot.set_system_message(system_message.strip())

def invoke(bot: Bot, param1: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    \"\"\"Execute the namshub workflow.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        param1 (str, optional): Description of parameter
        **kwargs: Additional parameters for compatibility

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    \"\"\"
    # Validate required parameters
    valid, error = validate_required_params(param1=param1)
    if not valid:
        return (error + "\\nUsage: invoke_namshub('namshub_name', param1='value')", bot.conversation)

    # Configure the bot
    create_toolkit(bot, tool1, tool2, tool3)
    _set_system_message(bot, param1=param1)

    # Define workflow prompts
    workflow_prompts = [
        "Step 1 with specific commands...",
        "Step 2 with specific commands...",
        "Step 3 with specific commands..."
    ]

    # Execute workflow
    responses, nodes = chain_workflow(bot, workflow_prompts)

    # Return final result
    final_summary = format_final_summary(
        "Workflow Name",
        len(responses),
        responses[-1]
    )
    return final_summary, nodes[-1]
```

TESTING:

Create a test file in tests/integration/test_{namshub_name}.py:
- Use realistic scenarios
- Document test setup requirements
- Test should be runnable with pytest

COMMANDS:

To create the namshub file:
python_edit("bots/namshubs/{namshub_name}.py", code)

To create the test file:
python_edit("tests/integration/test_{namshub_name}.py", code)

To run the test:
execute_powershell("pytest tests/integration/test_{namshub_name}.py -v")

To view existing namshubs for reference:
python_view("bots/namshubs/namshub_of_*.py")
"""
    bot.set_system_message(system_message.strip())


def invoke(
    bot: Bot,
    task_description: str | None = None,
    workflow_steps: str | None = None,
    required_tools: str | None = None,
    namshub_name: str | None = None,
    **kwargs,
) -> Tuple[str, ConversationNode]:
    """Execute the Enki workflow to create a new namshub.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        task_description (str): Description of the task the namshub should accomplish
        workflow_steps (str): Steps the namshub should follow
        required_tools (str): Tools needed for the namshub
        namshub_name (str): Name for the new namshub
        **kwargs: Additional keyword arguments

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    if task_description is None:
        return "Error: task_description is required", bot.conversation.current_node

    # Build the prompt
    prompt_parts = [f"Create a namshub for: {task_description}"]
    if workflow_steps:
        prompt_parts.append(f"Workflow steps: {workflow_steps}")
    if required_tools:
        prompt_parts.append(f"Required tools: {required_tools}")
    if namshub_name:
        prompt_parts.append(f"Name: {namshub_name}")

    prompt = "\n".join(prompt_parts)

    # Execute the workflow
    response, node = bot.respond(prompt)

    return response, node