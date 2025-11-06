"""Tool for invoking namshubs on the calling bot.

A namshub is a specialized workflow module that can be invoked on a bot to
execute a specific task or transformation. This tool allows bots to dynamically
load and execute namshubs on themselves.
"""

import importlib.util
import inspect
import os
from typing import Optional

from bots.dev.decorators import toolify
from bots.foundation.base import Bot


def _get_calling_bot() -> Optional[Bot]:
    """Helper function to get a reference to the calling bot.

    Returns:
        Optional[Bot]: Reference to the calling bot or None if not found
    """
    frame = inspect.currentframe()
    while frame:
        if frame.f_code.co_name == "_cvsn_respond" and "self" in frame.f_locals:
            potential_bot = frame.f_locals["self"]
            if isinstance(potential_bot, Bot):
                return potential_bot
        frame = frame.f_back
    return None


@toolify()
def invoke_namshub(namshub_name: str, kwargs: str = "{}") -> str:
    """Invoke a namshub workflow on yourself.

    A namshub is a specialized workflow that can modify your system prompt,
    temporarily replace your toolkit, and guide you through a specific task
    using functional prompts.

    Use when you need to:
    - Execute a specialized workflow (e.g., code review, documentation, testing)
    - Temporarily adopt a different role or capability set
    - Follow a structured multi-step process

    Parameters:
        namshub_name (str): Filepath or directory to a namshub file.
                           If a directory is provided, looks for namshub files in that directory.
                           If a file path is provided, loads directly from that path.
        kwargs (str): String representation of a dictionary containing keyword arguments
                     to pass to the namshub's invoke function. Default: "{}"
                     Example: '{"pr_number": "123"}' or '{"target_file": "main.py"}'

    Returns:
        str: Result of the namshub execution, including any responses or summaries

    Example:
        invoke_namshub("bots/namshubs/namshub_of_code_review.py", kwargs='{"target_file": "main.py"}')
        invoke_namshub("bots/namshubs/namshub_of_pull_requests.py", kwargs='{"pr_number": "123"}')
        invoke_namshub("bots/namshubs/")
    """
    import json

    bot = _get_calling_bot()
    if not bot:
        return "Error: Could not find calling bot"

    # Parse kwargs string into a dictionary
    try:
        kwargs_dict = json.loads(kwargs) if isinstance(kwargs, str) else kwargs
        if not isinstance(kwargs_dict, dict):
            return f"Error: kwargs must be a dictionary, got {type(kwargs_dict).__name__}"
    except json.JSONDecodeError as e:
        return f"Error: Invalid JSON in kwargs parameter: {str(e)}"

    # Determine if namshub_name is a directory or filepath
    if os.path.isdir(namshub_name):
        # It's a directory, list available namshubs
        namshub_files = [
            f for f in os.listdir(namshub_name)
            if f.endswith(".py") and not f.startswith("_")
        ]
        if not namshub_files:
            return f"Error: No namshub files found in directory '{namshub_name}'"

        return (
            f"Directory '{namshub_name}' contains the following namshubs:\n" +
            "\n".join(f"- {f}" for f in sorted(namshub_files)) +
            "\n\nPlease specify the full path to the namshub file you want to invoke."
        )

    # It's a filepath
    namshub_path = namshub_name
    module_name = os.path.splitext(os.path.basename(namshub_name))[0]

    # Check if the namshub exists
    if not os.path.exists(namshub_path):
        return f"Error: Namshub file '{namshub_name}' not found."

    try:
        # Load the namshub module dynamically
        spec = importlib.util.spec_from_file_location(module_name, namshub_path)
        if spec is None or spec.loader is None:
            return f"Error: Could not load namshub '{namshub_name}'"

        namshub_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(namshub_module)

        # Look for the main invocation function (should be named 'invoke' or 'run')
        invoke_func = None
        for func_name in ["invoke", "run", "execute"]:
            if hasattr(namshub_module, func_name):
                invoke_func = getattr(namshub_module, func_name)
                break

        if invoke_func is None:
            return (
                f"Error: Namshub '{namshub_name}' does not have an 'invoke', 'run', "
                f"or 'execute' function"
            )

        # Handle tool_use without tool_result issue
        # If the current node has tool_calls (the invoke_namshub call itself),
        # we need to add a dummy result before the namshub executes bot.respond()
        # to avoid API errors
        current_node = bot.conversation
        dummy_results_added = False
        original_results = None

        if current_node.tool_calls:
            dummy_results = []
            for tool_call in current_node.tool_calls:
                if tool_call.get("name") == "invoke_namshub":
                    # Use bot's tool_handler to generate provider-appropriate format
                    dummy_result = bot.tool_handler.generate_response_schema(
                        tool_call, "Namshub invocation in progress..."
                    )
                    dummy_results.append(dummy_result)

            if dummy_results:
                # Temporarily add dummy results
                original_results = list(getattr(current_node, "tool_results", []))
                current_node._add_tool_results(dummy_results)
                dummy_results_added = True

        # Save the original bot state
        original_tool_handler = bot.tool_handler
        original_system_message = bot.system_message if hasattr(bot, 'system_message') else None

        try:
            # Execute the namshub with kwargs
            result = invoke_func(bot, **kwargs_dict)

            # Return the result
            if isinstance(result, tuple):
                # If it returns (response, node), just return the response
                return str(result[0]) if result[0] else "Namshub completed successfully"
            else:
                return str(result) if result else "Namshub completed successfully"

        finally:
            # Remove dummy results if we added them
            if dummy_results_added:
                current_node.tool_results = original_results

            # Restore the original bot state
            bot.tool_handler = original_tool_handler
            if original_system_message is not None:
                bot.set_system_message(original_system_message)

    except Exception as e:
        import traceback
        error_trace = traceback.format_exc()
        return (
            f"Error executing namshub '{namshub_name}':\n{str(e)}\n\n"
            f"Traceback:\n{error_trace}"
        )