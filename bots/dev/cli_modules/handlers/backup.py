"""Backup management command handlers for the CLI."""

from typing import List

from bots.dev.cli_modules.config import CLIContext
from bots.foundation.base import Bot


class BackupHandler:
    """Handler for backup management commands."""

    def backup(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Manually create a backup of current bot state."""
        if context.create_backup("manual"):
            return "Backup created successfully"
        else:
            return "Backup failed - see error message above"

    def restore(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Restore bot from backup."""
        return context.restore_backup()

    def backup_info(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show information about current backup."""
        return context.get_backup_info()

    def undo(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Quick restore from backup (alias for /restore)."""
        return context.restore_backup()
