from pathlib import Path
from typing import Any, List, Tuple
import bots
import bots.flows.functional_prompts as fp
from bots.foundation.base import Bot, ConversationNode
from bots.tools.terminal_tools import execute_powershell
def clone_and_edit(
    local_dir: Path, repo_name: str, task_prompt: str, bot: Bot = None
) -> Tuple[List[str], List[ConversationNode]]:
    """Clone a GitHub repository and allow a bot to work on it until
    completion.
    Use when you need to:
    - Clone a repository and perform iterative modifications
    - Let a bot work autonomously until it completes its task
    - Maintain conversation context throughout the editing process
    This function is a specialized version of clone_and_fp that uses the
    prompt_while pattern to enable iterative work on a repository until the
    bot stops using tools.
    Args:
        local_dir (Path): Relative path to location where repo will be cloned
        repo_name (str): Name of repo to clone (format: "owner/repository")
        task_prompt (str): Instructions for the bot's task
        bot (Bot, optional): Bot instance to use. If None, creates a new
            AnthropicBot with code_tools and terminal_tools added
    Returns:
        Tuple[List[str], List[ConversationNode]]: A tuple containing:
            - List of responses from the bot's work session
            - List of conversation nodes containing those responses
    Examples:
        >>> # Basic usage
        >>> responses, nodes = clone_and_edit(
        ...     Path("./repos"),
        ...     "owner/repo",
        ...     "Refactor the code to improve modularity"
        ... )
        >>>
        >>> # Using a pre-configured bot
        >>> custom_bot = AnthropicBot()
        >>> custom_bot.add_tools(my_custom_tools)
        >>> responses, nodes = clone_and_edit(
        ...     Path("./repos"),
        ...     "owner/repo",
        ...     "Apply custom analysis using my_custom_tools",
        ...     bot=custom_bot
        ... )
    """
    first_prompt = (
        f"I've cloned the repository {repo_name}. First, use view_dir with "
        f"target_extensions=['*'] to see all files, then {task_prompt}"
    )
    return clone_and_fp(
        local_dir=local_dir,
        repo_name=repo_name,
        functional_prompt=fp.prompt_while,
        kwargs={
            "first_prompt": first_prompt,
            "stop_condition": fp.conditions.tool_not_used,
            "continue_prompt": "ok",
        },
        bot=bot,
    )
def clone_and_fp(
    local_dir: Path,
    repo_name: str,
    functional_prompt: fp.FunctionalPrompt,
    kwargs: Any,
    bot: Bot = None,
) -> Tuple[List[str], List[ConversationNode]]:
    """Clone a GitHub repository and apply a functional prompt pattern to it.
    Use when you need to:
    - Clone a GitHub repository and immediately process it with a functional
      pattern
    - Apply complex reasoning patterns (chain, branch, tree_of_thought) to
      repo analysis
    - Maintain bot state for future operations on the same repository
    This function combines GitHub repository cloning with the flexibility of
    functional prompt patterns, allowing sophisticated analysis and
    modification of repository content using any of the patterns defined in
    functional_prompts.py.
    Args:
        local_dir (Path): Relative path to location where repo will be cloned
        repo_name (str): Name of repo to clone (format: "owner/repository")
        functional_prompt (fp.FunctionalPrompt): The functional pattern to
            apply (e.g., fp.chain, fp.branch, fp.tree_of_thought)
        kwargs (Any): Arguments to pass to the functional prompt function
        bot (Bot, optional): Bot instance to use. If None, creates a new
            AnthropicBot with code_tools and terminal_tools added
    Returns:
        Tuple[List[str], List[ConversationNode]]: A tuple containing:
            - List of responses from the functional prompt execution
            - List of conversation nodes containing those responses
    Examples:
        >>> # Using chain pattern to analyze a repository
        >>> responses, nodes = clone_and_fp(
        ...     Path("./repos"),
        ...     "owner/repo",
        ...     fp.chain,
        ...     {"prompts": [
        ...         "Analyze code structure",
        ...         "Identify potential issues",
        ...         "Suggest improvements"
        ...     ]}
        ... )
        >>>
        >>> # Using branch pattern for multi-perspective analysis
        >>> responses, nodes = clone_and_fp(
        ...     Path("./repos"),
        ...     "owner/repo",
        ...     fp.branch,
        ...     {"prompts": [
        ...         "Security analysis",
        ...         "Performance analysis",
        ...         "Maintainability analysis"
        ...     ]}
        ... )
    Note:
        - The bot's state is saved in the cloned repository directory
        - The saved bot includes full conversation history and tool states
        - The function uses gh cli for cloning - ensure it's installed and
          configured
    """
    local_dir = Path(local_dir)
    local_dir.mkdir(parents=True, exist_ok=True)
    clone_path = local_dir / repo_name.split("/")[-1]
    if not clone_path.exists():
        cmd = "gh repo clone " + repo_name + " " + str(clone_path)
        result = execute_powershell(cmd)
        if not (clone_path / ".git").exists():
            raise RuntimeError(f"Failed to clone repo: {result}")
    if bot is None:
        bot = bots.AnthropicBot()
        bot.add_tools(bots.tools.code_tools)
        bot.add_tools(bots.tools.terminal_tools)
    # Add initial context about repository location
    if not kwargs.get("first_prompt"):
        if isinstance(kwargs.get("prompts"), list):
            msg = (
                "I've cloned the repository "
                + repo_name
                + " to "
                + str(clone_path)
                + ". "
            )
            kwargs["prompts"][0] = msg + kwargs["prompts"][0]
    try:
        result = functional_prompt(bot, **kwargs)
        bot.save(str(clone_path.joinpath(f"{repo_name}_editor.bot")))
        return result
    except Exception as e:
        print(f"Error during functional prompt execution: {e}")
        raise
