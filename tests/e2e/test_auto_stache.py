import os
import subprocess
import tempfile
import time
from pathlib import Path
from unittest.mock import patch

import pytest

from bots.dev.cli import CLI, CLIConfig, create_auto_stash

pytestmark = pytest.mark.e2e


def safe_rmtree(path):
    """Safely remove directory tree on Windows."""
    import shutil
    import stat

    def handle_remove_readonly(func, path, exc):
        if os.path.exists(path):
            os.chmod(path, stat.S_IWRITE)
            func(path)

    try:
        shutil.rmtree(path, onerror=handle_remove_readonly)
    except Exception:
        # If still fails, try again after a short delay
        time.sleep(0.1)
        try:
            shutil.rmtree(path, onerror=handle_remove_readonly)
        except Exception:
            pass  # Give up gracefully


class TestAutoStashConfig:
    """Test auto-stash configuration functionality."""

    def test_config_default_false(self):
        """Test that auto_stash defaults to False."""
        config = CLIConfig()
        assert config.auto_stash is False

    def test_config_save_load(self, tmp_path):
        """Test saving and loading auto_stash configuration."""
        # Change to temp directory for config file
        original_cwd = os.getcwd()
        os.chdir(tmp_path)

        try:
            config = CLIConfig()
            config.auto_stash = True
            config.save_config()

            # Create new config instance to test loading
            new_config = CLIConfig()
            assert new_config.auto_stash is True
        finally:
            os.chdir(original_cwd)

    def test_config_command_show(self):
        """Test /config command shows auto_stash setting."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()
        context.config.auto_stash = True

        result = handler.config(None, context, [])
        assert "auto_stash: True" in result

    def test_config_command_set(self):
        """Test /config set auto_stash command."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        # Test setting to true
        result = handler.config(None, context, ["set", "auto_stash", "true"])
        assert "Set auto_stash to True" in result
        assert context.config.auto_stash is True

        # Test setting to false
        result = handler.config(None, context, ["set", "auto_stash", "false"])
        assert "Set auto_stash to False" in result
        assert context.config.auto_stash is False

    def test_auto_stash_toggle_command(self):
        """Test /auto_stash toggle command."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        # Test enabling
        assert context.config.auto_stash is False
        result = handler.auto_stash(None, context, [])
        assert "Auto git stash enabled" in result
        assert context.config.auto_stash is True

        # Test disabling
        result = handler.auto_stash(None, context, [])
        assert "Auto git stash disabled" in result
        assert context.config.auto_stash is False


class TestCreateAutoStash:
    """Test the create_auto_stash function."""

    def setup_method(self):
        """Set up a temporary git repository for testing."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)

        # Create initial commit
        Path("README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)

    def test_no_changes_to_stash(self):
        """Test behavior when there are no changes to stash."""
        result = create_auto_stash()
        assert "No changes to stash" in result

    def test_real_ai_stash_message_generation(self):
        """Integration test with real AI API call."""
        # Skip if no API key available
        if not os.getenv("ANTHROPIC_API_KEY"):
            pytest.skip("ANTHROPIC_API_KEY not available")

        # Create meaningful changes and stage them
        Path("calculator.py").write_text(
            """
def add(a, b):
    return a + b

def multiply(a, b):
    return a * b
"""
        )
        subprocess.run(["git", "add", "calculator.py"], check=True)

        result = create_auto_stash()

        assert "Auto-stash created:" in result
        assert "WIP:" in result

        # Verify the AI generated a reasonable message
        stash_result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True)
        stash_message = stash_result.stdout.strip()
        assert "calculator" in stash_message.lower() or "add" in stash_message.lower() or "math" in stash_message.lower()


class TestLoadStashCommand:
    """Test the load_stash command functionality."""

    def setup_method(self):
        """Set up a temporary git repository with stashes."""
        self.temp_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.temp_dir)

        # Initialize git repo
        subprocess.run(["git", "init"], check=True, capture_output=True)
        subprocess.run(["git", "config", "user.email", "test@example.com"], check=True)
        subprocess.run(["git", "config", "user.name", "Test User"], check=True)

        # Create initial commit
        Path("README.md").write_text("# Test Repo")
        subprocess.run(["git", "add", "README.md"], check=True)
        subprocess.run(["git", "commit", "-m", "Initial commit"], check=True)

        # Create some stashes - need to actually create changes first
        Path("file1.txt").write_text("content 1")
        subprocess.run(["git", "add", "file1.txt"], check=True)
        subprocess.run(["git", "stash", "push", "-m", "WIP: first feature"], check=True)

        Path("file2.txt").write_text("content 2")
        subprocess.run(["git", "add", "file2.txt"], check=True)
        subprocess.run(["git", "stash", "push", "-m", "WIP: second feature"], check=True)

    def teardown_method(self):
        """Clean up temporary directory."""
        os.chdir(self.original_cwd)
        safe_rmtree(self.temp_dir)

    def test_load_stash_by_index(self):
        """Test loading stash by index."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        result = handler.load_stash(None, context, ["0"])
        assert "Successfully applied stash@{0}" in result

        # Verify file was restored
        assert Path("file2.txt").exists()
        assert Path("file2.txt").read_text() == "content 2"

    def test_load_stash_by_name(self):
        """Test loading stash by name pattern."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        result = handler.load_stash(None, context, ["first"])
        assert "Successfully applied" in result

        # Verify file was restored
        assert Path("file1.txt").exists()
        assert Path("file1.txt").read_text() == "content 1"

    def test_load_stash_not_found(self):
        """Test error when stash not found."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        result = handler.load_stash(None, context, ["nonexistent"])
        assert "Stash 'nonexistent' not found" in result

    def test_load_stash_no_args(self):
        """Test error when no arguments provided."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        result = handler.load_stash(None, context, [])
        assert "Usage: /load_stash <stash_name_or_index>" in result


class TestCLIIntegration:
    """Test auto-stash integration with CLI."""

    def test_commands_registered(self):
        """Test that auto-stash commands are registered in CLI."""
        cli = CLI()

        assert "/auto_stash" in cli.commands
        assert "/load_stash" in cli.commands
        assert "/config" in cli.commands

    def test_help_includes_auto_stash(self):
        """Test that help includes auto-stash commands."""
        from bots.dev.cli import CLIContext, SystemHandler

        handler = SystemHandler()
        context = CLIContext()

        help_text = handler.help(None, context, [])
        assert "/auto_stash" in help_text
        assert "/load_stash" in help_text
        assert "Toggle auto git stash" in help_text


class TestEdgeCases:
    """Test edge cases and error conditions."""

    def test_create_auto_stash_timeout(self):
        """Test timeout handling in create_auto_stash."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = subprocess.TimeoutExpired("git", 10)

            result = create_auto_stash()
            assert "Git command timed out" in result

    def test_create_auto_stash_general_exception(self):
        """Test general exception handling in create_auto_stash."""
        with patch("subprocess.run") as mock_run:
            mock_run.side_effect = Exception("Unexpected error")

            result = create_auto_stash()
            assert "Error in auto-stash: Unexpected error" in result


if __name__ == "__main__":
    pytest.main([__file__])
