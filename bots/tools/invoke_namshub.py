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

    DEPRECATED: This function uses stack introspection which is fragile.
    New tools should use the _bot parameter instead, which is automatically
    injected by ToolHandler.exec_requests().

    This function is kept for backward compatibility only.

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
def invoke_namshub(namshub_name: str, kwargs: str = "{}", _bot: Optional[Bot] = None) -> str:
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

    # Try injected bot first, fallback to deprecated method
    bot = _bot if _bot is not None else _get_calling_bot()
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
        namshub_files = [f for f in os.listdir(namshub_name) if f.endswith(".py") and not f.startswith("_")]
        if not namshub_files:
            return f"No namshub files found in directory: {namshub_name}"

        # Return list of available namshubs
        namshub_list = "\n".join([f"  - {f}" for f in sorted(namshub_files)])
        return f"Available namshubs in {namshub_name}:\n{namshub_list}\n\nUse invoke_namshub with a specific file path to execute one."

    # It's a file path, try to load and execute
    if not os.path.isfile(namshub_name):
        return f"Error: Namshub file not found: {namshub_name}"

    try:
        # Load the namshub module
        spec = importlib.util.spec_from_file_location("namshub_module", namshub_name)
        if spec is None or spec.loader is None:
            return f"Error: Could not load namshub from {namshub_name}"

        namshub_module = importlib.util.module_from_spec(spec)
        spec.loader.exec_module(namshub_module)

        # Look for the invoke function
        if not hasattr(namshub_module, "invoke"):
            return f"Error: Namshub {namshub_name} does not have an 'invoke' function"

        invoke_func = namshub_module.invoke

        # Save bot state before invoking namshub
        original_system_message = bot.system_message
        original_tools = bot.tool_handler.tools.copy()
        original_function_map = bot.tool_handler.function_map.copy()

        try:
            # Invoke the namshub with the bot and kwargs
            result = invoke_func(bot, **kwargs_dict)

            # Return the result
            return f"Namshub execution completed.\n\nResult:\n{result}"

        finally:
            # Restore bot state
            bot.system_message = original_system_message
            bot.tool_handler.tools = original_tools
            bot.tool_handler.function_map = original_function_map

    except Exception as e:
        import traceback

        error_trace = traceback.format_exc()
        return f"Error executing namshub {namshub_name}:\n{str(e)}\n\nTraceback:\n{error_trace}"
