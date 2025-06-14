import sys
import json
import os
import re
import platform
import argparse
import inspect
from datetime import datetime
from typing import Optional, List, Dict, Any, Callable, Tuple, get_type_hints, get_origin, get_args
import textwrap
from bots.foundation.openai_bots import ChatGPT_Bot
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode
import bots.tools.python_edit
import bots.tools.terminal_tools
import bots.tools.code_tools
import bots.flows.functional_prompts as fp
"""
Modern CLI with dynamic parameter collection for functional prompts.
This version uses function introspection to automatically handle parameter collection
for any functional prompt, eliminating hardcoded parameter logic.
"""
# Import platform-specific modules
if platform.system() == 'Windows':
    import msvcrt
else:
    import select
    import termios
    import tty

class DynamicParameterCollector:
    """Dynamically collect parameters for functional prompts based on their signatures."""

    def __init__(self):
        # Map parameter names to collection methods
        self.param_handlers = {'prompt_list': self._collect_prompts, 'prompts': self._collect_prompts, 'prompt': self._collect_single_prompt, 'first_prompt': self._collect_single_prompt, 'stop_condition': self._collect_condition, 'continue_prompt': self._collect_continue_prompt, 'recombinator_function': self._collect_recombinator, 'should_branch': self._collect_boolean, 'skip': self._collect_skip_labels, 'items': self._collect_items, 'dynamic_prompt': self._collect_dynamic_prompt}
        # Available conditions for user selection
        self.conditions = {'1': ('tool_used', fp.conditions.tool_used), '2': ('tool_not_used', fp.conditions.tool_not_used), '3': ('said_DONE', fp.conditions.said_DONE)}

    def collect_parameters(self, func: Callable) -> Optional[Dict[str, Any]]:
        """Dynamically collect parameters based on function signature."""
        try:
            sig = inspect.signature(func)
            params = {}
            print(f"\nCollecting parameters for {func.__name__}:")
            for param_name, param in sig.parameters.items():
                # Skip bot parameter - we'll provide this
                if param_name == 'bot':
                    continue
                # Skip callback parameter - we'll inject this automatically
                if param_name == 'callback':
                    continue
                print(f"  Parameter: {param_name} (default: {param.default})")
                # Use specific handler if available
                if param_name in self.param_handlers:
                    handler = self.param_handlers[param_name]
                    value = handler(param_name, param.default)
                else:
                    # Generic handler based on type
                    value = self._collect_generic_parameter(param_name, param.default)
                # Handle required vs optional parameters
                if value is None:
                    if param.default == inspect.Parameter.empty:
                        print(f"Required parameter '{param_name}' not provided")
                        return None
                    # Use default value for optional parameters
                elif value is not None:
                    params[param_name] = value
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
        choice = input("Select condition (or press enter for default): ").strip()
        if not choice and default != inspect.Parameter.empty:
            return default
        elif choice in self.conditions:
            return self.conditions[choice][1]
        else:
            print("Invalid condition selection")
            return None

    def _collect_continue_prompt(self, param_name: str, default: Any) -> Optional[str]:
        """Collect continue prompt with default handling."""
        if default != inspect.Parameter.empty:
            prompt = input(f"Enter {param_name} (default: '{default}'): ").strip()
            return prompt if prompt else default
        else:
            prompt = input(f"Enter {param_name}: ").strip()
            return prompt if prompt else None

    def _collect_boolean(self, param_name: str, default: Any) -> Optional[bool]:
        """Collect boolean parameter."""
        default_str = str(default) if default != inspect.Parameter.empty else "False"
        choice = input(f"Enter {param_name} (y/n, default: {default_str}): ").strip().lower()
        if not choice and default != inspect.Parameter.empty:
            return default
        elif choice in ['y', 'yes', 'true', '1']:
            return True
        elif choice in ['n', 'no', 'false', '0']:
            return False
        else:
            return default if default != inspect.Parameter.empty else False

    def _collect_skip_labels(self, param_name: str, default: Any) -> List[str]:
        """Collect skip labels for broadcast functions."""
        skip_input = input(f'Enter {param_name} (comma-separated, or empty for none): ').strip()
        if skip_input:
            return [label.strip() for label in skip_input.split(',')]
        else:
            return []

    def _collect_recombinator(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect recombinator function (simplified for now)."""
        choice = input(f"Use default recombinator for {param_name}? (y/n): ").strip().lower()
        if choice == 'y':
            return fp.recombinators.simple_concatenate if hasattr(fp, 'recombinators') else None
        return None

    def _collect_items(self, param_name: str, default: Any) -> Optional[List[Any]]:
        """Collect items for prompt_for function."""
        print("prompt_for requires a list of items - this is an advanced feature")
        print("Not yet implemented in this interface")
        return None

    def _collect_dynamic_prompt(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect dynamic prompt function."""
        print("dynamic_prompt requires a function - this is an advanced feature")
        print("Not yet implemented in this interface")
        return None

    def _collect_generic_parameter(self, param_name: str, default: Any) -> Optional[Any]:
        """Generic parameter collection for unknown parameter types."""
        if default != inspect.Parameter.empty:
            value = input(f"Enter {param_name} (default: {default}): ").strip()
            return value if value else default
        else:
            value = input(f"Enter {param_name}: ").strip()
            return value if value else None

class DynamicFunctionalPromptHandler:
    """Handler for functional prompt commands using dynamic parameter collection."""

    def __init__(self):
        self.collector = DynamicParameterCollector()
        # Automatically discover all functional prompt functions
        self.fp_functions = self._discover_fp_functions()

    def _discover_fp_functions(self) -> Dict[str, Callable]:
        """Automatically discover functional prompt functions from the fp module."""
        functions = {}
        # Get all functions from the fp module
        for name in dir(fp):
            obj = getattr(fp, name)
            if callable(obj) and (not name.startswith('_')):
                # Check if it looks like a functional prompt (takes bot as first param)
                try:
                    sig = inspect.signature(obj)
                    params = list(sig.parameters.keys())
                    if params and params[0] == 'bot':
                        functions[name] = obj
                except:
                    continue  # Skip if we can't inspect the signature
        return functions

    def execute(self, bot: Bot, context, args: List[str]) -> str:
        """Execute functional prompt wizard with dynamic parameter collection."""
        try:
            # Step 1: Choose functional prompt type
            print("\nAvailable functional prompts:")
            func_names = list(self.fp_functions.keys())
            for i, name in enumerate(func_names, 1):
                print(f"  {i}. {name}")
            choice = input("\nSelect functional prompt (number or name): ").strip()
            # Parse choice
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
            # Step 2: Dynamically collect parameters
            params = self.collector.collect_parameters(fp_function)
            if params is None:
                return "Parameter collection cancelled"
            # Step 3: Execute functional prompt
            context.conversation_backup = bot.conversation
            print(f"\nExecuting {fp_name}...")
            # Create callback for immediate tool result printing
            callback = create_tool_result_callback(context)
            params['callback'] = callback
            # Execute the function
            result = fp_function(bot, **params)
            # Handle results and display responses
            if isinstance(result, tuple) and len(result) == 2:
                responses, nodes = result
                # Handle both single response and list of responses
                if isinstance(responses, list):
                    for i, response in enumerate(responses):
                        if response:
                            pretty(f"Response {i+1}: {response}", bot.name, context.config.width, context.config.indent)
                    return f"Functional prompt '{fp_name}' completed with {len(responses)} responses"
                else:
                    if responses:
                        pretty(responses, bot.name, context.config.width, context.config.indent)
                    return f"Functional prompt '{fp_name}' completed"
            else:
                return f"Functional prompt '{fp_name}' completed with result: {result}"
        except Exception as e:
            return f"Error executing functional prompt: {str(e)}"

def create_tool_result_callback(context):
    """Create a callback function that prints tool results immediately."""

    def tool_result_callback(responses, nodes):
        # Print tool results for the most recent response
        if hasattr(context, 'bot_instance') and context.bot_instance:
            bot = context.bot_instance
            requests = bot.tool_handler.requests
            results = bot.tool_handler.results
            if requests and context.config.verbose:
                request_str = ''.join((clean_dict(r) for r in requests))
                result_str = ''.join((clean_dict(r) for r in results))
                pretty(f'Tool Requests\n\n{request_str}', "System", context.config.width, context.config.indent)
                if result_str.strip():
                    pretty(f'Tool Results\n\n{result_str}', "System", context.config.width, context.config.indent)
    return tool_result_callback

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
            config_data = {'verbose': self.verbose, 'width': self.width, 'indent': self.indent}
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
        self.bot_instance = None
        self.cached_leaves: List[ConversationNode] = []
class CLI2:
   """Main CLI class that orchestrates all handlers with dynamic parameter collection."""

   def __init__(self, bot_filename: Optional[str] = None):
       self.context = CLIContext()
       self.fp = DynamicFunctionalPromptHandler()
       self.bot_filename = bot_filename
        
       # Command registry (simplified for now)
       self.commands = {
           '/fp': self.fp.execute,
       }

   def run(self):
       """Main CLI loop."""
       try:
           print("Hello, world! CLI2 with Dynamic Parameter Collection")
            
           # Initialize bot
           self._initialize_new_bot()
            
           print("CLI2 started. Type /fp to test functional prompts or /exit to quit.")
            
           while True:
               try:
                   user_input = input(">>> ").strip()
                   if user_input == '/exit':
                       raise SystemExit(0)
                    
                   if not user_input:
                       continue
                    
                   if user_input.startswith('/fp'):
                       self._handle_command(self.context.bot_instance, user_input)
                   else:
                       self._handle_chat(self.context.bot_instance, user_input)
                        
               except KeyboardInterrupt:
                   print("\nUse /exit to quit")
               except EOFError:
                   break
               except Exception as e:
                   print(f"Error: {str(e)}")
       finally:
           print("Goodbye!")

   def _initialize_new_bot(self):
       """Initialize a new bot with default tools."""
       bot = AnthropicBot(allow_web_search=True)
       self.context.bot_instance = bot
       bot.add_tools(
           bots.tools.terminal_tools,
           bots.tools.python_edit,
           bots.tools.code_tools
       )

   def _handle_command(self, bot: Bot, user_input: str):
       """Handle command input."""
       if user_input.startswith('/fp'):
           result = self.fp.execute(bot, self.context, [])
           if result:
               pretty(result, "System", self.context.config.width, self.context.config.indent)

   def _handle_chat(self, bot: Bot, user_input: str):
       """Handle chat input."""
       callback = create_tool_result_callback(self.context)
       responses, nodes = fp.chain(bot, [user_input], callback=callback)
       if responses:
           pretty(responses[0], bot.name, self.context.config.width, self.context.config.indent)


def clean_dict(d: dict, indent: int=4, level: int=1):
    """Clean a dict containing recursive json dumped strings for printing"""
    for k, v in d.items():
        if isinstance(v, dict):
            clean_dict(v, indent, level + 1)
        if isinstance(v, str) and '\n' in v:
            lines = v.splitlines()
            for i, line in enumerate(lines):
                line = ' ' * indent * (level + 1) + line
                if i == 0:
                    line = '\n' + line
                lines[i] = line
            d[k] = '\n'.join(lines)
    cleaned_dict = json.dumps(d, indent=indent * level)
    cleaned_dict = re.sub('(?<!\\)\\n', '\n', cleaned_dict)
    cleaned_dict = cleaned_dict.replace('\\"', '"')
    cleaned_dict = cleaned_dict.replace('\\\\', '\\')
    return cleaned_dict

def pretty(string: str, name: Optional[str]=None, width: int=1000, indent: int=4) -> None:
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
            wrapped = textwrap.wrap(line, width=width, initial_indent=' ' * indent, subsequent_indent=' ' * indent)
        if wrapped:
            formatted_lines.extend(wrapped)
        else:
            formatted_lines.append(' ' * indent if i > 0 else prefix)
    for line in formatted_lines:
        print(line)

def main():
    """Simple test entry point."""
    print("CLI2 with Dynamic Parameter Collection")
    # Create a test bot
    bot = AnthropicBot(allow_web_search=True)
    bot.add_tools(bots.tools.terminal_tools, bots.tools.python_edit, bots.tools.code_tools)
    # Create context
    context = CLIContext()
    context.bot_instance = bot
    # Create handler
    handler = DynamicFunctionalPromptHandler()
    print(f"Discovered {len(handler.fp_functions)} functional prompt functions:")
    for name in handler.fp_functions.keys():
        print(f"  - {name}")
    # Test parameter collection for a simple function
    print("\n" + "=" * 50)
    print("Testing parameter collection for 'chain' function:")
    try:
        params = handler.collector.collect_parameters(fp.chain)
        print(f"Collected parameters: {params}")
    except Exception as e:
        print(f"Error: {e}")
if __name__ == '__main__':
    main()
