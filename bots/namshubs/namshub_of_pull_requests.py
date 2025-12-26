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
   Reference the CI/CD workflow at .github/workflows/pr-checks.yml for the exact commands.

   For linting issues (code-quality job):
   - Run: python -m bots.dev.remove_boms
   - Run: black .
   - Run: isort .

   For test failures (tests job):
   - Read the failing test file
   - Understand what's being tested
   - Fix the code or test as appropriate
   - Make surgical fixes

5. VERIFY FIXES
   Use the same checks as CI/CD (see .github/workflows/pr-checks.yml):
   - Run: python -m bots.dev.remove_boms
   - Run: black --check --diff .
   - Run: isort --check-only --diff .
   - Run: flake8 . --count --statistics --show-source
   - For tests: pytest tests/ -n 12 --tb=short -v --maxfail=10

6. POST UPDATE
   - Always post a comment: gh pr comment {pr_number} --body "## Update: [summary of changes]"

IMPORTANT NOTES:
- Run linters WITHOUT output truncation
- Get RUN_ID from the URL in gh pr checks output
- Wait 5 minutes between checks if actions are still running
- Always post an update comment when done
- Reference .github/workflows/pr-checks.yml for the authoritative CI/CD commands
"""
    bot.set_system_message(system_message.strip())


def invoke(bot: Bot, pr_number: str | None = None, **kwargs) -> Tuple[str, ConversationNode]:
    """Execute the PR workflow namshub.

    This function is called by invoke_namshub tool.

    Parameters:
        bot (Bot): The bot to execute the workflow on
        pr_number (str): The PR number to work on
        **kwargs: Additional keyword arguments

    Returns:
        Tuple[str, ConversationNode]: Final response and conversation node
    """
    if pr_number is None:
        return "Error: pr_number is required", bot.conversation.current_node

    # Set the system message for PR workflow
    _set_pr_system_message(bot, pr_number)

    # Execute the workflow steps
    prompts = [
        f"Check the status of PR #{pr_number}. Run 'gh pr checks {pr_number}' to see the CI/CD status.",
        "Extract the RUN_ID from the URL in the output. Check if the actions are still running. If they are still running, sleep for 5 minutes using either: execute_python with code 'import time; time.sleep(300)' OR execute_powershell with 'Start-Sleep -Seconds 300'. Then run 'gh run view <RUN_ID> --log-failed' to see what failed.",
        f"Try to extract any coderabbit comments: python -m bots.dev.pr_comment_parser <REPO> {pr_number}. Read and understand the AI prompts.",
        "Use branch_self to fix the identified issues. For linting: run black, isort, and remove_boms. For test failures: read the test file, understand the issue, and fix it. For coderabbit comments, make the suggested change unless it seems at odds with the code intent.",
        f"Post an update comment: gh pr comment {pr_number} --body '## Update: [summary of changes]'",
    ]

    for prompt in prompts:
        response, node = bot.respond(prompt)
        if "error" in response.lower() or "failed" in response.lower():
            return f"Workflow stopped due to error: {response}", node

    return "PR workflow completed successfully", bot.conversation.current_node
