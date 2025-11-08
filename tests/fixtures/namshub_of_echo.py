"""Echo namshub for testing parameter passing.

This namshub echoes back the provided message parameter.
Tests that parameters are correctly passed through invoke_namshub.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode


def invoke(bot: Bot, message: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the echo namshub.

    Parameters:
        bot (Bot): The bot to execute on
        message (str, optional): Message to echo back
        **kwargs: Additional parameters (ignored)

    Returns:
        Tuple[str, ConversationNode]: Echoed message and current node
    """
    if message is None:
        return ("Error: message parameter required", bot.conversation)

    return (f"Echo: {message}", bot.conversation)
