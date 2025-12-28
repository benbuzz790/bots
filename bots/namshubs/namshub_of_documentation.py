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


def invoke(bot: Bot, target_file: str | None = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the documentation generation namshub.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        target_file (str, optional): Path to the Python file to document.
                                     If not provided, attempts to extract from conversation.
        **kwargs: Additional keyword arguments

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # Execute the workflow
    if target_file:
        response = bot.respond(f"Generate documentation for {target_file}")
    else:
        response = bot.respond("Generate documentation for the target file")

    return response, bot.conversation
