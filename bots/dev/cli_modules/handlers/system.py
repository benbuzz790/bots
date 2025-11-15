"""System and configuration command handlers for the CLI."""

import subprocess
from typing import List

from bots.dev.cli_modules.config import CLIContext
from bots.dev.cli_modules.display import display_metrics, pretty
from bots.dev.cli_modules.utils import (
    COLOR_RESET,
    COLOR_SYSTEM,
    COLOR_USER,
    check_for_interrupt,
    restore_terminal,
    setup_raw_mode,
)
from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, Engines


def create_auto_stash() -> str:
    """Create an automatic git stash with AI-generated message based on current diff."""

    try:
        # Check for staged changes first
        staged_diff_result = subprocess.run(["git", "diff", "--cached"], capture_output=True, text=True, timeout=10)
        # Check for unstaged changes
        unstaged_diff_result = subprocess.run(["git", "diff"], capture_output=True, text=True, timeout=10)
        if staged_diff_result.returncode != 0 or unstaged_diff_result.returncode != 0:
            return f"Error getting git diff: {staged_diff_result.stderr or unstaged_diff_result.stderr}"
        staged_diff = staged_diff_result.stdout.strip()
        unstaged_diff = unstaged_diff_result.stdout.strip()
        # Combine both diffs for analysis, but prefer staged if available
        diff_content = staged_diff if staged_diff else unstaged_diff
        if not diff_content:
            return "No changes to stash"
        # Generate stash message using Haiku
        stash_message = "WIP: auto-stash before user message"  # fallback
        try:
            # Create a Haiku bot instance - use the module-level import
            haiku_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)
            # Create a prompt for generating the stash message
            prompt = (
                f"Based on this git diff, generate a concise commit-style message "
                f"(under 50 chars) describing the changes. Start with 'WIP: ' if not already present:\n\n"
                f"{diff_content}\n\nRespond with just the message, nothing else."
            )
            ai_message = haiku_bot.respond(prompt)
            if ai_message and ai_message.strip():
                ai_message = ai_message.strip()
                if not ai_message.startswith("WIP:"):
                    ai_message = f"WIP: {ai_message}"
                if len(ai_message) <= 72:  # Git recommended limit
                    stash_message = ai_message
        except Exception:
            # Use fallback message if AI generation fails
            pass
        # Create the stash - this will stash both staged and unstaged changes
        stash_result = subprocess.run(
            ["git", "stash", "push", "-m", stash_message],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if stash_result.returncode != 0:
            return f"Error creating stash: {stash_result.stderr}"
        return f"Auto-stash created: {stash_message}"
    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Error in auto-stash: {str(e)}"


class SystemHandler:
    """Handler for system and configuration commands."""

    def help(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show help message."""
        help_lines = [
            "This program is an interactive terminal that uses AI bots.",
            "It allows you to chat with the LLM, save and load bot states, and execute various commands.",
            "The bot has the ability to read and write files and can execute powershell and python code directly.",
            "The bot also has tools to help edit python files in an accurate and token-efficient way.",
            "",
            "Available commands:",
            "/help: Show this help message",
            "/verbose: Show tool requests and results (default on)",
            "/quiet: Hide tool requests and results",
            "/save: Save the current bot (prompts for filename)",
            "/load: Load a previously saved bot (prompts for filename)",
            '/up: "rewind" the conversation by one turn by moving up the conversation tree',
            "/down: Move down the conversation tree. Requests index of reply if there are multiple.",
            "/left: Move to this conversation node's left sibling",
            "/right: Move to this conversation node's right sibling",
            "/auto: Let the bot work autonomously until it sends a response that doesn't use tools (esc to quit)",
            "/root: Move to the root node of the conversation tree",
            "/lastfork: Move to the previous node (going up) that has multiple replies",
            "/nextfork: Move to the next node (going down) that has multiple replies",
            "/label: Show all labels, create new label, or jump to existing label",
            "/leaf [number]: Show all conversation endpoints (leaves) and optionally jump to one",
            "/fp: Execute functional prompts with dynamic parameter collection",
            "/combine_leaves: Combine all leaves below current node using a recombinator function",
            "/broadcast_fp: Execute functional prompts on all leaf nodes",
            "/p [search]: Load a saved prompt (searches by name and content, pre-fills input)",
            "/s [text]: Save a prompt - saves provided text or last user message if no text given",
            "/r: Show recent prompts and select one to load",
            "/d [search]: Delete a saved prompt",
            "/add_tool [tool_name]: Add a tool to the bot (shows list if no name provided)",
            "/config: Show or modify CLI configuration",
            "/auto_stash: Toggle auto git stash before user messages",
            "/load_stash <name_or_index>: Load a git stash by name or index",
            "/backup: Manually create a backup of current bot state",
            "/restore: Restore bot from backup",
            "/backup_info: Show information about current backup",
            "/undo: Quick restore from backup (alias for /restore)",
            "/exit: Exit the program",
            "",
            "Type your messages normally to chat.",
        ]
        return "\n".join(help_lines)

    def verbose(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Enable verbose mode."""
        if context.config.verbose:
            return "Tool output is already enabled (verbose mode is on)"
        context.config.verbose = True
        context.config.save_config()

        # Also enable metrics verbose output
        try:
            from bots.observability import metrics

            metrics.set_metrics_verbose(True)
        except Exception:
            pass

        return "Tool output enabled - will now show detailed tool requests and results"

    def quiet(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Disable verbose mode."""
        context.config.verbose = False
        context.config.save_config()

        # Also disable metrics verbose output
        try:
            from bots.observability import metrics

            metrics.set_metrics_verbose(False)
        except Exception:
            pass

        return "Tool output disabled"

    def config(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show or modify configuration."""
        if not args:
            config_lines = [
                "Current configuration:",
                f"    verbose: {context.config.verbose}",
                f"    width: {context.config.width}",
                f"    indent: {context.config.indent}",
                f"    auto_stash: {context.config.auto_stash}",
                f"    remove_context_threshold: {context.config.remove_context_threshold}",
                f"    auto_mode_neutral_prompt: {context.config.auto_mode_neutral_prompt}",
                f"    auto_mode_reduce_context_prompt: {context.config.auto_mode_reduce_context_prompt}",
                f"    max_tokens: {context.config.max_tokens}",
                f"    temperature: {context.config.temperature}",
                f"    auto_backup: {context.config.auto_backup}",
                f"    auto_restore_on_error: {context.config.auto_restore_on_error}",
                "Use '/config set <setting> <value>' to modify settings.",
            ]
            return "\n".join(config_lines)
        if len(args) >= 3 and args[0] == "set":
            setting = args[1]
            value = " ".join(args[2:])  # Allow spaces in prompt values
            try:
                if setting == "verbose":
                    new_verbose = value.lower() in ("true", "1", "yes", "on")
                    context.config.verbose = new_verbose
                    # Sync metrics verbose setting
                    try:
                        from bots.observability import metrics

                        metrics.set_metrics_verbose(new_verbose)
                    except Exception:
                        pass
                elif setting == "width":
                    context.config.width = int(value)
                elif setting == "indent":
                    context.config.indent = int(value)
                elif setting == "auto_stash":
                    context.config.auto_stash = value.lower() in ("true", "1", "yes", "on")
                elif setting == "remove_context_threshold":
                    context.config.remove_context_threshold = int(value)
                elif setting == "auto_mode_neutral_prompt":
                    context.config.auto_mode_neutral_prompt = value
                elif setting == "auto_mode_reduce_context_prompt":
                    context.config.auto_mode_reduce_context_prompt = value
                elif setting == "max_tokens":
                    context.config.max_tokens = int(value)
                elif setting == "temperature":
                    context.config.temperature = float(value)
                elif setting == "auto_backup":
                    context.config.auto_backup = value.lower() in ("true", "1", "yes", "on")
                elif setting == "auto_restore_on_error":
                    context.config.auto_restore_on_error = value.lower() in ("true", "1", "yes", "on")
                else:
                    return f"Unknown setting: {setting}"
                context.config.save_config()
                return f"Set {setting} to {getattr(context.config, setting)}"
            except ValueError:
                return f"Invalid value for {setting}: {value}"
        return "Usage: /config or /config set <setting> <value>"

    def auto(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Run bot autonomously until it stops using tools."""
        try:

            context.conversation_backup = bot.conversation
            old_settings = setup_raw_mode()
            context.old_terminal_settings = old_settings

            # Check for interrupt before starting
            if check_for_interrupt():
                restore_terminal(old_settings)
                return "Autonomous execution interrupted by user"

            # Create dynamic continue prompt using policy with configurable prompts
            continue_prompt = fp.dynamic_prompts.policy(
                rules=[
                    # High token count with cooldown expired -> request context reduction
                    (
                        lambda b, i: (
                            context.last_message_metrics
                            and context.last_message_metrics.get("input_tokens", 0)
                            > context.config.remove_context_threshold  # noqa: E501
                            and context.context_reduction_cooldown <= 0
                        ),
                        context.config.auto_mode_reduce_context_prompt,
                    ),
                ],
                default=context.config.auto_mode_neutral_prompt,
            )

            # Use prompt_while with the dynamic continue prompt
            def stop_on_no_tools(bot: Bot) -> bool:
                return not bot.tool_handler.requests

            # Track iteration count to know when we're past the first prompt
            iteration_count = [0]

            def auto_callback(responses, nodes):
                # Update cooldown after each iteration
                if context.last_message_metrics:
                    last_input_tokens = context.last_message_metrics.get("input_tokens", 0)
                    if (
                        last_input_tokens > context.config.remove_context_threshold
                        and context.context_reduction_cooldown <= 0  # noqa: E501
                    ):  # noqa: E501
                        context.context_reduction_cooldown = 3
                    elif context.context_reduction_cooldown > 0:
                        context.context_reduction_cooldown -= 1

                # Capture metrics after each response
                try:
                    from bots.observability import metrics

                    context.last_message_metrics = metrics.get_and_clear_last_metrics()
                except Exception:
                    pass

                # Check for interrupt
                if check_for_interrupt():
                    raise KeyboardInterrupt()

                # After each iteration, if we're continuing, display next user prompt
                iteration_count[0] += 1
                if not stop_on_no_tools(bot):
                    # NOTE: Metrics are displayed by verbose_callback, not here
                    # This prevents duplicate display and ensures correct timing (after bot response)

                    # Get the next prompt text
                    next_prompt = (
                        continue_prompt(bot, iteration_count[0]) if callable(continue_prompt) else continue_prompt
                    )  # noqa: E501

                    # Display the user prompt
                    pretty(
                        next_prompt,
                        "You",
                        context.config.width,
                        context.config.indent,
                        COLOR_USER,
                        newline_after_name=False,
                    )

            # Get the standard callback for display
            display_callback = context.callbacks.get_standard_callback()

            # Combine callbacks
            def combined_callback(responses, nodes):
                # First run auto callback for logic
                auto_callback(responses, nodes)
                # Then run display callback if it exists
                if display_callback:
                    display_callback(responses, nodes)

            # Display the first user prompt
            pretty(
                "ok",
                "You",
                context.config.width,
                context.config.indent,
                COLOR_USER,
                newline_after_name=False,
            )

            # Run the autonomous loop
            fp.prompt_while(
                bot,
                "ok",
                continue_prompt=continue_prompt,
                stop_condition=stop_on_no_tools,
                callback=combined_callback,
            )

            restore_terminal(old_settings)
            display_metrics(context, bot)
            return ""

        except KeyboardInterrupt:
            if context.old_terminal_settings:
                restore_terminal(context.old_terminal_settings)
            return "\nAutonomous execution interrupted by user"
        except Exception as e:
            if context.old_terminal_settings:
                restore_terminal(context.old_terminal_settings)
            return f"Error in autonomous mode: {str(e)}"

    def auto_stash(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Toggle auto git stash functionality."""
        context.config.auto_stash = not context.config.auto_stash
        context.config.save_config()
        if context.config.auto_stash:
            return "Auto git stash enabled"
        else:
            return "Auto git stash disabled"

    def load_stash(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Load a git stash by name or index."""
        try:
            if not args:
                return "Usage: /load_stash <name_or_index>"

            stash_identifier = " ".join(args)

            # Get list of stashes
            result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True, check=True)
            stashes = result.stdout.strip().split("\n")

            if not stashes or not stashes[0]:
                return "No stashes found"

            # Try to find the stash
            stash_to_apply = None

            # Check if it's a numeric index
            if stash_identifier.isdigit():
                index = int(stash_identifier)
                if 0 <= index < len(stashes):
                    stash_to_apply = f"stash@{{{index}}}"
            else:
                # Search by name in the stash message
                for stash in stashes:
                    if stash_identifier.lower() in stash.lower():
                        # Extract stash@{n} from the line
                        stash_to_apply = stash.split(":")[0]
                        break

            if not stash_to_apply:
                return f"Stash '{stash_identifier}' not found"

            # Apply the stash
            subprocess.run(["git", "stash", "apply", stash_to_apply], check=True, capture_output=True, text=True)

            return f"Successfully applied {stash_to_apply}"

        except subprocess.CalledProcessError as e:
            # Handle stderr - it's already a string when text=True
            error_msg = e.stderr if e.stderr else str(e)
            return f"Git error: {error_msg}"
        except Exception as e:
            return f"Error loading stash: {str(e)}"

    def add_tool(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Add a tool to the bot from available tool modules."""
        # Import all available tools
        from bots.tools.code_tools import view, view_dir
        from bots.tools.python_edit import python_edit, python_view
        from bots.tools.python_execution_tool import execute_python
        from bots.tools.self_tools import branch_self, list_context, remove_context
        from bots.tools.terminal_tools import execute_powershell
        from bots.tools.web_tool import web_search

        # Map of available tools
        available_tools = {
            "view": view,
            "view_dir": view_dir,
            "python_view": python_view,
            "python_edit": python_edit,
            "execute_python": execute_python,
            "execute_powershell": execute_powershell,
            "branch_self": branch_self,
            "list_context": list_context,
            "remove_context": remove_context,
            "web_search": web_search,
        }

        # If no args, show view_dir of python files and allow choice
        if not args:
            try:
                # Show available tools
                tools_list = "\n".join([f"  {i + 1}. {name}" for i, name in enumerate(sorted(available_tools.keys()))])
                pretty(
                    f"Available tools:\n{tools_list}\n\nEnter tool name or number to add:",
                    "System",
                    context.config.width,
                    context.config.indent,
                    COLOR_SYSTEM,
                )

                # Get user input
                choice = input(f"{COLOR_USER}> {COLOR_RESET}").strip()

                # Handle numeric choice
                try:
                    choice_num = int(choice)
                    tool_names = sorted(available_tools.keys())
                    if 1 <= choice_num <= len(tool_names):
                        choice = tool_names[choice_num - 1]
                except ValueError:
                    pass  # Not a number, treat as tool name

                args = [choice]
            except Exception as e:
                return f"Error: {str(e)}"

        # Add the specified tool(s)
        added = []
        not_found = []

        for tool_name in args:
            tool_name = tool_name.strip()
            if tool_name in available_tools:
                bot.add_tools(available_tools[tool_name])
                added.append(tool_name)
            else:
                not_found.append(tool_name)

        result = []
        if added:
            result.append(f"Added tools: {', '.join(added)}")
        if not_found:
            result.append(f"Tools not found: {', '.join(not_found)}")

        return "\n".join(result) if result else "No tools added"
