"""Helper functions for creating namshubs.

This module provides common utilities for building namshub workflows,
including toolkit creation, prompt formatting, and workflow patterns.
"""

from typing import Callable, List, Tuple

from bots.flows import functional_prompts as fp
from bots.foundation.base import Bot, ConversationNode


def create_toolkit(bot: Bot, *tools) -> None:
    """Merge additional tools into bot's existing toolkit.

    This is the standard way to add tools to a bot's toolkit in a namshub.
    The new tools are added to the bot's existing tools rather than replacing them.

    Parameters:
        bot (Bot): The bot whose toolkit will be expanded
        *tools: Variable number of tool functions or modules to add

    Example:
        from bots.tools.code_tools import view, view_dir
        from bots.tools.python_edit import python_view

        create_toolkit(bot, view, view_dir, python_view)
    """
    # Simply use the bot's existing add_tools method which merges tools
    bot.add_tools(*tools)


def instruction_prompts(prompts: List[str]) -> List[str]:
    """Prefix each prompt with 'INSTRUCTION: ' for better attention.

    The all-caps INSTRUCTION prefix helps the bot focus on each step
    and pairs well with the instruction_continue_prompt.

    Prevents duplicate prefixes if prompt already starts with "INSTRUCTION: ".

    Parameters:
        prompts (List[str]): List of prompt strings

    Returns:
        List[str]: Prompts with 'INSTRUCTION: ' prefix (no duplicates)

    Example:
        prompts = instruction_prompts([
            "Read the file",
            "Analyze the code",
            "Write a summary"
        ])
        # Returns: ["INSTRUCTION: Read the file", ...]

        # Prevents duplicates:
        prompts = instruction_prompts([
            "INSTRUCTION: Already prefixed",
            "Not prefixed"
        ])
        # Returns: ["INSTRUCTION: Already prefixed", "INSTRUCTION: Not prefixed"]
    """
    result = []
    for prompt in prompts:
        if prompt.startswith("INSTRUCTION: "):
            result.append(prompt)
        else:
            result.append(f"INSTRUCTION: {prompt}")
    return result


def instruction_continue_prompt() -> str:
    """Return the standard continue prompt for INSTRUCTION-based workflows.

    This prompt keeps the bot focused on completing the current instruction
    before moving to the next one.

    Returns:
        str: The continue prompt string

    Example:
        responses, nodes = fp.chain_while(
            bot,
            instruction_prompts(my_prompts),
            stop_condition=fp.conditions.tool_not_used,
            continue_prompt=instruction_continue_prompt()
        )
    """
    return "Focus on the previous INSTRUCTION. Only move on when explicitly instructed."


def chain_workflow(
    bot: Bot,
    prompts: List[str],
    use_instruction_pattern: bool = True,
    stop_condition: Callable[[Bot], bool] = None,
    callback: Callable = None,
) -> Tuple[List[str], List[ConversationNode]]:
    """Execute a chain_while workflow with sensible defaults.

    This is a convenience wrapper around fp.chain_while that applies
    the INSTRUCTION pattern by default and uses standard settings.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        prompts (List[str]): List of workflow step prompts
        use_instruction_pattern (bool): Whether to use INSTRUCTION prefix
                                        and continue prompt (default: True)
        stop_condition (Callable): Condition to stop iteration on each step
                                   (default: tool_not_used)
        callback (Callable): Optional callback after each response

    Returns:
        Tuple[List[str], List[ConversationNode]]: Responses and nodes

    Example:
        responses, nodes = chain_workflow(bot, [
            "Read the target file",
            "Analyze for issues",
            "Write a summary"
        ])
    """
    if stop_condition is None:
        stop_condition = fp.conditions.tool_not_used

    if use_instruction_pattern:
        prompts = instruction_prompts(prompts)
        continue_prompt = instruction_continue_prompt()
    else:
        continue_prompt = "ok"

    return fp.chain_while(bot, prompts, stop_condition=stop_condition, continue_prompt=continue_prompt, callback=callback)


def simple_workflow(bot: Bot, prompts: List[str], callback: Callable = None) -> Tuple[List[str], List[ConversationNode]]:
    """Execute a simple chain workflow without iteration.

    Use this when you want a straightforward sequence of prompts
    without iteration on each step.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        prompts (List[str]): List of workflow step prompts
        callback (Callable): Optional callback after each response

    Returns:
        Tuple[List[str], List[ConversationNode]]: Responses and nodes

    Example:
        responses, nodes = simple_workflow(bot, [
            "Read the file",
            "Summarize it"
        ])
    """
    return fp.chain(bot, prompts, callback=callback)


def iterative_workflow(
    bot: Bot,
    initial_prompt: str,
    continue_prompt: str = "ok",
    stop_condition: Callable[[Bot], bool] = None,
    callback: Callable = None,
) -> Tuple[List[str], List[ConversationNode]]:
    """Execute an iterative workflow with a single prompt.

    Use this when you want the bot to work on a single task iteratively
    until a condition is met.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        initial_prompt (str): The initial task prompt
        continue_prompt (str): Prompt for each iteration (default: "ok")
        stop_condition (Callable): When to stop iterating
                                   (default: tool_not_used)
        callback (Callable): Optional callback after each response

    Returns:
        Tuple[List[str], List[ConversationNode]]: Responses and nodes

    Example:
        responses, nodes = iterative_workflow(
            bot,
            "Fix all linting issues in the codebase",
            stop_condition=fp.conditions.tool_not_used
        )
    """
    if stop_condition is None:
        stop_condition = fp.conditions.tool_not_used

    return fp.prompt_while(
        bot, initial_prompt, continue_prompt=continue_prompt, stop_condition=stop_condition, callback=callback
    )


def validate_required_params(**params) -> Tuple[bool, str]:
    """Validate that required parameters are provided.

    Use this at the start of your invoke function to check parameters.

    Parameters:
        **params: Keyword arguments where key is param name and value
                 is the param value (or None if not provided)

    Returns:
        Tuple[bool, str]: (is_valid, error_message)
                         If valid, error_message is empty string

    Example:
        valid, error = validate_required_params(
            target_file=target_file,
            pr_number=pr_number
        )
        if not valid:
            return (error, bot.conversation)
    """
    missing = [name for name, value in params.items() if value is None]

    if missing:
        param_list = ", ".join(missing)
        return False, f"Error: Missing required parameter(s): {param_list}"

    return True, ""


def format_final_summary(workflow_name: str, step_count: int, final_response: str, max_length: int = 200) -> str:
    """Format a standard final summary for namshub completion.

    Parameters:
        workflow_name (str): Name of the workflow (e.g., "Code Review")
        step_count (int): Number of steps completed
        final_response (str): The final response text
        max_length (int): Maximum length of final_response excerpt

    Returns:
        str: Formatted summary string

    Example:
        summary = format_final_summary(
            "Code Review",
            len(responses),
            responses[-1]
        )
    """
    excerpt = final_response[:max_length]
    if len(final_response) > max_length:
        excerpt += "..."

    return f"{workflow_name} workflow completed.\n" f"Processed {step_count} steps.\n" f"Final status: {excerpt}"
