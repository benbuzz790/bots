"""No-op namshub for testing purposes.

This namshub does nothing - it's used as a test fixture to verify
namshub invocation mechanics without side effects.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode


def invoke(bot: Bot, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the no-op namshub (does nothing).

    Parameters:
        bot (Bot): The bot to execute on
        **kwargs: Accepts any parameters (ignored)

    Returns:
        Tuple[str, ConversationNode]: Simple success message and current node
    """
    return ("No-op namshub executed successfully.", bot.conversation)
