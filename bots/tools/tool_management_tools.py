"""Tools for managing the bot's tool system dynamically."""

import inspect
import os
from typing import Optional

from bots.dev.decorators import toolify
from bots.foundation.base import Bot


@toolify()
def view_tools(filter: str = "", verbose: bool = False, _bot: Optional[Bot] = None) -> str:
    """View available tools that can be loaded.

    Shows tools in the registry that can be loaded with load_tools().

    Parameters:
        filter (str): Optional filter string to search tool names/descriptions
        verbose (bool): If True, show descriptions. If False, show only signatures. Default False.

    Returns:
        str: List of available tools with their status and optionally descriptions
    """
    if not _bot or not _bot.tool_handler:
        return "Error: Could not access tool handler"

    registry_info = _bot.tool_handler.get_registry_info(filter)
    if not registry_info:
        return "No tools found in registry" + (f" matching '{filter}'" if filter else "")

    lines = ["Available Tools:", "=" * 60]
    for info in registry_info:
        status = "✓ LOADED" if info["loaded"] else "○ available"

        # Get function signature if available
        tool_name = info["name"]
        signature = tool_name + "()"  # Default

        # Try to get actual signature from the registry
        if _bot.tool_handler.tool_registry.get(tool_name):
            func = _bot.tool_handler.tool_registry[tool_name].get("function")
            if func and callable(func):
                try:
                    sig = inspect.signature(func)
                    signature = f"{tool_name}{sig}"
                except (ValueError, TypeError):
                    pass

        lines.append(f"\n{status} {signature}")

        if verbose and info.get("description"):
            lines.append(f"  {info['description']}")

    return "\n".join(lines)


@toolify()
def load_tools(tool_names: str, _bot: Optional[Bot] = None) -> str:
    """Load specific tools to make them available for use.

    Only tools in the registry can be loaded. Use view_tools() to see available tools.

    Parameters:
        tool_names (str): Comma-separated list of tool names to load
                         Example: "view_file,python_edit,execute_python"

    Returns:
        str: Confirmation of loaded tools or error messages
    """
    if not _bot or not _bot.tool_handler:
        return "Error: Could not access tool handler"

    # Parse tool names
    names = [n.strip() for n in tool_names.split(",") if n.strip()]
    if not names:
        return "Error: No tool names provided"

    results = []
    for name in names:
        if _bot.tool_handler.load_tool_by_name(name):
            results.append(f"✓ Loaded: {name}")
        else:
            results.append(f"✗ Failed: {name} (not in registry)")

    return "\n".join(results)


@toolify()
def load_code(code_or_filename: str, _bot: Optional[Bot] = None) -> str:
    """Load a new tool from code string or filename.

    **SECURITY WARNING**: This function uses exec() to execute arbitrary Python code
    with FULL Python capabilities. Only use with completely trusted code sources.

    Executing untrusted code can:
    - Execute arbitrary system commands
    - Access or modify any files
    - Exfiltrate sensitive data
    - Compromise the entire runtime environment
    - Install malware or backdoors

    DO NOT use this function with code from untrusted sources. There are no
    sandboxing restrictions - the code has full access to the Python runtime.

    Adds the tool to the active tools immediately.

    Parameters:
        code_or_filename (str): Either Python code defining a function,
                               or a filepath to a .py file

    Returns:
        str: Confirmation of loaded tool(s) or error messages
    """
    import types
    import warnings

    if not _bot or not _bot.tool_handler:
        return "Error: Could not access tool handler"

    # Check if it's a file path
    if os.path.isfile(code_or_filename):
        try:
            _bot.tool_handler._add_tools_from_file(code_or_filename)
            return f"Successfully loaded tools from {code_or_filename}"
        except Exception as e:
            return f"Error loading file: {str(e)}"

    # Treat as code string - emit security warning
    warnings.warn(
        "load_code() is executing arbitrary code via exec() with full Python capabilities. "
        "This poses serious security risks if the code is untrusted.",
        RuntimeWarning,
        stacklevel=2,
    )

    try:
        # Create a temporary module and execute the code with full Python access
        temp_module = types.ModuleType("temp_tool_module")

        # Execute code in the module's namespace (unrestricted)
        exec(code_or_filename, temp_module.__dict__)

        # Find functions in the executed namespace
        loaded = []
        for name, obj in temp_module.__dict__.items():
            if callable(obj) and not name.startswith("_"):
                _bot.tool_handler.add_tool(obj)
                loaded.append(name)

        if loaded:
            return f"Successfully loaded: {', '.join(loaded)}"
        else:
            return "No functions found in provided code"

    except Exception as e:
        return f"Error executing code: {str(e)}"
