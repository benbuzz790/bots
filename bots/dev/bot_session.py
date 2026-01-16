"""
BotSession - Clean interface for bot interactions.

Provides a simple input(str) -> str interface that handles all command parsing,
session management, and bot lifecycle internally. Designed to be used both by
the CLI and programmatically by plugins like obsidian-vault-agent.
"""

import textwrap
from typing import Callable, List, Optional

# Import all the handlers and context from CLI
from bots.dev.cli import (
    BackupHandler,
    CLIConfig,
    CLIContext,
    ConversationHandler,
    DynamicFunctionalPromptHandler,
    PromptHandler,
    StateHandler,
    SystemHandler,
    create_auto_stash,
)
from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines


class BotSession:
    """
    Simple session interface for bot interactions.

    Provides a clean input(str) -> str interface that handles:
    - Command parsing and execution
    - Session state management
    - Bot lifecycle management
    - Conversation navigation
    - Backup/restore functionality

    Example:
        session = BotSession()
        response = session.input("Hello, how are you?")
        response = session.input("/help")
        response = session.input("/save mybot")
    """

    def __init__(
        self,
        bot_filename: Optional[str] = None,
        function_filter: Optional[Callable] = None,
        auto_initialize: bool = True,
    ):
        """
        Initialize a new bot session.

        Args:
            bot_filename: Optional path to a saved bot file to load
            function_filter: Optional filter for functional prompts
            auto_initialize: If True, creates a new bot automatically. If False,
                           bot must be created with /load or manually.
        """
        # Initialize context and configuration
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
            "/clear": self.system.clear,
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
            "/models": self.system.models,
            "/switch": self.system.switch,
            "/d": self._handle_delete_prompt,
            "/r": self._handle_recent_prompts,
            "/backup": self.backup.backup,
            "/restore": self.backup.restore,
            "/backup_info": self.backup.backup_info,
            "/undo": self.backup.undo,
        }

        # Initialize metrics
        try:
            from bots.observability import metrics

            metrics.setup_metrics(verbose=False)
        except Exception as e:
            if self.context.config.verbose:
                print(f"Warning: metrics.setup_metrics failed: {e}")

    def input(self, user_input: str) -> str:
        """
        Process user input and return response.

        Handles both commands (starting with /) and regular chat messages.

        Args:
            user_input: The user's input string

        Returns:
            String response from the bot or command execution
        """
        if not user_input or not user_input.strip():
            return ""

        user_input = user_input.strip()

        # Handle /exit specially - return a signal
        if user_input == "/exit":
            return "__EXIT__"

        # Special case: bare "clear" command (no slash)
        if user_input.lower() == "clear":
            import os
            import platform

            if platform.system() == "Windows":
                os.system("cls")
            else:
                os.system("clear")
            return ""

        # Check if input contains a command at the end
        parts = user_input.split()
        has_command_at_end = len(parts) > 1 and parts[-1].startswith("/")

        responses = []

        if has_command_at_end:
            # Extract message and command
            message = " ".join(parts[:-1])
            command = parts[-1]

            # First send the message as chat
            if self.context.bot_instance and message:
                chat_response = self._handle_chat(self.context.bot_instance, message)
                if chat_response:
                    responses.append(chat_response)

            # Then execute the command
            cmd_response = self._handle_command(self.context.bot_instance, command)
            if cmd_response:
                responses.append(cmd_response)

        elif user_input.startswith("/"):
            # Command at start - handle normally
            cmd_response = self._handle_command(self.context.bot_instance, user_input)
            if cmd_response:
                responses.append(cmd_response)

        else:
            # Regular chat
            if self.context.bot_instance:
                chat_response = self._handle_chat(self.context.bot_instance, user_input)
                if chat_response:
                    responses.append(chat_response)
            else:
                responses.append("No bot instance. Use /load to load a bot or create one manually.")

        return "\n\n".join(responses) if responses else ""

    def _handle_command(self, bot: Optional[Bot], user_input: str) -> str:
        """Handle command input and return string response."""
        parts = user_input.split()
        command = None
        args = []

        if parts[0].startswith("/"):
            command = parts[0]
            args = parts[1:]
        elif parts[-1].startswith("/"):
            command = parts[-1]
            args = parts[:-1]
        else:
            command = parts[0]
            args = parts[1:]

        # Commands that should trigger auto-backup (risky operations)
        risky_commands = {"/fp", "/broadcast_fp", "/combine_leaves", "/auto", "/load"}

        if command in self.commands:
            try:
                # Auto-backup before risky commands
                if self.context.config.auto_backup and command in risky_commands:
                    self.context.create_backup(f"before_{command[1:]}")

                result = self.commands[command](bot, self.context, args)

                if result:
                    # Handle dict returns from handlers
                    if isinstance(result, dict):
                        result_type = result.get("type", "system")
                        message = result.get("message", result.get("content", str(result)))
                        return f"[{result_type}] {message}"
                    else:
                        # String or other return type
                        return str(result)
                return ""

            except Exception as e:
                error_msg = f"Command error: {str(e)}"

                # Try backup restoration on error
                if self.context.config.auto_restore_on_error and self.context.has_backup():
                    restore_result = self.context.restore_backup()
                    return f"{error_msg}\n{restore_result}"
                elif self.context.conversation_backup and bot:
                    # Fallback to old conversation backup system
                    bot.tool_handler.clear()
                    bot.conversation = self.context.conversation_backup
                    return f"{error_msg}\nRestored conversation from backup"

                return error_msg
        else:
            return "Unrecognized command. Try /help."

    def _handle_chat(self, bot: Bot, user_input: str) -> str:
        """Handle chat input and return bot response."""
        if not user_input:
            return ""

        try:
            # Track last user message for /s command
            self.last_user_message = user_input

            # Auto-backup before user message (if enabled)
            if self.context.config.auto_backup:
                self.context.create_backup("before_user_message")

            # Auto-stash if enabled
            stash_messages = []
            if self.context.config.auto_stash:
                stash_result = create_auto_stash()
                if "Auto-stash created:" in stash_result:
                    stash_messages.append(stash_result)
                elif "No changes to stash" not in stash_result:
                    stash_messages.append(stash_result)

            # Keep old conversation_backup for backward compatibility
            self.context.conversation_backup = bot.conversation

            # Get appropriate callback (respects verbose/quiet mode)
            callback = self.context.callbacks.get_standard_callback()

            # Execute the chat
            responses, _nodes = fp.chain(bot, [user_input], callback=callback)

            # Capture metrics after the response
            try:
                from bots.observability import metrics

                self.context.last_message_metrics = metrics.get_and_clear_last_metrics()
            except Exception as e:
                if self.context.config.verbose:
                    print(f"Warning: metrics.get_and_clear_last_metrics failed: {e}")

            # Combine stash messages with bot response
            result_parts = []
            if stash_messages:
                result_parts.extend(stash_messages)
            if responses and responses[0]:
                result_parts.append(responses[0])

            return "\n".join(result_parts) if result_parts else ""

        except Exception as e:
            error_msg = f"Chat error: {str(e)}"

            # Try backup restoration on error
            if self.context.config.auto_restore_on_error and self.context.has_backup():
                restore_result = self.context.restore_backup()
                return f"{error_msg}\n{restore_result}"
            elif self.context.conversation_backup:
                # Fallback to old conversation backup system
                bot.tool_handler.clear()
                bot.conversation = self.context.conversation_backup
                return f"{error_msg}\nRestored conversation from backup"

            return error_msg

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

    def _initialize_new_bot(self):
        """Initialize a new bot with default tools."""
        bot = AnthropicBot(
            model_engine=Engines.CLAUDE45_SONNET,
            max_tokens=self.context.config.max_tokens,
            temperature=self.context.config.temperature,
        )
        self.context.bot_instance = bot

        # Import and add tools
        from bots.tools.beep import piano
        from bots.tools.code_tools import view, view_dir
        from bots.tools.markdown_edit import markdown_edit, markdown_view
        from bots.tools.python_edit import python_edit, python_view
        from bots.tools.python_execution_tool import execute_python
        from bots.tools.self_tools import branch_self, remove_context
        from bots.tools.terminal_tools import execute_powershell, repair_mojibake
        from bots.tools.web_tool import web_search

        tools_to_add = [
            view,
            view_dir,
            python_view,
            markdown_view,
            execute_powershell,
            execute_python,
            branch_self,
            remove_context,
            web_search,
            python_edit,
            markdown_edit,
            piano,
            repair_mojibake,
        ]

        try:
            from bots.tools.invoke_namshub import invoke_namshub

            tools_to_add.append(invoke_namshub)
        except ImportError:
            pass

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

    @property
    def bot(self) -> Optional[Bot]:
        """Get the current bot instance."""
        return self.context.bot_instance

    def get_config(self) -> CLIConfig:
        """Get the current configuration."""
        return self.context.config

    def set_config(self, **kwargs):
        """Update configuration settings."""
        for key, value in kwargs.items():
            if hasattr(self.context.config, key):
                setattr(self.context.config, key, value)
