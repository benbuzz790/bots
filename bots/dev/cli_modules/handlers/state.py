"""
State management handler for CLI.

This module handles bot save/load operations and label rebuilding.
"""

import os
from typing import TYPE_CHECKING, List

if TYPE_CHECKING:
    from bots.dev.cli_modules.config import CLIContext
    from bots.foundation.base import Bot

from bots.dev.cli_modules.callbacks import RealTimeDisplayCallbacks
from bots.dev.cli_modules.utils import EscapeException, input_with_esc
from bots.foundation.base import Bot as BotClass


class StateHandler:
    """Handler for bot state management commands."""

    def save(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Save bot state."""
        try:
            try:
                filename = input_with_esc("Save filename (without extension): ").strip()
            except EscapeException:
                return "Save cancelled"
            if not filename:
                return "Save cancelled - no filename provided"
            if not filename.endswith(".bot"):
                filename = filename + ".bot"
            bot.save(filename)
            return f"Bot saved to {filename}"
        except Exception as e:
            return f"Error saving bot: {str(e)}"

    def load(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Load a bot from file."""
        try:
            if not args:
                filename = input("Enter filename to load: ").strip()
            else:
                filename = " ".join(args)
            if not filename:
                return "No filename provided"
            filename = self._load_bot_from_file(filename, context)
            if filename.startswith("Error") or filename.startswith("File not found"):
                return filename
            return f"Bot loaded from {filename}"
        except Exception as e:
            return f"Error loading bot: {str(e)}"

    def _load_bot_from_file(self, filename: str, context: "CLIContext") -> str:
        """Load bot from file and set up context."""
        try:
            if not filename.endswith(".bot"):
                filename += ".bot"
            if not os.path.exists(filename):
                # Try in current directory
                if os.path.exists(os.path.join(".", filename)):
                    filename = os.path.join(".", filename)
                else:
                    return f"File not found: {filename}"
            new_bot = BotClass.load(filename)
            while new_bot.conversation.replies:
                new_bot.conversation = new_bot.conversation.replies[-1]

            # Attach CLI callbacks for proper display
            new_bot.callbacks = RealTimeDisplayCallbacks(context)

            context.bot_instance = new_bot
            context.labeled_nodes = {}

            # Find the root of the conversation tree
            root_node = new_bot.conversation
            while root_node.parent:
                root_node = root_node.parent

            # Rebuild labels from the entire tree starting at root
            self._rebuild_labels(root_node, context)
            context.cached_leaves = []
            return filename
        except Exception as e:
            return f"Error loading bot: {str(e)}"

    def _rebuild_labels(self, node, context: "CLIContext"):
        """Recursively rebuild labeled nodes from conversation tree."""
        if hasattr(node, "labels"):
            for label in node.labels:
                context.labeled_nodes[label] = node
        for reply in node.replies:
            self._rebuild_labels(reply, context)
