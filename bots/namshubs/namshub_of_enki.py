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
    task_description: str = None,
    workflow_steps: str = None,
    required_tools: str = None,
    namshub_name: str = None,
    **kwargs,
) -> Tuple[str, ConversationNode]:
    """Execute the Enki workflow to create a new namshub.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        task_description (str, optional): What the namshub should accomplish
        workflow_steps (str, optional): Specific steps/commands involved
        required_tools (str, optional): Specific tools needed
        namshub_name (str, optional): Name for the namshub file (auto-generated if not provided)
        **kwargs: Additional parameters (unused, for compatibility)

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # Validate that we at least have a task description
    valid, error = validate_required_params(task_description=task_description)
    if not valid:
        return (
            error + "\nUsage: invoke_namshub('namshub_of_enki', task_description='description of what the namshub should do')",
            bot.conversation,
        )

    # Generate namshub name if not provided
    if not namshub_name:
        # Will be generated during workflow based on task description
        namshub_name = "[name tbd]"

    # BRANCH FIRST to preserve calling context
    # Save the original conversation state
    original_conversation = bot.conversation

    try:
        # Create a branch for the Enki workflow
        # This keeps the main conversation clean and allows Enki to work in isolation
        bot.conversation = original_conversation._add_reply(
            content=f"Starting Enki workflow to create: {namshub_name}", role="assistant"
        )

        # Configure the bot for namshub creation
        create_toolkit(bot, view, view_dir, python_view, python_edit, execute_powershell, execute_python)
        _set_enki_system_message(bot, namshub_name)

        # Define the Enki workflow
        workflow_prompts = [
            f"""INSTRUCTION: Gather complete requirements for the namshub.

Task description provided: {task_description}
Workflow steps provided: {workflow_steps if workflow_steps else 'None - need to determine'}
Required tools provided: {required_tools if required_tools else 'None - need to determine'}

Ask the user clarifying questions to understand:
1. What is the exact purpose and scope of this namshub?
2. What are the specific steps/commands that should be executed?
3. What are the required parameters (inputs)?
4. What should the output/result be?
5. What tools are needed? (consider redundancy)
6. What are common pitfalls or edge cases?
7. What should the namshub be named? (suggest: namshub_of_<purpose>)

Be thorough - the quality of the namshub depends on understanding these details.
When you have all the information, say REQUIREMENTS_COMPLETE.""",
            """INSTRUCTION: Design the namshub structure.

Based on the requirements, design:
1. The namshub name (if not already determined)
2. The toolkit (minimal + strategic redundancy)
3. The workflow structure (which functional prompts to use: chain_while, prompt_while, branch_while, etc.)
4. The system message content (include specific commands, workflow phases, common pitfalls)
5. The parameters for invoke()
6. The workflow prompts (concrete, actionable, with exact commands)

Write out your design plan clearly. When complete, say DESIGN_COMPLETE.""",
            """INSTRUCTION: Implement the namshub.

Create the namshub file at bots/namshubs/<namshub_name>.py following the structure:
- Module docstring explaining purpose
- Imports (from bots.namshubs.helpers and necessary tools)
- _set_system_message() helper function
- invoke() function with proper validation, toolkit setup, workflow execution, and return

Follow the design principles and structure shown in your system message.
Use python_edit to create the file.

When complete, say IMPLEMENTATION_COMPLETE.""",
            """INSTRUCTION: Create a test for the namshub.

Design a realistic test scenario that validates the namshub works correctly.
Create the test file at tests/integration/test_<namshub_name>.py

The test should:
- Import necessary modules and the namshub
- Set up any required test fixtures or files
- Create a bot instance
- Invoke the namshub with test parameters
- Assert that the expected outcome occurred
- Clean up any test artifacts

Document what needs to exist for the test to run.
Use python_edit to create the test file.

When complete, say TEST_CREATED.""",
            """INSTRUCTION: Run the test and verify the namshub works.

Run the test using:
execute_powershell("pytest tests/integration/test_<namshub_name>.py -v")

If the test fails:
- Analyze the error
- Fix the namshub or test as needed
- Run the test again

Continue until the test passes. Use execute_powershell as a backup if execute_python fails.

When the test passes, say TEST_PASSED.""",
            """INSTRUCTION: Final review and summary.

Review the completed namshub against the design principles:
1. Does it have bounded execution?
2. Are prompts concrete and actionable?
3. Is the toolkit minimal with strategic redundancy?
4. Does the system message provide clear cognitive framing?
5. Does it use appropriate functional prompts?
6. Does it fail fast with clear errors?
7. Does it close the loop with observable outputs?

Provide a summary of:
- Namshub name and location
- What it does
- How to use it (with example)
- Test location and status

Say ENKI_COMPLETE when done.""",
        ]

        # Execute the workflow using chain_workflow with INSTRUCTION pattern
        responses, nodes = chain_workflow(bot, workflow_prompts)

        # Return the final response
        final_summary = format_final_summary(f"Namshub Creation: {namshub_name}", len(responses), responses[-1])

        return final_summary, nodes[-1]

    finally:
        # Always restore the original conversation
        bot.conversation = original_conversation
