"""
BotSession - Clean interface for bot interactions.

Provides a simple input(str) -> str interface that handles all command parsing,
session management, and bot lifecycle internally. Designed to be used both by
the CLI and programmatically by plugins like obsidian-vault-agent.
"""

# Import all the handlers and context from CLI
from bots.foundation.base import Bot
from bots.utils.interrupt_handler import run_interruptible


def make_bot_interruptible(bot: Bot) -> None:
    """Wrap a bot's respond method to make it interruptible with Ctrl-C.

    This allows users to interrupt long-running bot operations (like API calls)
    by pressing Ctrl-C. The bot's state remains consistent after interruption.

    Args:
        bot: The bot instance to make interruptible

    Note:
        This modifies the bot's respond method in-place by wrapping it with
        interrupt handling logic. The original respond method is preserved
        and called from within the wrapper.
    """
    # Store the original respond method
    original_respond = bot.respond

    def interruptible_respond(prompt: str, role: str = "user") -> str:
        """Wrapped respond method that can be interrupted with Ctrl-C."""
        return run_interruptible(original_respond, prompt, role)

    # Replace the respond method with the interruptible version
    bot.respond = interruptible_respond
