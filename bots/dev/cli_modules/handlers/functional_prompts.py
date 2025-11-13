"""Functional prompt command handlers for the CLI."""

import inspect
from typing import Any, Callable, Dict, List, Optional

from bots.dev.cli_modules.config import CLIContext
from bots.dev.cli_modules.display import clean_dict, pretty
from bots.dev.cli_modules.utils import (
    COLOR_ASSISTANT,
    COLOR_TOOL_REQUEST,
    COLOR_TOOL_RESULT,
    EscapeException,
    find_leaves,
    input_with_esc,
)
from bots.flows import functional_prompts as fp
from bots.flows import recombinators
from bots.foundation.base import Bot


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
                                f"Response {i + 1}: {response}",
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
            leaves = find_leaves(bot.conversation)
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
