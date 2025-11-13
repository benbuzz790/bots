"""
State management handler for CLI.

This module handles bot save/load operations and label rebuilding.
"""

import glob
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
        """Load bot state."""
        try:
            # Display all .bot files in current directory
            bot_files = glob.glob("*.bot")

            if bot_files:
                print("\nAvailable .bot files:")
                for i, filename in enumerate(bot_files, 1):
                    print(f"  {i}. {filename}")
                print()
            else:
                print("\nNo .bot files found in current directory.")

            try:
                filename = input_with_esc("Load filename (or number from list): ").strip()
            except EscapeException:
                return "Load cancelled"
            if not filename:
                return "Load cancelled - no filename provided"

            # Check if input is a number referring to the list
            if filename.isdigit() and bot_files:
                file_index = int(filename) - 1
                if 0 <= file_index < len(bot_files):
                    filename = bot_files[file_index]
                else:
                    return f"Invalid selection. Must be between 1 and " f"{len(bot_files)}"

            return self._load_bot_from_file(filename, context)
        except Exception as e:
            return f"Error loading bot: {str(e)}"

    def _load_bot_from_file(self, filename: str, context: "CLIContext") -> str:
        """Load bot from file and update context.

        Used by both interactive load and CLI args.
        """
        try:
            if not os.path.exists(filename):
                if not filename.endswith(".bot"):
                    filename_with_ext = filename + ".bot"
                    if os.path.exists(filename_with_ext):
                        filename = filename_with_ext
                    else:
                        return f"File not found: {filename}"
                else:
                    return f"File not found: {filename}"
            new_bot = BotClass.load(filename)
            while new_bot.conversation.replies:
                new_bot.conversation = new_bot.conversation.replies[-1]

            # Attach CLI callbacks for proper display
            new_bot.callbacks = RealTimeDisplayCallbacks(context)

            context.bot_instance = new_bot
            context.labeled_nodes = {}
            self._rebuild_labels(new_bot.conversation, context)
            context.cached_leaves = []
            return f"Bot loaded from {filename}. Conversation restored to " f"most recent message."
        except Exception as e:
            return f"Error loading bot: {str(e)}"

    def _rebuild_labels(self, node, context: "CLIContext"):
        """Recursively rebuild labeled nodes from conversation tree."""
        if hasattr(node, "labels"):
            for label in node.labels:
                context.labeled_nodes[label] = node
        for reply in node.replies:
            self._rebuild_labels(reply, context)
