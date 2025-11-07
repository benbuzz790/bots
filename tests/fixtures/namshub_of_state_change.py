"""State change namshub for testing bot state modification.

This namshub modifies the bot's system message and returns.
Tests that namshubs can change bot state during execution.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode


def invoke(bot: Bot, new_message: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the state change namshub.

    Parameters:
        bot (Bot): The bot to execute on
        new_message (str, optional): New system message to set
        **kwargs: Additional parameters (ignored)

    Returns:
        Tuple[str, ConversationNode]: Confirmation message and current node
    """
    if new_message is None:
        new_message = "State changed by namshub_of_state_change"

    original_message = bot.system_message
    bot.set_system_message(new_message)

    return (
        f"System message changed from '{original_message}' to '{new_message}'",
        bot.conversation
    )