"""
Configuration and context management for CLI.
This module contains CLIConfig for persistent settings and CLIContext for
runtime state management including backup/restore functionality.
"""

import json
import os
import time
from typing import Any, Dict, List, Optional

from bots.foundation.base import Bot, ConversationNode


class CLIConfig:
    """Configuration management for CLI settings."""

    def __init__(self):
        self.verbose = True
        self.width = 160
        self.indent = 4
        self.auto_stash = False
        self.remove_context_threshold = 40000
        self.auto_mode_neutral_prompt = "ok"
        self.auto_mode_reduce_context_prompt = "trim useless context"
        self.max_tokens = 4096
        self.temperature = 1.0
        self.auto_backup = False
        self.auto_restore_on_error = False
        self.config_file = "cli_config.json"
        self.load_config()

    def load_config(self):
        """Load configuration from file if it exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)
                    self.verbose = config_data.get("verbose", True)
                    self.width = config_data.get("width", 160)
                    self.indent = config_data.get("indent", 4)
                    self.auto_stash = config_data.get("auto_stash", False)
                    self.remove_context_threshold = config_data.get("remove_context_threshold", 40000)
                    self.auto_mode_neutral_prompt = config_data.get("auto_mode_neutral_prompt", "ok")
                    self.auto_mode_reduce_context_prompt = config_data.get(
                        "auto_mode_reduce_context_prompt", "trim useless context"
                    )
                    self.max_tokens = config_data.get("max_tokens", 4096)
                    self.temperature = config_data.get("temperature", 1.0)
                    self.auto_backup = config_data.get("auto_backup", False)
                    self.auto_restore_on_error = config_data.get("auto_restore_on_error", False)
        except Exception:
            pass  # Use defaults if config loading fails

    def save_config(self):
        """Save current configuration to file."""
        try:
            config_data = {
                "verbose": self.verbose,
                "width": self.width,
                "indent": self.indent,
                "auto_stash": self.auto_stash,
                "remove_context_threshold": self.remove_context_threshold,
                "auto_mode_neutral_prompt": self.auto_mode_neutral_prompt,
                "auto_mode_reduce_context_prompt": (self.auto_mode_reduce_context_prompt),
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "auto_backup": self.auto_backup,
                "auto_restore_on_error": self.auto_restore_on_error,
            }
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            pass  # Fail silently if config saving fails


class CLIContext:
    """Shared context for CLI operations."""

    def __init__(self):
        self.config = CLIConfig()
        self.labeled_nodes: Dict[str, ConversationNode] = {}
        self.conversation_backup: Optional[ConversationNode] = None
        self.old_terminal_settings = None
        self.bot_instance = None
        self.cached_leaves: List[ConversationNode] = []
        # Import here to avoid circular dependency
        from bots.dev.cli.callbacks import CLICallbacks

        self.callbacks = CLICallbacks(self)
        # Track session start time for cumulative metrics
        self.session_start_time = time.time()
        # Track context reduction cooldown
        # (counts down from 3 after each trigger)
        # Starts at 0 so first time tokens exceed threshold, it triggers
        # immediately
        self.context_reduction_cooldown = 0
        # Track last message metrics
        # (captured once per message, used by both display and auto)
        self.last_message_metrics = None
        # Bot backup system - stores complete bot copies
        self.bot_backup: Optional[Bot] = None
        self.backup_metadata: Dict[str, Any] = {}
        self.backup_in_progress: bool = False

    def create_backup(self, reason: str = "manual") -> bool:
        """Create a complete backup of the current bot.

        Args:
            reason: Description of why backup was created
                    (e.g., "before_user_message")

        Returns:
            True if backup successful, False otherwise
        """
        if self.bot_instance is None:
            return False

        if self.backup_in_progress:
            return False  # Prevent concurrent backups

        try:
            self.backup_in_progress = True

            # Use bot's built-in copy mechanism (bot * 1) which properly
            # handles callbacks, api_key, and other bot-specific concerns
            backup_bot = (self.bot_instance * 1)[0]

            # Store metadata
            metadata = {
                "timestamp": time.time(),
                "reason": reason,
                "conversation_depth": self._get_conversation_depth(),
                "token_count": (self.last_message_metrics.get("input_tokens", 0) if self.last_message_metrics else 0),
            }

            self.bot_backup = backup_bot
            self.backup_metadata = metadata

            return True

        except Exception as e:
            # Fail gracefully - don't interrupt user flow
            if self.config.verbose:
                print(f"Backup failed: {e}")
            return False

        finally:
            self.backup_in_progress = False

    def restore_backup(self) -> str:
        """Restore bot from backup.

        Returns:
            Status message
        """
        if not self.has_backup():
            return "No backup available"

        try:
            # Use bot's built-in copy mechanism to create a fresh copy
            # from backup
            restored_bot = (self.bot_backup * 1)[0]

            # Assign the restored copy to the live instance
            self.bot_instance = restored_bot

            # Re-attach callbacks on the restored instance
            # (pointing to current context)
            from bots.dev.cli.callbacks import RealTimeDisplayCallbacks

            self.bot_instance.callbacks = RealTimeDisplayCallbacks(self)

            # Clear tool handler state to prevent corruption
            self.bot_instance.tool_handler.clear()

            # Reset conversation-related caches to avoid stale references
            self.labeled_nodes = {}
            self.conversation_backup = None
            self.cached_leaves = []

            # Format timestamp for display
            timestamp = self.backup_metadata.get("timestamp", 0)
            time_ago = time.time() - timestamp
            if time_ago < 60:
                time_str = f"{int(time_ago)} seconds ago"
            elif time_ago < 3600:
                time_str = f"{int(time_ago / 60)} minutes ago"
            else:
                time_str = f"{int(time_ago / 3600)} hours ago"

            reason = self.backup_metadata.get("reason", "unknown")

            # Don't clear backup - allow multiple restores to same point
            # User can create new backup if they want a new checkpoint

            return f"Restored from backup ({reason}, {time_str})"

        except Exception as e:
            return f"Restore failed: {str(e)}"

    def has_backup(self) -> bool:
        """Check if a backup is available.

        Returns:
            True if backup exists, False otherwise
        """
        return self.bot_backup is not None

    def get_backup_info(self) -> str:
        """Get information about the current backup.

        Returns:
            Formatted string with backup metadata
        """
        if not self.has_backup():
            return "No backup available"

        from datetime import datetime

        timestamp = self.backup_metadata.get("timestamp", 0)
        dt = datetime.fromtimestamp(timestamp)
        time_str = dt.strftime("%Y-%m-%d %H:%M:%S")

        reason = self.backup_metadata.get("reason", "unknown")
        depth = self.backup_metadata.get("conversation_depth", 0)
        tokens = self.backup_metadata.get("token_count", 0)

        return (
            f"Backup available:\n  Created: {time_str}\n  Reason: {reason}\n"
            f"  Conversation depth: {depth}\n  Token count: {tokens:,}"
        )

    def _get_conversation_depth(self) -> int:
        """Calculate depth of current conversation tree.

        Returns:
            Number of nodes from root to current position
        """
        if self.bot_instance is None:
            return 0

        depth = 0
        current = self.bot_instance.conversation
        while current.parent:
            depth += 1
            current = current.parent
        return depth
