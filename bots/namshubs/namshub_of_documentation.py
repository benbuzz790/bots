"""Documentation namshub - generates or improves documentation for Python code.

This namshub transforms the bot into a documentation specialist that:
1. Analyzes Python files to understand their structure and purpose
2. Generates or improves docstrings for modules, classes, and functions
3. Ensures documentation follows Python standards (PEP 257)
4. Adds type hints where missing
5. Creates clear, comprehensive documentation

The bot is equipped with code viewing and editing tools to read and
modify Python files.
"""

from typing import Tuple

from bots.foundation.base import Bot, ConversationNode
from bots.namshubs.helpers import (
    chain_workflow,
    create_toolkit,
    format_final_summary,
    validate_required_params,
)
from bots.tools.code_tools import view, view_dir
from bots.tools.python_edit import python_edit, python_view


def _set_documentation_system_message(bot: Bot, target_file: str) -> None:
    """Set specialized system message for documentation generation.

    Parameters:
        bot (Bot): The bot to configure
        target_file (str): Path to the file being documented
    """
    system_message = f"""You are an expert technical writer specializing in Python documentation.

Your task: Generate or improve documentation for {target_file}

Documentation standards:

1. MODULE DOCSTRINGS
   - Clear one-line summary
   - Detailed description of module purpose
   - List of key classes/functions if applicable
   - Usage examples for complex modules

2. CLASS DOCSTRINGS
   - Purpose and behavior of the class
   - Key attributes with types
   - Usage examples
   - Inheritance information if relevant

3. FUNCTION/METHOD DOCSTRINGS
   - Clear description of what the function does
   - Parameters section with types and descriptions
   - Returns section with type and description
   - Raises section for exceptions
   - Examples for complex functions

4. TYPE HINTS
   - Add type hints to function signatures
   - Use typing module for complex types
   - Be specific: List[str] not just list

5. STYLE
   - Follow PEP 257 conventions
   - Use triple double-quotes for docstrings
   - First line is a brief summary (imperative mood)
   - Blank line before detailed description
   - Be clear and concise

Use python_edit to add or improve documentation directly in the file.
"""
    bot.set_system_message(system_message.strip())


def invoke(bot: Bot, target_file: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the documentation generation namshub.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        target_file (str, optional): Path to the Python file to document.
                                     If not provided, attempts to extract from conversation.
        **kwargs: Additional parameters (unused, for compatibility)

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # If target_file not provided, try to extract from conversation context
    if not target_file:
        if bot.conversation.parent and bot.conversation.parent.content:
            content = bot.conversation.parent.content
            import re

            py_files = re.findall(r"[\w/\\.-]+\.py", content)
            if py_files:
                target_file = py_files[0]

    # Validate required parameters
    valid, error = validate_required_params(target_file=target_file)
    if not valid:
        return (error + "\nUsage: invoke_namshub('namshub_of_documentation', target_file='path/to/file.py')", bot.conversation)

    # Configure the bot for documentation
    create_toolkit(bot, view, view_dir, python_view, python_edit)
    _set_documentation_system_message(bot, target_file)

    # Define the documentation workflow
    workflow_prompts = [
        f"Read and analyze the target file: {target_file}. Use python_view to understand "
        "its structure, purpose, and existing documentation.",
        "Check the module-level docstring. If missing or inadequate, add or improve it. "
        "Include a clear summary and description of the module's purpose.",
        "Review all classes in the file. For each class, ensure it has a comprehensive "
        "docstring explaining its purpose, key attributes, and usage. Add or improve as needed.",
        "Review all functions and methods. Ensure each has a docstring with description, "
        "parameters, return value, and exceptions. Add type hints if missing.",
        "Do a final review of the documentation. Ensure consistency, clarity, and completeness. "
        "Check that all docstrings follow PEP 257 conventions.",
        f"Verify your changes. Use python_view to review the updated {target_file} and "
        "confirm all documentation is in place.",
    ]

    # Execute the workflow using chain_workflow with INSTRUCTION pattern
    responses, nodes = chain_workflow(bot, workflow_prompts)

    # Return the final response
    final_summary = format_final_summary("Documentation", len(responses), responses[-1])

    return final_summary, nodes[-1]
