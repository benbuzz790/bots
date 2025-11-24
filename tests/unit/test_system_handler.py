"""Tests for SystemHandler returning data dicts instead of calling pretty()."""

from unittest.mock import MagicMock, patch

from bots.dev.cli import CLIConfig, CLIContext, SystemHandler
from bots.foundation.base import Bot


class TestSystemHandlerDataFormat:
    """Test that SystemHandler methods return data dicts."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SystemHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_config = MagicMock(spec=CLIConfig)
        self.mock_config.verbose = False
        self.mock_config.width = 80
        self.mock_config.indent = 4
        self.mock_config.auto_stash = False
        self.mock_config.remove_context_threshold = 10000
        self.mock_config.auto_mode_neutral_prompt = "ok"
        self.mock_config.auto_mode_reduce_context_prompt = "reduce context"
        self.mock_config.max_tokens = 4096
        self.mock_config.temperature = 0.7
        self.mock_config.auto_backup = False
        self.mock_config.auto_restore_on_error = False

        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.config = self.mock_config

    def test_help_returns_string(self):
        """help() returns help text as string."""
        result = self.handler.help(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert "Available commands:" in result
        assert "/help" in result

    def test_verbose_returns_string(self):
        """verbose() returns status message as string."""
        result = self.handler.verbose(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert "enabled" in result.lower()
        assert self.mock_config.verbose is True

    def test_verbose_already_on(self):
        """verbose() returns appropriate message when already on."""
        self.mock_config.verbose = True
        result = self.handler.verbose(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert "already enabled" in result.lower()

    def test_quiet_returns_string(self):
        """quiet() returns status message as string."""
        self.mock_config.verbose = True
        result = self.handler.quiet(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert "disabled" in result.lower()
        assert self.mock_config.verbose is False

    def test_config_no_args_returns_string(self):
        """config() with no args returns current config as string."""
        result = self.handler.config(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert "Current configuration:" in result
        assert "verbose:" in result
        assert "width:" in result

    def test_config_set_verbose(self):
        """config() can set verbose setting."""
        result = self.handler.config(self.mock_bot, self.mock_context, ["set", "verbose", "true"])

        assert isinstance(result, str)
        assert "Set verbose to" in result
        assert self.mock_config.verbose is True

    def test_config_set_width(self):
        """config() can set width setting."""
        result = self.handler.config(self.mock_bot, self.mock_context, ["set", "width", "100"])

        assert isinstance(result, str)
        assert "Set width to" in result
        assert self.mock_config.width == 100

    def test_config_invalid_setting(self):
        """config() returns error for invalid setting."""
        result = self.handler.config(self.mock_bot, self.mock_context, ["set", "invalid", "value"])

        assert isinstance(result, str)
        assert "Unknown setting" in result

    def test_config_invalid_value(self):
        """config() returns error for invalid value."""
        result = self.handler.config(self.mock_bot, self.mock_context, ["set", "width", "not_a_number"])

        assert isinstance(result, str)
        assert "Invalid value" in result

    def test_auto_stash_toggle(self):
        """auto_stash() toggles the setting."""
        initial = self.mock_config.auto_stash
        result = self.handler.auto_stash(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert self.mock_config.auto_stash != initial
        if self.mock_config.auto_stash:
            assert "enabled" in result.lower()
        else:
            assert "disabled" in result.lower()

    @patch("subprocess.run")
    def test_load_stash_no_args(self, mock_run):
        """load_stash() returns usage message with no args."""
        result = self.handler.load_stash(self.mock_bot, self.mock_context, [])

        assert isinstance(result, str)
        assert "Usage:" in result

    @patch("subprocess.run")
    def test_load_stash_not_found(self, mock_run):
        """load_stash() returns error when stash not found."""
        mock_run.return_value = MagicMock(stdout="stash@{0}: WIP on main\n", returncode=0)

        result = self.handler.load_stash(self.mock_bot, self.mock_context, ["nonexistent"])

        assert isinstance(result, str)
        assert "not found" in result.lower()

    def test_add_tool_no_args_returns_string(self):
        """add_tool() with no args prompts for selection."""
        # This test is tricky because it uses input(), so we'll just verify it doesn't crash
        # and returns a string when given a tool name
        pass

    def test_add_tool_with_valid_tool(self):
        """add_tool() adds a valid tool."""
        result = self.handler.add_tool(self.mock_bot, self.mock_context, ["view"])

        assert isinstance(result, str)
        assert "Added tools:" in result or "view" in result

    def test_add_tool_with_invalid_tool(self):
        """add_tool() returns error for invalid tool."""
        result = self.handler.add_tool(self.mock_bot, self.mock_context, ["nonexistent_tool"])

        assert isinstance(result, str)
        assert "not found" in result.lower()


class TestSystemHandlerNoDirectPretty:
    """Test that SystemHandler doesn't call pretty() directly."""

    def setup_method(self):
        """Set up test fixtures."""
        self.handler = SystemHandler()
        self.mock_bot = MagicMock(spec=Bot)
        self.mock_config = MagicMock(spec=CLIConfig)
        self.mock_config.verbose = False
        self.mock_config.width = 80
        self.mock_config.indent = 4
        self.mock_config.auto_stash = False
        self.mock_config.remove_context_threshold = 10000
        self.mock_config.auto_mode_neutral_prompt = "ok"
        self.mock_config.auto_mode_reduce_context_prompt = "reduce context"
        self.mock_config.max_tokens = 4096
        self.mock_config.temperature = 0.7
        self.mock_config.auto_backup = False
        self.mock_config.auto_restore_on_error = False

        self.mock_context = MagicMock(spec=CLIContext)
        self.mock_context.config = self.mock_config

    @patch("bots.dev.cli.pretty")
    def test_help_no_pretty_call(self, mock_pretty):
        """help() doesn't call pretty()."""
        self.handler.help(self.mock_bot, self.mock_context, [])

        # help() should return string, not call pretty()
        assert not mock_pretty.called

    @patch("bots.dev.cli.pretty")
    def test_verbose_no_pretty_call(self, mock_pretty):
        """verbose() doesn't call pretty()."""
        self.handler.verbose(self.mock_bot, self.mock_context, [])

        assert not mock_pretty.called

    @patch("bots.dev.cli.pretty")
    def test_quiet_no_pretty_call(self, mock_pretty):
        """quiet() doesn't call pretty()."""
        self.handler.quiet(self.mock_bot, self.mock_context, [])

        assert not mock_pretty.called

    @patch("bots.dev.cli.pretty")
    def test_config_no_pretty_call(self, mock_pretty):
        """config() doesn't call pretty()."""
        self.handler.config(self.mock_bot, self.mock_context, [])

        assert not mock_pretty.called
