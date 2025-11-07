"""Error namshub for testing error handling.

This namshub deliberately raises an error to test error handling
in the invoke_namshub tool.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode


def invoke(bot: Bot, error_type: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the error namshub (raises an error).

    Parameters:
        bot (Bot): The bot to execute on
        error_type (str, optional): Type of error to raise (default: "ValueError")
        **kwargs: Additional parameters (ignored)

    Returns:
        Tuple[str, ConversationNode]: Never returns, always raises

    Raises:
        ValueError: If error_type is "ValueError" or not specified
        RuntimeError: If error_type is "RuntimeError"
        Exception: If error_type is anything else
    """
    if error_type is None or error_type == "ValueError":
        raise ValueError("Deliberate error from namshub_of_error")
    elif error_type == "RuntimeError":
        raise RuntimeError("Deliberate runtime error from namshub_of_error")
    else:
        raise Exception(f"Deliberate {error_type} from namshub_of_error")