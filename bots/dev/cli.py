import argparse
import inspect
import json
import os
import platform
import re
import sys
import textwrap
from typing import Any, Callable, Dict, List, Optional
import bots.flows.functional_prompts as fp
import bots.flows.recombinators as recombinators
import bots.tools.code_tools
import bots.tools.python_edit
import bots.tools.terminal_tools
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode
"""
CLI for bot interactions with improved architecture and dynamic parameter collection.

Architecture:
- Handler classes for logical command grouping
- Command registry for easy extensibility
- Dynamic parameter collection for functional prompts
- Robust error handling with conversation backup
- Configuration support for CLI settings
"""
if platform.system() == "Windows":
    import msvcrt
else:
    import select
    import termios
    import tty
COLOR_USER = '\033[36m'             # Cyan
COLOR_ASSISTANT = '\033[36m'        # Cyan
COLOR_SYSTEM = '\033[33m'           # Yellow
COLOR_ERROR = '\033[31m'            # Red
COLOR_RESET = '\033[0m'             # Reset
COLOR_BOLD = '\033[1m'              # Bold
COLOR_DIM = '\033[2m'               # Dim
COLOR_TOOL_REQUEST = '\033[34m'     # Blue
COLOR_TOOL_RESULT = '\033[32m'      # Green

class DynamicParameterCollector:
    """Dynamically collect parameters for functional prompts based on their signatures."""

    def __init__(self, function_filter: Optional[Callable[[str, Callable], bool]]=None):
        self.param_handlers = {"prompt_list": self._collect_prompts, "prompts": self._collect_prompts, "prompt": self._collect_single_prompt, "first_prompt": self._collect_single_prompt, "stop_condition": self._collect_condition, "continue_prompt": self._collect_continue_prompt, "recombinator_function": self._collect_recombinator, "should_branch": self._collect_boolean, "skip": self._collect_skip_labels, "items": self._collect_items, "dynamic_prompt": self._collect_dynamic_prompt, "functional_prompt": self._collect_functional_prompt}
        self.conditions = {"1": ("tool_used", fp.conditions.tool_used), "2": ("tool_not_used", fp.conditions.tool_not_used), "3": ("said_DONE", fp.conditions.said_DONE), "4": ("said_READY", fp.conditions.said_READY), "5": ("error_in_response", fp.conditions.error_in_response)}
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
        print(f"\nEnter {param_name} (empty line to finish):")
        while True:
            prompt = input(f"Prompt {len(prompts) + 1}: ").strip()
            if not prompt:
                break
            prompts.append(prompt)
        if not prompts:
            print("No prompts entered")
            return None
        return prompts

    def _collect_single_prompt(self, param_name: str, default: Any) -> Optional[str]:
        """Collect a single prompt from user."""
        prompt = input(f"Enter {param_name}: ").strip()
        return prompt if prompt else None

    def _collect_condition(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect stop condition from user."""
        print(f"\nAvailable stop conditions for {param_name}:")
        for key, (name, _) in self.conditions.items():
            print(f"  {key}. {name}")
        default_display = self._format_default_value(default)
        choice = input(f"Select condition (default: {default_display}): ").strip()
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
        if default != inspect.Parameter.empty:
            prompt = input(f"Enter {param_name} (default: {default_display}): ").strip()
            return prompt if prompt else default
        else:
            prompt = input(f"Enter {param_name}: ").strip()
            return prompt if prompt else None

    def _collect_boolean(self, param_name: str, default: Any) -> Optional[bool]:
        """Collect boolean parameter."""
        default_display = self._format_default_value(default)
        choice = input(f"Enter {param_name} (y/n, default: {default_display}): ").strip().lower()
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
        skip_input = input(f"Enter {param_name} (comma-separated, or empty for none): ").strip()
        if skip_input:
            return [label.strip() for label in skip_input.split(",")]
        else:
            return []

    def _collect_recombinator(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect recombinator function with available options."""
        print(f"\nAvailable recombinators for {param_name}:")
        recombinator_options = {"1": ("concatenate", recombinators.recombinators.concatenate), "2": ("llm_judge", recombinators.recombinators.llm_judge), "3": ("llm_vote", recombinators.recombinators.llm_vote), "4": ("llm_merge", recombinators.recombinators.llm_merge)}
        for key, (name, _) in recombinator_options.items():
            print(f"  {key}. {name}")
        default_display = self._format_default_value(default)
        choice = input(f"Select recombinator (default: {default_display}): ").strip()
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
        fp_options = {"1": ("single_prompt", fp.single_prompt), "2": ("chain", fp.chain), "3": ("branch", fp.branch), "4": ("tree_of_thought", fp.tree_of_thought), "5": ("prompt_while", fp.prompt_while), "6": ("chain_while", fp.chain_while), "7": ("branch_while", fp.branch_while)}
        for key, (name, _) in fp_options.items():
            print(f"  {key}. {name}")
        choice = input("Select functional prompt: ").strip()
        if choice in fp_options:
            return fp_options[choice][1]
        else:
            print("Invalid functional prompt selection, using single_prompt")
            return fp.single_prompt

    def _collect_generic_parameter(self, param_name: str, default: Any) -> Optional[Any]:
        """Generic parameter collection for unknown parameter types."""
        default_display = self._format_default_value(default)
        if default != inspect.Parameter.empty:
            value = input(f"Enter {param_name} (default: {default_display}): ").strip()
            return value if value else default
        else:
            value = input(f"Enter {param_name}: ").strip()
            return value if value else None

class CLIConfig:
    """Configuration management for CLI settings."""

    def __init__(self):
        self.verbose = True
        self.width = 1000
        self.indent = 4
        self.config_file = "cli_config.json"
        self.load_config()

    def load_config(self):
        """Load configuration from file if it exists."""
        try:
            if os.path.exists(self.config_file):
                with open(self.config_file, "r") as f:
                    config_data = json.load(f)
                    self.verbose = config_data.get("verbose", True)
                    self.width = config_data.get("width", 1000)
                    self.indent = config_data.get("indent", 4)
        except Exception:
            pass  # Use defaults if config loading fails

    def save_config(self):
        """Save current configuration to file."""
        try:
            config_data = {"verbose": self.verbose, "width": self.width, "indent": self.indent}
            with open(self.config_file, "w") as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            pass  # Fail silently if config saving fails

class CLICallbacks:
    """Centralized callback management for CLI operations."""

    def __init__(self, context: "CLIContext"):
        self.context = context

    def create_message_only_callback(self):
        """Create a callback that only prints bot messages, no tool info."""

        def message_only_callback(responses, nodes):
            if responses and responses[-1]:
                pretty(responses[-1], self.context.bot_instance.name if self.context.bot_instance else "Bot", self.context.config.width, self.context.config.indent, COLOR_ASSISTANT)
        return message_only_callback

    def create_verbose_callback(self):
        """Create a callback that shows everything: tool info first, then messages."""

        def verbose_callback(responses, nodes):
            if hasattr(self.context, "bot_instance") and self.context.bot_instance:
                bot = self.context.bot_instance
                requests = bot.tool_handler.requests
                results = bot.tool_handler.results
                if requests:
                    request_str = "".join((clean_dict(r) for r in requests))
                    pretty(f"Tool Requests\n\n{request_str}", "Tool Requests", self.context.config.width, self.context.config.indent, COLOR_TOOL_REQUEST)
                if results:
                    result_str = "".join((clean_dict(r) for r in results))
                    if result_str.strip():
                        pretty(f"Tool Results\n\n{result_str}", "Tool Results", self.context.config.width, self.context.config.indent, COLOR_TOOL_RESULT)
            if responses and responses[-1]:
                pretty(responses[-1], self.context.bot_instance.name if self.context.bot_instance else "Bot", self.context.config.width, self.context.config.indent, COLOR_ASSISTANT)
        return verbose_callback

    def create_quiet_callback(self):
        """Create a callback that shows tool usage summary first, then response."""

        def quiet_callback(responses, nodes):
            if nodes and nodes[-1] and hasattr(self.context, "bot_instance") and self.context.bot_instance:
                current_node = nodes[-1]
                if hasattr(current_node, "tool_calls") and current_node.tool_calls:
                    tool_names = []
                    for tool_call in current_node.tool_calls:
                        if "function" in tool_call and "name" in tool_call["function"]:
                            tool_names.append(tool_call["function"]["name"])
                        elif "name" in tool_call:
                            tool_names.append(tool_call["name"])
                    if tool_names:
                        pretty(f"Used tools: {', '.join(set(tool_names))}", "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
            if responses and responses[-1]:
                pretty(responses[-1], self.context.bot_instance.name if self.context.bot_instance else "Bot", self.context.config.width, self.context.config.indent, COLOR_ASSISTANT)
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
                    idx = int(input(f"Reply index (max {max_index}): "))
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

    def label(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Label current conversation node."""
        label = input("Label: ").strip()
        if not label:
            return "Label cannot be empty"
        context.labeled_nodes[label] = bot.conversation
        if not hasattr(bot.conversation, "labels"):
            bot.conversation.labels = []
        if label not in bot.conversation.labels:
            bot.conversation.labels.append(label)
        return f"Saved current node with label: {label}"

    def goto(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Go to labeled conversation node."""
        label = input("Label: ").strip()
        if label in context.labeled_nodes:
            context.conversation_backup = bot.conversation
            bot.conversation = context.labeled_nodes[label]
            if not self._ensure_assistant_node(bot):
                return f"Warning: Moved to node labeled '{label}' but ended up on user node with no assistant response"
            self._display_conversation_context(bot, context)
            return f"Moved to node labeled: {label}"
        return f"No node found with label: {label}"

    def showlabels(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show all labeled nodes."""
        if not context.labeled_nodes:
            return "No labels saved"
        result = "Saved labels:\n"
        for label, node in context.labeled_nodes.items():
            content_preview = node.content[:100] + "..." if len(node.content) > 100 else node.content
            result += f"  '{label}': {content_preview}\n"
        return result.rstrip()

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

    def _get_leaf_preview(self, leaf: ConversationNode, max_length: int=300) -> str:
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
        recombinator_options = {"1": ("concatenate", recombinators.recombinators.concatenate), "2": ("llm_judge", recombinators.recombinators.llm_judge), "3": ("llm_vote", recombinators.recombinators.llm_vote), "4": ("llm_merge", recombinators.recombinators.llm_merge)}
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
            pretty(final_response, bot.name, context.config.width, context.config.indent, COLOR_ASSISTANT)
            return f"Successfully combined {len(leaves)} leaves using {recombinator_name}"
        except Exception as e:
            return f"Error combining leaves: {str(e)}"

    def _find_leaves(self, node: ConversationNode) -> List[ConversationNode]:
        """Recursively find all leaf nodes from a given node."""
        leaves = []

        def dfs(current_node):
            if not current_node.replies:  # This is a leaf
                leaves.append(current_node)
            else:
                for reply in current_node.replies:
                    dfs(reply)
        dfs(node)
        return leaves

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
            pretty(bot.conversation.content, bot.name, context.config.width, context.config.indent, COLOR_ASSISTANT)

class StateHandler:
    """Handler for bot state management commands."""

    def save(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Save bot state."""
        try:
            filename = input("Save filename (without extension): ").strip()
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
            filename = input("Load filename: ").strip()
            if not filename:
                return "Load cancelled - no filename provided"
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
        help_lines = ["This program is an interactive terminal that uses AI bots.", "It allows you to chat with the LLM, save and load bot states, and execute various commands.", "The bot has the ability to read and write files and can execute powershell and python code directly.", "The bot also has tools to help edit python files in an accurate and token-efficient way.", "", "Available commands:", "/help: Show this help message", "/verbose: Show tool requests and results (default on)", "/quiet: Hide tool requests and results", "/save: Save the current bot (prompts for filename)", "/load: Load a previously saved bot (prompts for filename)", '/up: "rewind" the conversation by one turn by moving up the conversation tree', "/down: Move down the conversation tree. Requests index of reply if there are multiple.", "/left: Move to this conversation node's left sibling", "/right: Move to this conversation node's right sibling", "/auto: Let the bot work autonomously until it sends a response that doesn't use tools (esc to quit)", "/root: Move to the root node of the conversation tree", "/label: Save current node with a label for later reference", "/goto: Move to a previously labeled node", "/showlabels: Show all saved labels and their associated conversation content", "/leaf [number]: Show all conversation endpoints (leaves) and optionally jump to one", "/fp: Execute functional prompts with dynamic parameter collection", "/combine_leaves: Combine all leaves below current node using a recombinator function", "/broadcast_fp: Execute functional prompts on all leaf nodes", "/config: Show or modify CLI configuration", "/exit: Exit the program", "", "Type your messages normally to chat."]
        return "\n".join(help_lines)

    def verbose(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Enable verbose mode."""
        if context.config.verbose:
            return "Tool output is already enabled (verbose mode is on)"
        context.config.verbose = True
        context.config.save_config()
        return "Tool output enabled - will now show detailed tool requests and results"

    def quiet(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Disable verbose mode."""
        context.config.verbose = False
        context.config.save_config()
        return "Tool output disabled"

    def config(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show or modify configuration."""
        if not args:
            config_lines = ["Current configuration:", f"    verbose: {context.config.verbose}", f"    width: {context.config.width}", f"    indent: {context.config.indent}", "Use '/config set <setting> <value>' to modify settings."]
            return "\n".join(config_lines)
        if len(args) >= 3 and args[0] == "set":
            setting = args[1]
            value = args[2]
            try:
                if setting == "verbose":
                    context.config.verbose = value.lower() in ("true", "1", "yes", "on")
                elif setting == "width":
                    context.config.width = int(value)
                elif setting == "indent":
                    context.config.indent = int(value)
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
            print("Bot running autonomously. Press ESC to interrupt...")
            while True:
                if check_for_interrupt():
                    restore_terminal(old_settings)
                    return "Autonomous execution interrupted by user"
                callback = context.callbacks.get_standard_callback()
                responses, nodes = fp.chain(bot, ["ok"], callback=callback)
                if responses and (not bot.tool_handler.requests):
                    restore_terminal(old_settings)
                    return "Bot finished autonomous execution"
        except Exception as e:
            if context.old_terminal_settings:
                restore_terminal(context.old_terminal_settings)
            return f"Error during autonomous execution: {str(e)}"

class DynamicFunctionalPromptHandler:
    """Handler for functional prompt commands using dynamic parameter collection."""

    def __init__(self, function_filter: Optional[Callable[[str, Callable], bool]]=None):
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
            if _callback_type == "single":

                def single_callback(response: str, node):
                    pretty(response, context.bot_instance.name if context.bot_instance else "Bot", context.config.width, context.config.indent, COLOR_ASSISTANT)
                    if hasattr(context, "bot_instance") and context.bot_instance and context.config.verbose:
                        if hasattr(node, "tool_calls") and node.tool_calls:
                            tool_calls_str = "".join((clean_dict(call) for call in node.tool_calls))
                            pretty(f"Tool Requests\n\n{tool_calls_str}", "System", context.config.width, context.config.indent, COLOR_TOOL_REQUEST)
                        if hasattr(node, "tool_results") and node.tool_results:
                            tool_results_str = "".join((clean_dict(result) for result in node.tool_results))
                            if tool_results_str.strip():
                                pretty(f"Tool Results\n\n{tool_results_str}", "System", context.config.width, context.config.indent, COLOR_TOOL_RESULT)
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
                            pretty(f"Response {i+1}: {response}", bot.name, context.config.width, context.config.indent, COLOR_ASSISTANT)
                    return f"Functional prompt '{fp_name}' completed with {len(responses)} responses"
                else:
                    if responses:
                        pretty(responses, bot.name, context.config.width, context.config.indent, COLOR_ASSISTANT)
                    return f"Functional prompt '{fp_name}' completed"
            else:
                return f"Functional prompt '{fp_name}' completed with result: {result}"
        except Exception as e:
            return f"Error executing functional prompt: {str(e)}"

    def broadcast_fp(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Execute broadcast_fp functional prompt with leaf selection by number."""
        try:
            leaves = context.conversation._find_leaves(bot.conversation)
            if not leaves:
                return "No leaves found from current node"
            print(f"\nFound {len(leaves)} leaf nodes:")
            for i, leaf in enumerate(leaves):
                content_preview = context.conversation._get_leaf_preview(leaf)
                depth = context.conversation._calculate_depth(bot.conversation, leaf)
                labels = getattr(leaf, "labels", [])
                label_str = f" (labels: {', '.join(labels)})" if labels else ""
                print(f"  {i+1}. [depth {depth}]{label_str}: {content_preview}")
            leaf_selection = input("\nSelect leaves to broadcast to (e.g., '1,3,5' or 'all' for all leaves): ").strip()
            if not leaf_selection:
                return "No leaves selected"
            target_leaves = []
            if leaf_selection.lower() == "all":
                target_leaves = leaves
            else:
                try:
                    indices = [int(x.strip()) - 1 for x in leaf_selection.split(",")]
                    for idx in indices:
                        if 0 <= idx < len(leaves):
                            target_leaves.append(leaves[idx])
                        else:
                            return f"Invalid leaf number: {idx + 1}. Must be between 1 and {len(leaves)}"
                except ValueError:
                    return "Invalid leaf selection format. Use numbers separated by commas (e.g., '1,3,5') or 'all'"
            if not target_leaves:
                return "No valid leaves selected"
            print(f"\nSelected {len(target_leaves)} leaves for broadcast")
            print("\nSelect functional prompt to broadcast:")
            fp_options = {"1": ("single_prompt", fp.single_prompt), "2": ("chain", fp.chain), "3": ("branch", fp.branch), "4": ("tree_of_thought", fp.tree_of_thought), "5": ("prompt_while", fp.prompt_while), "6": ("chain_while", fp.chain_while), "7": ("branch_while", fp.branch_while)}
            for key, (name, _) in fp_options.items():
                print(f"  {key}. {name}")
            fp_choice = input("Select functional prompt: ").strip()
            if fp_choice not in fp_options:
                return "Invalid functional prompt selection"
            fp_name, fp_function = fp_options[fp_choice]
            print(f"\nCollecting parameters for {fp_name}:")
            params = self.collector.collect_parameters(fp_function)
            if params is None:
                return "Parameter collection cancelled"
            callback = context.callbacks.get_standard_callback()
            params["callback"] = callback
            context.conversation_backup = bot.conversation
            print(f"Broadcasting {fp_name} to {len(target_leaves)} selected leaves...")
            all_leaves = context.conversation._find_leaves(bot.conversation)
            temp_labels = {}
            skip_labels = []
            for i, leaf in enumerate(all_leaves):
                if leaf not in target_leaves:
                    temp_label = f"__temp_skip_{i}__"
                    if not hasattr(leaf, "labels"):
                        leaf.labels = []
                    leaf.labels.append(temp_label)
                    skip_labels.append(temp_label)
                    temp_labels[leaf] = temp_label
            try:
                responses, nodes = fp.broadcast_fp(bot, fp_function, skip=skip_labels, **params)
                successful_responses = [r for r in responses if r is not None]
                failed_count = len(responses) - len(successful_responses)
                result_msg = f"Broadcast completed: {len(successful_responses)} successful"
                if failed_count > 0:
                    result_msg += f", {failed_count} failed"
                return result_msg
            finally:
                for leaf, temp_label in temp_labels.items():
                    if hasattr(leaf, "labels") and temp_label in leaf.labels:
                        leaf.labels.remove(temp_label)
        except Exception as e:
            return f"Error in broadcast_fp: {str(e)}"

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

def clean_dict(d: dict, indent: int=4, level: int=1):
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

def display_tool_results(bot: Bot, context: CLIContext):
    """Display tool requests and results first, then bot message."""
    requests = bot.tool_handler.requests
    results = bot.tool_handler.results
    if requests and context.config.verbose:
        request_str = "".join((clean_dict(r) for r in requests))
        result_str = "".join((clean_dict(r) for r in results))
        pretty(f"Tool Requests\n\n{request_str}", "System", context.config.width, context.config.indent, COLOR_TOOL_REQUEST)
        pretty(f"Tool Results\n\n{result_str}", "System", context.config.width, context.config.indent, COLOR_TOOL_RESULT)
    elif requests and (not context.config.verbose):
        for request in requests:
            tool_name, _ = bot.tool_handler.tool_name_and_input(request)
            pretty(f"{bot.name} used {tool_name}", "System", context.config.width, context.config.indent, COLOR_SYSTEM)
    pretty(bot.conversation.content, bot.name, context.config.width, context.config.indent, COLOR_ASSISTANT)

def pretty(string: str, name: Optional[str]=None, width: int=1000, indent: int=4, color: str=COLOR_RESET) -> None:
    """Print a string nicely formatted with explicit color."""
    print()
    prefix = f"{color}{COLOR_BOLD}{name}: {COLOR_RESET}{color}" if name is not None else color
    if not isinstance(string, str):
        string = str(string)
    lines = string.split("\n")
    formatted_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            initial_line = prefix + line + COLOR_RESET
            wrapped = textwrap.wrap(initial_line, width=width, subsequent_indent=" " * indent)
        else:
            wrapped = textwrap.wrap(color + line + COLOR_RESET, width=width, initial_indent=" " * indent, subsequent_indent=" " * indent)
        if wrapped:
            formatted_lines.extend(wrapped)
        else:
            formatted_lines.append(" " * indent if i > 0 else prefix + COLOR_RESET)
    for line in formatted_lines:
        print(line)
    print()

class CLI:
    """Main CLI class that orchestrates all handlers."""

    def __init__(self, bot_filename: Optional[str]=None, function_filter: Optional[Callable[[str, Callable], bool]]=None):
        self.context = CLIContext()
        self.conversation = ConversationHandler()
        self.context.conversation = self.conversation  # Add reference for handlers to use
        self.state = StateHandler()
        self.system = SystemHandler()
        self.fp = DynamicFunctionalPromptHandler(function_filter)
        self.bot_filename = bot_filename
        self.commands = {"/help": self.system.help, "/verbose": self.system.verbose, "/quiet": self.system.quiet, "/config": self.system.config, "/save": self.state.save, "/load": self.state.load, "/up": self.conversation.up, "/down": self.conversation.down, "/left": self.conversation.left, "/right": self.conversation.right, "/root": self.conversation.root, "/label": self.conversation.label, "/goto": self.conversation.goto, "/showlabels": self.conversation.showlabels, "/leaf": self.conversation.leaf, "/combine_leaves": self.conversation.combine_leaves, "/auto": self.system.auto, "/fp": self.fp.execute, "/broadcast_fp": self.fp.broadcast_fp}

    def run(self):
        """Main CLI loop."""
        try:
            print("Hello, world! Combined CLI with Dynamic Parameter Collection")
            self.context.old_terminal_settings = setup_raw_mode()
            if self.bot_filename:
                result = self.state._load_bot_from_file(self.bot_filename, self.context)
                if "Error" in result or "File not found" in result:
                    print(f"Failed to load bot: {result}")
                    print("Starting with new bot instead...")
                    self._initialize_new_bot()
                else:
                    print(result)
                    if self.context.bot_instance:
                        pretty(f"Bot loaded: {self.context.bot_instance.name}", "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
            else:
                self._initialize_new_bot()
            print("CLI started. Type /help for commands or chat normally.")
            while True:
                try:
                    user_input = input(">>> ").strip()
                    if user_input == "/exit":
                        raise SystemExit(0)
                    if not user_input:
                        continue
                    words = user_input.split()
                    if not words:
                        continue
                    command = None
                    msg = None
                    if words[0].startswith("/"):
                        command = words[0]
                        msg = " ".join(words[1:]) if len(words) > 1 else None
                    elif words[-1].startswith("/"):
                        command = words[-1]
                        msg = " ".join(words[:-1]) if len(words) > 1 else None
                    else:
                        msg = user_input
                    if command:
                        if command not in self.commands:
                            pretty("Unrecognized command. Try /help.", "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
                            continue
                        if msg:
                            if command in ["/help", "/verbose", "/quiet", "/config", "/save", "/load", "/up", "/down", "/left", "/right", "/root", "/label", "/goto", "/showlabels", "/leaf", "/combine_leaves"]:
                                self._handle_command(self.context.bot_instance, user_input)
                                if command in ["/up", "/down", "/left", "/right", "/root", "/goto", "/leaf"]:
                                    self._handle_chat(self.context.bot_instance, msg)
                            else:
                                self._handle_chat(self.context.bot_instance, msg)
                                self._handle_command(self.context.bot_instance, user_input)
                        else:
                            self._handle_command(self.context.bot_instance, user_input)
                    else:
                        self._handle_chat(self.context.bot_instance, user_input)
                except KeyboardInterrupt:
                    print("\nUse /exit to quit")
                except EOFError:
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")
                    if self.context.conversation_backup:
                        self.context.bot_instance.conversation = self.context.conversation_backup
                        print("Restored conversation from backup")
        finally:
            restore_terminal(self.context.old_terminal_settings)
            print("Goodbye!")

    def _initialize_new_bot(self):
        """Initialize a new bot with default tools."""
        bot = AnthropicBot()
        self.context.bot_instance = bot
        from bots.tools.code_tools import view, view_dir
        from bots.tools.self_tools import branch_self
        
        bot.add_tools(bots.tools.terminal_tools, bots.tools.python_edit, view, view_dir)
        #This works well as a fallback:
        #bot.add_tools(bots.tools.terminal_tools, view, view_dir)

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
                    pretty(result, "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
            except Exception as e:
                pretty(f"Command error: {str(e)}", "Error", self.context.config.width, self.context.config.indent, COLOR_ERROR)
                if self.context.conversation_backup:
                    bot.conversation = self.context.conversation_backup
                    pretty("Restored conversation from backup", "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)
        else:
            pretty("Unrecognized command. Try /help.", "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)

    def _handle_chat(self, bot: Bot, user_input: str):
        """Handle chat input."""
        if not user_input:
            return
        try:
            self.context.conversation_backup = bot.conversation
            callback = self.context.callbacks.get_standard_callback()
            responses, nodes = fp.chain(bot, [user_input], callback=callback)
            pass
        except Exception as e:
            pretty(f"Chat error: {str(e)}", "Error", self.context.config.width, self.context.config.indent, COLOR_ERROR)
            if self.context.conversation_backup:
                bot.conversation = self.context.conversation_backup
                pretty("Restored conversation from backup", "System", self.context.config.width, self.context.config.indent, COLOR_SYSTEM)

def parse_args():
    """Parse command line arguments."""
    parser = argparse.ArgumentParser(description='Interactive CLI for AI bots with conversation management and dynamic parameter collection.', formatter_class=argparse.RawDescriptionHelpFormatter, epilog=textwrap.dedent("""
             Examples:
             python -m bots.dev.cli_combined                    # Start with new bot
             python -m bots.dev.cli_combined mybot.bot          # Load bot from file
             python -m bots.dev.cli_combined saved_conversation # Load bot (auto-adds .bot extension)
             """.strip()))
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