"""
CLI for bot interactions with improved architecture and dynamic parameter collection.
Architecture:
- Handler classes for logical command grouping
- Command registry for easy extensibility
- Dynamic parameter collection for functional prompts
- Robust error handling with conversation backup
- Configuration support for CLI settings
"""

import argparse
import os
import textwrap
from typing import Callable, List, Optional

# Disable console tracing output for CLI (too verbose)
# Must be set BEFORE importing any bots modules that might initialize tracing
if "BOTS_OTEL_EXPORTER" not in os.environ:
    os.environ["BOTS_OTEL_EXPORTER"] = "none"


# Try to import readline, with fallback for Windows
try:
    import readline

    HAS_READLINE = True
except ImportError:
    HAS_READLINE = False

from bots.dev.cli_modules.callbacks import RealTimeDisplayCallbacks
from bots.dev.cli_modules.config import CLIContext
from bots.dev.cli_modules.display import pretty
from bots.dev.cli_modules.handlers.backup import BackupHandler
from bots.dev.cli_modules.handlers.conversation import ConversationHandler
from bots.dev.cli_modules.handlers.functional_prompts import DynamicFunctionalPromptHandler
from bots.dev.cli_modules.handlers.prompts import PromptHandler
from bots.dev.cli_modules.handlers.state import StateHandler
from bots.dev.cli_modules.handlers.system import SystemHandler, create_auto_stash
from bots.dev.cli_modules.utils import (
    COLOR_ERROR,
    COLOR_RESET,
    COLOR_SYSTEM,
    COLOR_USER,
    restore_terminal,
    setup_raw_mode,
)
from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot
from bots.observability import tracing

# Disable tracing span processors to prevent console output
try:
    if hasattr(tracing, "_tracer_provider") and tracing._tracer_provider is not None:
        tracing._tracer_provider._active_span_processor._span_processors.clear()
except Exception:
    pass  # If this fails, traces will still show but it's not critical


class CLI:
    """Main CLI class that orchestrates all handlers."""

    def __init__(self, bot_filename: Optional[str] = None, function_filter: Optional[Callable] = None):
        """Initialize the CLI with handlers and context."""
        self.context = CLIContext()
        self.bot_filename = bot_filename
        self.function_filter = function_filter
        self.last_user_message = None
        self.pending_prefill = None

        # Initialize handlers
        self.system = SystemHandler()
        self.state = StateHandler()
        self.conversation = ConversationHandler()
        self.fp = DynamicFunctionalPromptHandler(function_filter=function_filter)
        self.prompts = PromptHandler()
        self.backup = BackupHandler()

        # Register commands
        self.commands = {
            "/help": self.system.help,
            "/verbose": self.system.verbose,
            "/quiet": self.system.quiet,
            "/config": self.system.config,
            "/auto_stash": self.system.auto_stash,
            "/load_stash": self.system.load_stash,
            "/save": self.state.save,
            "/load": self.state.load,
            "/up": self.conversation.up,
            "/down": self.conversation.down,
            "/left": self.conversation.left,
            "/right": self.conversation.right,
            "/root": self.conversation.root,
            "/lastfork": self.conversation.lastfork,
            "/nextfork": self.conversation.nextfork,
            "/label": self.conversation.label,
            "/leaf": self.conversation.leaf,
            "/combine_leaves": self.conversation.combine_leaves,
            "/auto": self.system.auto,
            "/fp": self.fp.execute,
            "/broadcast_fp": self.fp.broadcast_fp,
            "/p": self._handle_load_prompt,
            "/s": self._handle_save_prompt,
            "/add_tool": self.system.add_tool,
            "/d": self._handle_delete_prompt,
            "/r": self._handle_recent_prompts,
            "/backup": self.backup.backup,
            "/restore": self.backup.restore,
            "/backup_info": self.backup.backup_info,
            "/undo": self.backup.undo,
        }

        # Initialize metrics with verbose=False since CLI handles its own display
        try:
            from bots.observability import metrics

            metrics.setup_metrics(verbose=False)
        except Exception:
            pass

    def run(self):
        """Main CLI loop."""
        try:
            print("Hello, world! ")
            self.context.old_terminal_settings = setup_raw_mode()
            if self.bot_filename:
                result = self.state._load_bot_from_file(self.bot_filename, self.context)
                if "Error" in result or "File not found" in result:
                    pretty(
                        f"Failed to load: {result}",
                        "system",
                        self.context.config.width,
                        self.context.config.indent,
                        COLOR_SYSTEM,
                    )
                    pretty(
                        "Starting with new bot",
                        "system",
                        self.context.config.width,
                        self.context.config.indent,
                        COLOR_SYSTEM,
                    )
                    self._initialize_new_bot()
                else:
                    if self.context.bot_instance:
                        pretty(
                            f"{self.context.bot_instance.name} loaded",
                            "system",
                            self.context.config.width,
                            self.context.config.indent,
                            COLOR_SYSTEM,
                        )
            else:
                self._initialize_new_bot()
            while True:
                try:
                    if not self.context.bot_instance:
                        pretty(
                            "No bot instance available. Use /new to create one.",
                            "system",
                            self.context.config.width,
                            self.context.config.indent,
                            COLOR_SYSTEM,
                        )
                    user_input = input(f"{COLOR_USER}You: {COLOR_RESET}").strip()

                    # Handle /exit command early
                    if user_input == "/exit":
                        raise SystemExit(0)

                    if not user_input:
                        continue

                    # Check if input contains a command at the end
                    parts = user_input.split()
                    has_command_at_end = len(parts) > 1 and parts[-1].startswith("/")

                    if has_command_at_end:
                        # Extract message and command
                        message = " ".join(parts[:-1])
                        command = parts[-1]

                        # First send the message as chat
                        if self.context.bot_instance and message:
                            self._handle_chat(self.context.bot_instance, message)

                        # Then execute the command
                        self._handle_command(self.context.bot_instance, command)
                    elif user_input.startswith("/"):
                        # Command at start - handle normally
                        self._handle_command(self.context.bot_instance, user_input)
                    else:
                        # Regular chat
                        if self.context.bot_instance:
                            self._handle_chat(self.context.bot_instance, user_input)
                        else:
                            pretty(
                                "No bot instance. Use /new to create one.",
                                "system",
                                self.context.config.width,
                                self.context.config.indent,
                                COLOR_SYSTEM,
                            )
                except KeyboardInterrupt:
                    print("\nUse /exit to quit.")
                    continue
                except EOFError:
                    break
        finally:
            restore_terminal(self.context.old_terminal_settings)
            print("\nGoodbye!")

    def _handle_load_prompt(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Handle /p command to load prompts."""
        message, prefill_text = self.prompts.load_prompt(bot, context, args)
        if prefill_text:
            self.pending_prefill = prefill_text
        return message

    def _handle_save_prompt(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Handle /s command to save prompts."""
        return self.prompts.save_prompt(bot, context, args, self.last_user_message)

    def _handle_delete_prompt(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Handle /d command to delete prompts."""
        return self.prompts.delete_prompt(bot, context, args)

    def _handle_recent_prompts(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Handle /r command to show recent prompts."""
        message, prefill_text = self.prompts.recent_prompts(bot, context, args)
        if prefill_text:
            self.pending_prefill = prefill_text
        return message

    def _get_user_input(self, prompt_text: str = ">>> ") -> str:
        """Get user input, with optional pre-fill support."""
        if self.pending_prefill and HAS_READLINE:
            # Use readline to pre-fill the input
            def startup_hook():
                readline.insert_text(self.pending_prefill)
                readline.redisplay()

            readline.set_startup_hook(startup_hook)
            try:
                user_input = input(prompt_text)
                return user_input
            finally:
                readline.set_startup_hook(None)
                self.pending_prefill = None  # Clear after use
        elif self.pending_prefill:
            # Fallback for systems without readline
            print(f"Loaded prompt (edit as needed):\n{self.pending_prefill}")
            user_input = input(prompt_text)
            self.pending_prefill = None
            return user_input
        else:
            return input(prompt_text)

    def _initialize_new_bot(self):
        """Initialize a new bot with default tools."""
        from bots.foundation.base import Engines

        bot = AnthropicBot(
            model_engine=Engines.CLAUDE45_SONNET,
            max_tokens=self.context.config.max_tokens,
            temperature=self.context.config.temperature,
        )
        self.context.bot_instance = bot
        # Attach real-time display callback
        self.context.bot_instance.callbacks = RealTimeDisplayCallbacks(self.context)

        # bot.add_tools(bots.tools.terminal_tools, bots.tools.python_edit, bots.tools.code_tools, bots.tools.self_tools)
        from bots.tools.code_tools import view, view_dir
        from bots.tools.python_edit import python_edit, python_view
        from bots.tools.python_execution_tool import execute_python
        from bots.tools.self_tools import branch_self, list_context, remove_context
        from bots.tools.terminal_tools import execute_powershell
        from bots.tools.web_tool import web_search

        # Optional: import invoke_namshub if available (not released yet)
        tools_to_add = [
            view,
            view_dir,
            python_view,
            execute_powershell,
            execute_python,
            branch_self,
            remove_context,
            list_context,
            web_search,
            python_edit,
        ]

        try:
            from bots.tools.invoke_namshub import invoke_namshub

            tools_to_add.append(invoke_namshub)
        except ImportError:
            pass  # invoke_namshub not available, skip it

        bot.add_tools(*tools_to_add)

        sys_msg = textwrap.dedent(
            """
        You're a coding agent. Please follow these rules:
            1. Keep edits and even writing new files to small chunks. You have a low max_token limit
                and will hit tool errors if you try making too big of a change.
            2. Avoid using cd. Your terminal is stateful and will remember if you use cd.
                Instead, use full relative paths.
            3. Ex uno plura! You have a powerful tool called branch_self which you should use for
                multitasking or even just to save context in your main branch. Always use a concrete
                definition of done when branching.
        """
        ).strip()
        bot.system_message = sys_msg

        # This works well as a fallback:
        # bot.add_tools(bots.tools.terminal_tools, view, view_dir)

    def _handle_command(self, bot: Bot, user_input: str):
        """Handle command input."""
        parts = user_input.split()
        command = None
        args = []
        if parts[0].startswith("/"):
            command = parts[0]
            args = parts[1:]
        elif parts[-1].startswith("/"):
            command = parts[-1]
            args = parts[:-1]  # Everything except the command
        else:
            command = parts[0]
            args = parts[1:]

        # Commands that should trigger auto-backup (risky operations)
        risky_commands = {"/fp", "/broadcast_fp", "/combine_leaves", "/auto", "/load"}

        if command in self.commands:
            try:
                # Auto-backup before risky commands
                if self.context.config.auto_backup and command in risky_commands:
                    self.context.create_backup(f"before_{command[1:]}")  # Remove leading /

                result = self.commands[command](bot, self.context, args)
                if result:
                    pretty(result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
            except Exception as e:
                pretty(
                    f"Command error: {str(e)}",
                    "Error",
                    self.context.config.width,
                    self.context.config.indent,
                    COLOR_ERROR,  # noqa: E501
                )  # noqa: E501

                # Try new backup system first, fall back to old system
                if self.context.config.auto_restore_on_error and self.context.has_backup():
                    result = self.context.restore_backup()
                    pretty(result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
                elif self.context.conversation_backup and bot:
                    # Fallback to old conversation backup system
                    bot.tool_handler.clear()
                    bot.conversation = self.context.conversation_backup
                    pretty(
                        "Restored conversation from backup",
                        "system",
                        self.context.config.width,
                        self.context.config.indent,
                        COLOR_SYSTEM,
                    )
        else:
            pretty(
                "Unrecognized command. Try /help.",
                "system",
                self.context.config.width,
                self.context.config.indent,
                COLOR_SYSTEM,
            )

    def _handle_chat(self, bot: Bot, user_input: str):
        """Handle chat input."""
        if not user_input:
            return
        try:
            # Track last user message for /s command
            self.last_user_message = user_input

            # Auto-backup before user message (if enabled)
            if self.context.config.auto_backup:
                self.context.create_backup("before_user_message")

            # Auto-stash if enabled
            if self.context.config.auto_stash:
                stash_result = create_auto_stash()
                if "Auto-stash created:" in stash_result:
                    pretty(stash_result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
                elif "No changes to stash" not in stash_result:
                    # Show errors but not "no changes" message
                    pretty(stash_result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)

            # Keep old conversation_backup for backward compatibility during transition
            self.context.conversation_backup = bot.conversation
            callback = self.context.callbacks.get_standard_callback()
            responses, nodes = fp.chain(bot, [user_input], callback=callback)

            # Capture metrics after the response for potential future use
            try:
                from bots.observability import metrics

                self.context.last_message_metrics = metrics.get_and_clear_last_metrics()
            except Exception:
                pass

            # Note: Metrics are now displayed inside the verbose callback, not here
            # Quiet mode shows no metrics at all
        except Exception as e:
            pretty(f"Chat error: {str(e)}", "Error", self.context.config.width, self.context.config.indent, COLOR_ERROR)

            # Try new backup system first, fall back to old system
            if self.context.config.auto_restore_on_error and self.context.has_backup():
                result = self.context.restore_backup()
                pretty(result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
            elif self.context.conversation_backup:
                # Fallback to old conversation backup system
                bot.tool_handler.clear()
                bot.conversation = self.context.conversation_backup
                pretty(
                    "Restored conversation from backup",
                    "system",
                    self.context.config.width,
                    self.context.config.indent,
                    COLOR_SYSTEM,
                )


def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(
        description="Interactive CLI for AI bots with conversation management and dynamic parameter collection.",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=textwrap.dedent(
            """
             Examples:
             python -m bots.dev.cli_combined                    # Start with new bot
             python -m bots.dev.cli_combined mybot.bot          # Load bot from file
             python -m bots.dev.cli_combined saved_conversation # Load bot (auto-adds .bot extension)
             """.strip()
        ),
    )
    parser.add_argument("filename", nargs="?", help="Bot file to load (.bot extension will be added if not present)")
    return parser.parse_args()


def main(bot_filename=None, function_filter=None):
    """Entry point for the CLI."""
    if bot_filename is None:
        args = parse_args()
        bot_filename = args.filename
    cli = CLI(bot_filename=bot_filename, function_filter=function_filter)
    cli.run()


if __name__ == "__main__":
    main()
