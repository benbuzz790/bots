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
import inspect
import json
import os
import platform
import re
import sys
import textwrap
import time
from pathlib import Path
from typing import Any, Callable, Dict, List, Optional

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

from bots.flows import functional_prompts as fp
from bots.flows import recombinators
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode, ModuleLoadError
from bots.observability import tracing
from bots.observability.callbacks import BotCallbacks
from bots.utils.terminal_utils import create_color_scheme

# Disable tracing span processors to prevent console output
try:
    if hasattr(tracing, "_tracer_provider") and tracing._tracer_provider is not None:
        tracing._tracer_provider._active_span_processor._span_processors.clear()
except Exception:
    pass  # If this fails, traces will still show but it's not critical


class EscapeException(Exception):
    """Exception raised when user presses ESC to cancel input."""


def input_with_esc(prompt: str = "") -> str:
    """
    Get user input with ESC key support to cancel/interrupt.

    Args:
        prompt: The prompt string to display

    Returns:
        The user's input string

    Raises:
        EscapeException: If user presses ESC key
    """
    if platform.system() == "Windows":
        # Windows implementation
        import msvcrt

        print(prompt, end="", flush=True)
        chars = []
        while True:
            if msvcrt.kbhit():
                char = msvcrt.getch()
                if char == b"\x1b":  # ESC key
                    print()  # New line
                    raise EscapeException("Input cancelled by ESC key")
                elif char == b"\r":  # Enter key
                    print()  # New line
                    return "".join(chars)
                elif char == b"\x08":  # Backspace
                    if chars:
                        chars.pop()
                        # Erase character on screen
                        print("\b \b", end="", flush=True)
                elif char == b"\x03":  # Ctrl+C
                    print()
                    raise KeyboardInterrupt()
                else:
                    try:
                        decoded = char.decode("utf-8")
                        chars.append(decoded)
                        print(decoded, end="", flush=True)
                    except UnicodeDecodeError:
                        pass
    else:
        # Unix/Linux/Mac implementation
        import select
        import sys
        import termios
        import tty

        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(fd)
            print(prompt, end="", flush=True)
            chars = []

            while True:
                if select.select([sys.stdin], [], [], 0.1)[0]:
                    char = sys.stdin.read(1)

                    if char == "\x1b":  # ESC key
                        print("\r\n", end="", flush=True)
                        raise EscapeException("Input cancelled by ESC key")
                    elif char == "\r" or char == "\n":  # Enter key
                        print("\r\n", end="", flush=True)
                        return "".join(chars)
                    elif char == "\x7f":  # Backspace/Delete
                        if chars:
                            chars.pop()
                            print("\b \b", end="", flush=True)
                    elif char == "\x03":  # Ctrl+C
                        print("\r\n", end="", flush=True)
                        raise KeyboardInterrupt()
                    elif ord(char) >= 32:  # Printable characters
                        chars.append(char)
                        print(char, end="", flush=True)
        finally:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def _find_leaves_util(node: ConversationNode) -> List[ConversationNode]:
    """Utility function to recursively find all leaf nodes from a given node.

    This is a standalone utility that can be used by any handler.

    Args:
        node: The starting conversation node

    Returns:
        List of leaf nodes (nodes with no replies)
    """
    leaves = []

    def dfs(current_node):
        """Performs depth-first search traversal to find all leaf nodes in a tree structure.

        Traverses the tree recursively, identifying nodes without replies as leaves and
        adding them to the leaves collection.

        Args:
            current_node: The node to start traversal from. Must have a 'replies' attribute
                that is either empty (for leaf nodes) or contains child nodes.
        """
        if not current_node.replies:  # This is a leaf
            leaves.append(current_node)
        else:
            for reply in current_node.replies:
                dfs(reply)

    dfs(node)
    return leaves


if platform.system() == "Windows":
    import msvcrt
else:
    import select
    import termios
    import tty

# Color constants - will be initialized based on terminal capabilities
# These are set as module-level variables for backward compatibility
COLOR_USER = ""
COLOR_BOT = ""
COLOR_TOOL_NAME = ""
COLOR_TOOL_RESULT = ""
COLOR_METRICS = ""
COLOR_SYSTEM = ""
COLOR_ERROR = ""
COLOR_RESET = ""
COLOR_BOLD = ""
COLOR_DIM = ""
# Legacy colors for compatibility
COLOR_ASSISTANT = ""
COLOR_TOOL_REQUEST = ""


def _init_colors(color_mode: str = "auto"):
    """Initialize color constants based on terminal capabilities.

    Args:
        color_mode: Color mode - 'auto', 'always', or 'never'
    """
    global COLOR_USER, COLOR_BOT, COLOR_TOOL_NAME, COLOR_TOOL_RESULT
    global COLOR_METRICS, COLOR_SYSTEM, COLOR_ERROR, COLOR_RESET
    global COLOR_BOLD, COLOR_DIM, COLOR_ASSISTANT, COLOR_TOOL_REQUEST

    scheme = create_color_scheme(force=color_mode if color_mode != "auto" else None)

    COLOR_USER = scheme.USER
    COLOR_BOT = scheme.BOT
    COLOR_TOOL_NAME = scheme.TOOL_NAME
    COLOR_TOOL_RESULT = scheme.TOOL_RESULT
    COLOR_METRICS = scheme.METRICS
    COLOR_SYSTEM = scheme.SYSTEM
    COLOR_ERROR = scheme.ERROR
    COLOR_RESET = scheme.RESET
    COLOR_BOLD = scheme.BOLD
    COLOR_DIM = scheme.DIM
    COLOR_ASSISTANT = scheme.ASSISTANT
    COLOR_TOOL_REQUEST = scheme.TOOL_REQUEST


# Initialize colors with auto-detection by default
_init_colors("auto")


def create_auto_stash() -> str:
    """Create an automatic git stash with AI-generated message based on current diff.

    This creates a checkpoint without hiding your changes - the stash is immediately
    reapplied so you can continue working normally.
    """
    import subprocess

    from bots.foundation.base import Engines

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

        # Immediately reapply the stash to keep working directory unchanged
        # This makes it a "quicksave" rather than "put away"
        apply_result = subprocess.run(
            ["git", "stash", "apply"],
            capture_output=True,
            text=True,
            timeout=10,
        )
        if apply_result.returncode != 0:
            return f"Stash created but failed to reapply: {apply_result.stderr}"

        return f"Auto-stash created: {stash_message}"
    except subprocess.TimeoutExpired:
        return "Git command timed out"
    except Exception as e:
        return f"Error in auto-stash: {str(e)}"


class DynamicParameterCollector:
    """Dynamically collect parameters for functional prompts based on their signatures."""

    def __init__(self, function_filter: Optional[Callable[[str, Callable], bool]] = None):
        self.param_handlers = {
            "prompt_list": self._collect_prompts,
            "prompts": self._collect_prompts,
            "prompt": self._collect_single_prompt,
            "first_prompt": self._collect_single_prompt,
            "stop_condition": self._collect_condition,
            "continue_prompt": self._collect_continue_prompt,
            "recombinator_function": self._collect_recombinator,
            "should_branch": self._collect_boolean,
            "skip": self._collect_skip_labels,
            "items": self._collect_items,
            "dynamic_prompt": self._collect_dynamic_prompt,
            "functional_prompt": self._collect_functional_prompt,
        }
        self.conditions = {
            "1": ("tool_used", fp.conditions.tool_used),
            "2": ("tool_not_used", fp.conditions.tool_not_used),
            "3": ("said_DONE", fp.conditions.said_DONE),
            "4": ("said_READY", fp.conditions.said_READY),
            "5": ("error_in_response", fp.conditions.error_in_response),
        }
        self.function_filter = function_filter

    def _format_default_value(self, default: Any) -> str:
        """Format default values for clean display to users."""
        if default == inspect.Parameter.empty:
            return "required"
        elif callable(default):
            if hasattr(default, "__name__"):
                return f"function: {default.__name__}"
            else:
                return "function"
        elif isinstance(default, str):
            return f"'{default}'"
        elif isinstance(default, bool):
            return str(default)
        elif isinstance(default, (int, float)):
            return str(default)
        elif isinstance(default, list):
            if not default:
                return "empty list"
            elif len(default) <= 3:
                return f"[{', '.join(repr(item) for item in default)}]"
            else:
                return f"[{', '.join(repr(item) for item in default[:2])}, ... ({len(default)} items)]"
        elif default is None:
            return "None"
        else:
            str_repr = str(default)
            if len(str_repr) > 50:
                return f"{str_repr[:47]}..."
            return str_repr

    def collect_parameters(self, func: Callable) -> Optional[Dict[str, Any]]:
        """Dynamically collect parameters based on function signature."""
        try:
            sig = inspect.signature(func)
            params = {}
            print(f"\nCollecting parameters for {func.__name__}:")
            needs_single_callback = func.__name__ in ["tree_of_thought"]
            for param_name, param in sig.parameters.items():
                if param_name == "bot":
                    continue
                if param_name == "callback":
                    continue
                default_display = self._format_default_value(param.default)
                print(f"  Parameter: {param_name} (default: {default_display})")
                if param_name in self.param_handlers:
                    handler = self.param_handlers[param_name]
                    value = handler(param_name, param.default)
                else:
                    value = self._collect_generic_parameter(param_name, param.default)
                if value is None:
                    if param.default == inspect.Parameter.empty:
                        print(f"Required parameter '{param_name}' not provided")
                        return None
                elif value is not None:
                    params[param_name] = value
            params["_callback_type"] = "single" if needs_single_callback else "list"
            return params
        except Exception as e:
            print(f"Error collecting parameters: {e}")
            return None

    def _collect_prompts(self, param_name: str, default: Any) -> Optional[List[str]]:
        """Collect a list of prompts from user."""
        prompts = []
        print(f"\nEnter {param_name} (empty line to finish, ESC to cancel):")
        while True:
            try:
                prompt = input_with_esc(f"Prompt {len(prompts) + 1}: ").strip()
            except EscapeException:
                print("Cancelled")
                return None
            if not prompt:
                break
            prompts.append(prompt)
        if not prompts:
            print("No prompts entered")
            return None
        return prompts

    def _collect_single_prompt(self, param_name: str, default: Any) -> Optional[str]:
        """Collect a single prompt from user."""
        try:
            prompt = input_with_esc(f"Enter {param_name}: ").strip()
        except EscapeException:
            print("Cancelled")
            return None
        return prompt if prompt else None

    def _collect_condition(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect stop condition from user."""
        print(f"\nAvailable stop conditions for {param_name}:")
        for key, (name, _) in self.conditions.items():
            print(f"  {key}. {name}")
        default_display = self._format_default_value(default)
        try:
            choice = input_with_esc(f"Select condition (default: {default_display}): ").strip()
        except EscapeException:
            print("Cancelled")
            return None
        if not choice and default != inspect.Parameter.empty:
            return default
        elif choice in self.conditions:
            return self.conditions[choice][1]
        else:
            print("Invalid condition selection")
            return None

    def _collect_continue_prompt(self, param_name: str, default: Any) -> Optional[str]:
        """Collect continue prompt with default handling."""
        default_display = self._format_default_value(default)
        try:
            if default != inspect.Parameter.empty:
                prompt = input_with_esc(f"Enter {param_name} (default: {default_display}): ").strip()
                return prompt if prompt else default
            else:
                prompt = input_with_esc(f"Enter {param_name}: ").strip()
                return prompt if prompt else None
        except EscapeException:
            print("Cancelled")
            return None

    def _collect_boolean(self, param_name: str, default: Any) -> Optional[bool]:
        """Collect boolean parameter."""
        default_display = self._format_default_value(default)
        try:
            choice = input_with_esc(f"Enter {param_name} (y/n, default: {default_display}): ").strip().lower()
        except EscapeException:
            print("Cancelled")
            return None
        if not choice and default != inspect.Parameter.empty:
            return default
        elif choice in ["y", "yes", "true", "1"]:
            return True
        elif choice in ["n", "no", "false", "0"]:
            return False
        else:
            return default if default != inspect.Parameter.empty else False

    def _collect_skip_labels(self, param_name: str, default: Any) -> List[str]:
        """Collect skip labels for broadcast functions."""
        try:
            skip_input = input_with_esc(f"Enter {param_name} (comma-separated, or empty for none): ").strip()
        except EscapeException:
            print("Cancelled")
            return []
        if skip_input:
            return [label.strip() for label in skip_input.split(",")]
        else:
            return []

    def _collect_recombinator(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect recombinator function with available options."""
        print(f"\nAvailable recombinators for {param_name}:")
        recombinator_options = {
            "1": ("concatenate", recombinators.recombinators.concatenate),
            "2": ("llm_judge", recombinators.recombinators.llm_judge),
            "3": ("llm_vote", recombinators.recombinators.llm_vote),
            "4": ("llm_merge", recombinators.recombinators.llm_merge),
        }
        for key, (name, _) in recombinator_options.items():
            print(f"  {key}. {name}")
        default_display = self._format_default_value(default)
        try:
            choice = input_with_esc(f"Select recombinator (default: {default_display}): ").strip()
        except EscapeException:
            print("Cancelled")
            return None
        if not choice and default != inspect.Parameter.empty:
            return default
        elif choice in recombinator_options:
            return recombinator_options[choice][1]
        else:
            print("Invalid recombinator selection, using concatenate")
            return recombinators.recombinators.concatenate

    def _collect_items(self, param_name: str, default: Any) -> Optional[List[Any]]:
        """Collect items for prompt_for function - DESCOPED."""
        print(f"{param_name} is not supported in CLI interface")
        return None

    def _collect_dynamic_prompt(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect dynamic prompt function - DESCOPED."""
        print(f"{param_name} is not supported in CLI interface")
        return None

    def _collect_functional_prompt(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect functional prompt function for broadcast_fp."""
        print(f"\nAvailable functional prompts for {param_name}:")
        fp_options = {
            "1": ("single_prompt", fp.single_prompt),
            "2": ("chain", fp.chain),
            "3": ("branch", fp.branch),
            "4": ("tree_of_thought", fp.tree_of_thought),
            "5": ("prompt_while", fp.prompt_while),
            "6": ("chain_while", fp.chain_while),
            "7": ("branch_while", fp.branch_while),
            "8": ("par_branch", fp.par_branch),
            "9": ("par_branch_while", fp.par_branch_while),
        }
        for key, (name, _) in fp_options.items():
            print(f"  {key}. {name}")
        try:
            choice = input_with_esc("Select functional prompt: ").strip()
        except EscapeException:
            print("Cancelled")
            return None
        if choice in fp_options:
            return fp_options[choice][1]
        else:
            print("Invalid functional prompt selection, using single_prompt")
            return fp.single_prompt

    def _collect_generic_parameter(self, param_name: str, default: Any) -> Optional[Any]:
        """Generic parameter collection for unknown parameter types."""
        default_display = self._format_default_value(default)
        try:
            if default != inspect.Parameter.empty:
                value = input_with_esc(f"Enter {param_name} (default: {default_display}): ").strip()
                return value if value else default
            else:
                value = input_with_esc(f"Enter {param_name}: ").strip()
                return value if value else None
        except EscapeException:
            print("Cancelled")
            return None


class CLIConfig:
    """Configuration management for CLI settings."""

    def __init__(self):
        self.verbose = True
        self.width = 160
        self.indent = 4
        self.auto_stash = False
        self.remove_context_threshold = 999999  # Off by default (very large number)
        self.auto_mode_neutral_prompt = "ok"
        self.auto_mode_reduce_context_prompt = "trim useless context"
        self.max_tokens = 64000  # Maximum for Claude 4.5 Sonnet
        self.temperature = 0.3
        self.auto_backup = True  # Enable backups by default
        self.auto_restore_on_error = True  # Enable restore on error by default
        self.color = "auto"  # Color mode: 'auto', 'always', 'never'
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
                    self.remove_context_threshold = config_data.get("remove_context_threshold", 999999)
                    self.auto_mode_neutral_prompt = config_data.get("auto_mode_neutral_prompt", "ok")
                    self.auto_mode_reduce_context_prompt = config_data.get(
                        "auto_mode_reduce_context_prompt", "trim useless context"
                    )
                    self.max_tokens = config_data.get("max_tokens", 64000)
                    self.temperature = config_data.get("temperature", 0.3)
                    self.auto_backup = config_data.get("auto_backup", True)
                    self.auto_restore_on_error = config_data.get("auto_restore_on_error", True)
                    self.color = config_data.get("color", "auto")
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
                "auto_mode_reduce_context_prompt": self.auto_mode_reduce_context_prompt,
                "max_tokens": self.max_tokens,
                "temperature": self.temperature,
                "auto_backup": self.auto_backup,
                "auto_restore_on_error": self.auto_restore_on_error,
                "color": self.color,
            }
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            pass  # Fail silently if config saving fails


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
            """Callback function that displays only the last bot response message.

            Processes bot responses and displays the most recent non-empty response
            using pretty formatting with the bot's name.

            Args:
                responses: List of bot response messages, may contain empty values.
                nodes: Node objects associated with the responses (unused in this function).
            """
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
            """Callback function that displays bot metrics after processing responses.

            This callback is designed for verbose output mode where bot responses and tools
            are already shown in real-time. It only displays performance metrics at the end
            of processing if a bot instance is available in the context.

            Args:
                responses: The responses generated during processing.
                nodes: The nodes involved in the processing workflow.
            """
            if hasattr(self.context, "bot_instance") and self.context.bot_instance:
                bot = self.context.bot_instance
                display_metrics(self.context, bot)

        return verbose_callback

    def create_quiet_callback(self):
        """Create a callback that shows only user and bot messages (no tools, no metrics)."""

        def quiet_callback(responses, nodes):
            # In quiet mode, RealTimeDisplayCallbacks still shows the bot response
            # but we don't show tools or metrics
            """Callback function for quiet mode operation that suppresses tool and metrics display.

            In quiet mode, only bot responses are shown through RealTimeDisplayCallbacks
            while tool outputs and performance metrics are hidden.

            Args:
                responses: The response data from the system.
                nodes: The node data associated with the responses.
            """

        return quiet_callback

    def get_standard_callback(self):
        """Get the standard callback based on current config settings."""
        if self.context.config.verbose:
            return self.create_verbose_callback()
        else:
            return self.create_quiet_callback()


class CLIContext:
    """Shared context for CLI operations."""

    def __init__(self):
        self.config = CLIConfig()
        self.labeled_nodes: Dict[str, ConversationNode] = {}
        self.conversation_backup: Optional[ConversationNode] = None
        self.old_terminal_settings = None
        self.bot_instance = None
        self.cached_leaves: List[ConversationNode] = []
        self.callbacks = CLICallbacks(self)
        # Track session start time for cumulative metrics
        self.session_start_time = time.time()
        # Track context reduction cooldown (counts down from 3 after each trigger)
        # Starts at 0 so first time tokens exceed threshold, it triggers immediately
        self.context_reduction_cooldown = 0
        # Track last message metrics (captured once per message, used by both display and auto)
        self.last_message_metrics = None
        # Bot backup system - stores complete bot copies
        self.bot_backup: Optional[Bot] = None
        self.backup_metadata: Dict[str, Any] = {}
        self.backup_in_progress: bool = False

    def create_backup(self, reason: str = "manual") -> bool:
        """Create a complete backup of the current bot.

        Args:
            reason: Description of why backup was created (e.g., "before_user_message")

        Returns:
            True if backup successful, False otherwise
        """
        if self.bot_instance is None:
            return False

        if self.backup_in_progress:
            return False  # Prevent concurrent backups

        try:
            self.backup_in_progress = True

            # Safety check: Don't try to backup mock objects (used in tests)
            # Mock objects can cause infinite recursion when copied
            bot_type = type(self.bot_instance).__name__
            if "Mock" in bot_type:
                # Silently skip backup for mock objects
                return False

            # Use bot's built-in copy mechanism (bot * 1) which properly handles
            # callbacks, api_key, and other bot-specific concerns
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
            # Use bot's built-in copy mechanism to create a fresh copy from backup
            restored_bot = (self.bot_backup * 1)[0]

            # Assign the restored copy to the live instance
            self.bot_instance = restored_bot

            # Re-attach callbacks on the restored instance (pointing to current context)
            self.bot_instance.callbacks = RealTimeDisplayCallbacks(self)

            # Make the restored bot interruptible with Ctrl-C
            from bots.dev.bot_session import make_bot_interruptible

            make_bot_interruptible(self.bot_instance)

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


class PromptManager:
    """Manager for saving, loading, and editing prompts with recency tracking."""

    def __init__(self, prompts_file: str = "bots/prompts.json"):
        self.prompts_file = Path(prompts_file)
        self.prompts_data = self._load_prompts()

    def _load_prompts(self) -> Dict[str, Any]:
        """Load prompts from file or create empty structure."""
        if self.prompts_file.exists():
            try:
                with open(self.prompts_file, "r", encoding="utf-8") as f:
                    return json.load(f)
            except (json.JSONDecodeError, IOError):
                pass
        return {"recents": [], "prompts": {}}

    def _save_prompts(self):
        """Save prompts to file."""
        try:
            # Ensure directory exists
            self.prompts_file.parent.mkdir(parents=True, exist_ok=True)
            with open(self.prompts_file, "w", encoding="utf-8") as f:
                json.dump(self.prompts_data, f, indent=2, ensure_ascii=False)
        except IOError as e:
            raise Exception(f"Failed to save prompts: {e}")

    def _update_recents(self, prompt_name: str):
        """Update recency list, moving prompt to front."""
        recents = self.prompts_data["recents"]
        if prompt_name in recents:
            recents.remove(prompt_name)
        recents.insert(0, prompt_name)
        # Keep only first 5
        self.prompts_data["recents"] = recents[:5]

    def _generate_prompt_name(self, prompt_text: str) -> str:
        """Generate a name for the prompt using Claude Haiku."""
        try:
            from bots.foundation.anthropic_bots import AnthropicBot
            from bots.foundation.base import Engines

            # Create a quick Haiku bot for naming
            naming_bot = AnthropicBot(model_engine=Engines.CLAUDE3_HAIKU, max_tokens=100)

            # Truncate prompt if too long for naming
            truncated_prompt = prompt_text[:500] + "..." if len(prompt_text) > 500 else prompt_text

            naming_prompt = f"""Generate a short, descriptive name (2-4 words, snake_case) for this prompt:

{truncated_prompt}

Respond with just the name, no explanation."""

            response = naming_bot.respond(naming_prompt)
            # Clean up the response - extract just the name
            name = response.strip().lower()
            # Remove any non-alphanumeric characters except underscores
            name = re.sub(r"[^a-z0-9_]", "", name)
            # Ensure it's not empty
            if not name:
                name = "unnamed_prompt"
            return name

        except Exception:
            # Fallback to timestamp-based name
            return f"prompt_{int(time.time())}"

    def search_prompts(self, query: str) -> List[tuple]:
        """Search prompts by name and content. Returns list of (name, content) tuples."""
        if not query:
            # Return recents if no query
            results = []
            for name in self.prompts_data["recents"]:
                if name in self.prompts_data["prompts"]:
                    results.append((name, self.prompts_data["prompts"][name]))
            return results

        query_lower = query.lower()
        results = []

        for name, content in self.prompts_data["prompts"].items():
            # Search in name and content
            if query_lower in name.lower() or query_lower in content.lower():
                results.append((name, content))

        return results

    def save_prompt(self, prompt_text: str, name: str | None = None) -> str:
        """Save a prompt with optional name. If no name, generate one."""
        if not name:
            name = self._generate_prompt_name(prompt_text)

        # Ensure unique name
        original_name = name
        counter = 1
        while name in self.prompts_data["prompts"]:
            name = f"{original_name}_{counter}"
            counter += 1

        self.prompts_data["prompts"][name] = prompt_text
        self._update_recents(name)
        self._save_prompts()
        return name

    def load_prompt(self, name: str) -> str:
        """Load a prompt by name and update recency."""
        if name not in self.prompts_data["prompts"]:
            raise KeyError(f"Prompt '{name}' not found")

        self._update_recents(name)
        self._save_prompts()
        return self.prompts_data["prompts"][name]

    def get_prompt_names(self) -> List[str]:
        """Get all prompt names."""
        return list(self.prompts_data["prompts"].keys())

    def delete_prompt(self, name: str) -> bool:
        """Delete a prompt by name. Returns True if deleted, False if not found."""
        if name not in self.prompts_data["prompts"]:
            return False

        # Remove from prompts
        del self.prompts_data["prompts"][name]

        # Remove from recents if present
        if name in self.prompts_data["recents"]:
            self.prompts_data["recents"].remove(name)

        self._save_prompts()
        return True

    def get_recents(self) -> List[tuple]:
        """Get recent prompts as list of (name, content) tuples."""
        results = []
        for name in self.prompts_data["recents"]:
            if name in self.prompts_data["prompts"]:
                results.append((name, self.prompts_data["prompts"][name]))
        return results


class ConversationHandler:
    """Handler for conversation navigation commands."""

    def up(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Move up in conversation tree."""
        if bot.conversation.parent and bot.conversation.parent.parent:
            context.conversation_backup = bot.conversation
            original_position = bot.conversation
            bot.conversation = bot.conversation.parent.parent
            if not self._ensure_assistant_node(bot):
                return {
                    "type": "system",
                    "content": (
                        "Warning: Ended up on user node with no assistant response. Bumped to previous assistant node."
                    ),
                }

            # Don't call _ensure_valid_conversation_position here!
            # It can move us forward again, defeating the purpose of /up
            # The user explicitly wants to navigate backward, even if it means
            # landing on an assistant node with tool_calls (which is valid for viewing)

            # However, if we ended up at the exact same position, something went wrong
            if bot.conversation == original_position:
                return {"type": "system", "content": "Unable to move up - already at earliest accessible position"}

            # Return conversation content as message
            if bot.conversation.content:
                return {"type": "message", "role": "assistant", "content": bot.conversation.content}
            return {"type": "system", "content": "Moved up conversation tree"}
        return {"type": "system", "content": "At root - can't go up"}

    def down(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Move down in conversation tree."""
        if bot.conversation.replies:
            context.conversation_backup = bot.conversation
            if len(bot.conversation.replies) > 1:
                # Multiple replies - need to choose
                if args and args[0].isdigit():
                    index = int(args[0])
                    if 0 <= index < len(bot.conversation.replies):
                        bot.conversation = bot.conversation.replies[index]
                    else:
                        return {"type": "system", "content": f"Invalid index. Choose 0-{len(bot.conversation.replies)-1}"}
                else:
                    # Show options
                    options = "\n".join(
                        [f"{i}: {reply.content[:50]}..." for i, reply in enumerate(bot.conversation.replies) if reply.content]
                    )
                    return {"type": "system", "content": f"Multiple replies. Use /down <index>:\n{options}"}
            else:
                bot.conversation = bot.conversation.replies[0]
            if not self._ensure_assistant_node(bot):
                return {"type": "system", "content": "Warning: Ended up on user node with no assistant response"}

            # Don't call _ensure_valid_conversation_position here!
            # Users explicitly navigating want to VIEW messages at these positions
            # The pending_results mechanism handles tool context when sending new messages

            # Return conversation content as message
            if bot.conversation.content:
                return {"type": "message", "role": "assistant", "content": bot.conversation.content}
            return {"type": "system", "content": "Moved down conversation tree"}

        # Check if we need to move through tool result nodes
        if bot.conversation.role == "assistant" and bot.conversation.tool_calls:
            # Look for user node with tool_results
            next_node = None
            for reply in bot.conversation.replies:
                if reply.role == "user" and reply.tool_results:
                    next_node = reply
                    break
            if next_node:
                context.conversation_backup = bot.conversation
                # Move to assistant after tool results if available
                if next_node.replies:
                    bot.conversation = next_node.replies[0]
                else:
                    bot.conversation = next_node
                if not self._ensure_assistant_node(bot):
                    return {"type": "system", "content": "Warning: Ended up on user node with no assistant response"}

                # Don't call _ensure_valid_conversation_position here!
                # Users explicitly navigating want to VIEW messages at these positions

                # Return conversation content as message
                if bot.conversation.content:
                    return {"type": "message", "role": "assistant", "content": bot.conversation.content}
                return {"type": "system", "content": "Moved down conversation tree"}
        return {"type": "system", "content": "At leaf - can't go down"}

    def left(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Move left to sibling in conversation tree."""
        if not bot.conversation.parent:
            return {"type": "system", "content": "At root - can't go left"}
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return {"type": "system", "content": "Conversation has no siblings at this point"}
        current_index = next((i for i, reply in enumerate(replies) if reply is bot.conversation))
        next_index = (current_index - 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        if not self._ensure_assistant_node(bot):
            return {"type": "system", "content": "Warning: Ended up on user node with no assistant response"}

        # Don't call _ensure_valid_conversation_position here!
        # Users explicitly navigating want to VIEW messages at these positions
        # The pending_results mechanism handles tool context when sending new messages

        # Return conversation content as message
        if bot.conversation.content:
            return {"type": "message", "role": "assistant", "content": bot.conversation.content}
        return {"type": "system", "content": "Moved left in conversation tree"}

    def right(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Move right to sibling in conversation tree."""
        if not bot.conversation.parent:
            return {"type": "system", "content": "At root - can't go right"}
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return {"type": "system", "content": "Conversation has no siblings at this point"}
        current_index = next((i for i, reply in enumerate(replies) if reply is bot.conversation))
        next_index = (current_index + 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        if not self._ensure_assistant_node(bot):
            return {"type": "system", "content": "Warning: Ended up on user node with no assistant response"}

        # Don't call _ensure_valid_conversation_position here!
        # Users explicitly navigating want to VIEW messages at these positions
        # The pending_results mechanism handles tool context when sending new messages

        # Return conversation content as message
        if bot.conversation.content:
            return {"type": "message", "role": "assistant", "content": bot.conversation.content}
        return {"type": "system", "content": "Moved right in conversation tree"}

    def root(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Move to root of conversation tree."""
        context.conversation_backup = bot.conversation
        while bot.conversation.parent:
            bot.conversation = bot.conversation.parent
        if not self._ensure_assistant_node(bot):
            return {"type": "system", "content": "Warning: Ended up on user node with no assistant response"}

        # Don't call _ensure_valid_conversation_position here!
        # Users explicitly navigating want to VIEW messages at these positions
        # The pending_results mechanism handles tool context when sending new messages

        # Return conversation content as message
        if bot.conversation.content:
            return {"type": "message", "role": "assistant", "content": bot.conversation.content}
        return {"type": "system", "content": "Moved to root of conversation tree"}

    def lastfork(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move to the previous node (going up the tree) that has multiple replies."""
        current = bot.conversation

        # Traverse up the tree looking for a fork
        while current.parent:
            current = current.parent
            # Check if this node has multiple replies (is a fork)
            if len(current.replies) > 1:
                context.conversation_backup = bot.conversation
                bot.conversation = current
                if not self._ensure_assistant_node(bot):
                    return "Warning: Moved to fork but ended up on user node with no assistant response"
                self._display_conversation_context(bot, context)
                return f"Moved to previous fork ({len(current.replies)} branches)"

        return "No fork found going up the tree"

    def nextfork(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move to the next node (going down the tree) that has multiple replies."""
        # Use BFS to search down the tree for the first fork
        from collections import deque

        queue = deque([bot.conversation])
        visited = {bot.conversation}

        while queue:
            current = queue.popleft()

            # Check all replies of the current node
            for reply in current.replies:
                if reply not in visited:
                    visited.add(reply)

                    # Check if this reply has multiple replies (is a fork)
                    if len(reply.replies) > 1:
                        context.conversation_backup = bot.conversation
                        bot.conversation = reply
                        if not self._ensure_assistant_node(bot):
                            return "Warning: Moved to fork but ended up on user node with no assistant response"
                        self._display_conversation_context(bot, context)
                        return f"Moved to next fork ({len(reply.replies)} branches)"

                    # Add to queue to continue searching
                    queue.append(reply)

        return "No fork found going down the tree"

    def label(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Show all labels and create new label or jump to existing one."""
        # If no args provided, show all labels
        if not args:
            if hasattr(context, "labeled_nodes") and context.labeled_nodes:
                result = "Existing labels:\n"
                for label_name, node in context.labeled_nodes.items():
                    content_preview = node.content[:100] + "..." if len(node.content) > 100 else node.content
                    result += f"  '{label_name}': {content_preview}\n"
                result += "\nUse /label <name> to create a new label or jump to an existing one"
                return {"type": "system", "content": result}
            else:
                msg = "No labels saved yet.\n\n" "Use /label <name> to create a label at the current position"
                return {"type": "system", "content": msg}

        # Args provided - use as label name
        label = args[0].strip()

        if not label:
            return {"type": "system", "content": "No label entered"}

        # Check if label already exists
        if hasattr(context, "labeled_nodes") and label in context.labeled_nodes:
            # Jump to existing label
            context.conversation_backup = bot.conversation
            bot.conversation = context.labeled_nodes[label]
            if not self._ensure_assistant_node(bot):
                warning_msg = (
                    f"Warning: Moved to node labeled '{label}' but ended up on " "user node with no assistant response"
                )
                return {"type": "system", "content": warning_msg}

            # Return conversation content as message
            if bot.conversation.content:
                return {"type": "message", "role": "assistant", "content": bot.conversation.content}
            return {"type": "system", "content": f"Jumped to existing label: {label}"}
        else:
            # Create new label
            if not hasattr(context, "labeled_nodes"):
                context.labeled_nodes = {}
            context.labeled_nodes[label] = bot.conversation
            if not hasattr(bot.conversation, "labels"):
                bot.conversation.labels = []
            if label not in bot.conversation.labels:
                bot.conversation.labels.append(label)
            return {"type": "system", "content": f"Created new label: {label}"}

    # showlabels method removed - functionality merged into label method
    def leaf(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Show all leaf nodes and optionally jump to one by number."""
        leaves = self._find_leaves(bot.conversation)
        if not leaves:
            return {"type": "system", "content": "No leaves found from current node"}

        context.cached_leaves = leaves

        if args:
            try:
                leaf_index = int(args[0]) - 1  # Convert to 0-based index
                if leaf_index < 0 or leaf_index >= len(leaves):
                    return {
                        "type": "error",
                        "content": f"Invalid leaf number. Must be between 1 and {len(leaves)}",
                    }
                context.conversation_backup = bot.conversation
                bot.conversation = leaves[leaf_index]
                if not self._ensure_assistant_node(bot):
                    return {
                        "type": "system",
                        "content": (
                            (
                                f"Warning: Jumped to leaf {leaf_index + 1} but ended up on "
                                "user node with no assistant response"
                            )
                        ),
                    }

                # Return conversation content as message
                if bot.conversation.content:
                    return {"type": "message", "role": "assistant", "content": bot.conversation.content}
                content_preview = self._get_leaf_preview(leaves[leaf_index])
                return {"type": "system", "content": f"Jumped to leaf {leaf_index + 1}: {content_preview}"}
            except ValueError:
                return {"type": "error", "content": "Invalid leaf number. Must be a number."}

        # No args - return list of leaves
        result = "Found {} leaf nodes:\n".format(len(leaves))
        for i, leaf in enumerate(leaves):
            content_preview = self._get_leaf_preview(leaf)
            depth = self._calculate_depth(bot.conversation, leaf)
            labels = getattr(leaf, "labels", [])
            label_str = " (labels: {})".format(", ".join(labels)) if labels else ""
            result += "  {}. [depth {}]{}: {}\n".format(i + 1, depth, label_str, content_preview)
        result += "\nUse /leaf <number> to jump to a specific leaf"

        return {"type": "system", "content": result}

    def _get_leaf_preview(self, leaf: ConversationNode, max_length: int = 300) -> str:
        """Get a preview of leaf content, cutting from middle if too long."""
        content = leaf.content.strip()
        if len(content) <= max_length:
            return content
        half_length = (max_length - 5) // 2  # Account for " ... "
        start = content[:half_length].strip()
        end = content[-half_length:].strip()
        return f"{start} ... {end}"

    def combine_leaves(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Combine all leaves below current node using a recombinator function."""
        leaves = self._find_leaves(bot.conversation)
        if not leaves:
            return {"type": "system", "content": "No leaves found from current node"}
        if len(leaves) < 2:
            return {"type": "system", "content": "Need at least 2 leaves to combine"}

        # If args provided, use that as recombinator choice
        recombinator_options = {
            "1": ("concatenate", recombinators.recombinators.concatenate),
            "2": ("llm_judge", recombinators.recombinators.llm_judge),
            "3": ("llm_vote", recombinators.recombinators.llm_vote),
            "4": ("llm_merge", recombinators.recombinators.llm_merge),
            "concatenate": ("concatenate", recombinators.recombinators.concatenate),
            "llm_judge": ("llm_judge", recombinators.recombinators.llm_judge),
            "llm_vote": ("llm_vote", recombinators.recombinators.llm_vote),
            "llm_merge": ("llm_merge", recombinators.recombinators.llm_merge),
        }

        if args:
            choice = args[0].strip()
            if choice not in recombinator_options:
                return {"type": "error", "content": "Invalid recombinator selection"}
            recombinator_func = recombinator_options[choice][1]
        else:
            # No args - return list of options
            result = "Found {} leaves to combine.\nAvailable recombinators:\n".format(len(leaves))
            result += "  1. concatenate\n"
            result += "  2. llm_judge\n"
            result += "  3. llm_vote\n"
            result += "  4. llm_merge\n"
            result += "\nUse /combine_leaves <number or name> to combine"
            return {"type": "system", "content": result}

        try:
            responses = [leaf.content for leaf in leaves]
            context.conversation_backup = bot.conversation
            final_response, final_node = fp.recombine(bot, responses, leaves, recombinator_func)

            # Return the combined result as a message
            return {"type": "message", "role": "assistant", "content": final_response}
        except Exception as e:
            return {"type": "error", "content": "Error combining leaves: {}".format(str(e))}

    def _find_leaves(self, node: ConversationNode) -> List[ConversationNode]:
        """Recursively find all leaf nodes from a given node."""
        return _find_leaves_util(node)

    def _calculate_depth(self, start_node: ConversationNode, target_node: ConversationNode) -> int:
        """Calculate the depth/distance from start_node to target_node."""

        def find_path_length(current, target, depth=0):
            """Find the depth of a target node in a tree structure using depth-first search.

            Recursively traverses a tree starting from the current node to locate the target
            node and returns the depth at which it is found.

            Args:
                current: The current node being examined in the traversal.
                target: The target node to search for.
                depth (int): The current depth level in the tree traversal.

            Returns:
                int or None: The depth of the target node if found, None otherwise.
            """
            if current is target:
                return depth
            for reply in current.replies:
                result = find_path_length(reply, target, depth + 1)
                if result is not None:
                    return result
            return None

        depth = find_path_length(start_node, target_node)
        return depth if depth is not None else 0

    def _ensure_assistant_node(self, bot: Bot) -> bool:
        """Ensure we're on an assistant node, move to one if needed."""
        if bot.conversation.role == "assistant":
            return True
        if bot.conversation.replies:
            for reply in bot.conversation.replies:
                if reply.role == "assistant":
                    bot.conversation = reply
                    return True
        return False

    def _ensure_valid_conversation_position(self, bot: Bot) -> bool:
        """Ensure bot.conversation is at a valid position for API calls.

        A valid position means:
        1. We're on an assistant node (already handled by _ensure_assistant_node)
        2. If the assistant node has tool_calls, we need to move forward to include
           the tool_results in the conversation history.

        This prevents issue #206 where navigating to an assistant node with tool_calls
        causes API errors because tool_results are in a child node and not included
        in _build_messages().

        Returns:
            bool: True if position was adjusted, False if no adjustment needed
        """
        # Check if current node is assistant with tool_calls
        if bot.conversation.role == "assistant" and bot.conversation.tool_calls:
            # Check if there's a user reply with tool_results
            if bot.conversation.replies:
                for reply in bot.conversation.replies:
                    if reply.role == "user" and reply.tool_results:
                        # Move forward to include the tool_results
                        # If this user node has assistant replies, move to the first one
                        if reply.replies:
                            for assistant_reply in reply.replies:
                                if assistant_reply.role == "assistant":
                                    bot.conversation = assistant_reply
                                    return True
                        # Otherwise stay at the user node (unusual but valid)
                        bot.conversation = reply
                        return True

        return False

    def _display_conversation_context(self, bot: Bot, context: CLIContext):
        """Display current conversation context."""
        if bot.conversation.content:
            pretty(
                bot.conversation.content,
                bot.name,
                context.config.width,
                context.config.indent,
                COLOR_ASSISTANT,
                newline_after_name=False,
            )


class StateHandler:
    """Handler for bot state management commands."""

    def save(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Save bot state."""
        try:
            try:
                filename = input_with_esc("Save filename (without extension): ").strip()
            except EscapeException:
                return {"type": "system", "message": "Save cancelled"}
            if not filename:
                return {"type": "system", "message": "Save cancelled - no filename provided"}
            if not filename.endswith(".bot"):
                filename = filename + ".bot"
            bot.save(filename)
            return {"type": "system", "message": f"Bot saved to {filename}"}
        except Exception as e:
            return {"type": "error", "message": f"Error saving bot: {str(e)}"}

    def load(self, bot: Bot, context: CLIContext, args: List[str]) -> dict:
        """Load bot state."""
        try:
            # Display all .bot files in current directory
            import glob

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
                return {"type": "system", "message": "Load cancelled"}
            if not filename:
                return {"type": "system", "message": "Load cancelled - no filename provided"}

            # Check if input is a number referring to the list
            if filename.isdigit() and bot_files:
                file_index = int(filename) - 1
                if 0 <= file_index < len(bot_files):
                    filename = bot_files[file_index]
                else:
                    msg = f"Invalid selection. Must be between 1 and {len(bot_files)}"
                    return {"type": "error", "message": msg}

            return self._load_bot_from_file(filename, context)
        except Exception as e:
            return {"type": "error", "message": f"Error loading bot: {str(e)}"}

    def _load_bot_from_file(self, filename: str, context: CLIContext) -> dict:
        """Load bot from file and update context. Used by both interactive load and CLI args."""
        try:
            if not os.path.exists(filename):
                if not filename.endswith(".bot"):
                    filename_with_ext = filename + ".bot"
                    if os.path.exists(filename_with_ext):
                        filename = filename_with_ext
                    else:
                        return {"type": "error", "message": f"File not found: {filename}"}
                else:
                    return {"type": "error", "message": f"File not found: {filename}"}
            new_bot = Bot.load(filename)
            while new_bot.conversation.replies:
                new_bot.conversation = new_bot.conversation.replies[-1]

            # Attach CLI callbacks for proper display
            new_bot.callbacks = RealTimeDisplayCallbacks(context)

            # Make the bot interruptible with Ctrl-C
            from bots.dev.bot_session import make_bot_interruptible

            make_bot_interruptible(new_bot)

            context.bot_instance = new_bot
            context.labeled_nodes = {}
            self._rebuild_labels(new_bot.conversation, context)
            context.cached_leaves = []
            msg = f"Bot loaded from {filename}. Conversation restored to most recent message."
            return {"type": "system", "message": msg}
        except Exception as e:
            return {"type": "error", "message": f"Error loading bot: {str(e)}"}

    def _rebuild_labels(self, node: ConversationNode, context: CLIContext):
        """Recursively rebuild labeled nodes from conversation tree."""
        if hasattr(node, "labels"):
            for label in node.labels:
                context.labeled_nodes[label] = node
        for reply in node.replies:
            self._rebuild_labels(reply, context)


class SystemHandler:
    """Handler for system and configuration commands."""

    def help(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Display help information about available commands."""
        help_lines = [
            "Welcome to the Bot CLI!",
            "",
            "This is a command-line interface for interacting with an AI bot.",
            "It allows you to chat with the LLM, save and load bot states, and execute various commands.",
            "The bot has the ability to read and write files and can execute powershell and python code directly.",
            "The bot also has tools to help edit python files in an accurate and token-efficient way.",
            "",
            "Available commands:",
            "/help: Show this help message",
            "/clear: Clear the terminal screen (also works as bare 'clear')",
            "/verbose: Show tool requests and results (default on)",
            "/quiet: Hide tool requests and results",
            "/config: Show or modify configuration",
            "/auto_stash: Toggle auto git stash before user messages",
            "/load_stash: Load a previously saved auto-stash",
            "/save: Save the current bot (prompts for filename)",
            "/load: Load a previously saved bot (prompts for filename)",
            '/up: "rewind" the conversation by one turn by moving up the conversation tree',
            "/down: Move down the conversation tree (if there are multiple branches)",
            "/left: Move to the left sibling in the conversation tree",
            "/right: Move to the right sibling in the conversation tree",
            "/root: Jump to the root of the conversation tree",
            "/lastfork: Jump to the last fork point in the conversation",
            "/nextfork: Jump to the next fork point in the conversation",
            "/label <name>: Label the current conversation node for easy navigation",
            "/leaf: Show and navigate to conversation leaves (endpoints)",
            "/combine_leaves: Combine multiple conversation leaves",
            "/auto: Toggle auto mode",
            "/fp: Execute a functional prompt",
            "/broadcast_fp: Broadcast a functional prompt to all leaves",
            "/p: Load a saved prompt",
            "/s: Save the last user message as a reusable prompt",
            "/d: Delete a saved prompt",
            "/r: Show recent prompts",
            "/add_tool <file.py or module>: Add tools from a Python file or module",
            "/models: List available models",
            "/switch: Switch to a different model within the same provider",
            "/backup: Create a backup of the current bot state",
            "/restore: Restore from the most recent backup",
            "/backup_info: Show information about available backups",
            "/undo: Undo the last backup operation",
            "/exit: Exit the CLI",
            "",
            "You can also just type your message and press Enter to chat with the bot.",
            "The bot will respond and can use its tools to help you with various tasks.",
            "",
            "Tips:",
            "- Use /verbose to see what tools the bot is using",
            "- Use /save regularly to preserve your conversation",
            "- Use /label to mark important points in the conversation",
            "- Use /backup before trying something experimental",
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
                f"    color: {context.config.color}",
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
                elif setting == "color":
                    if value not in ("auto", "always", "never"):
                        return f"Invalid color mode: {value}. Use 'auto', 'always', or 'never'."
                    context.config.color = value
                    # Reinitialize colors with new setting
                    _init_colors(value)
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
            import bots.flows.functional_prompts as fp

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
                """Determines whether the bot should stop based on the absence of tool requests.

                Args:
                    bot (Bot): The bot instance to check for tool requests.

                Returns:
                    bool: True if the bot has no pending tool requests, False otherwise.
                """
                return not bot.tool_handler.requests

            # Track iteration count to know when we're past the first prompt
            iteration_count = [0]

            def auto_callback(responses, nodes):
                # Update cooldown after each iteration
                """Updates cooldown settings based on input token metrics from the last message.

                Checks if the input tokens from the last message exceed the configured threshold
                for context removal and adjusts cooldown accordingly.

                Args:
                    responses: Response data from previous operations.
                    nodes: Node objects being processed.
                """
                if context.last_message_metrics:
                    last_input_tokens = context.last_message_metrics.get("input_tokens", 0)
                    if (
                        last_input_tokens > context.config.remove_context_threshold
                        and context.context_reduction_cooldown <= 0  # noqa: E501
                    ):
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
                """Executes both auto callback and display callback functions in sequence.

                First runs the auto callback for logic processing, then conditionally runs
                the display callback if it exists.

                Args:
                    responses: Response data to be processed by the callbacks.
                    nodes: Node data to be processed by the callbacks.
                """
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
            responses, nodes = fp.prompt_while(
                bot,
                "ok",
                continue_prompt=continue_prompt,
                stop_condition=stop_on_no_tools,
                callback=combined_callback,
            )

            restore_terminal(old_settings)
            display_metrics(context, bot)

            # Return the final response if available
            # This fixes issue #231 - display final message instead of first
            if responses:
                return responses[-1]
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
        import subprocess

        if not args:
            return "Usage: /load_stash <stash_name_or_index>"

        stash_identifier = args[0]

        try:
            # First, get the list of stashes
            result = subprocess.run(["git", "stash", "list"], capture_output=True, text=True, check=True)
            stash_list = result.stdout.strip().split("\n") if result.stdout.strip() else []

            if not stash_list:
                return "No stashes found"

            # Try to find the stash by index or name pattern
            stash_to_apply = None

            # Check if it's a numeric index
            try:
                index = int(stash_identifier)
                if 0 <= index < len(stash_list):
                    stash_to_apply = f"stash@{{{index}}}"
            except ValueError:
                # Not a number, search by name pattern
                for i, stash_line in enumerate(stash_list):
                    if stash_identifier.lower() in stash_line.lower():
                        stash_to_apply = f"stash@{{{i}}}"
                        break

            if not stash_to_apply:
                return f"Stash '{stash_identifier}' not found"

            # Apply the stash
            subprocess.run(["git", "stash", "apply", stash_to_apply], check=True, capture_output=True)

            return f"Successfully applied {stash_to_apply}"

        except subprocess.CalledProcessError as e:
            return f"Git error: {e.stderr.decode() if e.stderr else str(e)}"
        except Exception as e:
            return f"Error loading stash: {str(e)}"

    def add_tool(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Add a tool to the bot from a Python file or module.

        Usage:
            /add_tool path/to/file.py
            /add_tool path/to/file.py::function_name
            /add_tool path/to/file1.py path/to/file2.py
        """
        if not args:
            return "Usage: /add_tool path/to/file.py [path/to/file.py::function_name ...]"

        import ast
        import importlib.util

        added_tools = []
        errors = []

        for arg in args:
            # Check if :: syntax is used for specific function
            if "::" in arg:
                filepath, func_name = arg.split("::", 1)

                # Validate function name is not empty
                if not func_name or func_name.strip() == "":
                    errors.append(f"Function name missing: {arg}")
                    continue

                # Validate file exists
                if not os.path.exists(filepath):
                    errors.append(f"File not found: {filepath}")
                    continue

                # Validate it's a Python file
                if not filepath.endswith(".py"):
                    errors.append(f"Not a Python file: {filepath}")
                    continue

                try:
                    # Load the module
                    spec = importlib.util.spec_from_file_location("temp_module", filepath)
                    if spec is None or spec.loader is None:
                        errors.append(f"Cannot load module from {filepath}")
                        continue

                    module = importlib.util.module_from_spec(spec)
                    spec.loader.exec_module(module)

                    # Get the specific function
                    if not hasattr(module, func_name):
                        errors.append(f"Function '{func_name}' not found in {filepath}")
                        continue

                    func = getattr(module, func_name)
                    if not callable(func):
                        errors.append(f"'{func_name}' in {filepath} is not callable")
                        continue

                    # Add the specific function
                    bot.add_tools(func)
                    added_tools.append(func_name)

                except SyntaxError as e:
                    errors.append(f"Syntax error in {filepath}: {e}")
                    continue
                except (FileNotFoundError, ModuleNotFoundError, TypeError, ModuleLoadError) as e:
                    errors.append(f"Error loading {filepath}: {e}")
                    continue

            else:
                # Whole file - validate before passing to bot.add_tools
                filepath = arg

                # Validate file exists
                if not os.path.exists(filepath):
                    errors.append(f"File not found: {filepath}")
                    continue

                # Validate it's a Python file
                if not filepath.endswith(".py"):
                    errors.append(f"Not a Python file: {filepath}")
                    continue

                # Check if file has any public functions
                try:
                    with open(filepath, "r", encoding="utf-8") as f:
                        tree = ast.parse(f.read())

                    public_funcs = [
                        node.name
                        for node in ast.walk(tree)
                        if isinstance(node, ast.FunctionDef) and not node.name.startswith("_")
                    ]

                    if not public_funcs:
                        errors.append(f"No public functions found in {filepath}")
                        continue

                except SyntaxError as e:
                    errors.append(f"Syntax error in {filepath}: {e}")
                    continue
                except (FileNotFoundError, ModuleNotFoundError, TypeError, ModuleLoadError) as e:
                    errors.append(f"Error loading {filepath}: {e}")
                    continue

                # Add all public functions from file
                try:
                    bot.add_tools(filepath)
                    added_tools.extend(public_funcs)
                except SyntaxError as e:
                    errors.append(f"Syntax error in {filepath}: {e}")
                    continue
                except (FileNotFoundError, ModuleNotFoundError, TypeError, ModuleLoadError) as e:
                    errors.append(f"Error loading {filepath}: {e}")
                    continue

        # Format response
        result_parts = []
        if added_tools:
            result_parts.append(f"Added tools: {', '.join(added_tools)}")
        if errors:
            result_parts.append("Errors:\n  " + "\n  ".join(errors))

        return "\n".join(result_parts) if result_parts else "No tools added"

    def models(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Display available models with metadata."""
        from bots.foundation.base import Engines

        output = []
        output.append("\n" + "=" * 100)
        output.append("Available Models")
        output.append("=" * 100)
        output.append(f"{'Model':<45} {'Provider':<12} {'Intelligence':<15} {'Max Tokens':<12} {'Cost ($/1M tokens)':<20}")
        output.append("-" * 100)

        for engine in Engines:
            info = engine.get_info()
            stars = "â­" * info["intelligence"]
            cost_str = f"${info['cost_input']:.2f} / ${info['cost_output']:.2f}"

            output.append(f"{engine.value:<45} {info['provider']:<12} {stars:<15} " f"{info['max_tokens']:<12} {cost_str:<20}")

        output.append("=" * 100)
        output.append("\nIntelligence: â­ = fast/cheap, â­â­ = balanced, â­â­â­ = most capable")
        output.append("Cost format: input / output per 1M tokens\n")

        return "\n".join(output)

    def switch(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Switch model engine."""
        from bots.foundation.base import Engines

        if not args:
            # Show available models from current provider only
            current_engine = bot.model_engine
            current_provider = current_engine.get_info()["provider"]

            # Filter engines by current provider
            provider_models = [e for e in Engines if e.get_info()["provider"] == current_provider]

            output = []
            output.append(f"\nCurrent model: {current_engine.value}\n")
            output.append(f"Available {current_provider} models:")
            output.append("-" * 80)

            for i, engine in enumerate(provider_models, 1):
                info = engine.get_info()
                stars = "⭐" * info["intelligence"]
                cost_str = f"${info['cost_input']:.2f}/${info['cost_output']:.2f}"
                marker = "→" if engine == current_engine else " "
                output.append(f"{marker} {i:2}. {engine.value:<40} {stars:<10} {info['max_tokens']:>6,} tokens | {cost_str}")

            output.append("-" * 80)
            output.append("\nUse /switch <number or model name> to switch models")
            output.append("Use /switch all to see models from all providers")
            return "\n".join(output)

        # Check if user wants to see all models
        if args[0].lower() == "all":
            output = []
            output.append("\nAll available models:")
            output.append("=" * 100)
            output.append(f"{'Model':<45} {'Provider':<12} {'Intelligence':<15} {'Max Tokens':<12} {'Cost ($/1M tokens)':<20}")
            output.append("-" * 100)

            for engine in Engines:
                info = engine.get_info()
                stars = "⭐" * info["intelligence"]
                cost_str = f"${info['cost_input']:.2f} / ${info['cost_output']:.2f}"

                output.append(f"{engine.value:<45} {info['provider']:<12} {stars:<15} {info['max_tokens']:<12} {cost_str:<20}")

            output.append("=" * 100)
            output.append("\nIntelligence: ⭐ = fast/cheap, ⭐⭐ = balanced, ⭐⭐⭐ = most capable")
            output.append("Cost format: input / output per 1M tokens\n")

            return "\n".join(output)

        # Try to parse as number (1-based index within current provider)
        target = args[0]
        current_engine = bot.model_engine
        current_provider = current_engine.get_info()["provider"]
        provider_models = [e for e in Engines if e.get_info()["provider"] == current_provider]

        try:
            index = int(target) - 1
            if 0 <= index < len(provider_models):
                new_engine = provider_models[index]
                bot.model_engine = new_engine
                return f"Switched to {new_engine.value}"
            else:
                return "Invalid model number. Use /switch to see available models."
        except ValueError:
            pass

        # Try to find by name (exact or partial match)
        target_lower = target.lower()

        # First try exact match
        for engine in Engines:
            if engine.value.lower() == target_lower:
                bot.model_engine = engine
                return f"Switched to {engine.value}"

        # Then try partial match
        matches = [e for e in Engines if target_lower in e.value.lower()]

        if len(matches) == 1:
            bot.model_engine = matches[0]
            return f"Switched to {matches[0].value}"
        elif len(matches) > 1:
            match_list = "\n".join([f"  - {e.value}" for e in matches])
            return f"Multiple matches found:\n{match_list}\n\nPlease be more specific."
        else:
            return f"Model '{target}' not found. Use /switch or /switch all to see available models."

    def clear(self, _bot: Bot, _context: CLIContext, _args: List[str]) -> str:
        """Clear the terminal screen."""
        import platform
        import shutil
        import subprocess

        # Use appropriate clear command for the platform
        if platform.system() == "Windows":
            # On Windows, use cmd built-in cls command
            subprocess.run(["cmd", "/c", "cls"], shell=False, check=False)
        else:
            # On Unix-like systems, check if clear is available
            clear_path = shutil.which("clear")
            if clear_path:
                subprocess.run([clear_path], shell=False, check=False)
            else:
                # Fallback to ANSI escape sequence
                print("\033[H\033[J", end="")

        return ""


class DynamicFunctionalPromptHandler:
    """Handler for functional prompt commands using dynamic parameter collection."""

    def __init__(self, function_filter: Optional[Callable[[str, Callable], bool]] = None):
        self.collector = DynamicParameterCollector(function_filter)
        self.fp_functions = self._discover_fp_functions()

    def _discover_fp_functions(self) -> Dict[str, Callable]:
        """Automatically discover functional prompt functions from the fp module."""
        functions = {}
        descoped_functions = {"prompt_for", "par_dispatch"}
        for name in dir(fp):
            obj = getattr(fp, name)
            if callable(obj) and (not name.startswith("_")) and (name not in descoped_functions):
                try:
                    sig = inspect.signature(obj)
                    params = list(sig.parameters.keys())
                    if params and params[0] == "bot":
                        if self.collector.function_filter is None or self.collector.function_filter(name, obj):
                            functions[name] = obj
                except Exception:
                    continue  # Skip if we can't inspect the signature
        return functions

    def execute(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Execute functional prompt wizard with dynamic parameter collection."""
        try:
            print("\nAvailable functional prompts:")
            func_names = list(self.fp_functions.keys())
            for i, name in enumerate(func_names, 1):
                print(f"  {i}. {name}")
            choice = input("\nSelect functional prompt (number or name): ").strip()
            fp_name = None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(func_names):
                    fp_name = func_names[idx]
            elif choice in self.fp_functions:
                fp_name = choice
            if not fp_name:
                return "Invalid selection"
            fp_function = self.fp_functions[fp_name]
            params = self.collector.collect_parameters(fp_function)
            if params is None:
                return "Parameter collection cancelled"
            context.conversation_backup = bot.conversation
            print(f"\nExecuting {fp_name}...")
            _callback_type = params.pop("_callback_type", "list")

            # Check if the function accepts a callback parameter
            sig = inspect.signature(fp_function)
            accepts_callback = "callback" in sig.parameters

            if accepts_callback:
                if _callback_type == "single":

                    def single_callback(response: str, node):
                        """Formats and displays a single response from a bot node using pretty printing.

                        Args:
                            response (str): The response text to be formatted and displayed.
                            node: The bot node that generated the response.
                        """
                        pretty(
                            response,
                            context.bot_instance.name if context.bot_instance else "Bot",
                            context.config.width,
                            context.config.indent,
                            COLOR_ASSISTANT,
                        )
                        if hasattr(context, "bot_instance") and context.bot_instance and context.config.verbose:
                            if hasattr(node, "tool_calls") and node.tool_calls:
                                tool_calls_str = "".join((clean_dict(call) for call in node.tool_calls))
                                pretty(
                                    f"Tool Requests\n\n{tool_calls_str}",
                                    "system",
                                    context.config.width,
                                    context.config.indent,
                                    COLOR_TOOL_REQUEST,
                                )
                            if hasattr(node, "tool_results") and node.tool_results:
                                tool_results_str = "".join((clean_dict(result) for result in node.tool_results))
                                if tool_results_str.strip():
                                    pretty(
                                        f"Tool Results\n\n{tool_results_str}",
                                        "system",
                                        context.config.width,
                                        context.config.indent,
                                        COLOR_TOOL_RESULT,
                                    )

                    params["callback"] = single_callback
                else:
                    callback = context.callbacks.get_standard_callback()
                    params["callback"] = callback

            result = fp_function(bot, **params)
            if isinstance(result, tuple) and len(result) == 2:
                responses, nodes = result
                if isinstance(responses, list):
                    for i, response in enumerate(responses):
                        if response:
                            pretty(
                                f"Response {i+1}: {response}",
                                bot.name,
                                context.config.width,
                                context.config.indent,
                                COLOR_ASSISTANT,
                                newline_after_name=False,
                            )
                    return f"Functional prompt '{fp_name}' completed with {len(responses)} responses"
                else:
                    if responses:
                        pretty(
                            responses,
                            bot.name,
                            context.config.width,
                            context.config.indent,
                            COLOR_ASSISTANT,
                            newline_after_name=False,
                        )
                    return f"Functional prompt '{fp_name}' completed"
            else:
                return f"Functional prompt '{fp_name}' completed with result: {result}"
        except Exception as e:
            return f"Error executing functional prompt: {str(e)}"

    def broadcast_fp(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Execute broadcast_fp functional prompt with leaf selection by number."""
        try:
            # Use the utility function to find leaves
            leaves = _find_leaves_util(bot.conversation)
            if not leaves:
                return "No leaves found from current node"
            print(f"\nFound {len(leaves)} leaf nodes:")
            for i, leaf in enumerate(leaves, 1):
                depth = 0
                current = leaf
                # Calculate depth safely, handling mock objects
                while hasattr(current, "parent") and current.parent and not current.parent._is_empty():
                    depth += 1
                    current = current.parent
                preview = leaf.content[:50] + "..." if len(leaf.content) > 50 else leaf.content
                print(f"  {i}. [depth {depth}]: {preview}")
            leaf_input = input("\nSelect leaves (comma-separated numbers or 'all'): ").strip()
            if leaf_input.lower() == "all":
                target_leaves = leaves
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in leaf_input.split(",")]
                    if not all(0 <= i < len(leaves) for i in indices):
                        return "Invalid leaf selection format. Use numbers separated by commas (e.g., '1,3,5') or 'all'"
                    target_leaves = [leaves[i] for i in indices]
                except (ValueError, IndexError):
                    return "Invalid leaf selection format. Use numbers separated by commas (e.g., '1,3,5') or 'all'"
            print(f"\nSelected {len(target_leaves)} leaves for broadcast")
            fp_options = [
                ("single_prompt", fp.single_prompt),
                ("chain", fp.chain),
                ("branch", fp.branch),
                ("tree_of_thought", fp.tree_of_thought),
                ("prompt_while", fp.prompt_while),
                ("chain_while", fp.chain_while),
                ("branch_while", fp.branch_while),
                ("par_branch", fp.par_branch),
                ("par_branch_while", fp.par_branch_while),
            ]
            print("\nAvailable functional prompts:")
            for i, (name, _) in enumerate(fp_options, 1):
                print(f"  {i}. {name}")
            fp_choice = input("\nSelect functional prompt (number or name): ").strip()
            selected_fp = None
            if fp_choice.isdigit():
                idx = int(fp_choice) - 1
                if 0 <= idx < len(fp_options):
                    selected_fp = fp_options[idx]
            else:
                for name, func in fp_options:
                    if name.lower() == fp_choice.lower():
                        selected_fp = (name, func)
                        break
            if not selected_fp:
                return "Invalid functional prompt selection"
            fp_name, fp_func = selected_fp
            print(f"\nUsing functional prompt: {fp_name}")
            params = self.collector.collect_parameters(fp_func)
            if params is None:
                return "Parameter collection cancelled"
            print(f"\nBroadcasting {fp_name} to {len(target_leaves)} leaves...")
            callback = context.callbacks.get_standard_callback()
            responses, nodes = fp.broadcast_fp(
                bot=bot, leaves=target_leaves, functional_prompt=fp_func, callback=callback, **params
            )
            print(f"\nBroadcast complete! Generated {len(responses)} responses")
            for i, response in enumerate(responses, 1):
                if response:
                    print(f"\nResponse {i}:")
                    pretty(
                        response,
                        bot.name,
                        context.config.width,
                        context.config.indent,
                        COLOR_ASSISTANT,
                        newline_after_name=False,
                    )
            return f"Broadcast complete with {len(responses)} responses"
        except Exception as e:
            return f"Error in broadcast_fp: {str(e)}"


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


def format_tool_data(data: dict, indent: int = 4, color: str = COLOR_RESET) -> str:
    """
    Format tool arguments or results in a clean, minimal way.
    No JSON braces, no quotes around keys, just key: value pairs.
    Keys are bolded for emphasis.

    Special case: If there's only one key-value pair, just return the value
    without the key name (assumes it's the primary/required input).
    """
    if not data:
        return "(empty)"

    # Special case: single input - just show the value without the key
    if len(data) == 1:
        key, value = next(iter(data.items()))
        if isinstance(value, str):
            return "\n" + value
        elif isinstance(value, dict):
            return "\n" + format_tool_data(value, indent, color)
        else:
            return "\n" + str(value)

    # Multiple inputs - show key: value pairs
    lines = []
    for key, value in data.items():
        # Strip underscores from parameter names for cleaner display
        display_key = key.replace("_", " ")
        # Bold the key name with color, keep colon and value colored too
        bold_key = f"{color}{COLOR_BOLD}{display_key}{COLOR_RESET}{color}:"

        if isinstance(value, dict):
            # Nested dict - format recursively with extra indent
            nested = format_tool_data(value, indent, color)
            lines.append(bold_key)
            for nested_line in nested.split("\n"):
                if nested_line:  # Skip empty lines
                    lines.append(" " * indent + nested_line)
        elif isinstance(value, str):
            # String value - handle multiline strings
            if "\n" in value:
                lines.append(bold_key)
                for line in value.split("\n"):
                    lines.append(" " * indent + line)
            else:
                lines.append(f"{bold_key} {value}")
        elif isinstance(value, (list, tuple)):
            # List/tuple - format as compact representation
            lines.append(f"{bold_key} {value}")
        else:
            # Other types (int, bool, None, etc.)
            lines.append(f"{bold_key} {value}")

    # Return the formatted lines joined with newlines
    return "\n" + "\n".join(lines)


def check_for_interrupt() -> bool:
    """Check if user pressed Escape without blocking execution."""
    if platform.system() == "Windows":
        if msvcrt.kbhit():
            key = msvcrt.getch()
            return key == b"\x1b"  # ESC key
        return False
    else:
        if select.select([sys.stdin], [], [], 0.0)[0]:
            key = sys.stdin.read(1)
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)
            return key == "\x1b"  # ESC key
        return False


def setup_raw_mode():
    """Set up terminal for raw input mode on Unix systems."""
    if platform.system() != "Windows":
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return old_settings


def restore_terminal(old_settings):
    """Restore terminal settings on Unix systems."""
    if platform.system() != "Windows" and old_settings is not None:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)


def clean_dict(d: dict, indent: int = 4, level: int = 1):
    """
    Clean a dict containing recursive json dumped strings for printing
    Returns: clean string representation of the dict
    """
    for k, v in d.items():
        if isinstance(v, dict):
            clean_dict(v, indent, level + 1)
        if isinstance(v, str) and "\n" in v:
            lines = v.splitlines()
            for i, line in enumerate(lines):
                line = " " * indent * (level + 1) + line
                if i == 0:
                    line = "\n" + line
                lines[i] = line
            d[k] = "\n".join(lines)
    cleaned_dict = json.dumps(d, indent=indent * level)
    cleaned_dict = re.sub(r"(?<!\\)\\n", "\n", cleaned_dict)
    cleaned_dict = cleaned_dict.replace('\\"', '"')
    cleaned_dict = cleaned_dict.replace("\\\\", "\\")
    return cleaned_dict


def display_metrics(context: CLIContext, bot: Bot):
    """Display API metrics if verbose mode is on."""
    if not context.config.verbose:
        return

    try:
        from bots.observability import metrics

        # Use cached metrics from context if available, otherwise get fresh ones
        if context.last_message_metrics is not None:
            last_metrics = context.last_message_metrics
        else:
            last_metrics = metrics.get_and_clear_last_metrics()

        # Check if there are any metrics to display
        if last_metrics["input_tokens"] == 0 and last_metrics["output_tokens"] == 0:
            return

        # Calculate total tokens for this call (including cached tokens)
        total_tokens = (
            last_metrics["input_tokens"] + last_metrics["output_tokens"] + last_metrics.get("cached_tokens", 0)
        )  # noqa: E501

        # Format the metrics in a single line: [tokens] | $[cost] | [time]s
        # Prepend newline to match format_tool_data behavior
        metrics_str = f"\n{total_tokens:,} | ${last_metrics['cost']:.4f} | {last_metrics['duration']:.2f}s"

        # Add session totals on second line
        try:
            session_tokens = metrics.get_total_tokens(context.session_start_time)
            session_cost = metrics.get_total_cost(context.session_start_time)

            metrics_str += f"\n{session_tokens['total']:,} | ${session_cost:.4f}"
        except Exception:
            # If session totals fail, just show the per-call metrics
            pass

        pretty(
            metrics_str,
            "metrics",
            context.config.width,
            context.config.indent,
            COLOR_METRICS,
            newline_after_name=True,
        )
        print()  # Add extra newline after metrics
    except Exception:
        pass


def pretty(
    string: str,
    name: Optional[str] = None,
    width: int = 1400,
    indent: int = 4,
    color: str = COLOR_RESET,
    newline_after_name: bool = True,
) -> None:
    """Print a string nicely formatted with explicit color."""
    print()
    if name is not None:
        if newline_after_name:
            prefix = f"{color}{COLOR_BOLD}{name}:{COLOR_RESET}\n{' ' * indent}{color}"
        else:
            prefix = f"{color}{COLOR_BOLD}{name}: {COLOR_RESET}{color}"
    else:
        prefix = color
    if not isinstance(string, str):
        string = str(string)

    # Safeguard: if string is too long, truncate it to prevent processing hangs
    max_length = 50000  # Reasonable limit for display
    if len(string) > max_length:
        string = string[:max_length] + "\n... (output truncated)"

    # Quick path for very simple strings - avoid regex overhead
    if len(string) < 1000 and "\n" not in string:
        print(prefix + string + COLOR_RESET)
        print()
        return

    lines = string.split("\n")
    formatted_lines = []

    # Limit number of lines to prevent excessive processing
    max_lines = 1000
    if len(lines) > max_lines:
        lines = lines[:max_lines]
        lines.append("... (output truncated)")

    for i, line in enumerate(lines):
        # Additional safeguard: skip wrapping for very long lines
        if len(line) > 10000:
            if i == 0:
                formatted_lines.append(prefix + line[:10000] + "... (line truncated)" + COLOR_RESET)
            else:
                formatted_lines.append(" " * indent + color + line[:10000] + "... (line truncated)" + COLOR_RESET)
            continue

        if i == 0:
            initial_line = prefix + line + COLOR_RESET
            try:
                wrapped = textwrap.wrap(
                    initial_line,
                    width=width,
                    subsequent_indent=" " * indent,
                    break_long_words=True,
                    break_on_hyphens=False,  # noqa: E501
                )
            except Exception:
                # Fallback if textwrap fails
                wrapped = [initial_line]
        else:
            try:
                wrapped = textwrap.wrap(
                    color + line + COLOR_RESET,
                    width=width,
                    initial_indent=" " * indent,
                    subsequent_indent=" " * indent,
                    break_long_words=True,
                    break_on_hyphens=False,
                )
            except Exception:
                # Fallback if textwrap fails
                wrapped = [" " * indent + color + line + COLOR_RESET]
        if wrapped:
            formatted_lines.extend(wrapped)
        else:
            formatted_lines.append(" " * indent if i > 0 else prefix + COLOR_RESET)
    for line in formatted_lines:
        print(line)
    print()


class CLI:
    """Main CLI class that orchestrates all handlers."""

    def __init__(self, bot_filename: Optional[str] = None, function_filter: Optional[Callable] = None):
        """Initialize the CLI with handlers and context."""
        # Import BotSession here to avoid circular imports
        from bots.dev.bot_session import BotSession

        # Create the underlying session
        self.session = BotSession(bot_filename=bot_filename, function_filter=function_filter, auto_initialize=True)

        # Keep references for backward compatibility
        self.context = self.session.context
        self.bot_filename = bot_filename
        self.function_filter = function_filter

        # Expose handlers for backward compatibility
        self.system = self.session.system
        self.state = self.session.state
        self.conversation = self.session.conversation
        self.fp = self.session.fp
        self.prompts = self.session.prompts
        self.backup = self.session.backup
        self.commands = self.session.commands

        # Expose internal methods for backward compatibility
        self._handle_chat = self.session._handle_chat
        self._handle_command = self.session._handle_command
        self._handle_load_prompt = self.session._handle_load_prompt
        self._handle_save_prompt = self.session._handle_save_prompt
        self._handle_delete_prompt = self.session._handle_delete_prompt
        self._handle_recent_prompts = self.session._handle_recent_prompts
        self._initialize_new_bot = self.session._initialize_new_bot

        # Attach real-time display callback to bot if it exists
        if self.context.bot_instance:
            self.context.bot_instance.callbacks = RealTimeDisplayCallbacks(self.context)

    @property
    def last_user_message(self):
        """Get last user message from session."""
        return self.session.last_user_message

    @last_user_message.setter
    def last_user_message(self, value):
        """Set last user message in session."""
        self.session.last_user_message = value

    @property
    def pending_prefill(self):
        """Get pending prefill from session."""
        return self.session.pending_prefill

    @pending_prefill.setter
    def pending_prefill(self, value):
        """Set pending prefill in session."""
        self.session.pending_prefill = value

    def run(self):
        """Main CLI loop with terminal I/O."""
        try:
            print("Hello, world! ")
            self.context.old_terminal_settings = setup_raw_mode()

            # Show load status
            if self.bot_filename:
                if self.context.bot_instance:
                    pretty(
                        f"{self.context.bot_instance.name} loaded",
                        "system",
                        self.context.config.width,
                        self.context.config.indent,
                        COLOR_SYSTEM,
                    )
                else:
                    pretty(
                        "Failed to load bot, starting with new bot",
                        "system",
                        self.context.config.width,
                        self.context.config.indent,
                        COLOR_SYSTEM,
                    )

            # Ensure bot has real-time callback
            if self.context.bot_instance:
                self.context.bot_instance.callbacks = RealTimeDisplayCallbacks(self.context)

            while True:
                try:
                    if not self.context.bot_instance:
                        pretty(
                            "No bot instance available. Use /load to create one.",
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

                    # Process through BotSession
                    response = self.session.input(user_input)

                    # Handle exit signal
                    if response == "__EXIT__":
                        raise SystemExit(0)

                    # Display response if not already displayed by callbacks
                    # The session returns responses for commands, but chat responses
                    # are displayed by the RealTimeDisplayCallbacks
                    if response and not user_input.startswith("/") and " /" not in user_input:
                        # This is a chat response - already displayed by callback
                        pass
                    elif response:
                        # This is a command response - display it
                        pretty(
                            response,
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


class PromptHandler:
    """Handler for prompt management commands."""

    def __init__(self):
        self.prompt_manager = PromptManager()

    def _get_input_with_prefill(self, prompt_text: str, prefill: str = "") -> str:
        """Get input with pre-filled text using readline if available."""
        if not HAS_READLINE or not prefill:
            return input(prompt_text)

        def startup_hook():
            """Startup hook function that inserts prefilled text into the readline buffer and refreshes the display.

            This function is typically used as a callback with readline to pre-populate
            the input line with default text when the user starts typing.

            Note:
                Requires 'prefill' variable to be defined in the enclosing scope.
            """
            readline.insert_text(prefill)
            readline.redisplay()

        readline.set_startup_hook(startup_hook)
        try:
            user_input = input(prompt_text)
            return user_input
        finally:
            readline.set_startup_hook(None)

    def load_prompt(self, bot: "Bot", context: "CLIContext", args: List[str]) -> tuple:
        """Load a saved prompt by name or search query.

        Returns tuple of (status_message, prompt_content) for use by CLI.
        """
        if not args:
            # Show recent prompts
            recents = self.prompt_manager.get_recents()
            if recents:
                print("\nRecent prompts:")
                for i, (name, _content) in enumerate(recents[:10], 1):
                    print(f"  {i}. {name}")

                try:
                    selection = input_with_esc("\nEnter number or name to load (ESC to cancel): ").strip()
                    if selection.isdigit():
                        idx = int(selection) - 1
                        if 0 <= idx < len(recents):
                            name = recents[idx][0]
                        else:
                            return ("Invalid selection.", None)
                    else:
                        name = selection
                except EscapeException:
                    return ("Load cancelled.", None)
            else:
                # No recents, prompt for search query
                try:
                    name = input_with_esc("\nEnter prompt name or search query: ").strip()
                    if not name:
                        return ("Load cancelled.", None)
                except EscapeException:
                    return ("Load cancelled.", None)
        else:
            name = " ".join(args)

        # Try exact match first
        try:
            content = self.prompt_manager.load_prompt(name)
            return (f"Loaded prompt: {name}", content)
        except KeyError:
            pass

        # Try fuzzy search
        matches = self.prompt_manager.search_prompts(name)

        if not matches:
            return ("No prompts found matching your search.", None)

        if len(matches) == 1:
            # Single match - load directly
            name, content = matches[0]
            self.prompt_manager.load_prompt(name)  # Update recency
            return (f"Loaded prompt: {name}", content)

        # Multiple matches - show selection with best match highlighted
        print(f"\nFound {len(matches)} matches (best match first):")
        for i, (name, content) in enumerate(matches[:10], 1):  # Limit to 10 results
            # Show preview of content
            preview = content[:80] + "..." if len(content) > 80 else content
            preview = preview.replace("\n", " ")  # Single line preview
            marker = "→" if i == 1 else " "
            print(f"  {marker} {i}. {name}: {preview}")

        if len(matches) > 10:
            print(f"  ... and {len(matches) - 10} more matches")

        try:
            selection = input_with_esc("\nEnter number or name to load (ESC to cancel): ").strip()
            if selection.isdigit():
                idx = int(selection) - 1
                if 0 <= idx < len(matches):
                    name, content = matches[idx]
                else:
                    return ("Invalid selection.", None)
            else:
                # Try to find by name in matches
                name = selection
                content = None
                for match_name, match_content in matches:
                    if match_name == name:
                        content = match_content
                        break
                if content is None:
                    return (f"'{name}' not in search results.", None)

            self.prompt_manager.load_prompt(name)  # Update recency
            return (f"Loaded prompt: {name}", content)
        except EscapeException:
            return ("Load cancelled.", None)

    def save_prompt(self, bot: "Bot", context: "CLIContext", args: List[str], last_user_message: str | None = None) -> str:
        """Save a prompt. If args provided, save the args. Otherwise save last user message."""
        try:
            if args:
                # Save the provided text
                prompt_text = " ".join(args)
            elif last_user_message:
                # Save the last user message
                prompt_text = last_user_message
            else:
                return "No prompt to save. Either provide text with /s or use /s after sending a message."

            if not prompt_text.strip():
                return "Cannot save empty prompt."

            # Generate name and save
            name = self.prompt_manager.save_prompt(prompt_text)
            return f"Saved prompt as: {name}"

        except Exception as e:
            return f"Error saving prompt: {str(e)}"

    def delete_prompt(self, bot: "Bot", context: "CLIContext", args: List[str]) -> str:
        """Delete a saved prompt."""
        try:
            # Get prompt name
            if args:
                query = " ".join(args)
            else:
                query = input("Enter prompt name or search: ").strip()

            if not query:
                return "Delete cancelled."

            # Search for matching prompts
            matches = self.prompt_manager.search_prompts(query)

            if not matches:
                return "No prompts found matching your search."

            if len(matches) == 1:
                # Single match - confirm and delete
                name, content = matches[0]
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"\nPrompt to delete: {name}")
                print(f"Content: {preview}")
                confirm = input("Delete this prompt? (y/n): ").strip().lower()

                if confirm == "y":
                    if self.prompt_manager.delete_prompt(name):
                        return f"Deleted prompt: {name}"
                    else:
                        return f"Failed to delete prompt: {name}"
                else:
                    return "Delete cancelled."

            # Multiple matches - show selection
            print(f"\nFound {len(matches)} matches:")
            for i, (name, content) in enumerate(matches[:10], 1):
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"  {i}. {name}: {preview}")

            if len(matches) > 10:
                print(f"  ... and {len(matches) - 10} more matches")

            # Get selection
            try:
                choice = input(f"\nSelect prompt to delete (1-{min(len(matches), 10)}): ").strip()
                if not choice:
                    return "Delete cancelled."

                choice_num = int(choice) - 1
                if choice_num < 0 or choice_num >= min(len(matches), 10):
                    return f"Invalid selection. Must be between 1 and {min(len(matches), 10)}."

                name, content = matches[choice_num]
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"\nPrompt to delete: {name}")
                print(f"Content: {preview}")
                confirm = input("Delete this prompt? (y/n): ").strip().lower()

                if confirm == "y":
                    if self.prompt_manager.delete_prompt(name):
                        return f"Deleted prompt: {name}"
                    else:
                        return f"Failed to delete prompt: {name}"
                else:
                    return "Delete cancelled."

            except ValueError:
                return "Invalid selection. Must be a number."

        except Exception as e:
            return f"Error deleting prompt: {str(e)}"

    def recent_prompts(self, bot: "Bot", context: "CLIContext", args: List[str]) -> tuple:
        """Show recently used prompts with search capability."""
        recents = self.prompt_manager.get_recents()

        if not recents:
            return ("No recent prompts found.", None)

        # Check if user provided a search query
        query = " ".join(args) if args else None

        if query:
            # Search in recent prompts
            matches = [
                (name, content)
                for name, content in recents  # Fixed: was unpacking 3 values
                if query.lower() in name.lower() or query.lower() in content.lower()
            ]

            if not matches:
                return (f"No recent prompts matching '{query}'", None)

            print(f"\nFound {len(matches)} matches (best match first):")
            for i, (name, content) in enumerate(matches[:10], 1):  # Limit to 10 results
                # Show preview of content
                preview = content[:80] + "..." if len(content) > 80 else content
                preview = preview.replace("\n", " ")  # Single line preview
                marker = "→" if i == 1 else " "
                print(f"  {marker} {i}. {name}")
                print(f"       {preview}")

            try:
                choice = input_with_esc("\nEnter number to load (or press ESC to cancel): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(matches):
                        name, content = matches[idx]
                        return (f"Loading prompt: {name}", content)
                    else:
                        return ("Invalid selection.", None)
                else:
                    return ("Selection cancelled.", None)
            except EscapeException:
                return ("Selection cancelled.", None)
        else:
            # Show all recent prompts
            print("\nRecent prompts (most recent first):")
            for i, (name, content) in enumerate(recents[:10], 1):  # Fixed: was unpacking 3 values
                # Show a preview
                preview = content[:60] + "..." if len(content) > 60 else content
                preview = preview.replace("\n", " ")
                marker = "→" if i == 1 else " "
                print(f"  {marker} {i}. {name}")
                print(f"       {preview}")

            if len(recents) > 10:
                print(f"  ... and {len(recents) - 10} more")

            try:
                choice = input_with_esc("\nEnter number to load (or press ESC to cancel): ").strip()
                if choice.isdigit():
                    idx = int(choice) - 1
                    if 0 <= idx < len(recents):
                        name, content = recents[idx]
                        return (f"Loading prompt: {name}", content)
                    else:
                        return ("Invalid selection.", None)
                else:
                    return ("Selection cancelled.", None)
            except EscapeException:
                return ("Selection cancelled.", None)


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
    parser.add_argument(
        "--color",
        choices=["auto", "always", "never"],
        default="auto",
        help="Control color output (default: auto)",
    )
    parser.add_argument(
        "--no-color",
        action="store_true",
        help="Disable color output (shorthand for --color=never)",
    )
    return parser.parse_args()


def main(bot_filename=None, function_filter=None):
    """Entry point for the CLI."""
    color_mode = "auto"  # Default color mode

    if bot_filename is None:
        args = parse_args()
        bot_filename = args.filename

        # Handle color arguments
        color_mode = "never" if args.no_color else args.color
        _init_colors(color_mode)

    cli = CLI(bot_filename=bot_filename, function_filter=function_filter)

    # Set color mode in config if it was specified via CLI args
    if bot_filename is None:
        cli.context.config.color = color_mode

    cli.run()


if __name__ == "__main__":
    main()
