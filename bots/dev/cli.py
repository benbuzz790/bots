"""
Modern CLI for bot interactions with improved architecture.
This module provides a clean, extensible command-line interface for interacting
with AI bots, featuring functional prompts, conversation management, and robust
error handling.
Architecture:
- Handler classes for logical command grouping
- Command registry for easy extensibility
- Wizard-style multi-input commands
- Robust error handling with conversation backup
- Configuration support for CLI settings
"""
import sys
import json
import os
import re
import platform
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Tuple
from tkinter import filedialog
import textwrap
# Import platform-specific modules
if platform.system() == 'Windows':
    import msvcrt
else:
    import select
    import termios
    import tty
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode
import bots.tools.python_edit
import bots.tools.terminal_tools
import bots.tools.code_tools
import bots.flows.functional_prompts as fp
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
                with open(self.config_file, 'r') as f:
                    config_data = json.load(f)
                    self.verbose = config_data.get('verbose', True)
                    self.width = config_data.get('width', 1000)
                    self.indent = config_data.get('indent', 4)
        except Exception:
            pass  # Use defaults if config loading fails
    def save_config(self):
        """Save current configuration to file."""
        try:
            config_data = {
                'verbose': self.verbose,
                'width': self.width,
                'indent': self.indent
            }
            with open(self.config_file, 'w') as f:
                json.dump(config_data, f, indent=2)
        except Exception:
            pass  # Fail silently if config saving fails
class CLIContext:
    """Shared context for CLI operations."""
    def __init__(self):
        self.config = CLIConfig()
        self.labeled_nodes: Dict[str, ConversationNode] = {}
        self.conversation_backup: Optional[ConversationNode] = None
        self.old_terminal_settings = None
class ConversationHandler:
    """Handler for conversation navigation commands."""
    def up(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move up in conversation tree."""
        if bot.conversation.parent and bot.conversation.parent.parent:
            context.conversation_backup = bot.conversation
            bot.conversation = bot.conversation.parent.parent
            return f"Moved up conversation tree"
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
            return "Moved down conversation tree"
        return "At leaf - can't go down"
    def left(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move left to sibling in conversation tree."""
        if not bot.conversation.parent:
            return "At root - can't go left"
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return "Conversation has no siblings at this point"
        current_index = next(i for i, reply in enumerate(replies) 
                           if reply is bot.conversation)
        next_index = (current_index - 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        return "Moved left in conversation tree"
    def right(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move right to sibling in conversation tree."""
        if not bot.conversation.parent:
            return "At root - can't go right"
        replies = bot.conversation.parent.replies
        if not replies or len(replies) <= 1:
            return "Conversation has no siblings at this point"
        current_index = next(i for i, reply in enumerate(replies) 
                           if reply is bot.conversation)
        next_index = (current_index + 1) % len(replies)
        context.conversation_backup = bot.conversation
        bot.conversation = replies[next_index]
        return "Moved right in conversation tree"
    def root(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Move to root of conversation tree."""
        context.conversation_backup = bot.conversation
        while bot.conversation.parent:
            bot.conversation = bot.conversation.parent
        return "Moved to root of conversation tree"
    def label(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Label current conversation node."""
        label = input("Label: ").strip()
        if not label:
            return "Label cannot be empty"
        context.labeled_nodes[label] = bot.conversation
        # Store label in conversation node for persistence
        if not hasattr(bot.conversation, 'labels'):
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
class StateHandler:
    """Handler for bot state management commands."""
    def save(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Save bot state."""
        try:
            filename = filedialog.asksaveasfilename(
                title="Save Bot",
                defaultextension=".json",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                bot.save(filename)
                return f"Bot saved to {filename}"
            return "Save cancelled"
        except Exception as e:
            return f"Error saving bot: {str(e)}"
    def load(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Load bot state."""
        try:
            filename = filedialog.askopenfilename(
                title="Load Bot",
                filetypes=[("JSON files", "*.json"), ("All files", "*.*")]
            )
            if filename:
                bot.load(filename)
                # Rebuild labeled nodes from conversation tree
                context.labeled_nodes = {}
                self._rebuild_labels(bot.conversation, context)
                return f"Bot loaded from {filename}"
            return "Load cancelled"
        except Exception as e:
            return f"Error loading bot: {str(e)}"
    def _rebuild_labels(self, node: ConversationNode, context: CLIContext):
        """Recursively rebuild labeled nodes from conversation tree."""
        if hasattr(node, 'labels'):
            for label in node.labels:
                context.labeled_nodes[label] = node
        for reply in node.replies:
            self._rebuild_labels(reply, context)
class SystemHandler:
    """Handler for system and configuration commands."""
    def help(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show help message."""
        return """
This program is an interactive terminal that uses AI bots.
It allows you to chat with the LLM, save and load bot states, and execute various commands.
The bot has the ability to read and write files and can execute powershell and python code directly.
The bot also has tools to help edit python files in an accurate and token-efficient way.
Available commands:
/help: Show this help message
/verbose: Show tool requests and results (default on)
/quiet: Hide tool requests and results
/save: Save the current bot
/load: Load a previously saved bot
/up: "rewind" the conversation by one turn by moving up the conversation tree
/down: Move down the conversation tree. Requests index of reply if there are multiple.
/left: Move to this conversation node's left sibling
/right: Move to this conversation node's right sibling
/auto: Let the bot work autonomously until it sends a response without using any tools
/root: Move to the root node of the conversation tree
/label: Save current node with a label for later reference
/goto: Move to a previously labeled node
/showlabels: Show all saved labels and their associated conversation content
/fp: Execute functional prompts (chain, branch, tree_of_thought, etc.)
/config: Show or modify CLI configuration
/exit: Exit the program
Type your messages normally to chat.
        """.strip()
    def verbose(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Enable verbose mode."""
        context.config.verbose = True
        context.config.save_config()
        return "Tool output enabled"
    def quiet(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Disable verbose mode."""
        context.config.verbose = False
        context.config.save_config()
        return "Tool output disabled"
    def config(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Show or modify configuration."""
        if not args:
            return f"""Current configuration:
  verbose: {context.config.verbose}
  width: {context.config.width}
  indent: {context.config.indent}
Use '/config set <setting> <value>' to modify settings."""
        if len(args) >= 3 and args[0] == 'set':
            setting = args[1]
            value = args[2]
            try:
                if setting == 'verbose':
                    context.config.verbose = value.lower() in ('true', '1', 'yes', 'on')
                elif setting == 'width':
                    context.config.width = int(value)
                elif setting == 'indent':
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
            context.conversation_backup = bot.conversation
            # Set up interrupt checking
            old_settings = setup_raw_mode()
            context.old_terminal_settings = old_settings
            print("Bot running autonomously. Press ESC to interrupt...")
            final_response = None
            while True:
                if check_for_interrupt():
                    restore_terminal(old_settings)
                    return "Autonomous execution interrupted by user"
                response = bot.respond("ok")
                final_response = response  # Keep track of the last response
                display_tool_results(bot, context)
                pretty(final_response, bot.name, context.config.width, context.config.indent)
                if not bot.tool_handler.requests:
                    restore_terminal(old_settings)
                    return "Bot finished autonomous execution"
        except Exception as e:
            if context.old_terminal_settings:
                restore_terminal(context.old_terminal_settings)
            return f"Error during autonomous execution: {str(e)}"

class FunctionalPromptHandler:
    """Handler for functional prompt commands."""
    def __init__(self):
        self.fp_functions = {
            'chain': fp.chain,
            'chain_while': fp.chain_while,
            'prompt_while': fp.prompt_while,
            'branch': fp.branch,
            'branch_while': fp.branch_while,
            'par_branch': fp.par_branch,
            'par_branch_while': fp.par_branch_while,
            'tree_of_thought': fp.tree_of_thought,
            'prompt_for': fp.prompt_for,
            'par_dispatch': fp.par_dispatch
        }
    def execute(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Execute functional prompt wizard."""
        try:
            # Step 1: Choose functional prompt type
            print("\nAvailable functional prompts:")
            for i, name in enumerate(self.fp_functions.keys(), 1):
                print(f"  {i}. {name}")
            choice = input("\nSelect functional prompt (number or name): ").strip()
            # Parse choice
            fp_name = None
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(self.fp_functions):
                    fp_name = list(self.fp_functions.keys())[idx]
            else:
                if choice in self.fp_functions:
                    fp_name = choice
            if not fp_name:
                return "Invalid selection"
            fp_function = self.fp_functions[fp_name]
            # Step 2: Collect parameters based on function
            params = self._collect_parameters(fp_name, fp_function)
            if params is None:
                return "Parameter collection cancelled"
            # Step 3: Execute functional prompt
            context.conversation_backup = bot.conversation
            print(f"\nExecuting {fp_name}...")
            result = fp_function(bot, **params)
            # Step 4: Handle results
            if isinstance(result, tuple) and len(result) == 2:
                responses, nodes = result
                if isinstance(responses, list):
                    return f"Functional prompt '{fp_name}' completed with {len(responses)} responses"
                else:
                    return f"Functional prompt '{fp_name}' completed"
            else:
                return f"Functional prompt '{fp_name}' completed"
        except Exception as e:
            return f"Error executing functional prompt: {str(e)}"
    def _collect_parameters(self, fp_name: str, fp_function: Callable) -> Optional[Dict[str, Any]]:
        """Collect parameters for the chosen functional prompt."""
        params = {}
        # Common parameters for most functions
        if fp_name in ['chain', 'branch', 'par_branch', 'tree_of_thought']:
            prompts = self._collect_prompts()
            if prompts is None:
                return None
            params['prompts'] = prompts
        elif fp_name in ['chain_while', 'prompt_while', 'branch_while', 'par_branch_while']:
            # Single prompt for while functions
            prompt = input("Enter prompt: ").strip()
            if not prompt:
                return None
            params['prompt'] = prompt
            # Collect stop condition
            condition = self._collect_condition()
            if condition is None:
                return None
            params['stop_condition'] = condition
        elif fp_name == 'prompt_for':
            # Dynamic prompt function
            print("prompt_for requires a dynamic prompt function and data.")
            print("This is an advanced feature - implement custom logic as needed.")
            return None
        elif fp_name == 'par_dispatch':
            print("par_dispatch requires multiple bots and a functional prompt.")
            print("This is an advanced feature - implement custom logic as needed.")
            return None
        # Additional parameters for specific functions
        if fp_name == 'tree_of_thought':
            recombinator = self._collect_recombinator()
            if recombinator:
                params['recombinator_function'] = recombinator
        return params
    def _collect_prompts(self) -> Optional[List[str]]:
        """Collect a list of prompts from user."""
        prompts = []
        print("\nEnter prompts (empty line to finish):")
        while True:
            prompt = input(f"Prompt {len(prompts) + 1}: ").strip()
            if not prompt:
                break
            prompts.append(prompt)
        if not prompts:
            print("No prompts entered")
            return None
        return prompts
    def _collect_condition(self) -> Optional[Callable]:
        """Collect stop condition from user."""
        conditions = {
            '1': ('tool_used', fp.conditions.tool_used),
            '2': ('tool_not_used', fp.conditions.tool_not_used),
            '3': ('said_DONE', fp.conditions.said_DONE),
            '4': ('said_STOP', fp.conditions.said_STOP),
            '5': ('said_FINISHED', fp.conditions.said_FINISHED),
        }
        print("\nAvailable stop conditions:")
        for key, (name, _) in conditions.items():
            print(f"  {key}. {name}")
        choice = input("Select condition: ").strip()
        if choice in conditions:
            return conditions[choice][1]
        print("Invalid condition selection")
        return None
    def _collect_recombinator(self) -> Optional[Callable]:
        """Collect recombinator function (simplified for now)."""
        choice = input("Use default recombinator? (y/n): ").strip().lower()
        if choice == 'y':
            return fp.recombinators.simple_concatenate
        return None
# Utility functions (from original auto_terminal.py)
def check_for_interrupt() -> bool:
    """Check if user pressed Escape without blocking execution."""
    if platform.system() == 'Windows':
        if msvcrt.kbhit():
            key = msvcrt.getch()
            return key == b'\x1b'  # ESC key
        return False
    else:
        if select.select([sys.stdin], [], [], 0.0)[0]:
            key = sys.stdin.read(1)
            termios.tcflush(sys.stdin, termios.TCIOFLUSH)
            return key == '\x1b'  # ESC key
        return False
def setup_raw_mode():
    """Set up terminal for raw input mode on Unix systems."""
    if platform.system() != 'Windows':
        fd = sys.stdin.fileno()
        old_settings = termios.tcgetattr(fd)
        try:
            tty.setraw(sys.stdin.fileno())
        except termios.error:
            termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
        return old_settings
    return None
def restore_terminal(old_settings):
    """Restore terminal settings on Unix systems."""
    if platform.system() != 'Windows' and old_settings is not None:
        fd = sys.stdin.fileno()
        termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)

def clean_dict(d: dict, indent: int = 4, level: int = 1):
    """
    Clean a dict containing recursive json dumped strings for printing
    Returns: clean string representation of the dict
    """
    for k, v in d.items():
        if isinstance(v, dict):
            clean_dict(v, indent, level+1)
        if isinstance(v, str) and '\n' in v:
            lines = v.splitlines()
            for i, line in enumerate(lines):
                line = ' '*indent*(level+1) + line
                if i == 0: line = '\n' + line
                lines[i] = line
            d[k] = '\n'.join(lines)
    cleaned_dict = json.dumps(d, indent=indent*level)
    cleaned_dict = re.sub(r'(?<!\\)\\n', '\n', cleaned_dict)
    cleaned_dict = cleaned_dict.replace('\\"', '"')
    cleaned_dict = cleaned_dict.replace('\\\\', '\\')
    return cleaned_dict

def display_tool_results(bot: Bot, context: CLIContext):
    """Display tool requests and results in a readable format with bot message first."""
    requests = bot.tool_handler.requests
    results = bot.tool_handler.results
    pretty(bot.conversation.content, bot.name, context.config.width, context.config.indent)
    if not requests:
        return
    if context.config.verbose:
        request_str = ''.join(clean_dict(r) for r in requests)
        result_str = ''.join(clean_dict(r) for r in results)
        pretty(f'Tool Requests\n\n{request_str}', "System", context.config.width, context.config.indent)
        pretty(f'Tool Results\n\n{result_str}', "System", context.config.width, context.config.indent)
    else:
        for request in requests:
            tool_name, _ = bot.tool_handler.tool_name_and_input(request)
            pretty(f'{bot.name} used {tool_name}', "System", context.config.width, context.config.indent)

def pretty(string: str, name: Optional[str] = None, width: int = 1000, indent: int = 4) -> None:
    """Print a string nicely formatted."""
    prefix = f"{name}: " if name is not None else ""
    if not isinstance(string, str):
        string = str(string)
    lines = string.split('\n')
    formatted_lines = []
    for i, line in enumerate(lines):
        if i == 0:
            initial_line = prefix + line
            wrapped = textwrap.wrap(initial_line, width=width, subsequent_indent=' ' * indent)
        else:
            wrapped = textwrap.wrap(
                line, width=width, initial_indent=' ' * indent, subsequent_indent=' ' * indent
            )
        if wrapped:
            formatted_lines.extend(wrapped)
        else:
            formatted_lines.append(' ' * indent if i > 0 else prefix)
    for line in formatted_lines:
        print(line)
class CLI:
    """Main CLI class that orchestrates all handlers."""
    def __init__(self):
        self.context = CLIContext()
        self.conversation = ConversationHandler()
        self.state = StateHandler()
        self.system = SystemHandler()
        self.fp = FunctionalPromptHandler()
        # Command registry
        self.commands = {
            '/help': self.system.help,
            '/verbose': self.system.verbose,
            '/quiet': self.system.quiet,
            '/config': self.system.config,
            '/save': self.state.save,
            '/load': self.state.load,
            '/up': self.conversation.up,
            '/down': self.conversation.down,
            '/left': self.conversation.left,
            '/right': self.conversation.right,
            '/root': self.conversation.root,
            '/label': self.conversation.label,
            '/goto': self.conversation.goto,
            '/showlabels': self.conversation.showlabels,
            '/auto': self.system.auto,
            '/fp': self.fp.execute,
        }
    def run(self):
        """Main CLI loop."""
        try:
            self.context.old_terminal_settings = setup_raw_mode()
            # Initialize bot
            bot = AnthropicBot()
            bot.add_tools(
                bots.tools.terminal_tools,
                bots.tools.code_tools.view_dir,
                bots.tools.python_execution_tool,
            )
            print("CLI started. Type /help for commands or chat normally.")
            pretty(f"Bot initialized: {bot.name}", "System")
            while True:
                try:
                    user_input = input(">>> ").strip()
                    if user_input == '/exit':
                                raise SystemExit(0)
                    # Parse input for commands at start or end (like auto_terminal.py)
                    if not user_input:
                        continue
                    words = user_input.split()
                    if not words:
                        continue
                    # Check for command at start or end
                    command = None
                    msg = None
                    if words[0].startswith('/'):
                        command = words[0]
                        msg = ' '.join(words[1:]) if len(words) > 1 else None
                    elif words[-1].startswith('/'):
                        command = words[-1]
                        msg = ' '.join(words[:-1]) if len(words) > 1 else None
                    else:
                        msg = user_input
                    # Handle the input
                    if command:
                        if msg:
                            # Command with message - handle chat first, then command
                            self._handle_chat(bot, msg)
                        # Handle the command (pass the full command string for compatibility)
                        self._handle_command(bot, command)
                    else:
                        # Regular chat
                        self._handle_chat(bot, user_input)
                except KeyboardInterrupt:
                    print("\nUse /exit to quit")
                except EOFError:
                    break
                except Exception as e:
                    print(f"Error: {str(e)}")
                    if self.context.conversation_backup:
                        bot.conversation = self.context.conversation_backup
                        print("Restored conversation from backup")
        finally:
            restore_terminal(self.context.old_terminal_settings)
            print("Goodbye!")
    def _handle_command(self, bot: Bot, user_input: str):
        """Handle command input."""
        parts = user_input.split()
        command = parts[0]
        args = parts[1:] if len(parts) > 1 else []
        if command in self.commands:
            try:
                result = self.commands[command](bot, self.context, args)
                if result:
                    pretty(result, "System", self.context.config.width, self.context.config.indent)
                # Show bot response for navigation commands
                if command in ['/up', '/down', '/left', '/right', '/root', '/goto'] and bot.conversation:
                    pretty(bot.conversation.content, bot.name, self.context.config.width, self.context.config.indent)
            except Exception as e:
                pretty(f"Command error: {str(e)}", "Error", self.context.config.width, self.context.config.indent)
                if self.context.conversation_backup:
                    bot.conversation = self.context.conversation_backup
                    pretty("Restored conversation from backup", "System")
        else:
            pretty("Unrecognized command. Try /help.", "System", self.context.config.width, self.context.config.indent)

    def _handle_chat(self, bot: Bot, user_input: str):
        """Handle chat input."""
        if not user_input:
            return
        try:
            self.context.conversation_backup = bot.conversation
            response = bot.respond(user_input)
            pretty(response, bot.name, self.context.config.width, self.context.config.indent)
            # Show tool output if verbose
            display_tool_results(bot, self.context)
        except Exception as e:
            pretty(f"Chat error: {str(e)}", "Error", self.context.config.width, self.context.config.indent)
            if self.context.conversation_backup:
                bot.conversation = self.context.conversation_backup
                pretty("Restored conversation from backup", "System")
def main():
    """Entry point for the CLI."""
    cli = CLI()
    cli.run()
if __name__ == '__main__':
    main()


