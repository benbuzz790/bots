"""Automated documentation review and improvement system.
Use this module when you need to automatically review and improve code-level
documentation across a Python project using LLM-powered bots.
The module:
1. Finds all Python files in the project (excluding tools and test directories)
2. Creates multiple bots to review documentation in parallel
3. Uses chain_while to ensure thorough documentation review
4. Makes direct improvements to documentation using Python editing tools
NOTE: This is an expensive operation. For a project this size, expect $20 - $40
in api costs
"""

import os
import textwrap
from typing import List, Tuple

from bots.flows import functional_prompts as fp
from bots.foundation.anthropic_bots import AnthropicBot
from bots.foundation.base import Bot, ConversationNode, Engines
from bots.tools import code_tools, python_editing_tools


def find_python_files(
    start_path: str,
    exclude_list: List[str] = [],
) -> List[str]:
    """Recursively find all Python files in a directory with exclusions.
    Use when you need to gather Python files for documentation review while
    excluding tool-related files and specific directories that don't need
    documentation review.
    Parameters:
        start_path (str): Root directory to start search from. Should be the
            project root.
        exclude_list (List[str]): list of subdirectory names to exclude from
            search. (default: [])
    Returns:
        List[str]: List of absolute paths to Python files that should be
            reviewed
    Excludes:
        - tools and files with 'tool' in the name
        - issue103 directory
        - project_tree directory
        - benbuzz790 directory
        - private_tests directory
    """
    excluded_dirs = exclude_list
    python_files = []
    for root, dirs, files in os.walk(start_path):
        dirs[:] = [d for d in dirs if d not in excluded_dirs]
        for file in files:
            if file.endswith(".py"):
                python_files.append(os.path.join(root, file))
    return python_files


def create_doc_review_bot(num: int) -> Bot:
    """Create and configure a bot specialized for documentation review.
    Use when you need to create a new documentation review bot instance with
    appropriate tools and context for reviewing Python documentation.
    Parameters:
        num (int): Unique identifier for the bot instance, used in naming
    Returns:
        Bot: Configured AnthropicBot instance with:
            - Documentation specialist role
            - Code review tools
            - Python editing tools
            - Appropriate system message
    """
    bot = AnthropicBot(
        model_engine=Engines.CLAUDE35_SONNET_20241022,
        temperature=0.2,
        name=f"DocReviewer{num}",
        role="Documentation Specialist",
        role_description="Reviews documentation for python files",
        autosave=False,
    )
    bot.add_tools(code_tools)
    bot.add_tools(python_editing_tools)
    bot.set_system_message(
        "You are an expert in Python documentation standards and best "
        "practices. Your task is to review and improve code documentation "
        "using Python's standard documentation patterns including type hints, "
        "and docstrings. You do not change code or add features, you strictly "
        "document. When you find docs lacking, use the available tools to fix "
        "them directly."
    )
    return bot


def review_file_documentation(
    bot: Bot,
) -> Tuple[List[str], List[ConversationNode]]:
    """Execute a thorough documentation review process for a Python file.
    Use when you need to systematically review and improve documentation in a
    Python file using a chain of prompts and automated fixes.
    Parameters:
        bot (Bot): Configured documentation review bot that has been
            initialized with a target file path in its conversation context
    Returns:
        Tuple[List[str], List[ConversationNode]]:
            - List of responses from the documentation review process
            - List of conversation nodes tracking the review history
    Note:
        The bot must be initialized with a TARGET FILE path before calling
        this function. The review checks for:
        1. Module-level docstring
        2. Class docstrings
        3. Method/function docstrings with parameters and return types
    """
    prompts = [
        "First, let's read the project context to understand documentation "
        "standards. Please read bot_context.txt and README.md.",
        ("Now, let's examine the TARGET FILE. Use the view tool to " "read this file."),
        textwrap.dedent(
            """
                    Review the file's documentation and make improvements
                    where needed. For each issue you find, use the appropriate
                    tools to fix it directly. Check for:
                    1. Module-level docstring:
                    - Clear description of the module's purpose
                    2. Class docstrings:
                    - Class purpose and behavior
                    - Important attributes
                    3. Method/function docstrings:
                    - Clear description of what the function does
                    - All parameters documented with types
                    - Return value documented with type
                    """
        ),
        ("Review the TARGET FILE one final time to ensure all " "documentation is complete and consistent."),
    ]
    return fp.chain_while(
        bot,
        prompts,
        stop_condition=fp.conditions.tool_not_used_debug,
        continue_prompt="ok",
    )


def main():
    """Coordinate parallel documentation review across all Python files.
    Use when you need to execute a full project documentation review that:
    1. Identifies all relevant Python files
    2. Creates parallel bot instances
    3. Executes documentation review for each file
    4. Reports progress
    """
    project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", ".."))
    python_files = find_python_files(project_root)
    print(f"Found {len(python_files)} Python files to review")
    for file in python_files:
        print(f"- {file}")
    bots = [create_doc_review_bot(n) for n, _ in enumerate(python_files)]
    for bot, file in zip(bots, python_files):
        bot.respond(
            f"NOTE: The TARGET FILE is {file}. Respond with exclusively 'ok' "
            f"if you understand. Further instructions are incoming."
        )
    fp.par_dispatch(bots, review_file_documentation)


if __name__ == "__main__":
    main()
