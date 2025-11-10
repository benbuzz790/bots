"""
End-to-end tests for CLI backup system.
"""

from unittest.mock import Mock

import pytest

from bots.dev.cli import BackupHandler, CLIContext
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Engines


class TestCLIBackupSystem:
    """Test the CLI backup system."""

    def test_backup_creation(self):
        """Test that backups can be created successfully."""
        context = CLIContext()
        context.bot_instance = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)

        # Create a backup
        result = context.create_backup("test_backup")

        assert result is True
        assert context.has_backup() is True
        assert context.backup_metadata["reason"] == "test_backup"
        assert context.bot_backup is not None
        assert context.bot_backup is not context.bot_instance  # Should be a copy

    def test_backup_restore(self):
        """Test that backups can be restored."""
        context = CLIContext()
        context.bot_instance = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)

        # Create a backup
        context.create_backup("before_change")

        # Simulate a change to the bot
        context.bot_instance.conversation = Mock()

        # Restore backup
        result = context.restore_backup()

        assert "Restored from backup" in result
        assert context.bot_instance.conversation is not None
        # Verify restored conversation matches original structure
        # Since restore creates a copy, we check structural properties
        assert hasattr(context.bot_instance.conversation, "content")
        assert hasattr(context.bot_instance.conversation, "role")
        # Verify it's not the Mock object we set
        assert not isinstance(context.bot_instance.conversation, Mock)

    def test_no_backup_available(self):
        """Test behavior when no backup is available."""
        context = CLIContext()

        assert context.has_backup() is False
        result = context.restore_backup()
        assert result == "No backup available"

    def test_backup_info(self):
        """Test backup info display."""
        context = CLIContext()
        context.bot_instance = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)

        # No backup yet
        info = context.get_backup_info()
        assert info == "No backup available"

        # Create backup
        context.create_backup("test_reason")

        # Check info
        info = context.get_backup_info()
        assert "Backup available" in info
        assert "test_reason" in info

    def test_backup_prevents_concurrent_backups(self):
        """Test that concurrent backups are prevented."""
        context = CLIContext()
        context.bot_instance = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)

        # Set backup in progress flag
        context.backup_in_progress = True

        # Try to create backup
        result = context.create_backup("concurrent_test")

        assert result is False

    def test_backup_handler_commands(self):
        """Test BackupHandler command methods."""
        handler = BackupHandler()
        context = CLIContext()
        bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
        context.bot_instance = bot

        # Test backup command
        result = handler.backup(bot, context, [])
        assert "Backup created successfully" in result

        # Test backup_info command
        result = handler.backup_info(bot, context, [])
        assert "Backup available" in result

        # Test restore command
        result = handler.restore(bot, context, [])
        assert "Restored from backup" in result

        # Test undo command (alias for restore)
        context.create_backup("test")
        result = handler.undo(bot, context, [])
        assert "Restored from backup" in result

    def test_backup_with_conversation_changes(self):
        """Test that backup captures conversation state."""
        context = CLIContext()
        bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
        context.bot_instance = bot

        # Get the initial conversation state
        initial_conversation = bot.conversation

        # Helper function to calculate depth
        def get_depth(node):
            depth = 0
            current = node
            while current.parent is not None:
                depth += 1
                current = current.parent
            return depth

        # Simulate a conversation change by adding a user message using the bot's node type
        # (without making an actual API call)
        from bots.foundation.anthropic_bots import AnthropicNode

        user_node = AnthropicNode(content="test user message", role="user", parent=initial_conversation)
        initial_conversation.replies.append(user_node)
        bot.conversation = user_node

        # Capture the conversation state at backup time
        backup_depth = get_depth(bot.conversation)
        original_content = bot.conversation.content

        # Create backup
        result = context.create_backup("before_more_changes")
        assert result is True, "Backup creation should succeed"

        # Make more changes - add another message
        assistant_node = AnthropicNode(content="test assistant message", role="assistant", parent=user_node)
        user_node.replies.append(assistant_node)
        bot.conversation = assistant_node

        # Verify content changed after modification
        intermediate_content = bot.conversation.content
        intermediate_depth = get_depth(bot.conversation)
        assert intermediate_content != original_content, "Content should have changed before restore"
        assert intermediate_depth > backup_depth, "Conversation should be deeper after changes"

        # Restore
        restore_result = context.restore_backup()
        assert "Restored from backup" in restore_result, f"Expected restore success, got: {restore_result}"

        # Check that we're back to the backed up state
        assert context.bot_instance is not None
        assert context.bot_instance.conversation is not None

        # Verify the conversation was reverted to the backup state
        restored_depth = get_depth(context.bot_instance.conversation)
        assert restored_depth == backup_depth, f"Conversation depth should be {backup_depth}, got {restored_depth}"
        assert context.bot_instance.conversation.content == original_content, "Conversation content should match backup state"


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
