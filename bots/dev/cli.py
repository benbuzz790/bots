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
from bots.foundation.base import Bot, ConversationNode
from bots.observability import tracing
from bots.observability.callbacks import BotCallbacks

# Disable tracing span processors to prevent console output
try:
    if hasattr(tracing, "_tracer_provider") and tracing._tracer_provider is not None:
        tracing._tracer_provider._active_span_processor._span_processors.clear()
except Exception:
    pass  # If this fails, traces will still show but it's not critical


class EscapeException(Exception):
    """Exception raised when user presses ESC to cancel input."""

    pass


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
COLOR_USER = "\033[36m"  # Cyan (not dim)
COLOR_BOT = "\033[95m"  # Light Pink/Magenta
COLOR_TOOL_NAME = "\033[2m\033[33m"  # Dim Yellow
COLOR_TOOL_RESULT = "\033[2m\033[32m"  # Dim Green
COLOR_METRICS = "\033[2m\033[37m"  # Very Dim Gray
COLOR_SYSTEM = "\033[2m\033[33m"  # Dim Yellow
COLOR_ERROR = "\033[31m"  # Red
COLOR_RESET = "\033[0m"  # Reset
COLOR_BOLD = "\033[1m"  # Bold
COLOR_DIM = "\033[2m"  # Dim
# Legacy colors for compatibility
COLOR_ASSISTANT = COLOR_BOT
COLOR_TOOL_REQUEST = "\033[34m"  # Blue


def create_auto_stash() -> str:
    """Create an automatic git stash with AI-generated message based on current diff."""
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
        self.remove_context_threshold = 40000
        self.auto_mode_neutral_prompt = "ok"
        self.auto_mode_reduce_context_prompt = "trim useless context"
        self.max_tokens = 4096
        self.temperature = 1.0
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

    def save_prompt(self, prompt_text: str, name: str = None) -> str:
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

    def up(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move up in conversation tree."""
        if bot.conversation.parent and bot.conversation.parent.parent:
            context.conversation_backup = bot.conversation
            bot.conversation = bot.conversation.parent.parent
            if not self._ensure_assistant_node(bot):
                return "Warning: Ended up on user node with no assistant response. Bumped to previous assistant node."
            self._display_conversation_context(bot, context)
            return "Moved up conversation tree"
        return "At root - can't go up"

    def down(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move down in conversation tree."""
        if bot.conversation.replies:
            max_index = len(bot.conversation.replies) - 1
            idx = 0
            if max_index > 0:
                try:
                    try:
                        idx = int(input_with_esc(f"Reply index (max {max_index}): "))
                    except EscapeException:
                        return "Selection cancelled"
                    if idx < 0 or idx > max_index:
                        return f"Invalid index. Must be between 0 and {max_index}"
                except ValueError:
                    return "Invalid index. Must be a number"
            context.conversation_backup = bot.conversation
            next_node = bot.conversation.replies[idx]
            if next_node.replies:
                bot.conversation = next_node.replies[0]
            else:
                bot.conversation = next_node
            if not self._ensure_assistant_node(bot):
                return "Warning: Ended up on user node with no assistant response"
            self._display_conversation_context(bot, context)
            return "Moved down conversation tree"
        return "At leaf - can't go down"

    def left(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move left to sibling in conversation tree."""
        if not bot.conversation.parent:
            return "At root - can't go left"
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return "Conversation has no siblings at this point"
        current_index = next((i for i, reply in enumerate(replies) if reply is bot.conversation))
        next_index = (current_index - 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        if not self._ensure_assistant_node(bot):
            return "Warning: Ended up on user node with no assistant response"
        self._display_conversation_context(bot, context)
        return "Moved left in conversation tree"

    def right(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move right to sibling in conversation tree."""
        if not bot.conversation.parent:
            return "At root - can't go right"
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return "Conversation has no siblings at this point"
        current_index = next((i for i, reply in enumerate(replies) if reply is bot.conversation))
        next_index = (current_index + 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        if not self._ensure_assistant_node(bot):
            return "Warning: Ended up on user node with no assistant response"
        self._display_conversation_context(bot, context)
        return "Moved right in conversation tree"

    def root(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move to root of conversation tree."""
        context.conversation_backup = bot.conversation
        while bot.conversation.parent:
            bot.conversation = bot.conversation.parent
        if not self._ensure_assistant_node(bot):
            return "Warning: Ended up on user node with no assistant response"
        self._display_conversation_context(bot, context)
        return "Moved to root of conversation tree"
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

    def label(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show all labels and create new label or jump to existing one."""
        # First, show all existing labels (like showlabels)
        if context.labeled_nodes:
            print("Existing labels:")
            for label_name, node in context.labeled_nodes.items():
                content_preview = node.content[:100] + "..." if len(node.content) > 100 else node.content
                print(f"  '{label_name}': {content_preview}")
            print()
        else:
            print("No labels saved yet.")
            print()

        # Get label input from user
        try:
            label = input_with_esc("Enter label name (new to create, existing to jump): ").strip()
        except EscapeException:
            return "Label operation cancelled"
        if not label:
            return "No label entered"

        # Check if label already exists
        if label in context.labeled_nodes:
            # Jump to existing label (like goto)
            context.conversation_backup = bot.conversation
            bot.conversation = context.labeled_nodes[label]
            if not self._ensure_assistant_node(bot):
                return f"Warning: Moved to node labeled '{label}' but ended up on user node with no assistant response"
            self._display_conversation_context(bot, context)
            return f"Jumped to existing label: {label}"
        else:
            # Create new label (like original label behavior)
            context.labeled_nodes[label] = bot.conversation
            if not hasattr(bot.conversation, "labels"):
                bot.conversation.labels = []
            if label not in bot.conversation.labels:
                bot.conversation.labels.append(label)
            return f"Created new label: {label}"

    # showlabels method removed - functionality merged into label method
    def leaf(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show all leaf nodes and optionally jump to one by number."""
        leaves = self._find_leaves(bot.conversation)
        if not leaves:
            return "No leaves found from current node"
        context.cached_leaves = leaves
        if args:
            try:
                leaf_index = int(args[0]) - 1  # Convert to 0-based index
                if leaf_index < 0 or leaf_index >= len(leaves):
                    return f"Invalid leaf number. Must be between 1 and {len(leaves)}"
                context.conversation_backup = bot.conversation
                bot.conversation = leaves[leaf_index]
                if not self._ensure_assistant_node(bot):
                    return f"Warning: Jumped to leaf {leaf_index + 1} but ended up on user node with no assistant response"
                self._display_conversation_context(bot, context)
                content_preview = self._get_leaf_preview(leaves[leaf_index])
                return f"Jumped to leaf {leaf_index + 1}: {content_preview}"
            except ValueError:
                return "Invalid leaf number. Must be a number."
        result = f"Found {len(leaves)} leaf nodes:\n"
        for i, leaf in enumerate(leaves):
            content_preview = self._get_leaf_preview(leaf)
            depth = self._calculate_depth(bot.conversation, leaf)
            labels = getattr(leaf, "labels", [])
            label_str = f" (labels: {', '.join(labels)})" if labels else ""
            result += f"  {i+1}. [depth {depth}]{label_str}: {content_preview}\n"
        result += f"\nEnter a number (1-{len(leaves)}) to jump to that leaf, or press Enter to stay: "
        try:
            choice = input(result).strip()
            if choice:
                leaf_index = int(choice) - 1
                if 0 <= leaf_index < len(leaves):
                    context.conversation_backup = bot.conversation
                    bot.conversation = leaves[leaf_index]
                    if not self._ensure_assistant_node(bot):
                        return f"Warning: Jumped to leaf {leaf_index + 1} but ended up on user node with no assistant response"
                    self._display_conversation_context(bot, context)
                    content_preview = self._get_leaf_preview(leaves[leaf_index])
                    return f"Jumped to leaf {leaf_index + 1}: {content_preview}"
                else:
                    return f"Invalid choice. Must be between 1 and {len(leaves)}"
            else:
                return "Staying at current position"
        except ValueError:
            return "Invalid input. Staying at current position"
        except (EOFError, KeyboardInterrupt):
            return "Cancelled. Staying at current position"

    def _get_leaf_preview(self, leaf: ConversationNode, max_length: int = 300) -> str:
        """Get a preview of leaf content, cutting from middle if too long."""
        content = leaf.content.strip()
        if len(content) <= max_length:
            return content
        half_length = (max_length - 5) // 2  # Account for " ... "
        start = content[:half_length].strip()
        end = content[-half_length:].strip()
        return f"{start} ... {end}"

    def combine_leaves(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Combine all leaves below current node using a recombinator function."""
        leaves = self._find_leaves(bot.conversation)
        if not leaves:
            return "No leaves found from current node"
        if len(leaves) < 2:
            return "Need at least 2 leaves to combine"
        print(f"\nFound {len(leaves)} leaves to combine.")
        print("Available recombinators:")
        recombinator_options = {
            "1": ("concatenate", recombinators.recombinators.concatenate),
            "2": ("llm_judge", recombinators.recombinators.llm_judge),
            "3": ("llm_vote", recombinators.recombinators.llm_vote),
            "4": ("llm_merge", recombinators.recombinators.llm_merge),
        }
        for key, (name, _) in recombinator_options.items():
            print(f"  {key}. {name}")
        choice = input("Select recombinator: ").strip()
        if choice not in recombinator_options:
            return "Invalid recombinator selection"
        recombinator_func = recombinator_options[choice][1]
        recombinator_name = recombinator_options[choice][0]
        try:
            responses = [leaf.content for leaf in leaves]
            context.conversation_backup = bot.conversation
            print(f"Combining {len(leaves)} leaves using {recombinator_name}...")
            final_response, final_node = fp.recombine(bot, responses, leaves, recombinator_func)
            pretty(
                final_response,
                bot.name,
                context.config.width,
                context.config.indent,
                COLOR_ASSISTANT,
                newline_after_name=False,
            )
            return f"Successfully combined {len(leaves)} leaves using {recombinator_name}"
        except Exception as e:
            return f"Error combining leaves: {str(e)}"

    def _find_leaves(self, node: ConversationNode) -> List[ConversationNode]:
        """Recursively find all leaf nodes from a given node."""
        return _find_leaves_util(node)

    def _calculate_depth(self, start_node: ConversationNode, target_node: ConversationNode) -> int:
        """Calculate the depth/distance from start_node to target_node."""

        def find_path_length(current, target, depth=0):
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

    def save(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Save bot state."""
        try:
            try:
                filename = input_with_esc("Save filename (without extension): ").strip()
            except EscapeException:
                return "Save cancelled"
            if not filename:
                return "Save cancelled - no filename provided"
            if not filename.endswith(".bot"):
                filename = filename + ".bot"
            bot.save(filename)
            return f"Bot saved to {filename}"
        except Exception as e:
            return f"Error saving bot: {str(e)}"

    def load(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
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
                return "Load cancelled"
            if not filename:
                return "Load cancelled - no filename provided"

            # Check if input is a number referring to the list
            if filename.isdigit() and bot_files:
                file_index = int(filename) - 1
                if 0 <= file_index < len(bot_files):
                    filename = bot_files[file_index]
                else:
                    return f"Invalid selection. Must be between 1 and {len(bot_files)}"

            return self._load_bot_from_file(filename, context)
        except Exception as e:
            return f"Error loading bot: {str(e)}"

    def _load_bot_from_file(self, filename: str, context: CLIContext) -> str:
        """Load bot from file and update context. Used by both interactive load and CLI args."""
        try:
            if not os.path.exists(filename):
                if not filename.endswith(".bot"):
                    filename_with_ext = filename + ".bot"
                    if os.path.exists(filename_with_ext):
                        filename = filename_with_ext
                    else:
                        return f"File not found: {filename}"
                else:
                    return f"File not found: {filename}"
            new_bot = Bot.load(filename)
            while new_bot.conversation.replies:
                new_bot.conversation = new_bot.conversation.replies[-1]

            # Attach CLI callbacks for proper display
            new_bot.callbacks = RealTimeDisplayCallbacks(context)

            context.bot_instance = new_bot
            context.labeled_nodes = {}
            self._rebuild_labels(new_bot.conversation, context)
            context.cached_leaves = []
            return f"Bot loaded from {filename}. Conversation restored to most recent message."
        except Exception as e:
            return f"Error loading bot: {str(e)}"

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
                            and context.last_message_metrics.get("input_tokens", 0) > context.config.remove_context_threshold
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
                    if last_input_tokens > context.config.remove_context_threshold and context.context_reduction_cooldown <= 0:
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
                    next_prompt = continue_prompt(bot, iteration_count[0]) if callable(continue_prompt) else continue_prompt

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
                tools_list = "\n".join([f"  {i+1}. {name}" for i, name in enumerate(sorted(available_tools.keys()))])
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

        # Calculate total tokens for this call
        total_tokens = last_metrics["input_tokens"] + last_metrics["output_tokens"]

        # Format the metrics in a single line: [tokens] | $[cost] | [time]s
        metrics_str = f"{total_tokens:,} | ${last_metrics['cost']:.4f} | {last_metrics['duration']:.2f}s"

        # Add session totals on second line
        try:
            session_tokens = metrics.get_total_tokens(context.session_start_time)
            session_cost = metrics.get_total_cost(context.session_start_time)

            metrics_str += f"\n{session_tokens['total']:,} | ${session_cost:.4f}"
        except Exception:
            # If session totals fail, just show the per-call metrics
            pass

        pretty(metrics_str, "metrics", context.config.width, context.config.indent, COLOR_METRICS, newline_after_name=True)
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
                    initial_line, width=width, subsequent_indent=" " * indent, break_long_words=True, break_on_hyphens=False
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
        from bots import Engines

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
        from bots.tools.invoke_namshub import invoke_namshub

        bot.add_tools(
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
            invoke_namshub,
        )

        sys_msg = textwrap.dedent(
            """You're a coding agent. When greeting users, always start with "Hello! I'm here to help you".
        Please follow these rules:
                1. Keep edits and even writing new files to small chunks. You have a low max_token limit
                   and will hit tool errors if you try making too big of a change.
                2. Avoid using cd. Your terminal is stateful and will remember if you use cd.
                   Instead, use full relative paths.
        """
        )
        bot.set_system_message(sys_msg)

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
        if command in self.commands:
            try:
                result = self.commands[command](bot, self.context, args)
                if result:
                    pretty(result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
            except Exception as e:
                pretty(f"Command error: {str(e)}", "Error", self.context.config.width, self.context.config.indent, COLOR_ERROR)
                if self.context.conversation_backup and bot:
                    # Clear tool handler state to prevent corruption from failed tool executions
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

            # Auto-stash if enabled
            if self.context.config.auto_stash:
                stash_result = create_auto_stash()
                if "Auto-stash created:" in stash_result:
                    pretty(stash_result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
                elif "No changes to stash" not in stash_result:
                    # Show errors but not "no changes" message
                    pretty(stash_result, "system", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)

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
            if self.context.conversation_backup:
                # Clear tool handler state to prevent corruption from failed tool executions
                bot.tool_handler.clear()
                bot.conversation = self.context.conversation_backup
                pretty(
                    "Restored conversation from backup",
                    "system",
                    self.context.config.width,
                    self.context.config.indent,
                    COLOR_SYSTEM,
                )


class PromptHandler:
    """Handler for prompt management commands."""

    def __init__(self):
        self.prompt_manager = PromptManager()

    def _get_input_with_prefill(self, prompt_text: str, prefill: str = "") -> str:
        """Get input with pre-filled text using readline if available."""
        if not HAS_READLINE or not prefill:
            return input(prompt_text)

        def startup_hook():
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

    def save_prompt(self, bot: "Bot", context: "CLIContext", args: List[str], last_user_message: str = None) -> str:
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
        """Show recent prompts and optionally select one. Returns (message, prefill_text)."""
        try:
            recents = self.prompt_manager.get_recents()

            if not recents:
                return ("No recent prompts.", None)

            # Show recents
            print(f"\nRecent prompts ({len(recents)}):")
            for i, (name, content) in enumerate(recents, 1):
                preview = content[:100] + "..." if len(content) > 100 else content
                preview = preview.replace("\n", " ")
                print(f"  {i}. {name}: {preview}")

            # Get selection
            try:
                choice = input(f"\nSelect prompt (1-{len(recents)}, or Enter to cancel): ").strip()
                if not choice:
                    return ("Selection cancelled.", None)

                choice_num = int(choice) - 1
                if choice_num < 0 or choice_num >= len(recents):
                    return (f"Invalid selection. Must be between 1 and {len(recents)}.", None)

                name, content = recents[choice_num]
                self.prompt_manager.load_prompt(name)  # Update recency

                return (f"Loaded prompt: {name}", content)

            except ValueError:
                return ("Invalid selection. Must be a number.", None)

        except Exception as e:
            return (f"Error loading recent prompts: {str(e)}", None)


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