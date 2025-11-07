"""PR workflow namshub - handles GitHub pull request CI/CD workflow.

This namshub transforms the bot into a PR management specialist that:
1. Checks PR status and CI/CD pipeline results
2. Analyzes failed tests and linting issues
3. Extracts CodeRabbit AI prompts for actionable feedback
4. Fixes identified issues using appropriate tools
5. Posts update comments to the PR

The bot is equipped with terminal tools, code viewing, and Python editing
capabilities to diagnose and fix issues.
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
from bots.tools.python_execution_tool import execute_python
from bots.tools.self_tools import branch_self
from bots.tools.terminal_tools import execute_powershell


def _set_pr_system_message(bot: Bot, pr_number: str) -> None:
    """Set specialized system message for PR workflow.

    Parameters:
        bot (Bot): The bot to configure
        pr_number (str): The PR number being worked on
    """
    system_message = f"""You are a coding agent working on PR #{pr_number}.

Your workflow:

1. CHECK STATUS
   - Run: gh pr checks {pr_number}
   - Get RUN_ID from the URL in the output
   - If actions are still running, wait 5 minutes before checking again:
     * Python: execute_python with code: import time; time.sleep(300)
     * PowerShell: Start-Sleep -Seconds 300
   - Run: gh run view <RUN_ID> --log-failed

2. ANALYZE FAILURES
   - Look for patterns: error, FAILED, would reformat, AssertionError, E[0-9]{{3}}, F[0-9]{{3}}
   - Run: gh run view <RUN_ID> --log | Select-String -Pattern
     "error|FAILED|would reformat|AssertionError|E[0-9]{{3}}|F[0-9]{{3}}" -Context 2,2

3. EXTRACT CODE RABBIT PROMPTS
   - Run: python -m bots.dev.pr_comment_parser <REPO> {pr_number}
   - Follow the actionable prompts from CodeRabbit

4. FIX ISSUES
   Linting issues:
   - Run formatters: black . && isort . && python -m bots.dev.remove_boms
   - Check: black --check --diff . && isort --check-only --diff . &&
     flake8 . --count --statistics --show-source

   Test failures:
   - Read the failing test file
   - Understand what's being tested
   - Fix the code or test as appropriate
   - Make surgical fixes

5. POST UPDATE
   - Always post a comment: gh pr comment {pr_number} --body "## Update: [summary of changes]"

IMPORTANT NOTES:
- Run linters WITHOUT output truncation
- Get RUN_ID from the URL in gh pr checks output
- Wait 5 minutes between checks if actions are still running
- Always post an update comment when done
- Version mismatch: CI may have different linter versions, update local:
  pip install --upgrade black isort flake8
"""
    bot.set_system_message(system_message.strip())


def invoke(bot: Bot, pr_number: str = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the PR workflow namshub.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        pr_number (str, optional): The PR number to work on.
                                   If not provided, attempts to extract from conversation.
        **kwargs: Additional parameters (unused, for compatibility)

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    # If pr_number not provided, try to extract from conversation context
    if not pr_number:
        if bot.conversation.parent and bot.conversation.parent.content:
            content = bot.conversation.parent.content
            import re
            pr_patterns = [
                r'#(\d+)',
                r'PR\s*#?(\d+)',
                r'pull request\s*#?(\d+)',
            ]
            for pattern in pr_patterns:
                match = re.search(pattern, content, re.IGNORECASE)
                if match:
                    pr_number = match.group(1)
                    break

    # Validate required parameters
    valid, error = validate_required_params(pr_number=pr_number)
    if not valid:
        return (
            error + "\nUsage: invoke_namshub('namshub_of_pull_requests', pr_number='123')",
            bot.conversation
        )

    # Configure the bot for PR workflow
    create_toolkit(bot, branch_self, execute_powershell, execute_python, view, view_dir, python_view, python_edit)
    _set_pr_system_message(bot, pr_number)

    # Define the PR workflow
    workflow_prompts = [
        f"Check the status of PR #{pr_number}. Run 'gh pr checks {pr_number}' to see the CI/CD status.",

        "Extract the RUN_ID from the URL in the output. Check if the actions are still running. "
        "If they are still running, sleep for 5 minutes using either: "
        "execute_python with code 'import time; time.sleep(300)' OR "
        "execute_powershell with 'Start-Sleep -Seconds 300'. "
        "Then run 'gh run view <RUN_ID> --log-failed' to see what failed.",

        "View the failures. Use Select-String to filter for errors: "
        "gh run view <RUN_ID> --log | Select-String -Pattern "
        "\"error|FAILED|would reformat|AssertionError|E[0-9]{3}|F[0-9]{3}\" -Context 2,2",

        "Try to extract any coderabbit comments: python -m bots.dev.pr_comment_parser <REPO> "
        f"{pr_number}. Read and understand the AI prompts.",

        "Use branch_self to fix the identified issues. For linting: run black, isort, and remove_boms. "
        "For test failures: read the test file, understand the issue, and fix it. For coderabbit comments, "
        "make the suggested change unless it seems at odds with the code intent. You should branch "
        "for each task or related group of tasks and clear everything up in parallel. You branch_self tool "
        "is pretty powerful. You should use a clear definition of done to keep branches on task, and specify "
        "reporting requirements for their last text message (not files), because the text of the last message "
        "'bubbles up' to you. Note that each branch is a copy of you with all your context, so you do not need "
        "to be too specific with your task description - but you do with def of done and reporting reqs. Take "
        "your time and work step by step. Be sure to gather sufficient context before implementing a fix.",

        "Verify your fixes, then run the linters again to confirm: black --check --diff . && "
        "isort --check-only --diff . && flake8 . --count --statistics --show-source",

        f"Post an update comment to PR #{pr_number} summarizing what you fixed: "
        f"gh pr comment {pr_number} --body \"## Update: [your summary here]\".",

        "Finally, push. Thanks for your hard work."
    ]

    # Execute the workflow using chain_workflow with INSTRUCTION pattern
    responses, nodes = chain_workflow(bot, workflow_prompts)

    # Return the final response
    final_summary = format_final_summary(
        f"PR #{pr_number}",
        len(responses),
        responses[-1]
    )

    return final_summary, nodes[-1]
