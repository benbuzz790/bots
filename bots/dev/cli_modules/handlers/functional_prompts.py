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
        self.function_filter = function_filter

    def _format_default_value(self, default: Any) -> str:
        """Format default value for display."""
        if default == inspect.Parameter.empty:
            return "required"
        elif default is None:
            return "None"
        elif isinstance(default, str):
            return f'"{default}"'
        else:
            return str(default)

    def collect_parameters(self, func: Callable) -> Optional[Dict[str, Any]]:
        """Collect parameters for a functional prompt function."""
        sig = inspect.signature(func)
        params = {}
        callback_type = "list"  # Default callback type

        for param_name, param in sig.parameters.items():
            if param_name == "bot":
                continue  # Skip bot parameter

            # Determine parameter type and collect accordingly
            if param_name in ["prompts", "prompt_list"]:
                value = self._collect_prompts(param_name, param.default)
            elif param_name == "prompt":
                value = self._collect_single_prompt(param_name, param.default)
            elif param_name == "stop_condition":
                value = self._collect_condition(param_name, param.default)
            elif param_name == "continue_prompt":
                value = self._collect_continue_prompt(param_name, param.default)
            elif param_name == "should_branch":
                value = self._collect_boolean(param_name, param.default)
            elif param_name == "skip":
                value = self._collect_skip_labels(param_name, param.default)
            elif param_name == "recombinator_function":
                value = self._collect_recombinator(param_name, param.default)
            elif param_name == "items":
                value = self._collect_items(param_name, param.default)
            elif param_name == "dynamic_prompt":
                value = self._collect_dynamic_prompt(param_name, param.default)
            elif param_name == "functional_prompt":
                value = self._collect_functional_prompt(param_name, param.default)
            elif param_name == "callback":
                # Skip callback - we'll handle it separately
                continue
            else:
                value = self._collect_generic_parameter(param_name, param.default)

            if value is None and param.default == inspect.Parameter.empty:
                return None  # Required parameter not provided

            if value is not None:
                params[param_name] = value

        # Store callback type for later use
        params["_callback_type"] = callback_type

        return params

    def _collect_prompts(self, param_name: str, default: Any) -> Optional[List[str]]:
        """Collect a list of prompts."""
        print(f"\nEnter prompts for {param_name} (one per line, empty line to finish):")
        prompts = []
        while True:
            try:
                prompt = input_with_esc(f"  Prompt {len(prompts) + 1}: ")
                if not prompt:
                    break
                prompts.append(prompt)
            except EscapeException:
                return None
        return prompts if prompts else default

    def _collect_single_prompt(self, param_name: str, default: Any) -> Optional[str]:
        """Collect a single prompt."""
        try:
            default_display = self._format_default_value(default)
            prompt = input_with_esc(f"Enter {param_name} (default: {default_display}): ")
            return prompt if prompt else default
        except EscapeException:
            return None

    def _collect_condition(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect a stop condition."""
        print(f"\nAvailable conditions for {param_name}:")
        conditions_list = [
            ("tool_not_used", fp.conditions.tool_not_used),
            ("said_DONE", fp.conditions.said_DONE),
            ("said_READY", fp.conditions.said_READY),
        ]
        for i, (name, _) in enumerate(conditions_list, 1):
            print(f"  {i}. {name}")

        try:
            choice = input_with_esc("Select condition (number or name, or press Enter for default): ")
            if not choice:
                return default if default != inspect.Parameter.empty else fp.conditions.tool_not_used

            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(conditions_list):
                    return conditions_list[idx][1]
            else:
                for name, cond in conditions_list:
                    if name.lower() == choice.lower():
                        return cond
            return default if default != inspect.Parameter.empty else fp.conditions.tool_not_used
        except EscapeException:
            return None

    def _collect_continue_prompt(self, param_name: str, default: Any) -> Optional[str]:
        """Collect a continue prompt."""
        try:
            default_display = self._format_default_value(default)
            prompt = input_with_esc(f"Enter {param_name} (default: {default_display}): ")
            return prompt if prompt else (default if default != inspect.Parameter.empty else "ok")
        except EscapeException:
            return None

    def _collect_boolean(self, param_name: str, default: Any) -> Optional[bool]:
        """Collect a boolean value."""
        try:
            default_display = self._format_default_value(default)
            value = input_with_esc(f"Enter {param_name} (true/false, default: {default_display}): ")
            if not value:
                return default if default != inspect.Parameter.empty else False
            return value.lower() in ("true", "yes", "1", "t", "y")
        except EscapeException:
            return None

    def _collect_skip_labels(self, param_name: str, default: Any) -> List[str]:
        """Collect skip labels."""
        try:
            labels_str = input_with_esc(f"Enter {param_name} (comma-separated, or press Enter to skip): ")
            if not labels_str:
                return default if default != inspect.Parameter.empty else []
            return [label.strip() for label in labels_str.split(",")]
        except EscapeException:
            return []

    def _collect_recombinator(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect a recombinator function."""
        print(f"\nAvailable recombinators for {param_name}:")
        recombinator_list = [
            ("concatenate", recombinators.recombinators.concatenate),
            ("llm_judge", recombinators.recombinators.llm_judge),
            ("llm_vote", recombinators.recombinators.llm_vote),
            ("llm_merge", recombinators.recombinators.llm_merge),
        ]
        for i, (name, _) in enumerate(recombinator_list, 1):
            print(f"  {i}. {name}")

        try:
            choice = input_with_esc("Select recombinator (number or name): ")
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(recombinator_list):
                    return recombinator_list[idx][1]
            else:
                for name, recom in recombinator_list:
                    if name.lower() == choice.lower():
                        return recom
            return default if default != inspect.Parameter.empty else None
        except EscapeException:
            return None

    def _collect_items(self, param_name: str, default: Any) -> Optional[List[Any]]:
        """Collect a list of items."""
        print(f"\nEnter items for {param_name} (one per line, empty line to finish):")
        items = []
        while True:
            try:
                item = input_with_esc(f"  Item {len(items) + 1}: ")
                if not item:
                    break
                items.append(item)
            except EscapeException:
                return None
        return items if items else default

    def _collect_dynamic_prompt(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect a dynamic prompt function."""
        # For now, return a simple lambda that returns the item as-is
        print(f"\nUsing default dynamic prompt for {param_name} (returns item as prompt)")
        return lambda item: str(item)

    def _collect_functional_prompt(self, param_name: str, default: Any) -> Optional[Callable]:
        """Collect a functional prompt function."""
        print(f"\nAvailable functional prompts for {param_name}:")
        fp_list = [
            ("single_prompt", fp.single_prompt),
            ("chain", fp.chain),
            ("branch", fp.branch),
        ]
        for i, (name, _) in enumerate(fp_list, 1):
            print(f"  {i}. {name}")

        try:
            choice = input_with_esc("Select functional prompt (number or name): ")
            if choice.isdigit():
                idx = int(choice) - 1
                if 0 <= idx < len(fp_list):
                    return fp_list[idx][1]
            else:
                for name, func in fp_list:
                    if name.lower() == choice.lower():
                        return func
            return default if default != inspect.Parameter.empty else fp.single_prompt
        except EscapeException:
            return None

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
        self.collector = DynamicParameterCollector(function_filter=function_filter)
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
                                pretty(
                                    f"Tool Results\n\n{tool_results_str}",
                                    "system",
                                    context.config.width,
                                    context.config.indent,
                                    COLOR_TOOL_RESULT,
                                )

                    params["callback"] = single_callback
                else:
                    params["callback"] = context.callbacks.get_standard_callback()

            fp_function(bot, **params)
            return f"Executed {fp_name} successfully"
        except Exception as e:
            return f"Error executing functional prompt: {str(e)}"

    def broadcast_fp(self, bot: Bot, context: CLIContext, args: List[str]) -> str:
        """Execute functional prompts on all leaf nodes."""
        try:
            # Find all leaves using the imported function
            leaves = find_leaves(bot.conversation)
            if not leaves:
                return "No leaves found from current node"

            # Get skip labels if provided
            skip_labels = []
            if args and args[0] == "--skip":
                skip_labels = args[1:]

            # Filter leaves by skip labels
            target_leaves = []
            for leaf in leaves:
                should_skip = False
                if hasattr(leaf, "labels"):
                    for label in leaf.labels:
                        if label in skip_labels:
                            should_skip = True
                            break
                if not should_skip:
                    target_leaves.append(leaf)

            if not target_leaves:
                return "No leaves remaining after filtering by skip labels"

            print(f"\nFound {len(target_leaves)} leaf nodes to broadcast to")

            # Show available functional prompts
            print("\nAvailable functional prompts:")
            fp_options = list(self.fp_functions.items())
            for i, (name, _) in enumerate(fp_options, 1):
                print(f"  {i}. {name}")

            # Get user selection
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

            # Pop the callback type and select appropriate callback
            _callback_type = params.pop("_callback_type", "list")

            # Check if the function accepts a callback parameter
            sig = inspect.signature(fp_func)
            accepts_callback = "callback" in sig.parameters

            if accepts_callback:
                if _callback_type == "single":
                    callback = context.callbacks.get_single_callback()
                else:
                    callback = context.callbacks.get_standard_callback()
            else:
                callback = None

            print(f"\nBroadcasting {fp_name} to {len(target_leaves)} leaves...")

            # Call broadcast_fp with cleaned params
            if callback is not None:
                responses, nodes = fp.broadcast_fp(
                    bot=bot, leaves=target_leaves, functional_prompt=fp_func, callback=callback, **params
                )
            else:
                responses, nodes = fp.broadcast_fp(bot=bot, leaves=target_leaves, functional_prompt=fp_func, **params)

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
