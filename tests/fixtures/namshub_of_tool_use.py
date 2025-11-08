"""Tool use namshub for testing toolkit modification.

This namshub adds execute_python to the toolkit,
then uses it to execute a simple calculation.
Tests that adding tools to the toolkit works correctly.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import create_toolkit
from bots.tools.python_execution_tool import execute_python


def invoke(bot: Bot, expression: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the tool use namshub.

    Parameters:
        bot (Bot): The bot to execute on
        expression (str, optional): Python expression to evaluate (default: "2 + 2")
        **kwargs: Additional parameters (ignored)

    Returns:
        Tuple[str, ConversationNode]: Result of evaluation and current node
    """
    if expression is None:
        expression = "2 + 2"

    # Add execute_python to toolkit
    create_toolkit(bot, execute_python)

    # Execute the expression
    result = execute_python(f"print({expression})")

    return (f"Evaluated '{expression}' = {result.strip()}", bot.conversation)
