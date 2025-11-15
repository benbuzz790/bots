"""
Callback management for CLI operations.
This module contains callback classes for displaying bot responses, tool calls,
and metrics in real-time during CLI operations.
"""

from typing import TYPE_CHECKING

from bots.observability.callbacks import BotCallbacks

if TYPE_CHECKING:
    from bots.dev.cli_modules.config import CLIContext
# Import display utilities
from bots.dev.cli_modules.display import display_metrics, format_tool_data, pretty
from bots.dev.cli_modules.utils import COLOR_BOT, COLOR_TOOL_NAME, COLOR_TOOL_RESULT


class RealTimeDisplayCallbacks(BotCallbacks):
    """Callback that displays bot response and tools in real-time as they execute."""

    def __init__(self, context: "CLIContext"):
        self.context = context

    def on_api_call_complete(self, metadata=None):
        """Display bot response immediately after API call completes, before tools execute."""
        if metadata and "bot_response" in metadata:
            bot_response = metadata["bot_response"]
            bot_name = self.context.bot_instance.name if self.context.bot_instance else "Bot"
            pretty(
                bot_response,
                bot_name,
                self.context.config.width,
                self.context.config.indent,
                COLOR_BOT,
                newline_after_name=False,
            )

    def on_tool_start(self, tool_name: str, metadata=None):
        """Display tool request when it starts - show only the tool name and input parameters."""
        if not self.context.config.verbose:
            return
        if metadata and "tool_args" in metadata:
            # Extract just the input arguments, not the full request schema
            tool_args = metadata["tool_args"]
            # Format the arguments cleanly without JSON braces or quotes
            if tool_args:
                args_str = format_tool_data(tool_args, color=COLOR_TOOL_NAME)
            else:
                args_str = "(no arguments)"
            # Strip underscores from tool name for cleaner display
            display_name = tool_name.replace("_", " ")
            pretty(
                args_str,
                display_name,
                self.context.config.width,
                self.context.config.indent,
                COLOR_TOOL_NAME,
            )

    def on_tool_complete(self, tool_name: str, result, metadata=None):
        """Display tool result when it completes - show just the result, not wrapped in a dict."""
        if not self.context.config.verbose:
            return
        if result is not None:
            # Display result directly without wrapping in {'result': ...}
            if isinstance(result, str):
                # Add leading newline for string results
                result_str = "\n" + result
            elif isinstance(result, dict):
                result_str = format_tool_data(result, color=COLOR_TOOL_RESULT)
            else:
                result_str = "\n" + str(result)
            pretty(
                result_str,
                "result",  # lowercase to match tool name formatting
                self.context.config.width,
                self.context.config.indent,
                COLOR_TOOL_RESULT,
            )


class CLICallbacks:
    """Centralized callback management for CLI operations."""

    def __init__(self, context: "CLIContext"):
        self.context = context

    def create_message_only_callback(self):
        """Create a callback that only prints bot messages, no tool info."""

        def message_only_callback(responses, nodes):
            if responses and responses[-1]:
                bot_name = self.context.bot_instance.name if self.context.bot_instance else "Bot"
                pretty(
                    responses[-1],
                    bot_name,
                    self.context.config.width,
                    self.context.config.indent,
                    COLOR_BOT,
                    newline_after_name=False,
                )

        return message_only_callback

    def create_verbose_callback(self):
        """
        Create a callback that shows only metrics.
        Bot response and tools are shown in real-time by RealTimeDisplayCallbacks.
        """

        def verbose_callback(responses, nodes):
            # Bot response and tools are already displayed in real-time
            # Just show metrics at the end
            if hasattr(self.context, "bot_instance") and self.context.bot_instance:
                bot = self.context.bot_instance
                display_metrics(self.context, bot)

        return verbose_callback

    def create_quiet_callback(self):
        """Create a callback that shows only user and bot messages (no tools, no metrics)."""

        def quiet_callback(responses, nodes):
            # In quiet mode, RealTimeDisplayCallbacks still shows the bot response
            # but we don't show tools or metrics
            pass

        return quiet_callback

    def get_standard_callback(self):
        """Get the standard callback based on current config settings."""
        if self.context.config.verbose:
            return self.create_verbose_callback()
        else:
            return self.create_quiet_callback()
