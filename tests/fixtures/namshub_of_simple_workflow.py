"""Simple workflow namshub for testing functional prompts.

This namshub executes a simple 3-step workflow using chain.
Tests that workflow execution works correctly.
"""

from typing import Tuple

from bots.flows import functional_prompts as fp
from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import create_toolkit


def _set_system_message(bot: Bot, task: str) -> None:
    """Set system message for the workflow."""
    system_message = f"""You are executing a simple workflow.

Task: {task}

Respond to each step with a brief confirmation.
"""
    bot.set_system_message(system_message.strip())


def invoke(bot: Bot, task: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the simple workflow namshub.

    Parameters:
        bot (Bot): The bot to execute on
        task (str, optional): Description of the task (default: "test workflow")
        **kwargs: Additional parameters (ignored)

    Returns:
        Tuple[str, ConversationNode]: Final response and final node
    """
    if task is None:
        task = "test workflow"

    # Configure bot
    create_toolkit(bot)  # No tools needed
    _set_system_message(bot, task)

    # Define simple workflow
    prompts = [
        "Step 1: Acknowledge the task",
        "Step 2: Confirm understanding",
        "Step 3: Report completion"
    ]

    # Execute workflow
    responses, nodes = fp.chain(bot, prompts)

    return (f"Workflow completed: {responses[-1]}", nodes[-1])