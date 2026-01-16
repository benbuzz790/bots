"""Tools for managing the bot's tool system dynamically."""

import inspect
import os

from bots.dev.decorators import toolify


def _get_calling_bot():
    """Get the Bot instance that called the current tool."""
    frame = inspect.currentframe()
    try:
        while frame:
            frame = frame.f_back
            if frame and "self" in frame.f_locals:
                obj = frame.f_locals["self"]
                # Check if it's a Bot instance
                if hasattr(obj, "tool_handler") and hasattr(obj, "respond"):
                    return obj
    finally:
        del frame
    return None


@toolify()
def view_tools(filter: str = "") -> str:
    """View available tools that can be loaded.

    Shows tools in the registry that can be loaded with load_tools().

    Parameters:
        filter (str): Optional filter string to search tool names/descriptions

    Returns:
        str: List of available tools with their status and descriptions
    """
    bot = _get_calling_bot()
    if not bot or not bot.tool_handler:
        return "Error: Could not access tool handler"

    registry_info = bot.tool_handler.get_registry_info(filter)

    if not registry_info:
        return "No tools found in registry" + (f" matching '{filter}'" if filter else "")

    lines = ["Available Tools:", "=" * 60]
    for info in registry_info:
        status = "✓ LOADED" if info["loaded"] else "○ available"
        lines.append(f"\n{status} {info['name']}")
        if info.get("description"):
            lines.append(f"  {info['description']}")

    return "\n".join(lines)


@toolify()
def load_tools(tool_names: str) -> str:
    """Load specific tools to make them available for use.

    Only tools in the registry can be loaded. Use view_tools() to see available tools.

    Parameters:
        tool_names (str): Comma-separated list of tool names to load
                         Example: "view_file,python_edit,execute_python"

    Returns:
        str: Confirmation of loaded tools or error messages
    """
    bot = _get_calling_bot()
    if not bot or not bot.tool_handler:
        return "Error: Could not access tool handler"

    # Parse tool names
    names = [n.strip() for n in tool_names.split(",") if n.strip()]
    if not names:
        return "Error: No tool names provided"

    results = []
    for name in names:
        if bot.tool_handler.load_tool_by_name(name):
            results.append(f"✓ Loaded: {name}")
        else:
            results.append(f"✗ Failed: {name} (not in registry)")

    return "\n".join(results)


@toolify()
def load_code(code_or_filename: str) -> str:
    """Load a new tool from code string or filename.

    Adds the tool to the active tools immediately.

    Parameters:
        code_or_filename (str): Either Python code defining a function,
                               or a filepath to a .py file

    Returns:
        str: Confirmation of loaded tool(s) or error messages
    """
    bot = _get_calling_bot()
    if not bot or not bot.tool_handler:
        return "Error: Could not access tool handler"

    # Check if it's a file path
    if os.path.isfile(code_or_filename):
        try:
            bot.tool_handler._add_tools_from_file(code_or_filename)
            return f"Successfully loaded tools from {code_or_filename}"
        except Exception as e:
            return f"Error loading file: {str(e)}"

    # Treat as code string
    try:
        # Create a temporary module and execute the code
        import types

        temp_module = types.ModuleType("temp_tool_module")
        exec(code_or_filename, temp_module.__dict__)

        # Find functions in the module
        loaded = []
        for name, obj in temp_module.__dict__.items():
            if callable(obj) and not name.startswith("_"):
                bot.tool_handler.add_tool(obj)
                loaded.append(name)

        if loaded:
            return f"Successfully loaded: {', '.join(loaded)}"
        else:
            return "No functions found in provided code"

    except Exception as e:
        return f"Error executing code: {str(e)}"
